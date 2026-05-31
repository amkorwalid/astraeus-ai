import pytest

from composition_engine.schema import (
    AnchorPoint,
    AudioClip,
    Composition,
    ImageOverlay,
    Position,
    Resolution,
    TextOverlay,
    TextStyle,
    Track,
    TrackType,
    Transition,
    TransitionType,
    VideoClip,
)
from render_worker.filter_graph import FilterGraphBuilder
from render_worker.parser import parse_composition


def _comp(*tracks, width=1920, height=1080, fps=30, duration=10.0) -> Composition:
    return Composition(
        resolution=Resolution(width=width, height=height),
        fps=fps,
        duration=duration,
        tracks=list(tracks),
    )


def _build(comp, output="/tmp/out.mp4", input_files=None) -> list[str]:
    plan = parse_composition(comp)
    files = input_files or {clip.src: f"/tmp/{clip.id}.mp4"
                            for t in comp.tracks for clip in t.clips
                            if hasattr(clip, "src")}
    return FilterGraphBuilder().build_command(plan, output, files)


# ── Basic structure ────────────────────────────────────────────────────────────

def test_no_video_raises():
    comp = _comp()
    plan = parse_composition(comp)
    with pytest.raises(ValueError, match="no video tracks"):
        FilterGraphBuilder().build_command(plan, "/tmp/out.mp4", {})


def test_output_path_is_last_arg():
    clip = VideoClip(id="c1", src="s://c.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track), output="/custom/out.mp4",
                 input_files={"s://c.mp4": "/tmp/c.mp4"})
    assert cmd[-1] == "/custom/out.mp4"


