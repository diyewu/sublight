from __future__ import annotations

import json
import os
import sys
from pathlib import Path


APP_NAME = "SubLight"


def user_config_dir() -> Path:
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / APP_NAME


def recent_projects_path() -> Path:
    return user_config_dir() / "recent-projects.json"


def autosave_project_path() -> Path:
    return user_config_dir() / "autosave.sublight.json"


def load_recent_projects(limit: int = 10) -> list[str]:
    path = recent_projects_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    projects = [str(item) for item in data if isinstance(item, str)]
    return projects[:limit]


def remember_project(path: Path, limit: int = 10) -> list[str]:
    resolved = str(path.expanduser().resolve())
    projects = [item for item in load_recent_projects(limit=limit) if item != resolved]
    projects.insert(0, resolved)
    projects = projects[:limit]
    recent_path = recent_projects_path()
    recent_path.parent.mkdir(parents=True, exist_ok=True)
    recent_path.write_text(
        json.dumps(projects, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return projects
