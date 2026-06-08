from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QComboBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sublight.core.models import Cue, HighlightSpan, KeywordRule, Project
from sublight.core.project import load_project, save_project
from sublight.core.srt import parse_srt
from sublight.exporters.ass_exporter import write_keyword_report
from sublight.exporters.ffmpeg import ffprobe_duration, ffprobe_size
from sublight.exporters.video_exporter import burn_video, render_overlay
from sublight.styles.ass import write_ass
from sublight.styles.presets import STYLE_PRESETS, merge_style_preset


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SubLight")
        self.resize(1180, 760)

        self.project = Project()
        self.project_path: Path | None = None
        self.current_index: int | None = None

        self.subtitle_list = QListWidget()
        self.subtitle_list.currentRowChanged.connect(self.select_cue)

        self.cue_editor = QTextEdit()
        self.cue_editor.setPlaceholderText("Import an SRT file to start.")

        self.style_combo = QComboBox()
        self.style_combo.addItems(sorted(STYLE_PRESETS))
        self.style_combo.setCurrentText(self.project.active_style)
        self.style_combo.currentTextChanged.connect(self.set_active_style)

        self.video_label = QLabel("No video imported")
        self.project_label = QLabel("Untitled project")
        self.status_label = QLabel("Ready")

        self.setCentralWidget(self.build_layout())
        self.refresh_view()

    def build_layout(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        top_bar = QHBoxLayout()
        for label, handler in (
            ("Import SRT", self.import_srt),
            ("Import Video", self.import_video),
            ("Open Project", self.open_project),
            ("Save Project", self.save_project_as),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            top_bar.addWidget(button)
        top_bar.addStretch(1)
        top_bar.addWidget(self.project_label)
        layout.addLayout(top_bar)

        body = QGridLayout()
        body.addWidget(self.build_subtitle_box(), 0, 0)
        body.addWidget(self.build_editor_box(), 0, 1)
        body.addWidget(self.build_style_export_box(), 0, 2)
        body.setColumnStretch(0, 2)
        body.setColumnStretch(1, 4)
        body.setColumnStretch(2, 2)
        layout.addLayout(body, 1)
        layout.addWidget(self.status_label)
        return root

    def build_subtitle_box(self) -> QGroupBox:
        box = QGroupBox("Subtitles")
        layout = QVBoxLayout(box)
        layout.addWidget(self.subtitle_list)
        return box

    def build_editor_box(self) -> QGroupBox:
        box = QGroupBox("Cue Editor")
        layout = QVBoxLayout(box)
        layout.addWidget(self.cue_editor)

        controls = QHBoxLayout()
        for label, handler in (
            ("Highlight Selection", self.highlight_selection),
            ("Clear Cue Highlights", self.clear_cue_highlights),
            ("Apply Selection Globally", self.apply_selection_globally),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            controls.addWidget(button)
        layout.addLayout(controls)
        return box

    def build_style_export_box(self) -> QGroupBox:
        box = QGroupBox("Style and Export")
        layout = QVBoxLayout(box)
        layout.addWidget(QLabel("Style preset"))
        layout.addWidget(self.style_combo)
        layout.addWidget(self.video_label)

        for label, handler in (
            ("Export ASS", self.export_ass),
            ("Export Green Overlay", self.export_green_overlay),
            ("Burn Video", self.export_burned_video),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            layout.addWidget(button)

        layout.addStretch(1)
        return box

    def import_srt(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import SRT",
            "",
            "SubRip subtitles (*.srt)",
        )
        if not path:
            return
        try:
            cues = parse_srt(Path(path))
        except Exception as exc:
            self.show_error("Failed to import SRT", exc)
            return
        self.project.srt_path = path
        self.project.cues = cues
        self.current_index = 0 if cues else None
        self.refresh_view()
        self.status_label.setText(f"Imported {len(cues)} subtitle cues")

    def import_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Video",
            "",
            "Video files (*.mp4 *.mov *.mkv *.webm);;All files (*)",
        )
        if not path:
            return
        self.project.video_path = path
        self.refresh_view()
        self.status_label.setText(f"Imported video: {Path(path).name}")

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SubLight Project",
            "",
            "SubLight project (*.sublight.json);;JSON files (*.json)",
        )
        if not path:
            return
        try:
            self.project = load_project(Path(path))
        except Exception as exc:
            self.show_error("Failed to open project", exc)
            return
        self.project_path = Path(path)
        self.current_index = 0 if self.project.cues else None
        self.refresh_view()
        self.status_label.setText(f"Opened project: {Path(path).name}")

    def save_project_as(self) -> None:
        default_path = str(self.project_path or Path.cwd() / "project.sublight.json")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save SubLight Project",
            default_path,
            "SubLight project (*.sublight.json);;JSON files (*.json)",
        )
        if not path:
            return
        try:
            save_project(self.project, Path(path))
        except Exception as exc:
            self.show_error("Failed to save project", exc)
            return
        self.project_path = Path(path)
        self.refresh_view()
        self.status_label.setText(f"Saved project: {Path(path).name}")

    def select_cue(self, row: int) -> None:
        if row < 0 or row >= len(self.project.cues):
            self.current_index = None
            self.cue_editor.clear()
            return
        self.commit_editor_text()
        self.current_index = row
        self.cue_editor.setPlainText(self.project.cues[row].text)

    def set_active_style(self, style_name: str) -> None:
        self.project.active_style = style_name

    def highlight_selection(self) -> None:
        index = self.require_current_cue()
        if index is None:
            return
        cursor = self.cue_editor.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        if start == end:
            self.status_label.setText("Select text in the cue editor first")
            return
        self.commit_editor_text()
        cue = self.project.cues[index]
        spans = cue.manual_highlights + (
            HighlightSpan(start=start, end=end, source="manual"),
        )
        self.project.cues[index] = replace(cue, manual_highlights=spans)
        self.refresh_subtitle_item(index)
        self.status_label.setText("Highlighted selected text")

    def clear_cue_highlights(self) -> None:
        index = self.require_current_cue()
        if index is None:
            return
        self.commit_editor_text()
        cue = self.project.cues[index]
        self.project.cues[index] = replace(cue, manual_highlights=())
        self.refresh_subtitle_item(index)
        self.status_label.setText("Cleared cue highlights")

    def apply_selection_globally(self) -> None:
        cursor = self.cue_editor.textCursor()
        selected = cursor.selectedText().strip()
        if not selected:
            self.status_label.setText("Select a word or phrase first")
            return
        if not any(rule.text == selected for rule in self.project.keyword_rules):
            self.project.keyword_rules.append(KeywordRule(text=selected))
        self.status_label.setText(f"Added global keyword: {selected}")

    def export_ass(self) -> None:
        if not self.project.cues:
            self.status_label.setText("Import subtitles first")
            return
        default_path = Path(self.project.srt_path or "subtitles.srt").with_suffix(".ass")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export ASS",
            str(default_path),
            "Advanced SubStation Alpha (*.ass)",
        )
        if not path:
            return
        try:
            self.write_ass_output(Path(path))
        except Exception as exc:
            self.show_error("Failed to export ASS", exc)
            return
        self.status_label.setText(f"Exported ASS: {Path(path).name}")

    def export_green_overlay(self) -> None:
        if not self.project.cues:
            self.status_label.setText("Import subtitles first")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Green Overlay",
            "subtitle-overlay.mov",
            "QuickTime movie (*.mov)",
        )
        if not path:
            return
        try:
            ass_path = Path(path).with_suffix(".ass")
            self.write_ass_output(ass_path)
            width, height = self.export_size()
            duration = self.export_duration()
            render_overlay(
                ass_path,
                Path(path),
                width=width,
                height=height,
                duration=duration,
                fps=int(self.project.export_settings.get("fps", 30)),
            )
        except Exception as exc:
            self.show_error("Failed to export overlay", exc)
            return
        self.status_label.setText(f"Exported overlay: {Path(path).name}")

    def export_burned_video(self) -> None:
        if not self.project.video_path:
            self.status_label.setText("Import a video first")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Burn Video",
            "highlighted.mp4",
            "MP4 video (*.mp4)",
        )
        if not path:
            return
        try:
            ass_path = Path(path).with_suffix(".ass")
            self.write_ass_output(ass_path)
            burn_video(Path(self.project.video_path), ass_path, Path(path))
        except Exception as exc:
            self.show_error("Failed to burn video", exc)
            return
        self.status_label.setText(f"Exported burned video: {Path(path).name}")

    def write_ass_output(self, path: Path) -> None:
        self.commit_editor_text()
        width, height = self.export_size()
        preset = merge_style_preset(preset_name=self.project.active_style)
        keywords = [rule.text for rule in self.project.keyword_rules if rule.enabled]
        write_ass(
            self.project.cues,
            keywords,
            path,
            width=width,
            height=height,
            preset=preset,
        )
        write_keyword_report(keywords, path.with_suffix(".keywords.md"), self.project.cues)

    def export_size(self) -> tuple[int, int]:
        if self.project.video_path:
            size = ffprobe_size(Path(self.project.video_path))
            if size:
                return size
        return (
            int(self.project.export_settings.get("width", 1920)),
            int(self.project.export_settings.get("height", 1080)),
        )

    def export_duration(self) -> float:
        if self.project.video_path:
            duration = ffprobe_duration(Path(self.project.video_path))
            if duration is not None:
                return duration
        return max(cue.end_ms for cue in self.project.cues) / 1000

    def commit_editor_text(self) -> None:
        if self.current_index is None:
            return
        if self.current_index >= len(self.project.cues):
            return
        text = self.cue_editor.toPlainText()
        cue = self.project.cues[self.current_index]
        if cue.text != text:
            self.project.cues[self.current_index] = replace(cue, text=text)
            self.refresh_subtitle_item(self.current_index)

    def refresh_view(self) -> None:
        self.subtitle_list.blockSignals(True)
        self.subtitle_list.clear()
        for index, cue in enumerate(self.project.cues):
            self.subtitle_list.addItem(self.item_for_cue(index, cue))
        self.subtitle_list.blockSignals(False)

        if self.current_index is not None and self.project.cues:
            self.subtitle_list.setCurrentRow(self.current_index)
            self.cue_editor.setPlainText(self.project.cues[self.current_index].text)
        elif not self.project.cues:
            self.cue_editor.clear()

        self.style_combo.setCurrentText(self.project.active_style)
        self.video_label.setText(
            f"Video: {Path(self.project.video_path).name}"
            if self.project.video_path
            else "No video imported"
        )
        self.project_label.setText(
            self.project_path.name if self.project_path else "Untitled project"
        )

    def refresh_subtitle_item(self, index: int) -> None:
        if index < 0 or index >= len(self.project.cues):
            return
        self.subtitle_list.blockSignals(True)
        self.subtitle_list.takeItem(index)
        self.subtitle_list.insertItem(index, self.item_for_cue(index, self.project.cues[index]))
        self.subtitle_list.setCurrentRow(index)
        self.subtitle_list.blockSignals(False)

    def item_for_cue(self, index: int, cue: Cue) -> QListWidgetItem:
        highlight_marker = " *" if cue.manual_highlights else ""
        label = f"{index + 1:03d}{highlight_marker}  {cue.text[:58]}"
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, cue.index)
        return item

    def require_current_cue(self) -> int | None:
        if self.current_index is None or self.current_index >= len(self.project.cues):
            self.status_label.setText("Select a subtitle cue first")
            return None
        return self.current_index

    def show_error(self, title: str, exc: Exception) -> None:
        QMessageBox.critical(self, title, str(exc))
        self.status_label.setText(f"{title}: {exc}")
