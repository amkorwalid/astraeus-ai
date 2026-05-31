import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

from composition_engine.schema import (
    AudioClip,
    Composition,
    ImageOverlay,
    TextOverlay,
    TrackType,
    VideoClip,
)
from composition_engine.resolver import resolve_z_order


@dataclass
class VideoStage:
    track_id: str
    clips: list[VideoClip]


@dataclass
class AudioStage:
    track_id: str
    clips: list[AudioClip]


@dataclass
class TextOverlayStage:
    track_id: str
    overlays: list[TextOverlay]


@dataclass
class ImageOverlayStage:
    track_id: str
    overlays: list[ImageOverlay]


RenderStage = VideoStage | AudioStage | TextOverlayStage | ImageOverlayStage


@dataclass
class RenderPlan:
    composition: Composition
    stages: list[RenderStage] = field(default_factory=list)
    work_dir: str = "/tmp/astraeus_render"


def parse_composition(comp: Composition, work_dir: str = "/tmp/astraeus_render") -> RenderPlan:
    """Convert a Composition into an ordered RenderPlan (no I/O)."""
    plan = RenderPlan(composition=comp, work_dir=work_dir)
    ordered_tracks = resolve_z_order(comp)

    for track in ordered_tracks:
        if track.type == TrackType.video:
            video_clips = sorted(
                [c for c in track.clips if isinstance(c, VideoClip)],
                key=lambda c: c.startOnTimeline,
            )
            if video_clips:
                plan.stages.append(VideoStage(track_id=track.id, clips=video_clips))

        elif track.type == TrackType.audio:
            audio_clips = sorted(
                [c for c in track.clips if isinstance(c, AudioClip)],
                key=lambda c: c.startOnTimeline,
            )
            if audio_clips:
                plan.stages.append(AudioStage(track_id=track.id, clips=audio_clips))

        elif track.type == TrackType.text:
            text_overlays = sorted(
                [o for o in track.overlays if isinstance(o, TextOverlay)],
                key=lambda o: o.startOnTimeline,
            )
            if text_overlays:
                plan.stages.append(TextOverlayStage(track_id=track.id, overlays=text_overlays))

        elif track.type == TrackType.image:
            image_overlays = sorted(
                [o for o in track.overlays if isinstance(o, ImageOverlay)],
                key=lambda o: o.startOnTimeline,
            )
            if image_overlays:
                plan.stages.append(ImageOverlayStage(track_id=track.id, overlays=image_overlays))

    return plan


def collect_media_srcs(plan: RenderPlan) -> set[str]:
    """Return all media src URLs referenced in the render plan."""
    srcs: set[str] = set()
    for stage in plan.stages:
        if isinstance(stage, VideoStage):
            for clip in stage.clips:
                srcs.add(clip.src)
        elif isinstance(stage, AudioStage):
            for clip in stage.clips:
                srcs.add(clip.src)
        elif isinstance(stage, ImageOverlayStage):
            for overlay in stage.overlays:
                srcs.add(overlay.src)
    return srcs


def download_media_files(
    srcs: set[str],
    cache_dir: str = "/tmp/astraeus_cache",
) -> dict[str, str]:
    """Download media files from DO Spaces to a local cache. Returns src -> local_path."""
    import boto3
    from app.config import settings

    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    client = boto3.client(
        "s3",
        region_name=settings.DO_SPACES_REGION,
        endpoint_url=settings.DO_SPACES_ENDPOINT,
        aws_access_key_id=settings.DO_SPACES_KEY,
        aws_secret_access_key=settings.DO_SPACES_SECRET,
    )

    prefix = f"{settings.DO_SPACES_ENDPOINT}/{settings.DO_SPACES_BUCKET}/"
    result: dict[str, str] = {}

    for src in srcs:
        if not src.startswith(prefix):
            result[src] = src
            continue

        storage_key = src[len(prefix):]
        cache_key = hashlib.sha256(storage_key.encode()).hexdigest()[:16]
        ext = os.path.splitext(storage_key)[1] or ".bin"
        local_path = os.path.join(cache_dir, cache_key + ext)

        if not os.path.exists(local_path):
            client.download_file(settings.DO_SPACES_BUCKET, storage_key, local_path)

        result[src] = local_path

    return result
