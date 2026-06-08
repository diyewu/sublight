from __future__ import annotations

import unittest
from pathlib import Path

from scripts.create_tutorial_video import SCENES


ROOT = Path(__file__).resolve().parents[1]


class TutorialAssetTests(unittest.TestCase):
    def test_tutorial_storyboard_covers_main_workflow(self) -> None:
        titles = [scene.title for scene in SCENES]

        self.assertEqual(
            titles,
            [
                "Import SRT",
                "Pick Keywords",
                "Tune Style",
                "Queue Exports",
                "Back To Editor",
            ],
        )

    def test_tutorial_video_asset_exists(self) -> None:
        path = ROOT / "examples" / "tutorial-video.mp4"

        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 50_000)


if __name__ == "__main__":
    unittest.main()

