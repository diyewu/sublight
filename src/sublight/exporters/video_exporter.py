from __future__ import annotations

from pathlib import Path

from .ffmpeg import ffmpeg_filter_path, run_ffmpeg


def burn_video(video_path: Path, ass_path: Path, output_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"ass={ffmpeg_filter_path(ass_path)}",
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-c:a",
        "copy",
        str(output_path),
    ]
    run_ffmpeg(cmd)


def burn_preview_segment(
    video_path: Path,
    ass_path: Path,
    output_path: Path,
    *,
    start_seconds: float,
    duration_seconds: float = 5.0,
) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{max(start_seconds, 0):.3f}",
        "-t",
        f"{max(duration_seconds, 0.1):.3f}",
        "-i",
        str(video_path),
        "-vf",
        f"ass={ffmpeg_filter_path(ass_path)}",
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "veryfast",
        "-c:a",
        "copy",
        str(output_path),
    ]
    run_ffmpeg(cmd)


def render_overlay(
    ass_path: Path,
    output_path: Path,
    *,
    width: int,
    height: int,
    duration: float,
    fps: int,
) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x00FF00:s={width}x{height}:r={fps}:d={duration:.3f}",
        "-vf",
        f"ass={ffmpeg_filter_path(ass_path)},colorkey=0x00FF00:0.08:0.0,format=argb",
        "-c:v",
        "qtrle",
        str(output_path),
    ]
    run_ffmpeg(cmd)
