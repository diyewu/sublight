from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sublight.styles.presets import merge_style_preset


class StyleJsonTests(unittest.TestCase):
    def test_merge_style_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "brand.json"
            path.write_text(
                json.dumps(
                    {
                        "font_size": 60,
                        "keyword_font_size": 72,
                        "highlight_color": "#00E5FF",
                        "keyword_scale": 1.08,
                    }
                ),
                encoding="utf-8",
            )
            preset = merge_style_preset(preset_name="bold-yellow", style_json=str(path))

        self.assertEqual(preset.font_size, 60)
        self.assertEqual(preset.keyword_font_size, 72)
        self.assertEqual(preset.resolved_keyword_font_size(), 72)
        self.assertEqual(preset.highlight_color, "#00E5FF")
        self.assertEqual(preset.keyword_scale, 1.08)

    def test_keyword_font_size_falls_back_to_scale_for_old_styles(self) -> None:
        preset = merge_style_preset(
            preset_name="bold-yellow",
            overrides={"font_size": 50, "keyword_scale": 1.2},
        )

        self.assertIsNone(preset.keyword_font_size)
        self.assertEqual(preset.resolved_keyword_font_size(), 60)

    def test_unknown_style_json_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps({"not_a_field": True}), encoding="utf-8")

            with self.assertRaises(ValueError):
                merge_style_preset(preset_name="bold-yellow", style_json=str(path))


if __name__ == "__main__":
    unittest.main()
