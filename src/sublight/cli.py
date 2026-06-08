#!/usr/bin/env python3
"""
Generate keyword-highlighted subtitles from SRT.

Outputs:
  - ASS subtitle file with inline keyword styles
  - keyword report for review
  - optional burned-in video
  - optional transparent MOV subtitle overlay for importing back into editors
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{primary_color},{primary_color},{outline_color},{back_color},{bold},0,0,0,100,100,0,0,{border_style},{outline},{shadow},{alignment},{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


DEFAULT_STOPWORDS = {
    "一个",
    "一些",
    "这个",
    "那个",
    "这些",
    "那些",
    "自己",
    "因为",
    "所以",
    "但是",
    "然后",
    "就是",
    "其实",
    "感觉",
    "可能",
    "应该",
    "比较",
    "如果",
    "不是",
    "没有",
    "可以",
    "需要",
    "还是",
    "现在",
    "之前",
    "之后",
    "下来",
    "起来",
    "里面",
    "这里",
    "那里",
    "这么",
    "这么个",
    "一遍",
    "一下",
    "大家",
    "我们",
    "你们",
    "他们",
    "它们",
    "时候",
    "东西",
    "问题",
    "内容",
    "视频",
    "时间",
    "工具",
    "方式",
    "方案",
    "操作",
    "进行",
    "做法",
    "今天",
    "比如",
    "而是",
    "先别",
    "先做",
    "直接",
    "执行",
    "关注",
    "普通人",
    "也能",
    "做出",
    "记住",
    "玩转",
    "下一",
    "第二",
    "第三",
    "第一",
    "几个",
    "告诉",
    "这三",
    "目标",
    "结构",
    "上线",
    "完美",
    "系统",
    "跟进",
    "用户",
    "介绍",
    "提交",
    "感觉",
    "知道",
    "看到",
    "发现",
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "you",
    "your",
}


DOMAIN_TERMS = [
    "剪映",
    "CapCut",
    "字幕",
    "关键词",
    "高亮",
    "自动字幕",
    "识别字幕",
    "文稿匹配",
    "开源工具",
    "知识库",
    "时间线",
    "草稿",
    "导出",
    "导入",
    "AI",
    "LLM",
    "API",
    "MCP",
    "Codex",
    "ChatGPT",
    "Python",
    "脚本",
    "工作流",
    "自动化",
    "模型",
    "提示词",
    "转写",
    "校对",
    "复盘",
    "需求",
    "方案",
]


@dataclass(frozen=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class StylePreset:
    font: str = "STHeiti"
    font_size: int = 54
    margin_v: int = 82
    max_line_width: int = 34
    primary_color: str = "#FFFFFF"
    highlight_color: str = "#FFD400"
    outline_color: str = "#000000"
    keyword_outline_color: str = "#000000"
    back_color: str = "#000000"
    back_alpha: int = 127
    bold: bool = True
    keyword_bold: bool = True
    keyword_scale: float = 1.0
    outline: float = 3.0
    keyword_outline: float = 4.0
    shadow: float = 0.0
    alignment: int = 2
    border_style: int = 1


STYLE_PRESETS: dict[str, StylePreset] = {
    "bold-yellow": StylePreset(
        font_size=54,
        margin_v=82,
        highlight_color="#FFD400",
        outline=3.0,
        keyword_outline=4.0,
    ),
    "clean-blue": StylePreset(
        font_size=50,
        margin_v=86,
        highlight_color="#4DD8FF",
        outline=2.4,
        keyword_outline=3.2,
        shadow=0.4,
    ),
    "warm-orange": StylePreset(
        font_size=52,
        margin_v=84,
        primary_color="#FFF9EF",
        highlight_color="#FF8A2A",
        outline_color="#17120D",
        keyword_outline_color="#17120D",
        outline=3.0,
        keyword_outline=4.0,
    ),
    "large-focus": StylePreset(
        font_size=64,
        margin_v=74,
        max_line_width=26,
        highlight_color="#FFE600",
        keyword_scale=1.08,
        outline=4.0,
        keyword_outline=5.0,
    ),
    "soft-box": StylePreset(
        font_size=48,
        margin_v=74,
        primary_color="#FFFFFF",
        highlight_color="#FFE15A",
        outline_color="#000000",
        keyword_outline_color="#000000",
        back_color="#000000",
        back_alpha=96,
        outline=1.0,
        keyword_outline=2.4,
        shadow=0.0,
        border_style=3,
    ),
}


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def parse_srt_time(value: str) -> int:
    match = re.fullmatch(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})", value.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value!r}")
    hours, minutes, seconds, millis = match.groups()
    millis = millis.ljust(3, "0")[:3]
    return (
        int(hours) * 3_600_000
        + int(minutes) * 60_000
        + int(seconds) * 1_000
        + int(millis)
    )


def ass_time(ms: int) -> str:
    ms = max(ms, 0)
    cs = round(ms / 10)
    hours = cs // 360_000
    cs %= 360_000
    minutes = cs // 6_000
    cs %= 6_000
    seconds = cs // 100
    centis = cs % 100
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centis:02d}"


def parse_srt(path: Path) -> list[Cue]:
    text = read_text(path).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    blocks = re.split(r"\n{2,}", text)
    cues: list[Cue] = []
    synthetic_index = 1
    timing_re = re.compile(
        r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*"
        r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
    )

    for block in blocks:
        lines = [line.strip("\ufeff") for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        timing_line_idx = next((i for i, line in enumerate(lines) if "-->" in line), -1)
        if timing_line_idx < 0:
            continue

        timing_match = timing_re.search(lines[timing_line_idx])
        if not timing_match:
            continue

        index = synthetic_index
        if timing_line_idx > 0 and lines[0].strip().isdigit():
            index = int(lines[0].strip())

        body = "\n".join(lines[timing_line_idx + 1 :]).strip()
        body = re.sub(r"<[^>]+>", "", body)
        body = html.unescape(body)
        if not body:
            continue

        cues.append(
            Cue(
                index=index,
                start_ms=parse_srt_time(timing_match.group("start")),
                end_ms=parse_srt_time(timing_match.group("end")),
                text=body,
            )
        )
        synthetic_index += 1

    return cues


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def load_keywords(args: argparse.Namespace, cues: list[Cue]) -> list[str]:
    keywords: list[str] = []
    if args.keywords:
        keywords.extend(split_keywords(args.keywords))
    if args.keywords_file:
        for line in read_text(Path(args.keywords_file)).splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                keywords.extend(split_keywords(line))

    if not keywords:
        keywords = auto_keywords(cues, limit=args.auto_keywords)

    seen: set[str] = set()
    result: list[str] = []
    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue
        key = normalize_text(keyword)
        if key and key not in seen:
            seen.add(key)
            result.append(keyword)
    return sorted(result, key=len, reverse=True)


def split_keywords(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,，;；|、\n]+", value) if item.strip()]


def auto_keywords(cues: list[Cue], limit: int) -> list[str]:
    full_text = "\n".join(cue.text for cue in cues)
    scores: dict[str, float] = {}
    total_len = max(len(full_text), 1)

    for term in DOMAIN_TERMS:
        count = len(re.findall(re.escape(term), full_text, flags=re.IGNORECASE))
        if count:
            scores[term] = scores.get(term, 0.0) + count * (4.0 + min(len(term), 8))

    for token in re.findall(r"[A-Za-z][A-Za-z0-9_+#.-]{1,}", full_text):
        lowered = token.lower()
        if lowered in DEFAULT_STOPWORDS:
            continue
        scores[token] = scores.get(token, 0.0) + 3.0 + math.log2(len(token) + 1)

    cjk_runs = re.findall(r"[\u4e00-\u9fff]{2,}", full_text)
    for run in cjk_runs:
        for n in range(2, min(8, len(run)) + 1):
            for i in range(0, len(run) - n + 1):
                gram = run[i : i + n]
                if gram in DEFAULT_STOPWORDS:
                    continue
                if any(stop in gram for stop in ("这个", "那个", "然后", "就是", "可以", "没有")):
                    continue
                count = full_text.count(gram)
                if count < 2:
                    continue
                density_boost = min(3.0, count * 400 / total_len)
                scores[gram] = scores.get(gram, 0.0) + count * (n ** 1.35) + density_boost

    ranked = sorted(scores.items(), key=lambda item: (item[1], len(item[0])), reverse=True)
    selected: list[str] = []
    for term, score in ranked:
        if score <= 0:
            continue
        norm = normalize_text(term)
        if len(norm) < 2:
            continue
        if any(norm in normalize_text(existing) for existing in selected):
            continue
        if any(normalize_text(existing) in norm and len(term) <= len(existing) + 1 for existing in selected):
            continue
        selected.append(term)
        if len(selected) >= limit:
            break
    return selected


def ass_escape(text: str) -> str:
    text = text.replace("\\", r"\\")
    text = text.replace("{", r"\{").replace("}", r"\}")
    return text.replace("\n", r"\N")


def ass_color(rgb_hex: str, alpha: int = 0) -> str:
    value = rgb_hex.strip().lstrip("#")
    if len(value) != 6 or not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise ValueError(f"Invalid color: {rgb_hex!r}; expected #RRGGBB")
    if not 0 <= alpha <= 255:
        raise ValueError(f"Invalid alpha: {alpha!r}; expected 0-255")
    rr, gg, bb = value[0:2], value[2:4], value[4:6]
    return f"&H{alpha:02X}{bb.upper()}{gg.upper()}{rr.upper()}&"


def load_style_preset(args: argparse.Namespace) -> StylePreset:
    preset = STYLE_PRESETS[args.style_preset]

    if args.style_json:
        style_path = Path(args.style_json).expanduser().resolve()
        style_data = json.loads(read_text(style_path))
        valid_fields = set(StylePreset.__dataclass_fields__)
        unknown_fields = sorted(set(style_data) - valid_fields)
        if unknown_fields:
            raise ValueError(f"Unknown style field(s): {', '.join(unknown_fields)}")
        preset = replace(preset, **style_data)

    overrides = {}
    for arg_name, field_name in (
        ("font", "font"),
        ("font_size", "font_size"),
        ("margin_v", "margin_v"),
        ("max_line_width", "max_line_width"),
        ("highlight_color", "highlight_color"),
        ("outline", "outline"),
        ("shadow", "shadow"),
    ):
        value = getattr(args, arg_name)
        if value is not None:
            overrides[field_name] = value

    if overrides:
        preset = replace(preset, **overrides)

    return preset


def list_style_presets() -> None:
    for name, preset in STYLE_PRESETS.items():
        print(
            f"{name}: font_size={preset.font_size}, "
            f"highlight={preset.highlight_color}, outline={preset.outline}, "
            f"box={'yes' if preset.border_style == 3 else 'no'}"
        )


def display_width(text: str) -> int:
    width = 0
    for ch in text:
        width += 2 if "\u4e00" <= ch <= "\u9fff" else 1
    return width


def wrap_cjk_line(text: str, max_width: int) -> str:
    raw = re.sub(r"\s+", " ", text.strip())
    if display_width(raw) <= max_width:
        return raw

    break_chars = "，。！？；、,.!?; "
    lines: list[str] = []
    start = 0
    while start < len(raw):
        width = 0
        last_break = -1
        end = start
        while end < len(raw):
            ch = raw[end]
            width += 2 if "\u4e00" <= ch <= "\u9fff" else 1
            if ch in break_chars:
                last_break = end + 1
            if width > max_width:
                break
            end += 1

        if end >= len(raw):
            lines.append(raw[start:].strip())
            break
        if last_break > start:
            end = last_break
        lines.append(raw[start:end].strip())
        start = end

    return "\n".join(line for line in lines if line)


def find_keyword_spans(text: str, keywords: Iterable[str]) -> list[tuple[int, int]]:
    lowered = text.lower()
    spans: list[tuple[int, int]] = []

    for keyword in keywords:
        if not keyword:
            continue
        pattern = re.escape(keyword)
        flags = re.IGNORECASE if re.search(r"[A-Za-z]", keyword) else 0
        for match in re.finditer(pattern, text, flags=flags):
            start, end = match.span()
            if start == end:
                continue
            if re.search(r"[A-Za-z0-9]", keyword):
                before = lowered[start - 1] if start > 0 else ""
                after = lowered[end] if end < len(lowered) else ""
                if before and re.match(r"[a-z0-9_]", before):
                    continue
                if after and re.match(r"[a-z0-9_]", after):
                    continue
            if any(not (end <= a or start >= b) for a, b in spans):
                continue
            spans.append((start, end))

    return sorted(spans)


def style_text(text: str, keywords: list[str], preset: StylePreset) -> str:
    spans = find_keyword_spans(text, keywords)
    if not spans:
        return ass_escape(text)

    chunks: list[str] = []
    cursor = 0
    tag_parts = [
        r"\b1" if preset.keyword_bold else r"\b0",
        r"\c" + ass_color(preset.highlight_color),
        r"\3c" + ass_color(preset.keyword_outline_color),
        rf"\bord{preset.keyword_outline:g}",
    ]
    if preset.keyword_scale != 1.0:
        tag_parts.append(rf"\fs{round(preset.font_size * preset.keyword_scale)}")
    start_tag = "{" + "".join(tag_parts) + "}"
    end_tag = r"{\rDefault}"
    for start, end in spans:
        chunks.append(ass_escape(text[cursor:start]))
        chunks.append(start_tag + ass_escape(text[start:end]) + end_tag)
        cursor = end
    chunks.append(ass_escape(text[cursor:]))
    return "".join(chunks)


def write_ass(
    cues: list[Cue],
    keywords: list[str],
    out_path: Path,
    *,
    width: int,
    height: int,
    preset: StylePreset,
) -> None:
    header = ASS_HEADER.format(
        width=width,
        height=height,
        font=preset.font,
        font_size=preset.font_size,
        primary_color=ass_color(preset.primary_color),
        outline_color=ass_color(preset.outline_color),
        back_color=ass_color(preset.back_color, preset.back_alpha),
        bold=1 if preset.bold else 0,
        border_style=preset.border_style,
        outline=preset.outline,
        shadow=preset.shadow,
        alignment=preset.alignment,
        margin_l=40,
        margin_r=40,
        margin_v=preset.margin_v,
    )

    lines = [header]
    for cue in cues:
        wrapped = wrap_cjk_line(cue.text, preset.max_line_width)
        styled = style_text(wrapped, keywords, preset)
        lines.append(
            "Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n".format(
                start=ass_time(cue.start_ms),
                end=ass_time(cue.end_ms),
                text=styled,
            )
        )

    out_path.write_text("".join(lines), encoding="utf-8")


def write_keyword_report(keywords: list[str], out_path: Path, cues: list[Cue]) -> None:
    text = "\n".join(cue.text for cue in cues)
    lines = ["# Subtitle Highlight Keywords", ""]
    for keyword in keywords:
        count = len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE))
        lines.append(f"- {keyword} ({count})")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


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
    subprocess.run(cmd, check=True)


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
    subprocess.run(cmd, check=True)


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


def main() -> int:
    args = parse_args()
    if args.list_style_presets:
        list_style_presets()
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

    keywords = load_keywords(args, cues)
    if not keywords:
        print("No keywords found. Pass --keywords or --keywords-file.", file=sys.stderr)
        return 2

    try:
        preset = load_style_preset(args)
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
