from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HighlightSpan:
    start: int
    end: int
    style_role: str = "keyword"
    source: str = "manual"


@dataclass(frozen=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str
    id: str | None = None
    manual_highlights: tuple[HighlightSpan, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class KeywordRule:
    text: str
    case_sensitive: bool = False
    match_whole_word: bool = True
    enabled: bool = True
    style_role: str = "keyword"


@dataclass
class Project:
    version: int = 1
    srt_path: str | None = None
    video_path: str | None = None
    cues: list[Cue] = field(default_factory=list)
    keyword_rules: list[KeywordRule] = field(default_factory=list)
    active_style: str = "bold-yellow"
    custom_styles: dict[str, dict[str, Any]] = field(default_factory=dict)
    export_settings: dict[str, Any] = field(default_factory=dict)
