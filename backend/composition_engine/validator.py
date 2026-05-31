from composition_engine.schema import Composition, VideoClip, TrackType


class CompositionValidationError(ValueError):
    pass


def validate_composition(composition: Composition) -> None:
    """Raises CompositionValidationError if the composition is invalid."""
    if composition.fps <= 0:
        raise CompositionValidationError(f"fps must be > 0, got {composition.fps}")
    if composition.duration < 0:
        raise CompositionValidationError(f"duration must be >= 0, got {composition.duration}")
    if composition.resolution.width <= 0:
        raise CompositionValidationError(f"resolution.width must be > 0, got {composition.resolution.width}")
    if composition.resolution.height <= 0:
        raise CompositionValidationError(f"resolution.height must be > 0, got {composition.resolution.height}")

    for track in composition.tracks:
        _validate_track_clips(track, composition.duration)
        _validate_track_overlays(track, composition.duration)


def _validate_track_clips(track, composition_duration: float) -> None:
    for clip in track.clips:
        _validate_time_range(clip.id, clip.startOnTimeline, clip.endOnTimeline, composition_duration)
        if isinstance(clip, VideoClip):
            if clip.trimIn < 0:
                raise CompositionValidationError(
                    f"Clip '{clip.id}': trimIn must be >= 0, got {clip.trimIn}"
                )
            if clip.trimOut is not None and clip.trimOut <= clip.trimIn:
                raise CompositionValidationError(
                    f"Clip '{clip.id}': trimOut ({clip.trimOut}) must be > trimIn ({clip.trimIn})"
                )

    _detect_overlaps(track.id, track.clips)


def _validate_track_overlays(track, composition_duration: float) -> None:
    for overlay in track.overlays:
        _validate_time_range(overlay.id, overlay.startOnTimeline, overlay.endOnTimeline, composition_duration)


def _validate_time_range(item_id: str, start: float, end: float, max_duration: float) -> None:
    if start < 0:
        raise CompositionValidationError(
            f"Item '{item_id}': startOnTimeline must be >= 0, got {start}"
        )
    if end <= start:
        raise CompositionValidationError(
            f"Item '{item_id}': endOnTimeline ({end}) must be > startOnTimeline ({start})"
        )
    if max_duration > 0 and end > max_duration:
        raise CompositionValidationError(
            f"Item '{item_id}': endOnTimeline ({end}) exceeds composition duration ({max_duration})"
        )


def _detect_overlaps(track_id: str, clips) -> None:
    if len(clips) < 2:
        return
    sorted_clips = sorted(clips, key=lambda c: c.startOnTimeline)
    for i in range(len(sorted_clips) - 1):
        a = sorted_clips[i]
        b = sorted_clips[i + 1]
        if a.endOnTimeline > b.startOnTimeline:
            raise CompositionValidationError(
                f"Track '{track_id}': clips '{a.id}' and '{b.id}' overlap "
                f"({a.endOnTimeline} > {b.startOnTimeline})"
            )
