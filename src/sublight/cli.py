#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sublight.core.keywords import load_keywords
from sublight.core.srt import parse_srt
from sublight.exporters.ass_exporter import write_keyword_report
from sublight.exporters.ffmpeg import ffprobe_duration, ffprobe_size
from sublight.exporters.video_exporter import burn_video, render_overlay
from sublight.styles.ass import write_ass
from sublight.styles.presets import STYLE_PRESETS, merge_style_preset, style_preset_lines


def default_output_path(input_path: Path, suffix: str, extension: str) -> Path:
    return input_path.with_name(f"{input_path.stem}{suffix}{extension}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate keyword-highlighted ASS subtitles from SRT."
    )
    parser.add_argument("input", type=Path, nargs="?", help="Input .srt file")
    parser.add_argument(
        "--style-preset",
        choices=sorted(STYLE_PRESETS),
        default="bold-yellow",
        help="Built-in subtitle style preset",
    )
    parser.add_argument("--style-json", help="JSON file with StylePreset fields to override")
    parser.add_argument(
        "--list-style-presets",
        action="store_true",
        help="List built-in style presets and exit",
    )
    parser.add_argument("--keywords", help="Comma/semicolon separated keywords")
    parser.add_argument("--keywords-file", help="One keyword per line")
    parser.add_argument("--auto-keywords", type=int, default=24, help="Auto keyword count")
    parser.add_argument("--output", type=Path, help="Output .ass path")
    parser.add_argument("--report", type=Path, help="Output keyword report path")
    parser.add_argument("--video", type=Path, help="Optional video to burn subtitles into")
    parser.add_argument("--burn-output", type=Path, help="Burned video output path")
    parser.add_argument(
        "--overlay-output",
        type=Path,
        help="Transparent .mov overlay output path for importing into Jianying/CapCut",
    )
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--font")
    parser.add_argument("--font-size", type=int)
    parser.add_argument("--margin-v", type=int)
    parser.add_argument("--max-line-width", type=int)
    parser.add_argument("--highlight-color")
    parser.add_argument("--outline", type=float)
    parser.add_argument("--shadow", type=float)
    return parser.parse_args()


def style_overrides_from_args(args: argparse.Namespace) -> dict[str, object]:
    return {
        "font": args.font,
        "font_size": args.font_size,
        "margin_v": args.margin_v,
        "max_line_width": args.max_line_width,
        "highlight_color": args.highlight_color,
        "outline": args.outline,
        "shadow": args.shadow,
    }


def main() -> int:
    args = parse_args()
    if args.list_style_presets:
        print("\n".join(style_preset_lines()))
        return 0

    if args.input is None:
        print("Input must be an .srt file with timestamps.", file=sys.stderr)
        return 2

    input_path = args.input.expanduser().resolve()
    if input_path.suffix.lower() != ".srt":
        print("Input must be an .srt file with timestamps.", file=sys.stderr)
        return 2
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 2

    cues = parse_srt(input_path)
    if not cues:
        print(f"No subtitle cues found in {input_path}", file=sys.stderr)
        return 2

    video_path = args.video.expanduser().resolve() if args.video else None
    width = args.width
    height = args.height
    if video_path and video_path.exists():
        size = ffprobe_size(video_path)
        if size:
            width, height = size

    keywords = load_keywords(
        cues,
        keywords=args.keywords,
        keywords_file=args.keywords_file,
        auto_keyword_limit=args.auto_keywords,
    )
    if not keywords:
        print("No keywords found. Pass --keywords or --keywords-file.", file=sys.stderr)
        return 2

    try:
        preset = merge_style_preset(
            preset_name=args.style_preset,
            style_json=args.style_json,
            overrides=style_overrides_from_args(args),
        )
    except Exception as exc:
        print(f"Invalid style: {exc}", file=sys.stderr)
        return 2

    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else default_output_path(input_path, ".highlighted", ".ass")
    )
    report_path = (
        args.report.expanduser().resolve()
        if args.report
        else default_output_path(input_path, ".keywords", ".md")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    write_ass(
        cues,
        keywords,
        output_path,
        width=width,
        height=height,
        preset=preset,
    )
    write_keyword_report(keywords, report_path, cues)

    print(f"ASS: {output_path}")
    print(f"Keywords: {report_path}")
    print(f"Style preset: {args.style_preset}")
    print("Selected keywords:")
    print(", ".join(keywords))

    if video_path:
        if not video_path.exists():
            print(f"Video not found: {video_path}", file=sys.stderr)
            return 2
        burn_output = (
            args.burn_output.expanduser().resolve()
            if args.burn_output
            else default_output_path(video_path, ".highlighted", ".mp4")
        )
        burn_video(video_path, output_path, burn_output)
        print(f"Burned video: {burn_output}")

    if args.overlay_output:
        overlay_path = args.overlay_output.expanduser().resolve()
        duration = None
        if video_path and video_path.exists():
            duration = ffprobe_duration(video_path)
        if duration is None:
            duration = max(cue.end_ms for cue in cues) / 1000
        render_overlay(
            output_path,
            overlay_path,
            width=width,
            height=height,
            duration=duration,
            fps=args.fps,
        )
        print(f"Transparent overlay: {overlay_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
