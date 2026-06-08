from __future__ import annotations

from sublight.core.models import HighlightSpan


def normalized_manual_spans(
    spans: tuple[HighlightSpan, ...],
    *,
    text_length: int,
) -> tuple[HighlightSpan, ...]:
    ranges: list[tuple[int, int]] = []
    for span in spans:
        start = max(0, min(span.start, text_length))
        end = max(0, min(span.end, text_length))
        if start < end:
            ranges.append((start, end))
    return tuple(HighlightSpan(start, end, source="manual") for start, end in merge_ranges(ranges))


def add_manual_spans(
    spans: tuple[HighlightSpan, ...],
    selections: list[tuple[int, int]],
    *,
    text_length: int,
) -> tuple[HighlightSpan, ...]:
    ranges = [(span.start, span.end) for span in spans]
    ranges.extend(selections)
    return tuple(HighlightSpan(start, end, source="manual") for start, end in merge_ranges(
        clamp_ranges(ranges, text_length=text_length)
    ))


def remove_manual_spans(
    spans: tuple[HighlightSpan, ...],
    selections: list[tuple[int, int]],
    *,
    text_length: int,
) -> tuple[HighlightSpan, ...]:
    remaining = clamp_ranges([(span.start, span.end) for span in spans], text_length=text_length)
    removals = merge_ranges(clamp_ranges(selections, text_length=text_length))
    for remove_start, remove_end in removals:
        next_remaining: list[tuple[int, int]] = []
        for start, end in remaining:
            if end <= remove_start or start >= remove_end:
                next_remaining.append((start, end))
                continue
            if start < remove_start:
                next_remaining.append((start, remove_start))
            if remove_end < end:
                next_remaining.append((remove_end, end))
        remaining = next_remaining
    return tuple(HighlightSpan(start, end, source="manual") for start, end in merge_ranges(remaining))


def ranges_are_covered(
    spans: tuple[HighlightSpan, ...],
    selections: list[tuple[int, int]],
    *,
    text_length: int,
) -> bool:
    selected_ranges = merge_ranges(clamp_ranges(selections, text_length=text_length))
    if not selected_ranges:
        return False
    covered_ranges = merge_ranges(
        clamp_ranges([(span.start, span.end) for span in spans], text_length=text_length)
    )
    for selected_start, selected_end in selected_ranges:
        cursor = selected_start
        for covered_start, covered_end in covered_ranges:
            if covered_end <= cursor:
                continue
            if covered_start > cursor:
                break
            cursor = max(cursor, covered_end)
            if cursor >= selected_end:
                break
        if cursor < selected_end:
            return False
    return True


def clamp_ranges(
    ranges: list[tuple[int, int]],
    *,
    text_length: int,
) -> list[tuple[int, int]]:
    clamped: list[tuple[int, int]] = []
    for start, end in ranges:
        clamped_start = max(0, min(start, text_length))
        clamped_end = max(0, min(end, text_length))
        if clamped_start < clamped_end:
            clamped.append((clamped_start, clamped_end))
    return clamped


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue
        previous_start, previous_end = merged[-1]
        merged[-1] = (previous_start, max(previous_end, end))
    return merged
