from __future__ import annotations

import subprocess
import shutil
from pathlib import Path


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