def test_ffmpeg_is_first_arg():
    clip = VideoClip(id="c1", src="s://c.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track), input_files={"s://c.mp4": "/tmp/c.mp4"})
    assert cmd[0] == "ffmpeg"


def test_overwrite_flag_present():
    clip = VideoClip(id="c1", src="s://c.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track), input_files={"s://c.mp4": "/tmp/c.mp4"})
    assert "-y" in cmd


def test_codec_libx264_present():
    clip = VideoClip(id="c1", src="s://c.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track), input_files={"s://c.mp4": "/tmp/c.mp4"})
    assert "libx264" in cmd


# ── Single clip ────────────────────────────────────────────────────────────────

def test_single_clip_filter_complex_has_trim():
    clip = VideoClip(id="c1", src="s://c.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track), input_files={"s://c.mp4": "/tmp/c.mp4"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "trim" in fc
    assert "setpts=PTS-STARTPTS" in fc


def test_single_clip_with_trimin():
    clip = VideoClip(id="c1", src="s://c.mp4",
                     startOnTimeline=0.0, endOnTimeline=5.0, trimIn=2.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track), input_files={"s://c.mp4": "/tmp/c.mp4"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "trim=start=2.0" in fc or "trim=start=2." in fc


# ── Multiple clips ─────────────────────────────────────────────────────────────

def test_two_cut_clips_use_concat():
    clips = [
        VideoClip(id="c1", src="s://c1.mp4", startOnTimeline=0.0, endOnTimeline=5.0),
        VideoClip(id="c2", src="s://c2.mp4", startOnTimeline=5.0, endOnTimeline=10.0),
    ]
    track = Track(id="t1", type=TrackType.video, clips=clips)
    cmd = _build(_comp(track),
                 input_files={"s://c1.mp4": "/tmp/c1.mp4", "s://c2.mp4": "/tmp/c2.mp4"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "concat" in fc
    assert "xfade" not in fc


def test_crossfade_transition_uses_xfade():
    clips = [
        VideoClip(id="c1", src="s://c1.mp4", startOnTimeline=0.0, endOnTimeline=5.0),
        VideoClip(
            id="c2", src="s://c2.mp4", startOnTimeline=5.0, endOnTimeline=10.0,
            transition=Transition(type=TransitionType.crossfade, duration=0.5),
        ),
    ]
    track = Track(id="t1", type=TrackType.video, clips=clips)
    cmd = _build(_comp(track),
                 input_files={"s://c1.mp4": "/tmp/c1.mp4", "s://c2.mp4": "/tmp/c2.mp4"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "xfade" in fc
    assert "fade" in fc


def test_xfade_offset_is_first_clip_duration_minus_transition():
    clips = [
        VideoClip(id="c1", src="s://c1.mp4", startOnTimeline=0.0, endOnTimeline=10.0),
        VideoClip(
            id="c2", src="s://c2.mp4", startOnTimeline=10.0, endOnTimeline=20.0,
            transition=Transition(type=TransitionType.fade, duration=1.0),
        ),
    ]
    track = Track(id="t1", type=TrackType.video, clips=clips)
    cmd = _build(_comp(track, duration=20.0),
                 input_files={"s://c1.mp4": "/tmp/c1.mp4", "s://c2.mp4": "/tmp/c2.mp4"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    # offset = 10 - 1 = 9.0
    assert "offset=9.000" in fc


# ── Audio ──────────────────────────────────────────────────────────────────────

def test_audio_track_maps_audio():
    v_clip = VideoClip(id="v1", src="s://v.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    a_clip = AudioClip(id="a1", src="s://a.mp3", startOnTimeline=0.0, endOnTimeline=5.0)
    tracks = [
        Track(id="tv", type=TrackType.video, clips=[v_clip]),
        Track(id="ta", type=TrackType.audio, clips=[a_clip]),
    ]
    cmd = _build(_comp(*tracks),
                 input_files={"s://v.mp4": "/tmp/v.mp4", "s://a.mp3": "/tmp/a.mp3"})
    assert "-map" in cmd
    cmd_str = " ".join(cmd)
    assert "aac" in cmd_str


def test_audio_volume_applied():
    v_clip = VideoClip(id="v1", src="s://v.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    a_clip = AudioClip(id="a1", src="s://a.mp3", startOnTimeline=0.0, endOnTimeline=5.0,
                       volume=0.5)
    tracks = [
        Track(id="tv", type=TrackType.video, clips=[v_clip]),
        Track(id="ta", type=TrackType.audio, clips=[a_clip]),
    ]
    cmd = _build(_comp(*tracks),
                 input_files={"s://v.mp4": "/tmp/v.mp4", "s://a.mp3": "/tmp/a.mp3"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "volume=0.5" in fc


# ── Overlays ───────────────────────────────────────────────────────────────────

def test_text_overlay_uses_drawtext():
    v_clip = VideoClip(id="v1", src="s://v.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    overlay = TextOverlay(
        id="t1", text="Hello World",
        startOnTimeline=1.0, endOnTimeline=4.0,
        position=Position(x=100, y=200),
    )
    tracks = [
        Track(id="tv", type=TrackType.video, clips=[v_clip]),
        Track(id="tt", type=TrackType.text, overlays=[overlay]),
    ]
    cmd = _build(_comp(*tracks),
                 input_files={"s://v.mp4": "/tmp/v.mp4"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "drawtext" in fc
    assert "Hello World" in fc


def test_image_overlay_uses_overlay_filter():
    v_clip = VideoClip(id="v1", src="s://v.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    img = ImageOverlay(
        id="img1", src="s://logo.png",
        startOnTimeline=0.0, endOnTimeline=5.0,
        position=Position(x=50, y=50, anchor=AnchorPoint.top_left),
    )
    tracks = [
        Track(id="tv", type=TrackType.video, clips=[v_clip]),
        Track(id="ti", type=TrackType.image, overlays=[img]),
    ]
    cmd = _build(_comp(*tracks),
                 input_files={"s://v.mp4": "/tmp/v.mp4", "s://logo.png": "/tmp/logo.png"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "overlay" in fc
    assert "scale" in fc


def test_text_overlay_enable_range():
    v_clip = VideoClip(id="v1", src="s://v.mp4", startOnTimeline=0.0, endOnTimeline=10.0)
    overlay = TextOverlay(
        id="t1", text="Caption",
        startOnTimeline=2.0, endOnTimeline=6.0,
        position=Position(x=0, y=0),
    )
    tracks = [
        Track(id="tv", type=TrackType.video, clips=[v_clip]),
        Track(id="tt", type=TrackType.text, overlays=[overlay]),
    ]
    cmd = _build(_comp(*tracks, duration=10.0),
                 input_files={"s://v.mp4": "/tmp/v.mp4"})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "between(t,2.000,6.000)" in fc


# ── Resolution & FPS ───────────────────────────────────────────────────────────

def test_output_resolution_in_command():
    clip = VideoClip(id="c1", src="s://c.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track, width=1280, height=720),
                 input_files={"s://c.mp4": "/tmp/c.mp4"})
    assert "1280x720" in cmd


def test_output_fps_in_command():
    clip = VideoClip(id="c1", src="s://c.mp4", startOnTimeline=0.0, endOnTimeline=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    cmd = _build(_comp(track, fps=24),
                 input_files={"s://c.mp4": "/tmp/c.mp4"})
    r_idx = cmd.index("-r")
    assert cmd[r_idx + 1] == "24"
