import re
from typing import Optional

from composition_engine.schema import (
    AnchorPoint,
    AudioClip,
    ImageOverlay,
    Position,
    TextOverlay,
    TransitionType,
    VideoClip,
)
from render_worker.parser import (
    AudioStage,
    ImageOverlayStage,
    RenderPlan,
    TextOverlayStage,
    VideoStage,
)

_XFADE_MAP = {
    TransitionType.fade: "fade",
    TransitionType.crossfade: "fade",
    TransitionType.dissolve: "dissolve",
    TransitionType.slide: "slideright",
}

# Near-zero duration used for cut transitions in an xfade chain
_CUT_XFADE_DURATION = 0.001


def _safe(s: str) -> str:
    """Sanitize a string for use as an FFmpeg filter label."""
    return re.sub(r"[^a-zA-Z0-9]", "_", s)


def _overlay_xy(position: Position, video_width: int, video_height: int) -> tuple[str, str]:
    """Return FFmpeg overlay filter x/y expressions for the given anchor."""
    px, py = int(position.x), int(position.y)
    anchor = position.anchor
    if anchor == AnchorPoint.top_left:
        return str(px), str(py)
    elif anchor == AnchorPoint.top:
        return f"(main_w-overlay_w)/2+{px}", str(py)
    elif anchor == AnchorPoint.top_right:
        return f"main_w-overlay_w+{px}", str(py)
    elif anchor == AnchorPoint.left:
        return str(px), f"(main_h-overlay_h)/2+{py}"
    elif anchor == AnchorPoint.center:
        return f"(main_w-overlay_w)/2+{px}", f"(main_h-overlay_h)/2+{py}"
    elif anchor == AnchorPoint.right:
        return f"main_w-overlay_w+{px}", f"(main_h-overlay_h)/2+{py}"
    elif anchor == AnchorPoint.bottom_left:
        return str(px), f"main_h-overlay_h+{py}"
    elif anchor == AnchorPoint.bottom:
        return f"(main_w-overlay_w)/2+{px}", f"main_h-overlay_h+{py}"
    elif anchor == AnchorPoint.bottom_right:
        return f"main_w-overlay_w+{px}", f"main_h-overlay_h+{py}"
    return str(px), str(py)


def _drawtext_xy(position: Position, video_width: int, video_height: int) -> tuple[str, str]:
    """Return FFmpeg drawtext x/y expressions for the given anchor."""
    px, py = int(position.x), int(position.y)
    anchor = position.anchor
    if anchor == AnchorPoint.top_left:
        return str(px), str(py)
    elif anchor == AnchorPoint.top:
        return f"(w-tw)/2+{px}", str(py)
    elif anchor == AnchorPoint.top_right:
        return f"w-tw+{px}", str(py)
    elif anchor == AnchorPoint.left:
        return str(px), f"(h-lh)/2+{py}"
    elif anchor == AnchorPoint.center:
        return f"(w-tw)/2+{px}", f"(h-lh)/2+{py}"
    elif anchor == AnchorPoint.right:
        return f"w-tw+{px}", f"(h-lh)/2+{py}"
    elif anchor == AnchorPoint.bottom_left:
        return str(px), f"h-lh+{py}"
    elif anchor == AnchorPoint.bottom:
        return f"(w-tw)/2+{px}", f"h-lh+{py}"
    elif anchor == AnchorPoint.bottom_right:
        return f"w-tw+{px}", f"h-lh+{py}"
    return str(px), str(py)


