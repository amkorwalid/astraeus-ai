import json
import pytest
from composition_engine.schema import (
    Composition,
    Resolution,
    Track,
    TrackType,
    VideoClip,
    AudioClip,
    TextOverlay,
    ImageOverlay,
    Position,
    Animation,
    AnimationTypeIn,
    AnimationTypeOut,
    AnchorPoint,
)


def make_empty_composition(fps=30, duration=60.0) -> Composition:
    return Composition(
        resolution=Resolution(width=1920, height=1080),
        fps=fps,
        duration=duration,
        tracks=[],
    )


def test_empty_composition_defaults():
    c = make_empty_composition()
    assert c.fps == 30
    assert c.duration == 60.0
    assert c.tracks == []
    assert c.resolution.width == 1920


def test_animation_alias_serialization():
    """'in' and 'out' must be used in JSON, not 'in_' and 'out_'."""
    anim = Animation(
        **{"in": "fadeIn", "out": "fadeOut", "duration": 1.0}
    )
    assert anim.in_ == AnimationTypeIn.fade_in
    assert anim.out_ == AnimationTypeOut.fade_out

    dumped = anim.model_dump(by_alias=True)
    assert "in" in dumped
    assert "out" in dumped
    assert "in_" not in dumped
    assert "out_" not in dumped


def test_animation_json_roundtrip():
    anim = Animation(**{"in": "slideIn", "out": "slideOut", "duration": 0.3})
    json_str = anim.model_dump_json(by_alias=True)
    data = json.loads(json_str)
    assert data["in"] == "slideIn"
    assert data["out"] == "slideOut"

    restored = Animation.model_validate(data)
    assert restored.in_ == AnimationTypeIn.slide_in


def test_video_clip_defaults():
    clip = VideoClip(id="v1", src="s3://bucket/file.mp4", startOnTimeline=0.0, endOnTimeline=10.0)
    assert clip.trimIn == 0.0
    assert clip.trimOut is None
    assert clip.transition is None


def test_audio_clip_defaults():
    clip = AudioClip(id="a1", src="s3://bucket/audio.mp3", startOnTimeline=0.0, endOnTimeline=5.0)
    assert clip.volume == 1.0
    assert clip.fadeIn is None


def test_image_overlay_defaults():
    overlay = ImageOverlay(
        id="img1",
        src="s3://bucket/img.png",
        startOnTimeline=0.0,
        endOnTimeline=5.0,
        position=Position(x=0.5, y=0.5),
    )
    assert overlay.opacity == 1.0
    assert overlay.width is None


def test_position_default_anchor():
    pos = Position(x=100, y=200)
    assert pos.anchor == AnchorPoint.center


def test_track_empty_clips_and_overlays():
    track = Track(id="t1", type=TrackType.video)
    assert track.clips == []
    assert track.overlays == []


def test_composition_with_video_track():
    clip = VideoClip(id="v1", src="s3://clip.mp4", startOnTimeline=0.0, endOnTimeline=10.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip])
    comp = Composition(
        resolution=Resolution(width=1280, height=720),
        fps=24,
        duration=10.0,
        tracks=[track],
    )
    assert len(comp.tracks) == 1
    assert len(comp.tracks[0].clips) == 1
