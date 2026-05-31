import re
from typing import Callable, Optional

ProgressCallback = Callable[[float], None]

_TIME_RE = re.compile(r"time=(\d+):(\d+):([\d.]+)")
_DURATION_RE = re.compile(r"Duration:\s+(\d+):(\d+):([\d.]+)")


def _hms_to_seconds(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_progress(line: str) -> Optional[dict]:
    """Extract current encode time from an FFmpeg stderr progress line."""
    m = _TIME_RE.search(line)
    if not m:
        return None
    return {
        "time_seconds": _hms_to_seconds(m.group(1), m.group(2), m.group(3)),
        "raw": line,
    }


def parse_duration(line: str) -> Optional[float]:
    """Extract total duration in seconds from an FFmpeg stderr header line."""
    m = _DURATION_RE.search(line)
    if not m:
        return None
    return _hms_to_seconds(m.group(1), m.group(2), m.group(3))


def make_progress_callback(
    total_duration: float,
    on_progress: ProgressCallback,
) -> Callable[[str], None]:
    """Return a callback that translates FFmpeg stderr lines to 0–100 progress."""
    def callback(line: str) -> None:
        result = parse_progress(line)
        if result and total_duration > 0:
            pct = min(result["time_seconds"] / total_duration * 100.0, 99.0)
            on_progress(pct)

    return callback
