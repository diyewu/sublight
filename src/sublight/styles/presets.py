from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from sublight.core.srt import read_text

from .schema import StylePreset


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


def merge_style_preset(
    *,
    preset_name: str,
    style_json: str | None = None,
    overrides: dict[str, object] | None = None,
) -> StylePreset:
    preset = STYLE_PRESETS[preset_name]

    if style_json:
        style_path = Path(style_json).expanduser().resolve()
        style_data = json.loads(read_text(style_path))
        valid_fields = set(StylePreset.__dataclass_fields__)
        unknown_fields = sorted(set(style_data) - valid_fields)
        if unknown_fields:
            raise ValueError(f"Unknown style field(s): {', '.join(unknown_fields)}")
        preset = replace(preset, **style_data)

    clean_overrides = {key: value for key, value in (overrides or {}).items() if value is not None}
    if clean_overrides:
        preset = replace(preset, **clean_overrides)

    return preset


def style_preset_lines() -> list[str]:
    lines: list[str] = []
    for name, preset in STYLE_PRESETS.items():
        lines.append(
            f"{name}: font_size={preset.font_size}, "
            f"highlight={preset.highlight_color}, outline={preset.outline}, "
            f"box={'yes' if preset.border_style == 3 else 'no'}"
        )
    return lines
