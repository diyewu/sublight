from __future__ import annotations

import re
from pathlib import Path

from sublight.core.highlights import find_keyword_spans
from sublight.core.models import Cue, HighlightSpan

from .schema import StylePreset


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


def merged_highlight_spans(
    text: str,
    keywords: list[str],
    manual_spans: tuple[HighlightSpan, ...] = (),
) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []

    for span in sorted(manual_spans, key=lambda item: (item.start, item.end)):
        start = max(0, min(span.start, len(text)))
        end = max(0, min(span.end, len(text)))
        if start >= end:
            continue
        if any(not (end <= a or start >= b) for a, b in spans):
            continue
        spans.append((start, end))

    for start, end in find_keyword_spans(text, keywords):
        if any(not (end <= a or start >= b) for a, b in spans):
            continue
        spans.append((start, end))

    return sorted(spans)


def style_text(
    text: str,
    keywords: list[str],
    preset: StylePreset,
    manual_spans: tuple[HighlightSpan, ...] = (),
) -> str:
    spans = merged_highlight_spans(text, keywords, manual_spans)
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
    keyword_font_size = preset.resolved_keyword_font_size()
    if preset.keyword_font_size is not None or keyword_font_size != preset.font_size:
        tag_parts.append(rf"\fs{keyword_font_size}")
    start_tag = "{" + "".join(tag_parts) + "}"
    end_tag = r"{\rDefault}"
    for start, end in spans:
        chunks.append(ass_escape(text[cursor:start]))
        chunks.append(start_tag + ass_escape(text[start:end]) + end_tag)
        cursor = end
    chunks.append(ass_escape(text[cursor:]))
    return "".join(chunks)


def render_ass(
    cues: list[Cue],
    keywords: list[str],
    *,
    width: int,
    height: int,
    preset: StylePreset,
) -> str:
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
        manual_spans = cue.manual_highlights if wrapped == cue.text else ()
        styled = style_text(wrapped, keywords, preset, manual_spans)
        lines.append(
            "Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n".format(
                start=ass_time(cue.start_ms),
                end=ass_time(cue.end_ms),
                text=styled,
            )
        )

    return "".join(lines)


def write_ass(
    cues: list[Cue],
    keywords: list[str],
    out_path: Path,
    *,
    width: int,
    height: int,
    preset: StylePreset,
) -> None:
    out_path.write_text(
        render_ass(cues, keywords, width=width, height=height, preset=preset),
        encoding="utf-8",
    )
