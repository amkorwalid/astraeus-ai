"""
Manual test: mix audio track over a video clip.

Usage:
    cd backend
    python -m tests.manual.test_audio_mix /path/to/video.mp4 /path/to/audio.mp3

Output: /tmp/astraeus_test_audio_mix.mp4
"""
import sys
from render_worker.executor import FFmpegExecutor


def run(video: str, audio: str, output: str = "/tmp/astraeus_test_audio_mix.mp4") -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-i", audio,
        "-filter_complex",
        "[1:a]atrim=start=0,asetpts=PTS-STARTPTS,volume=0.8[amixed]",
        "-map", "0:v",
        "-map", "[amixed]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output,
    ]

    print(f"Mixing audio {audio} over {video} → {output}")

    def on_line(line: str) -> None:
        if "time=" in line:
            print(f"  {line}", end="\r")

    FFmpegExecutor().run(cmd, on_stderr_line=on_line)
    print(f"\nDone → {output}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])
