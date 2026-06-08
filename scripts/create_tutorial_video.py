from __future__ import annotations

import argparse
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Scene:
    title: str
    subtitle: str
    accent: str


SCENES = [
    Scene("Import SRT", "Open subtitles and attach the matching video.", "SubLight"),
    Scene("Pick Keywords", "Mark text manually or accept suggested keywords.", "keywords"),
    Scene("Tune Style", "Preview fonts, colors, outlines, and caption boxes.", "style"),
    Scene("Queue Exports", "Render multiple presets without babysitting ffmpeg.", "queue"),
    Scene("Back To Editor", "Use green overlays or burned MP4s in your workflow.", "overlay"),
]


def drawtext(text: str, *, y: int, size: int, color: str) -> str:
    escaped = text.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")
    return (
        f"drawtext=text='{escaped}':fontcolor={color}:fontsize={size}:"
        f"x=(w-text_w)/2:y={y}"
    )


def make_scene(scene: Scene, path: Path, *, duration: float) -> None:
    filters = [
        "drawbox=x=96:y=86:w=1088:h=548:color=0x151b22@0.94:t=fill",
        "drawbox=x=96:y=86:w=1088:h=12:color=0x4dd8ff@1:t=fill",
        drawtext("SubLight tutorial", y=140, size=30, color="0x4dd8ff"),
        drawtext(scene.title, y=235, size=72, color="white"),
        drawtext(scene.subtitle, y=348, size=34, color="0xd7e2df"),
        drawtext(scene.accent, y=468, size=54, color="0xffd400"),
    ]
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x0a0d10:s=1280x720:r=30:d={duration:.3f}",
            "-vf",
            ",".join(filters),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
    )


def create_tutorial_video(output: Path, *, duration_per_scene: float = 3.2) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        scene_paths = []
        for index, scene in enumerate(SCENES, start=1):
            scene_path = tmp_path / f"scene-{index:02d}.mp4"
            make_scene(scene, scene_path, duration=duration_per_scene)
            scene_paths.append(scene_path)

        concat_list = tmp_path / "concat.txt"
        concat_list.write_text(
            "".join(f"file '{path}'\n" for path in scene_paths),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(output),
            ],
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the SubLight tutorial video.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("examples/tutorial-video.mp4"),
    )
    parser.add_argument("--duration-per-scene", type=float, default=3.2)
    args = parser.parse_args()
    create_tutorial_video(args.output, duration_per_scene=args.duration_per_scene)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

