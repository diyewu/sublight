from __future__ import annotations

import re
from collections.abc import Iterable


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