class FilterGraphBuilder:
    def build_command(
        self,
        plan: RenderPlan,
        output_path: str,
        input_files: dict[str, str],
    ) -> list[str]:
        comp = plan.composition
        width = comp.resolution.width
        height = comp.resolution.height
        fps = comp.fps

        video_stages = [s for s in plan.stages if isinstance(s, VideoStage)]
        audio_stages = [s for s in plan.stages if isinstance(s, AudioStage)]
        text_stages = [s for s in plan.stages if isinstance(s, TextOverlayStage)]
        image_stages = [s for s in plan.stages if isinstance(s, ImageOverlayStage)]

        if not video_stages:
            raise ValueError("Composition has no video tracks — cannot render")

        cmd = ["ffmpeg", "-y"]
        input_index: dict[str, int] = {}

        def add_input(src: str) -> int:
            local = input_files.get(src, src)
            if local not in input_index:
                n = len(input_index)
                cmd.extend(["-i", local])
                input_index[local] = n
            return input_index[local]

        # Register inputs in order: video, audio, image overlays
        primary_stage = video_stages[0]
        for clip in primary_stage.clips:
            add_input(clip.src)
        for stage in audio_stages:
            for clip in stage.clips:
                add_input(clip.src)
        for stage in image_stages:
            for overlay in stage.overlays:
                add_input(overlay.src)

        parts: list[str] = []

        # --- Build primary video stream ---
        clips = primary_stage.clips
        vclip_labels: list[str] = []
        clip_durations: list[float] = []

        for clip in clips:
            idx = input_index[input_files.get(clip.src, clip.src)]
            duration = clip.endOnTimeline - clip.startOnTimeline
            trim_start = clip.trimIn or 0.0
            trim_end = clip.trimOut if clip.trimOut is not None else (trim_start + duration)
            lbl = f"vc_{_safe(clip.id)}"

            parts.append(
                f"[{idx}:v]trim=start={trim_start:.6f}:end={trim_end:.6f},"
                f"setpts=PTS-STARTPTS[{lbl}]"
            )
            vclip_labels.append(lbl)
            clip_durations.append(trim_end - trim_start)

        if len(clips) == 1:
            current_v = vclip_labels[0]
        else:
            has_xfade = any(
                clips[i].transition and clips[i].transition.type != TransitionType.cut
                for i in range(1, len(clips))
            )

            if not has_xfade:
                concat_in = "".join(f"[{lbl}]" for lbl in vclip_labels)
                parts.append(f"{concat_in}concat=n={len(clips)}:v=1:a=0[concat_v]")
                current_v = "concat_v"
            else:
                cur = vclip_labels[0]
                cumulative_dur = clip_durations[0]
                xf_count = 0
                for i in range(1, len(clips)):
                    clip = clips[i]
                    next_lbl = vclip_labels[i]
                    out_lbl = f"xf{xf_count}"

                    if clip.transition and clip.transition.type != TransitionType.cut:
                        xfade_type = _XFADE_MAP.get(clip.transition.type, "fade")
                        td = clip.transition.duration or 0.5
                    else:
                        xfade_type = "fade"
                        td = _CUT_XFADE_DURATION

                    offset = max(0.0, cumulative_dur - td)
                    parts.append(
                        f"[{cur}][{next_lbl}]xfade=transition={xfade_type}:"
                        f"duration={td:.3f}:offset={offset:.3f}[{out_lbl}]"
                    )
                    cumulative_dur += clip_durations[i] - td
                    cur = out_lbl
                    xf_count += 1

                current_v = cur

        # --- Dedicated audio tracks ---
        audio_labels: list[str] = []

        for ai, stage in enumerate(audio_stages):
            track_labels: list[str] = []

            for clip in stage.clips:
                idx = input_index[input_files.get(clip.src, clip.src)]
                duration = clip.endOnTimeline - clip.startOnTimeline
                lbl = f"ac_{_safe(clip.id)}"

                chain = (
                    f"[{idx}:a]atrim=start=0:end={duration:.6f},"
                    f"asetpts=PTS-STARTPTS"
                )

                if clip.volume != 1.0:
                    chain += f",volume={clip.volume:.4f}"
                if clip.fadeIn:
                    chain += f",afade=t=in:st=0:d={clip.fadeIn:.3f}"
                if clip.fadeOut:
                    fo_start = max(0.0, duration - clip.fadeOut)
                    chain += f",afade=t=out:st={fo_start:.3f}:d={clip.fadeOut:.3f}"
                if clip.startOnTimeline > 0.0:
                    delay_ms = int(clip.startOnTimeline * 1000)
                    chain += f",adelay={delay_ms}|{delay_ms}"

                chain += f"[{lbl}]"
                parts.append(chain)
                track_labels.append(lbl)

            if len(track_labels) == 1:
                audio_labels.append(track_labels[0])
            elif len(track_labels) > 1:
                concat_in = "".join(f"[{l}]" for l in track_labels)
                track_lbl = f"ta_{_safe(stage.track_id)}"
                parts.append(
                    f"{concat_in}concat=n={len(track_labels)}:v=0:a=1[{track_lbl}]"
                )
                audio_labels.append(track_lbl)

        # Mix all audio streams
        final_audio: Optional[str] = None
        if len(audio_labels) == 1:
            final_audio = audio_labels[0]
        elif len(audio_labels) > 1:
            mix_in = "".join(f"[{l}]" for l in audio_labels)
            parts.append(f"{mix_in}amix=inputs={len(audio_labels)}:duration=first[amix]")
            final_audio = "amix"

        # --- Image overlays (applied in z-order) ---
        for ii, stage in enumerate(image_stages):
            for ji, overlay in enumerate(stage.overlays):
                idx = input_index[input_files.get(overlay.src, overlay.src)]
                src_lbl = f"img_in_{ii}_{ji}"
                overlay_input = src_lbl
                out_lbl = f"vid_img_{ii}_{ji}"

                # Always create a labeled stream to avoid "already connected" errors
                if overlay.width or overlay.height:
                    w = int(overlay.width) if overlay.width else -1
                    h = int(overlay.height) if overlay.height else -1
                    parts.append(f"[{idx}:v]scale={w}:{h}[{src_lbl}]")
                else:
                    parts.append(f"[{idx}:v]scale=iw:ih[{src_lbl}]")

                if overlay.opacity < 1.0:
                    opacity_lbl = f"img_op_{ii}_{ji}"
                    parts.append(
                        f"[{overlay_input}]format=rgba,"
                        f"colorchannelmixer=aa={overlay.opacity:.3f}[{opacity_lbl}]"
                    )
                    overlay_input = opacity_lbl

                x, y = _overlay_xy(overlay.position, width, height)
                enable = (
                    f"between(t,{overlay.startOnTimeline:.3f},{overlay.endOnTimeline:.3f})"
                )
                parts.append(
                    f"[{current_v}][{overlay_input}]overlay={x}:{y}:"
                    f"enable='{enable}'[{out_lbl}]"
                )
                current_v = out_lbl

        # --- Text overlays (applied on top) ---
        for ti, stage in enumerate(text_stages):
            for tj, overlay in enumerate(stage.overlays):
                x, y = _drawtext_xy(overlay.position, width, height)
                out_lbl = f"vid_txt_{ti}_{tj}"

                fontsize = 24
                fontcolor = "white"
                if overlay.style:
                    if overlay.style.fontSize:
                        fontsize = int(overlay.style.fontSize)
                    if overlay.style.color:
                        raw = overlay.style.color.lstrip("#")
                        fontcolor = f"0x{raw}" if len(raw) in (6, 8) else overlay.style.color

                safe_text = (
                    overlay.text
                    .replace("\\", "\\\\")
                    .replace("'", "\\'")
                    .replace(":", "\\:")
                )
                enable = (
                    f"between(t,{overlay.startOnTimeline:.3f},{overlay.endOnTimeline:.3f})"
                )
                drawtext = (
                    f"drawtext=text='{safe_text}':x={x}:y={y}:"
                    f"fontsize={fontsize}:fontcolor={fontcolor}:enable='{enable}'"
                )
                parts.append(f"[{current_v}]{drawtext}[{out_lbl}]")
                current_v = out_lbl

        # --- Assemble final command ---
        cmd += ["-filter_complex", ";".join(parts)]
        cmd += ["-map", f"[{current_v}]"]
        if final_audio:
            cmd += ["-map", f"[{final_audio}]"]

        cmd += [
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "medium",
            "-s", f"{width}x{height}",
            "-r", str(fps),
        ]
        if final_audio:
            cmd += ["-c:a", "aac", "-b:a", "192k"]

        cmd.append(output_path)
        return cmd
