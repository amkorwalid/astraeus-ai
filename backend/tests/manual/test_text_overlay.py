"""
Manual test: burn a text overlay using FFmpeg drawtext.

Usage:
    cd backend
    python -m tests.manual.test_text_overlay /path/to/video.mp4 "Your text here"

Output: /tmp/astraeus_test_text_overlay.mp4
"""
import sys
from render_worker.executor import FFmpegExecutor


def run(
    video: str,
    text: str = "Astraeus AI",
    output: str = "/tmp/astraeus_test_text_overlay.mp4",
) -> None:
    safe_text = text.replace("'", "\\'").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-vf",
        f"drawtext=text='{safe_text}':x=(w-tw)/2:y=h-lh-40:"
        f"fontsize=48:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=5",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-c:a", "copy",
        output,
    ]

    print(f"Burning text '{text}' onto {video} → {output}")

    def on_line(line: str) -> None:
        if "time=" in line:
            print(f"  {line}", end="\r")

    FFmpegExecutor().run(cmd, on_stderr_line=on_line)
    print(f"\nDone → {output}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    text = sys.argv[2] if len(sys.argv) > 2 else "Astraeus AI"
    run(sys.argv[1], text)
