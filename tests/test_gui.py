from __future__ import annotations

import importlib.util
import unittest


class GuiModuleTests(unittest.TestCase):
    def test_gui_app_module_imports_without_pyside6(self) -> None:
        from sublight.gui import app

        self.assertTrue(callable(app.main))

    @unittest.skipUnless(importlib.util.find_spec("PySide6"), "PySide6 is not installed")
    def test_main_window_imports_when_pyside6_available(self) -> None:
        from sublight.gui.main_window import MainWindow

        self.assertEqual(MainWindow.__name__, "MainWindow")


if __name__ == "__main__":
    unittest.main()
