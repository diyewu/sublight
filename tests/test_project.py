from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sublight.core.models import Cue, HighlightSpan, KeywordRule, Project
from sublight.core.project import load_project, save_project
from sublight.styles.ass import render_ass
from sublight.styles.presets import merge_style_preset


class ProjectTests(unittest.TestCase):
    def test_save_and_load_project(self) -> None:
        cue = Cue(
            id="cue-1",
            index=1,
            start_ms=0,
            end_ms=1500,
            text="Hello Codex",
            manual_highlights=(HighlightSpan(start=6, end=11),),
        )
        project = Project(
            srt_path="input.srt",
            video_path="video.mp4",
            cues=[cue],
            keyword_rules=[KeywordRule(text="Codex")],
            active_style="clean-blue",
            custom_styles={"brand": {"highlight_color": "#00E5FF"}},
            export_settings={"width": 1280, "height": 720},
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project.sublight.json"
            save_project(project, path)
            loaded = load_project(path)

        self.assertEqual(loaded.active_style, "clean-blue")
        self.assertTrue(loaded.srt_path.endswith("input.srt"))
        self.assertEqual(loaded.cues[0].manual_highlights[0].start, 6)
        self.assertEqual(loaded.keyword_rules[0].text, "Codex")
        self.assertEqual(loaded.custom_styles["brand"]["highlight_color"], "#00E5FF")
        self.assertEqual(loaded.export_settings["width"], 1280)

    def test_load_project_migrates_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.sublight.json"
            path.write_text(
                json.dumps(
                    {
                        "cues": [
                            {
                                "index": 1,
                                "start_ms": 0,
                                "end_ms": 1000,
                                "text": "Hello",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            project = load_project(path)

        self.assertEqual(project.version, 1)
        self.assertEqual(project.active_style, "bold-yellow")
        self.assertEqual(project.cues[0].manual_highlights, ())

    def test_manual_highlights_render_without_keyword_rule(self) -> None:
        cue = Cue(
            index=1,
            start_ms=0,
            end_ms=1000,
            text="Hello Codex",
            manual_highlights=(HighlightSpan(start=6, end=11),),
        )
        preset = merge_style_preset(preset_name="bold-yellow")

        ass = render_ass([cue], [], width=1280, height=720, preset=preset)

        self.assertIn(r"{\b1\c&H0000D4FF&\3c&H00000000&\bord4}Codex{\rDefault}", ass)


if __name__ == "__main__":
    unittest.main()
