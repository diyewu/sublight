from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from sublight.exporters.ffmpeg import require_tool
from sublight.exporters.video_exporter import burn_preview_segment


class FfmpegHelperTests(unittest.TestCase):
    def test_require_tool_reports_missing_binary(self) -> None:
        with patch("shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                require_tool("ffmpeg")

    def test_preview_export_command_contains_segment_options(self) -> None:
        captured: dict[str, list[str]] = {}

        def fake_run(cmd: list[str]) -> None:
            captured["cmd"] = cmd

        with patch("sublight.exporters.video_exporter.run_ffmpeg", side_effect=fake_run):
            burn_preview_segment(
                Path("input.mp4"),
                Path("captions.ass"),
                Path("preview.mp4"),
                start_seconds=12.5,
                duration_seconds=5.0,
            )

        cmd = captured["cmd"]
        self.assertIn("-ss", cmd)
        self.assertIn("12.500", cmd)
        self.assertIn("-t", cmd)
        self.assertIn("5.000", cmd)
        self.assertEqual(cmd[-1], "preview.mp4")


if __name__ == "__main__":
    unittest.main()
