from composition_engine.schema import Composition, Track


def normalize_composition(composition: Composition) -> Composition:
    """Sort clips by startOnTimeline and snap all times to frame boundaries."""
    fps = composition.fps
    normalized_tracks = [_normalize_track(track, fps) for track in composition.tracks]
    return composition.model_copy(update={"tracks": normalized_tracks})


def _normalize_track(track: Track, fps: int) -> Track:
    snapped_clips = [_snap_clip(clip, fps) for clip in track.clips]
    sorted_clips = sorted(snapped_clips, key=lambda c: c.startOnTimeline)

    snapped_overlays = [_snap_overlay(overlay, fps) for overlay in track.overlays]
    sorted_overlays = sorted(snapped_overlays, key=lambda o: o.startOnTimeline)

    return track.model_copy(update={"clips": sorted_clips, "overlays": sorted_overlays})


def _snap(t: float, fps: int) -> float:
    return round(t * fps) / fps


def _snap_clip(clip, fps: int):
    updates = {
        "startOnTimeline": _snap(clip.startOnTimeline, fps),
        "endOnTimeline": _snap(clip.endOnTimeline, fps),
    }
    return clip.model_copy(update=updates)


def _snap_overlay(overlay, fps: int):
    updates = {
        "startOnTimeline": _snap(overlay.startOnTimeline, fps),
        "endOnTimeline": _snap(overlay.endOnTimeline, fps),
    }
    return overlay.model_copy(update=updates)
