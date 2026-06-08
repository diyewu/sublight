from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sublight.config import load_recent_projects, remember_project


class ConfigTests(unittest.TestCase):
    def test_recent_projects_are_deduplicated_and_limited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_root = Path(tmp) / "config"
            first = Path(tmp) / "one.sublight.json"
            second = Path(tmp) / "two.sublight.json"
            first.touch()
            second.touch()

            with patch("sublight.config.user_config_dir", return_value=config_root):
                remember_project(first, limit=2)
                remember_project(second, limit=2)
                remember_project(first, limit=2)
                projects = load_recent_projects(limit=2)

        self.assertEqual(projects, [str(first.resolve()), str(second.resolve())])


if __name__ == "__main__":
    unittest.main()
