import json
import pytest
from composition_engine.schema import (
    Composition,
    Resolution,
    Track,
    TrackType,
    VideoClip,
    TextOverlay,
    Position,
    Animation,
)
from composition_engine.serializer import (
    composition_to_dict,
    composition_from_dict,
    composition_to_json,
    composition_from_json,
)


def make_full_composition() -> Composition:
    anim = Animation(**{"in": "fadeIn", "out": "fadeOut", "duration": 0.5})
    overlay = TextOverlay(
        id="txt1",
        text="Hello World",
        startOnTimeline=0.0,
        endOnTimeline=5.0,
        position=Position(x=0.5, y=0.5),
        animation=anim,
    )
    clip = VideoClip(id="v1", src="s3://bucket/clip.mp4", startOnTimeline=0.0, endOnTimeline=10.0)
    track = Track(id="t1", type=TrackType.video, clips=[clip], overlays=[overlay])
    return Composition(
        resolution=Resolution(width=1920, height=1080),
        fps=30,
        duration=60.0,
        tracks=[track],
    )


def test_composition_roundtrip_via_dict():
    original = make_full_composition()
    d = composition_to_dict(original)
    restored = composition_from_dict(d)

    assert restored.fps == original.fps
    assert restored.duration == original.duration
    assert len(restored.tracks) == 1
    assert len(restored.tracks[0].clips) == 1
    assert restored.tracks[0].clips[0].id == "v1"


def test_composition_roundtrip_via_json():
    original = make_full_composition()
    json_str = composition_to_json(original)
    restored = composition_from_json(json_str)

    assert restored.resolution.width == 1920
    assert restored.fps == 30


def test_animation_alias_in_dict():
    """Serialized dict must use 'in'/'out' keys, not 'in_'/'out_'."""
    comp = make_full_composition()
    d = composition_to_dict(comp)

    overlay_dict = d["tracks"][0]["overlays"][0]
    animation_dict = overlay_dict["animation"]
    assert "in" in animation_dict
    assert "out" in animation_dict
    assert "in_" not in animation_dict
    assert "out_" not in animation_dict


def test_animation_alias_in_json():
    comp = make_full_composition()
    json_str = composition_to_json(comp)
    data = json.loads(json_str)

    animation_data = data["tracks"][0]["overlays"][0]["animation"]
    assert "in" in animation_data
    assert "in_" not in animation_data


def test_from_dict_restores_animation_in_field():
    comp = make_full_composition()
    d = composition_to_dict(comp)
    restored = composition_from_dict(d)

    anim = restored.tracks[0].overlays[0].animation
    assert anim is not None
    from composition_engine.schema import AnimationTypeIn
    assert anim.in_ == AnimationTypeIn.fade_in


def test_empty_composition_roundtrip():
    comp = Composition(resolution=Resolution(width=1280, height=720), fps=24, duration=0.0, tracks=[])
    d = composition_to_dict(comp)
    restored = composition_from_dict(d)
    assert restored.fps == 24
    assert restored.tracks == []
