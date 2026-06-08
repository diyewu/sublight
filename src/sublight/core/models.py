from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class HighlightSpan:
    start: int
    end: int
    style_role: str = "keyword"
    source: str = "keyword"


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
