import pytest
from composition_engine.schema import (
    Composition,
    Resolution,
    Track,
    TrackType,
    VideoClip,
    AudioClip,
)
from composition_engine.validator import validate_composition, CompositionValidationError


def make_composition(**kwargs) -> Composition:
    defaults = dict(
        resolution=Resolution(width=1920, height=1080),
        fps=30,
        duration=60.0,
        tracks=[],
    )
    defaults.update(kwargs)
    return Composition(**defaults)


def make_video_clip(id="v1", start=0.0, end=10.0) -> VideoClip:
    return VideoClip(id=id, src="s3://bucket/clip.mp4", startOnTimeline=start, endOnTimeline=end)


def make_audio_clip(id="a1", start=0.0, end=10.0) -> AudioClip:
    return AudioClip(id=id, src="s3://bucket/audio.mp3", startOnTimeline=start, endOnTimeline=end)


def test_valid_empty_composition():
    validate_composition(make_composition())


def test_valid_composition_with_clips():
    clip = make_video_clip()
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    comp = make_composition(tracks=[track])
    validate_composition(comp)


def test_invalid_fps_zero():
    with pytest.raises(CompositionValidationError, match="fps"):
        validate_composition(make_composition(fps=0))


def test_invalid_fps_negative():
    with pytest.raises(CompositionValidationError, match="fps"):
        validate_composition(make_composition(fps=-1))


def test_invalid_duration_negative():
    with pytest.raises(CompositionValidationError, match="duration"):
        validate_composition(make_composition(duration=-1.0))


def test_invalid_resolution_width_zero():
    with pytest.raises(CompositionValidationError, match="resolution.width"):
        validate_composition(make_composition(resolution=Resolution(width=0, height=1080)))


def test_invalid_resolution_height_negative():
    with pytest.raises(CompositionValidationError, match="resolution.height"):
        validate_composition(make_composition(resolution=Resolution(width=1920, height=-1)))


def test_clip_start_negative():
    clip = make_video_clip(start=-1.0, end=10.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    with pytest.raises(CompositionValidationError, match="startOnTimeline"):
        validate_composition(make_composition(tracks=[track]))


def test_clip_end_before_start():
    clip = make_video_clip(start=10.0, end=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    with pytest.raises(CompositionValidationError, match="endOnTimeline"):
        validate_composition(make_composition(tracks=[track]))


def test_clip_end_equals_start():
    clip = make_video_clip(start=5.0, end=5.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    with pytest.raises(CompositionValidationError, match="endOnTimeline"):
        validate_composition(make_composition(tracks=[track]))


def test_clip_exceeds_duration():
    clip = make_video_clip(start=0.0, end=70.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    with pytest.raises(CompositionValidationError, match="exceeds composition duration"):
        validate_composition(make_composition(duration=60.0, tracks=[track]))


def test_video_clip_trim_in_negative():
    clip = VideoClip(id="v1", src="s3://x.mp4", startOnTimeline=0.0, endOnTimeline=10.0, trimIn=-1.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    with pytest.raises(CompositionValidationError, match="trimIn"):
        validate_composition(make_composition(tracks=[track]))


def test_video_clip_trim_out_before_trim_in():
    clip = VideoClip(id="v1", src="s3://x.mp4", startOnTimeline=0.0, endOnTimeline=10.0, trimIn=5.0, trimOut=3.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    with pytest.raises(CompositionValidationError, match="trimOut"):
        validate_composition(make_composition(tracks=[track]))


def test_overlapping_clips_detected():
    clip_a = make_video_clip(id="a", start=0.0, end=10.0)
    clip_b = make_video_clip(id="b", start=8.0, end=20.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip_a, clip_b])
    with pytest.raises(CompositionValidationError, match="overlap"):
        validate_composition(make_composition(duration=60.0, tracks=[track]))


def test_adjacent_clips_do_not_overlap():
    clip_a = make_video_clip(id="a", start=0.0, end=10.0)
    clip_b = make_video_clip(id="b", start=10.0, end=20.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip_a, clip_b])
    validate_composition(make_composition(duration=60.0, tracks=[track]))


def test_audio_clips_in_audio_track_validated():
    clip = make_audio_clip(start=0.0, end=10.0)
    track = Track(id="t1", type=TrackType.audio, clips=[clip])
    validate_composition(make_composition(tracks=[track]))


def test_zero_duration_composition_allows_empty_tracks():
    validate_composition(make_composition(duration=0.0, tracks=[]))
