import enum
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class AnchorPoint(str, enum.Enum):
    top_left = "top-left"
    top = "top"
    top_right = "top-right"
    left = "left"
    center = "center"
    right = "right"
    bottom_left = "bottom-left"
    bottom = "bottom"
    bottom_right = "bottom-right"


class AnimationTypeIn(str, enum.Enum):
    none = "none"
    fade_in = "fadeIn"
    slide_in = "slideIn"
    scale_in = "scaleIn"


class AnimationTypeOut(str, enum.Enum):
    none = "none"
    fade_out = "fadeOut"
    slide_out = "slideOut"
    scale_out = "scaleOut"


class TransitionType(str, enum.Enum):
    cut = "cut"
    fade = "fade"
    crossfade = "crossfade"
    slide = "slide"
    dissolve = "dissolve"


class TrackType(str, enum.Enum):
    video = "video"
    audio = "audio"
    text = "text"
    image = "image"
    ai_overlay = "ai_overlay"


class Resolution(BaseModel):
    width: int
    height: int


class Position(BaseModel):
    x: float
    y: float
    anchor: AnchorPoint = AnchorPoint.center


class TextStyle(BaseModel):
    fontFamily: Optional[str] = None
    fontSize: Optional[float] = None
    color: Optional[str] = None
    bold: bool = False
    italic: bool = False
    shadow: bool = False
    backgroundColor: Optional[str] = None


class Animation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    in_: AnimationTypeIn = Field(default=AnimationTypeIn.none, alias="in")
    out_: AnimationTypeOut = Field(default=AnimationTypeOut.none, alias="out")
    duration: float = 0.5


class Transition(BaseModel):
    type: TransitionType
    duration: Optional[float] = None


class VideoClip(BaseModel):
    id: str
    src: str
    startOnTimeline: float
    endOnTimeline: float
    trimIn: float = 0.0
    trimOut: Optional[float] = None
    transition: Optional[Transition] = None


class AudioClip(BaseModel):
    id: str
    src: str
    startOnTimeline: float
    endOnTimeline: float
    volume: float = 1.0
    fadeIn: Optional[float] = None
    fadeOut: Optional[float] = None


class AIOverlayClip(BaseModel):
    id: str
    src: str
    startOnTimeline: float
    endOnTimeline: float
    prompt: Optional[str] = None
    ai_task_id: Optional[str] = None


class TextOverlay(BaseModel):
    id: str
    text: str
    startOnTimeline: float
    endOnTimeline: float
    position: Position
    style: Optional[TextStyle] = None
    animation: Optional[Animation] = None


class ImageOverlay(BaseModel):
    id: str
    src: str
    startOnTimeline: float
    endOnTimeline: float
    position: Position
    width: Optional[float] = None
    height: Optional[float] = None
    opacity: float = 1.0


ClipUnion = Union[VideoClip, AudioClip, AIOverlayClip]
OverlayUnion = Union[TextOverlay, ImageOverlay]


class Track(BaseModel):
    id: str
    type: TrackType
    source: Optional[str] = None
    clips: list[ClipUnion] = []
    overlays: list[OverlayUnion] = []


class Composition(BaseModel):
    resolution: Resolution
    fps: int
    duration: float
    tracks: list[Track] = []
