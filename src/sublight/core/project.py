from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import Cue, HighlightSpan, KeywordRule, Project
from .srt import read_text


PROJECT_VERSION = 1


def span_to_dict(span: HighlightSpan) -> dict[str, Any]:
    return asdict(span)


def span_from_dict(data: dict[str, Any]) -> HighlightSpan:
    return HighlightSpan(
        start=int(data["start"]),
        end=int(data["end"]),
        style_role=str(data.get("style_role", "keyword")),
        source=str(data.get("source", "manual")),
    )


def cue_to_dict(cue: Cue) -> dict[str, Any]:
    return {
        "id": cue.id,
        "index": cue.index,
        "start_ms": cue.start_ms,
        "end_ms": cue.end_ms,
        "text": cue.text,
        "manual_highlights": [span_to_dict(span) for span in cue.manual_highlights],
    }


def cue_from_dict(data: dict[str, Any]) -> Cue:
    return Cue(
        id=data.get("id"),
        index=int(data["index"]),
        start_ms=int(data["start_ms"]),
        end_ms=int(data["end_ms"]),
        text=str(data["text"]),
        manual_highlights=tuple(
            span_from_dict(span) for span in data.get("manual_highlights", [])
        ),
    )


def keyword_rule_to_dict(rule: KeywordRule) -> dict[str, Any]:
    return asdict(rule)


def keyword_rule_from_dict(data: dict[str, Any]) -> KeywordRule:
    return KeywordRule(
        text=str(data["text"]),
        case_sensitive=bool(data.get("case_sensitive", False)),
        match_whole_word=bool(data.get("match_whole_word", True)),
        enabled=bool(data.get("enabled", True)),
        style_role=str(data.get("style_role", "keyword")),
    )


def project_to_dict(project: Project) -> dict[str, Any]:
    return {
        "version": PROJECT_VERSION,
        "srt_path": project.srt_path,
        "video_path": project.video_path,
        "cues": [cue_to_dict(cue) for cue in project.cues],
        "keyword_rules": [keyword_rule_to_dict(rule) for rule in project.keyword_rules],
        "active_style": project.active_style,
        "custom_styles": project.custom_styles,
        "export_settings": project.export_settings,
    }


def project_from_dict(data: dict[str, Any], *, base_dir: Path | None = None) -> Project:
    migrated = migrate_project_data(data)
    return Project(
        version=int(migrated["version"]),
        srt_path=resolve_project_path(migrated.get("srt_path"), base_dir),
        video_path=resolve_project_path(migrated.get("video_path"), base_dir),
        cues=[cue_from_dict(cue) for cue in migrated.get("cues", [])],
        keyword_rules=[
            keyword_rule_from_dict(rule) for rule in migrated.get("keyword_rules", [])
        ],
        active_style=str(migrated.get("active_style", "bold-yellow")),
        custom_styles=dict(migrated.get("custom_styles", {})),
        export_settings=dict(migrated.get("export_settings", {})),
    )


def migrate_project_data(data: dict[str, Any]) -> dict[str, Any]:
    migrated = dict(data)
    migrated.setdefault("version", PROJECT_VERSION)
    migrated.setdefault("srt_path", None)
    migrated.setdefault("video_path", None)
    migrated.setdefault("cues", [])
    migrated.setdefault("keyword_rules", [])
    migrated.setdefault("active_style", "bold-yellow")
    migrated.setdefault("custom_styles", {})
    migrated.setdefault("export_settings", {})

    for cue in migrated["cues"]:
        cue.setdefault("manual_highlights", [])

    return migrated


def resolve_project_path(path_value: str | None, base_dir: Path | None) -> str | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute() or base_dir is None:
        return str(path)
    return str((base_dir / path).resolve())


def save_project(project: Project, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(project_to_dict(project), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_project(path: Path) -> Project:
    data = json.loads(read_text(path))
    return project_from_dict(data, base_dir=path.parent)
