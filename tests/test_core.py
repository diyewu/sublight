from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sublight.core.highlights import find_keyword_spans
from sublight.core.keywords import load_keywords
from sublight.core.srt import parse_srt, parse_srt_time
from sublight.styles.ass import ass_color, render_ass
from sublight.styles.presets import merge_style_preset


class SrtTests(unittest.TestCase):
    def test_parse_srt_time(self) -> None:
        self.assertEqual(parse_srt_time("00:01:02,345"), 62_345)
        self.assertEqual(parse_srt_time("1:02:03.4"), 3_723_400)

    def test_parse_srt_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.srt"
            path.write_text(
                "\ufeff1\n"
                "00:00:00,000 --> 00:00:01,500\n"
                "<b>Hello</b> Codex\n\n"
                "2\n"
                "00:00:02,000 --> 00:00:03,000\n"
                "飞书知识库\n",
                encoding="utf-8",
            )
            cues = parse_srt(path)

        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].text, "Hello Codex")
        self.assertEqual(cues[1].start_ms, 2_000)
        self.assertEqual(cues[1].text, "飞书知识库")


class KeywordTests(unittest.TestCase):
    def test_load_keywords_deduplicates_normalized_terms(self) -> None:
        keywords = load_keywords([], keywords="Codex,codex,飞书知识库", auto_keyword_limit=5)
        self.assertEqual(keywords, ["Codex", "飞书知识库"])

    def test_find_keyword_spans_respects_ascii_word_boundary(self) -> None:
        spans = find_keyword_spans("Codex and myCodex are different", ["Codex"])
        self.assertEqual(spans, [(0, 5)])


class StyleTests(unittest.TestCase):
    def test_ass_color_converts_rgb_to_ass_bgr(self) -> None:
        self.assertEqual(ass_color("#FFD400"), "&H0000D4FF&")
        self.assertEqual(ass_color("#000000", 127), "&H7F000000&")

    def test_merge_style_preset_with_overrides(self) -> None:
        preset = merge_style_preset(
            preset_name="bold-yellow",
            overrides={"font_size": 42, "highlight_color": "#00E5FF"},
        )
        self.assertEqual(preset.font_size, 42)
        self.assertEqual(preset.highlight_color, "#00E5FF")

    def test_render_ass_contains_highlight_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.srt"
            path.write_text(
                "1\n00:00:00,000 --> 00:00:01,500\nHello Codex\n",
                encoding="utf-8",
            )
            cues = parse_srt(path)
        preset = merge_style_preset(preset_name="bold-yellow")
        ass = render_ass(cues, ["Codex"], width=1280, height=720, preset=preset)

        self.assertIn("PlayResX: 1280", ass)
        self.assertIn(r"{\b1\c&H0000D4FF&\3c&H00000000&\bord4}Codex{\rDefault}", ass)


if __name__ == "__main__":
    unittest.main()
