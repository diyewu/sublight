from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal, Slot


class ExportWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, job: Callable[[], None], success_message: str) -> None:
        super().__init__()
        self.job = job
        self.success_message = success_message

    @Slot()
    def run(self) -> None:
        try:
            self.job()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(self.success_message)
