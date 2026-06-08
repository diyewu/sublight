from __future__ import annotations

from dataclasses import dataclass


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
