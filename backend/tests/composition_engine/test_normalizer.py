import pytest
from composition_engine.schema import (
    Composition,
    Resolution,
    Track,
    TrackType,
    VideoClip,
    AudioClip,
    TextOverlay,
    Position,
)
from composition_engine.normalizer import normalize_composition


def make_video_clip(id: str, start: float, end: float) -> VideoClip:
    return VideoClip(id=id, src="s3://x.mp4", startOnTimeline=start, endOnTimeline=end)


def make_audio_clip(id: str, start: float, end: float) -> AudioClip:
    return AudioClip(id=id, src="s3://x.mp3", startOnTimeline=start, endOnTimeline=end)


def make_text_overlay(id: str, start: float, end: float) -> TextOverlay:
    return TextOverlay(
        id=id, text="Hello", startOnTimeline=start, endOnTimeline=end,
        position=Position(x=0.5, y=0.5),
    )


def test_clips_sorted_by_start_time():
    clips = [
        make_video_clip("c", 20.0, 30.0),
        make_video_clip("a", 0.0, 10.0),
        make_video_clip("b", 10.0, 20.0),
    ]
    track = Track(id="t1", type=TrackType.video, clips=clips)
    comp = Composition(resolution=Resolution(width=1920, height=1080), fps=30, duration=60.0, tracks=[track])

    result = normalize_composition(comp)
    ids = [c.id for c in result.tracks[0].clips]
    assert ids == ["a", "b", "c"]


def test_times_snapped_to_frame_boundaries_30fps():
    clip = make_video_clip("v1", start=1.0 / 3, end=2.0 / 3)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    comp = Composition(resolution=Resolution(width=1920, height=1080), fps=30, duration=60.0, tracks=[track])

    result = normalize_composition(comp)
    c = result.tracks[0].clips[0]
    # 1/3 * 30 = 10 frames → 10/30 = 0.333...
    assert c.startOnTimeline == round((1.0 / 3) * 30) / 30
    assert c.endOnTimeline == round((2.0 / 3) * 30) / 30


def test_times_snapped_to_frame_boundaries_24fps():
    clip = make_video_clip("v1", start=0.5, end=1.04166)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    comp = Composition(resolution=Resolution(width=1920, height=1080), fps=24, duration=60.0, tracks=[track])

    result = normalize_composition(comp)
    c = result.tracks[0].clips[0]
    assert c.startOnTimeline == round(0.5 * 24) / 24
    assert c.endOnTimeline == round(1.04166 * 24) / 24


def test_overlays_sorted_and_snapped():
    overlays = [
        make_text_overlay("b", 10.0, 20.0),
        make_text_overlay("a", 0.0, 10.0),
    ]
    track = Track(id="t1", type=TrackType.text, overlays=overlays)
    comp = Composition(resolution=Resolution(width=1920, height=1080), fps=30, duration=60.0, tracks=[track])

    result = normalize_composition(comp)
    ids = [o.id for o in result.tracks[0].overlays]
    assert ids == ["a", "b"]


def test_normalize_does_not_mutate_original():
    clip = make_video_clip("v1", start=20.0, end=30.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    comp = Composition(resolution=Resolution(width=1920, height=1080), fps=30, duration=60.0, tracks=[track])

    result = normalize_composition(comp)
    assert comp is not result
    assert comp.tracks[0].clips[0].startOnTimeline == 20.0


def test_empty_tracks_normalize_cleanly():
    comp = Composition(resolution=Resolution(width=1920, height=1080), fps=30, duration=60.0, tracks=[])
    result = normalize_composition(comp)
    assert result.tracks == []
