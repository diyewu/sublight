from __future__ import annotations

import subprocess
from pathlib import Path


def ffprobe_duration(path: Path) -> float | None:
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
    subprocess.run(cmd, check=True)
