from __future__ import annotations

import re
from pathlib import Path

from sublight.core.models import Cue


def write_keyword_report(keywords: list[str], out_path: Path, cues: list[Cue]) -> None:
    text = "\n".join(cue.text for cue in cues)
    lines = ["# Subtitle Highlight Keywords", ""]
    for keyword in keywords:
        count = len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE))
        lines.append(f"- {keyword} ({count})")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
