"""
Manual test: concat two video clips into one MP4.

Usage:
    cd backend
    python -m tests.manual.test_concat /path/to/clip1.mp4 /path/to/clip2.mp4

Output: /tmp/astraeus_test_concat.mp4
"""
import sys
from render_worker.executor import FFmpegExecutor, FFmpegError


def run(clip1: str, clip2: str, output: str = "/tmp/astraeus_test_concat.mp4") -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", clip1,
        "-i", clip2,
        "-filter_complex",
        "[0:v]trim=start=0,setpts=PTS-STARTPTS[v0];"
        "[1:v]trim=start=0,setpts=PTS-STARTPTS[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[outv]",
        "-map", "[outv]",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        output,
    ]

    print(f"Concatenating {clip1} + {clip2} → {output}")
    stderr_lines = []

    def on_line(line: str) -> None:
        stderr_lines.append(line)
        if "frame=" in line or "time=" in line:
            print(f"  {line}", end="\r")

    FFmpegExecutor().run(cmd, on_stderr_line=on_line)
    print(f"\nDone → {output}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])
