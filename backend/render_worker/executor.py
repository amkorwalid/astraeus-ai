import subprocess
from typing import Callable, Optional


class FFmpegError(Exception):
    def __init__(self, returncode: int, stderr: str):
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"FFmpeg exited with code {returncode}: {stderr[-500:]}")


class FFmpegExecutor:
    def run(
        self,
        cmd: list[str],
        on_stderr_line: Optional[Callable[[str], None]] = None,
    ) -> None:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stderr_lines: list[str] = []
        assert proc.stderr is not None

        for line in proc.stderr:
            line = line.rstrip()
            stderr_lines.append(line)
            if on_stderr_line:
                on_stderr_line(line)

        proc.wait()
        if proc.returncode != 0:
            raise FFmpegError(proc.returncode, "\n".join(stderr_lines[-50:]))
