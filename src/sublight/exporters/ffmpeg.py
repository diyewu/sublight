from __future__ import annotations

import subprocess
import shutil
import time
from pathlib import Path
from threading import Lock


def find_tool(name: str) -> str | None:
    return shutil.which(name)


def require_tool(name: str) -> str:
    path = find_tool(name)
    if path is None:
        raise FileNotFoundError(
            f"{name} was not found. Install ffmpeg and make sure `{name}` is on PATH."
        )
    return path


def require_ffmpeg_tools() -> None:
    require_tool("ffmpeg")
    require_tool("ffprobe")


def ffprobe_duration(path: Path) -> float | None:
    require_tool("ffprobe")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception:
        return None


def ffprobe_size(path: Path) -> tuple[int, int] | None:
    require_tool("ffprobe")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        value = result.stdout.strip().splitlines()[0]
        width, height = value.split("x")
        return int(width), int(height)
    except Exception:
        return None


def ffmpeg_filter_path(path: Path) -> str:
    escaped = str(path.resolve()).replace("\\", "\\\\").replace("'", r"\'")
    return f"filename='{escaped}'"


def run_ffmpeg(cmd: list[str]) -> None:
    require_tool("ffmpeg")
    subprocess.run(cmd, check=True)


class FfmpegCancelled(RuntimeError):
    pass


class FfmpegRunner:
    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._cancelled = False
        self._lock = Lock()

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            process = self._process
        if process is not None and process.poll() is None:
            process.terminate()

    def run(self, cmd: list[str]) -> None:
        require_tool("ffmpeg")
        if self.cancelled:
            raise FfmpegCancelled("Export cancelled")

        process = subprocess.Popen(cmd)
        with self._lock:
            self._process = process

        try:
            while True:
                return_code = process.poll()
                if return_code is not None:
                    if self.cancelled:
                        raise FfmpegCancelled("Export cancelled")
                    if return_code:
                        raise subprocess.CalledProcessError(return_code, cmd)
                    return
                if self.cancelled:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    raise FfmpegCancelled("Export cancelled")
                time.sleep(0.1)
        finally:
            with self._lock:
                if self._process is process:
                    self._process = None
