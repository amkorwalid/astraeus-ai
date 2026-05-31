import pytest

from composition_engine.schema import (
    AudioClip,
    Composition,
    ImageOverlay,
    Position,
    Resolution,
    TextOverlay,
    Track,
    TrackType,
    VideoClip,
)
from render_worker.parser import (
    AudioStage,
    ImageOverlayStage,
    RenderPlan,
    TextOverlayStage,
    VideoStage,
    collect_media_srcs,
    parse_composition,
)


def _comp(*tracks, duration=10.0) -> Composition:
    return Composition(
        resolution=Resolution(width=1920, height=1080),
        fps=30,
        duration=duration,
        tracks=list(tracks),
    )


def _video_clip(id="v1", src="s://clip.mp4", start=0.0, end=5.0) -> VideoClip:
    return VideoClip(id=id, src=src, startOnTimeline=start, endOnTimeline=end)


def _audio_clip(id="a1", src="s://audio.mp3", start=0.0, end=5.0) -> AudioClip:
    return AudioClip(id=id, src=src, startOnTimeline=start, endOnTimeline=end)


# ── parse_composition ──────────────────────────────────────────────────────────

def test_empty_composition_produces_empty_plan():
    plan = parse_composition(_comp())
    assert plan.stages == []


def test_single_video_clip_creates_video_stage():
    track = Track(id="t1", type=TrackType.video, clips=[_video_clip()])
    plan = parse_composition(_comp(track))
    assert len(plan.stages) == 1
    assert isinstance(plan.stages[0], VideoStage)
    assert len(plan.stages[0].clips) == 1


def test_single_audio_clip_creates_audio_stage():
    track = Track(id="t1", type=TrackType.audio, clips=[_audio_clip()])
    plan = parse_composition(_comp(track))
    assert len(plan.stages) == 1
    assert isinstance(plan.stages[0], AudioStage)


def test_z_order_places_audio_before_video():
    video_track = Track(id="tv", type=TrackType.video, clips=[_video_clip()])
    audio_track = Track(id="ta", type=TrackType.audio, clips=[_audio_clip()])
    # Video track listed first in composition, but z-order puts audio at index 0
    plan = parse_composition(_comp(video_track, audio_track))
    assert isinstance(plan.stages[0], AudioStage)
    assert isinstance(plan.stages[1], VideoStage)


def test_video_clips_sorted_by_start_time():
    clips = [
        _video_clip(id="v2", src="s://c2.mp4", start=5.0, end=10.0),
        _video_clip(id="v1", src="s://c1.mp4", start=0.0, end=5.0),
    ]
    track = Track(id="t1", type=TrackType.video, clips=clips)
    plan = parse_composition(_comp(track))
    stage = plan.stages[0]
    assert isinstance(stage, VideoStage)
    assert stage.clips[0].id == "v1"
    assert stage.clips[1].id == "v2"


def test_empty_video_track_produces_no_stage():
    track = Track(id="t1", type=TrackType.video, clips=[])
    plan = parse_composition(_comp(track))
    assert plan.stages == []


def test_text_overlay_stage():
    overlay = TextOverlay(
        id="txt1", text="Hello",
        startOnTimeline=0.0, endOnTimeline=3.0,
        position=Position(x=100, y=100),
    )
    track = Track(id="t1", type=TrackType.text, overlays=[overlay])
    plan = parse_composition(_comp(track))
    assert len(plan.stages) == 1
    assert isinstance(plan.stages[0], TextOverlayStage)


def test_image_overlay_stage():
    overlay = ImageOverlay(
        id="img1", src="s://logo.png",
        startOnTimeline=0.0, endOnTimeline=5.0,
        position=Position(x=50, y=50),
    )
    track = Track(id="t1", type=TrackType.image, overlays=[overlay])
    plan = parse_composition(_comp(track))
    assert len(plan.stages) == 1
    assert isinstance(plan.stages[0], ImageOverlayStage)


def test_work_dir_is_set():
    plan = parse_composition(_comp(), work_dir="/custom/dir")
    assert plan.work_dir == "/custom/dir"


# ── collect_media_srcs ─────────────────────────────────────────────────────────

def test_collect_srcs_from_video_and_image():
    video_clip = _video_clip(src="s://video.mp4")
    img_overlay = ImageOverlay(
        id="i1", src="s://logo.png",
        startOnTimeline=0.0, endOnTimeline=5.0,
        position=Position(x=0, y=0),
    )
    tracks = [
        Track(id="tv", type=TrackType.video, clips=[video_clip]),
        Track(id="ti", type=TrackType.image, overlays=[img_overlay]),
    ]
    plan = parse_composition(_comp(*tracks))
    srcs = collect_media_srcs(plan)
    assert "s://video.mp4" in srcs
    assert "s://logo.png" in srcs


def test_collect_srcs_excludes_text_overlays():
    overlay = TextOverlay(
        id="t1", text="Hi",
        startOnTimeline=0.0, endOnTimeline=3.0,
        position=Position(x=0, y=0),
    )
    track = Track(id="t1", type=TrackType.text, overlays=[overlay])
    plan = parse_composition(_comp(track))
    srcs = collect_media_srcs(plan)
    assert srcs == set()


def test_collect_srcs_deduplicates():
    clip1 = _video_clip(id="v1", src="s://same.mp4", start=0.0, end=5.0)
    clip2 = _video_clip(id="v2", src="s://same.mp4", start=5.0, end=10.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip1, clip2])
    plan = parse_composition(_comp(track))
    srcs = collect_media_srcs(plan)
    assert srcs == {"s://same.mp4"}
