from __future__ import annotations

import html
import re
from pathlib import Path

from .models import Cue


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
