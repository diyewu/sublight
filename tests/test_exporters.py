from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from sublight.exporters.ffmpeg import FfmpegCancelled, FfmpegRunner, require_tool
from sublight.exporters.video_exporter import burn_preview_segment, burn_video


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

    def test_burn_video_accepts_custom_runner(self) -> None:
        captured: dict[str, list[str]] = {}

        def fake_runner(cmd: list[str]) -> None:
            captured["cmd"] = cmd

        burn_video(
            Path("input.mp4"),
            Path("captions.ass"),
            Path("output.mp4"),
            runner=fake_runner,
        )

        self.assertEqual(captured["cmd"][0], "ffmpeg")
        self.assertEqual(captured["cmd"][-1], "output.mp4")

    def test_ffmpeg_runner_can_be_cancelled_before_start(self) -> None:
        runner = FfmpegRunner()
        runner.cancel()

        with patch("sublight.exporters.ffmpeg.require_tool", return_value="ffmpeg"):
            with self.assertRaises(FfmpegCancelled):
                runner.run(["ffmpeg", "-version"])


if __name__ == "__main__":
    unittest.main()
