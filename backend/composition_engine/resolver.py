from composition_engine.schema import Composition, Track, TrackType

_Z_ORDER = {
    TrackType.audio: 0,
    TrackType.video: 1,
    TrackType.image: 2,
    TrackType.ai_overlay: 3,
    TrackType.text: 4,
}


def resolve_z_order(composition: Composition) -> list[Track]:
    """Return tracks sorted by z-index (bottom to top render order).

    Within the same type, the original list order is preserved.
    """
    return sorted(composition.tracks, key=lambda t: (_Z_ORDER.get(t.type, 99), composition.tracks.index(t)))
