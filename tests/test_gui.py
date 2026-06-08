from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class GuiModuleTests(unittest.TestCase):
    def test_gui_app_module_imports_without_pyside6(self) -> None:
        from sublight.gui import app

        self.assertTrue(callable(app.main))

    def test_gui_app_runs_as_top_level_pyinstaller_script(self) -> None:
        script_path = (
            Path(__file__).resolve().parents[1] / "src" / "sublight" / "gui" / "app.py"
        )
        spec = importlib.util.spec_from_file_location("pyinstaller_app", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        qtwidgets = types.ModuleType("PySide6.QtWidgets")
        main_window_module = types.ModuleType("sublight.gui.main_window")
        events: list[str] = []

        class FakeQApplication:
            def __init__(self, argv: list[str]) -> None:
                events.append("app")

            def exec(self) -> int:
                events.append("exec")
                return 0

        class FakeMainWindow:
            def __init__(self) -> None:
                events.append("window")

            def show(self) -> None:
                events.append("show")

        qtwidgets.QApplication = FakeQApplication
        main_window_module.MainWindow = FakeMainWindow

        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(
            sys.modules,
            {
                "PySide6": types.ModuleType("PySide6"),
                "PySide6.QtWidgets": qtwidgets,
                "sublight.gui.main_window": main_window_module,
            },
        ):
            spec.loader.exec_module(module)
            self.assertEqual(module.main(), 0)

        self.assertEqual(events, ["app", "window", "show", "exec"])

    @unittest.skipUnless(importlib.util.find_spec("PySide6"), "PySide6 is not installed")
    def test_main_window_imports_when_pyside6_available(self) -> None:
        from sublight.gui.main_window import MainWindow

        self.assertEqual(MainWindow.__name__, "MainWindow")


if __name__ == "__main__":
    unittest.main()
