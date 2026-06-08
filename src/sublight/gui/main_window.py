from __future__ import annotations

import html
import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from collections.abc import Callable

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sublight.config import autosave_project_path, load_recent_projects, remember_project
from sublight.core.keywords import auto_keywords
from sublight.core.models import Cue, HighlightSpan, KeywordRule, Project
from sublight.core.project import load_project, save_project
from sublight.core.spans import add_manual_spans, ranges_are_covered, remove_manual_spans
from sublight.core.srt import parse_srt
from sublight.exporters.ass_exporter import write_keyword_report
from sublight.exporters.ffmpeg import (
    FfmpegRunner,
    ffprobe_duration,
    ffprobe_size,
    require_ffmpeg_tools,
)
from sublight.exporters.video_exporter import (
    burn_preview_segment,
    burn_video,
    render_overlay,
)
from sublight.gui.export_worker import ExportWorker
from sublight.styles.ass import write_ass
from sublight.styles.presets import STYLE_PRESETS, merge_style_preset
from sublight.styles.schema import StylePreset


STYLE_DISPLAY_NAMES = {
    "bold-yellow": "醒目黄",
    "clean-blue": "清爽蓝",
    "warm-orange": "暖橙",
    "large-focus": "大字强调",
    "soft-box": "柔和底框",
}


def style_display_name(style_name: str) -> str:
    return STYLE_DISPLAY_NAMES.get(style_name, style_name)


@dataclass(frozen=True)
class ExportQueueItem:
    label: str
    job: Callable[[FfmpegRunner], None]
    success_message: str


class SubtitleHighlightView(QTextEdit):
    selection_finished = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setPlaceholderText("导入 SRT 后，可直接拖选字幕文字进行高亮。再次拖选已高亮文字会取消高亮。")
        self.setStyleSheet(
            "QTextEdit { background: #121212; color: #f7f7f7; border: 1px solid #444;"
            " padding: 14px; selection-background-color: #315a8a; }"
        )

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().mouseReleaseEvent(event)
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.selection_finished.emit(cursor.selectionStart(), cursor.selectionEnd())


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SubLight")
        self.resize(1180, 760)

        self.project = Project()
        self.project_path: Path | None = None
        self.current_index: int | None = None
        self.cue_document_ranges: dict[int, tuple[int, int]] = {}

        self.subtitle_list = QListWidget()
        self.subtitle_list.currentRowChanged.connect(self.select_cue)

        self.subtitle_highlight_view = SubtitleHighlightView()
        self.subtitle_highlight_view.selection_finished.connect(
            self.toggle_document_selection_highlight
        )
        self.subtitle_highlight_view.cursorPositionChanged.connect(
            self.sync_current_cue_from_document_cursor
        )
        self.keyword_suggestions = QListWidget()
        self.keyword_suggestions.setSelectionMode(QAbstractItemView.MultiSelection)

        self.style_combo = QComboBox()
        for style_name in sorted(STYLE_PRESETS):
            self.style_combo.addItem(style_display_name(style_name), style_name)
        self.style_combo.currentIndexChanged.connect(self.set_active_style_from_combo)
        self.recent_combo = QComboBox()
        self.recent_combo.addItem("最近项目")
        self.recent_combo.activated.connect(self.open_recent_project)

        self.custom_style_name = QLineEdit()
        self.custom_style_name.setPlaceholderText("自定义样式名称")
        self.font_input = QLineEdit()
        self.font_size_spin = self.int_spin(8, 180)
        self.margin_v_spin = self.int_spin(0, 400)
        self.max_line_width_spin = self.int_spin(8, 80)
        self.primary_color_input = QLineEdit()
        self.highlight_color_input = QLineEdit()
        self.outline_color_input = QLineEdit()
        self.keyword_outline_color_input = QLineEdit()
        self.back_color_input = QLineEdit()
        self.back_alpha_spin = self.int_spin(0, 255)
        self.bold_check = QCheckBox("普通文字加粗")
        self.keyword_bold_check = QCheckBox("高亮文字加粗")
        self.keyword_scale_spin = self.double_spin(0.5, 2.0, 0.01)
        self.outline_spin = self.double_spin(0.0, 12.0, 0.1)
        self.keyword_outline_spin = self.double_spin(0.0, 14.0, 0.1)
        self.shadow_spin = self.double_spin(0.0, 12.0, 0.1)
        self.alignment_spin = self.int_spin(1, 9)
        self.border_style_spin = self.int_spin(1, 3)
        self.batch_styles_list = QListWidget()
        self.batch_styles_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for name in sorted(STYLE_PRESETS):
            item = QListWidgetItem(style_display_name(name))
            item.setData(Qt.UserRole, name)
            self.batch_styles_list.addItem(item)
        self.export_queue_list = QListWidget()
        self.export_queue_list.setMinimumHeight(96)
        self.style_preview_label = QLabel()
        self.style_preview_label.setAlignment(Qt.AlignCenter)
        self.style_preview_label.setMinimumHeight(92)
        self.style_preview_label.setTextFormat(Qt.RichText)
        self.style_preview_label.setStyleSheet(
            "background: #101418; border: 1px solid #303941; border-radius: 6px;"
            " padding: 14px;"
        )

        self.video_label = QLabel("未导入视频")
        self.project_label = QLabel("未命名项目")
        self.status_label = QLabel("就绪")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.cancel_export_button = QPushButton("取消导出")
        self.cancel_export_button.clicked.connect(self.cancel_export)
        self.cancel_export_button.setEnabled(False)
        self.export_thread: QThread | None = None
        self.export_worker: ExportWorker | None = None
        self.active_ffmpeg_runner: FfmpegRunner | None = None
        self.export_queue: list[ExportQueueItem] = []

        self.connect_style_editor_signals()
        self.setCentralWidget(self.build_layout())
        self.refresh_recent_projects()
        self.load_style_into_editor(self.current_style())
        self.refresh_view()
        self.refresh_style_preview()
        self.offer_autosave_restore()

    def int_spin(self, minimum: int, maximum: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        return spin

    def double_spin(self, minimum: float, maximum: float, step: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setDecimals(2)
        return spin

    def build_layout(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        top_bar = QHBoxLayout()
        for label, handler in (
            ("导入字幕", self.import_srt),
            ("导入视频", self.import_video),
            ("打开项目", self.open_project),
            ("保存项目", self.save_project_as),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            top_bar.addWidget(button)
        top_bar.addWidget(self.recent_combo)
        top_bar.addStretch(1)
        top_bar.addWidget(self.project_label)
        layout.addLayout(top_bar)

        body = QGridLayout()
        body.addWidget(self.build_subtitle_box(), 0, 0)
        body.addWidget(self.build_highlight_box(), 0, 1)
        body.addWidget(self.build_style_export_box(), 0, 2)
        body.setColumnStretch(0, 2)
        body.setColumnStretch(1, 4)
        body.setColumnStretch(2, 2)
        layout.addLayout(body, 1)
        progress_row = QHBoxLayout()
        progress_row.addWidget(self.progress_bar, 1)
        progress_row.addWidget(self.cancel_export_button)
        layout.addLayout(progress_row)
        layout.addWidget(self.status_label)
        return root

    def build_subtitle_box(self) -> QGroupBox:
        box = QGroupBox("字幕列表")
        layout = QVBoxLayout(box)
        layout.addWidget(self.subtitle_list)
        return box

    def build_highlight_box(self) -> QGroupBox:
        box = QGroupBox("字幕高亮")
        layout = QVBoxLayout(box)
        hint = QLabel("直接在下方字幕中拖选文字：未高亮会变成高亮，已高亮会取消。")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(self.subtitle_highlight_view)
        return box

    def build_style_export_box(self) -> QGroupBox:
        box = QGroupBox("样式与导出")
        layout = QVBoxLayout(box)
        layout.addWidget(QLabel("样式预设"))
        layout.addWidget(self.style_combo)
        layout.addWidget(self.custom_style_name)

        style_grid = QGridLayout()
        style_fields = [
            ("字体", self.font_input),
            ("字号", self.font_size_spin),
            ("底部边距", self.margin_v_spin),
            ("最大行宽", self.max_line_width_spin),
            ("普通颜色", self.primary_color_input),
            ("高亮颜色", self.highlight_color_input),
            ("描边颜色", self.outline_color_input),
            ("高亮描边", self.keyword_outline_color_input),
            ("底框颜色", self.back_color_input),
            ("底框透明度", self.back_alpha_spin),
            ("高亮缩放", self.keyword_scale_spin),
            ("描边粗细", self.outline_spin),
            ("高亮描边粗细", self.keyword_outline_spin),
            ("阴影", self.shadow_spin),
            ("对齐", self.alignment_spin),
            ("边框样式", self.border_style_spin),
        ]
        for row, (label, widget) in enumerate(style_fields):
            style_grid.addWidget(QLabel(label), row, 0)
            style_grid.addWidget(widget, row, 1)
        layout.addLayout(style_grid)
        layout.addWidget(self.bold_check)
        layout.addWidget(self.keyword_bold_check)

        style_buttons = QHBoxLayout()
        for label, handler in (
            ("保存样式", self.save_custom_style),
            ("导入样式", self.import_style_json),
            ("导出样式", self.export_style_json),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            style_buttons.addWidget(button)
        layout.addLayout(style_buttons)
        layout.addWidget(QLabel("样式预览"))
        layout.addWidget(self.style_preview_label)

        layout.addWidget(self.video_label)
        layout.addWidget(QLabel("批量导出预设"))
        layout.addWidget(self.batch_styles_list)
        layout.addWidget(QLabel("导出队列"))
        layout.addWidget(self.export_queue_list)
        queue_buttons = QHBoxLayout()
        for label, handler in (
            ("开始队列", self.start_next_queued_export),
            ("清空队列", self.clear_export_queue),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            queue_buttons.addWidget(button)
        layout.addLayout(queue_buttons)

        for label, handler in (
            ("导出 ASS 字幕", self.export_ass),
            ("导出绿幕字幕层", self.export_green_overlay),
            ("导出 5 秒预览", self.export_preview_segment),
            ("导出选中预设", self.export_selected_presets),
            ("烧录到视频", self.export_burned_video),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            layout.addWidget(button)

        layout.addStretch(1)
        return box

    def import_srt(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入 SRT 字幕",
            "",
            "SRT 字幕 (*.srt)",
        )
        if not path:
            return
        try:
            cues = parse_srt(Path(path))
        except Exception as exc:
            self.show_error("导入字幕失败", exc)
            return
        self.project.srt_path = path
        self.project.cues = cues
        self.current_index = 0 if cues else None
        self.refresh_view()
        self.autosave_project()
        self.status_label.setText(f"已导入 {len(cues)} 条字幕")

    def import_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入视频",
            "",
            "视频文件 (*.mp4 *.mov *.mkv *.webm);;所有文件 (*)",
        )
        if not path:
            return
        self.project.video_path = path
        self.refresh_view()
        self.autosave_project()
        self.status_label.setText(f"已导入视频：{Path(path).name}")

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开 SubLight 项目",
            "",
            "SubLight 项目 (*.sublight.json);;JSON 文件 (*.json)",
        )
        if not path:
            return
        try:
            self.project = load_project(Path(path))
        except Exception as exc:
            self.show_error("打开项目失败", exc)
            return
        self.project_path = Path(path)
        self.remember_current_project()
        self.current_index = 0 if self.project.cues else None
        self.refresh_view()
        self.autosave_project()
        self.status_label.setText(f"已打开项目：{Path(path).name}")

    def save_project_as(self) -> None:
        default_path = str(self.project_path or Path.cwd() / "project.sublight.json")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存 SubLight 项目",
            default_path,
            "SubLight 项目 (*.sublight.json);;JSON 文件 (*.json)",
        )
        if not path:
            return
        try:
            save_project(self.project, Path(path))
        except Exception as exc:
            self.show_error("保存项目失败", exc)
            return
        self.project_path = Path(path)
        self.remember_current_project()
        self.refresh_view()
        self.autosave_project()
        self.status_label.setText(f"已保存项目：{Path(path).name}")

    def open_recent_project(self, index: int) -> None:
        if index <= 0:
            return
        path = Path(self.recent_combo.itemData(index))
        if not path.exists():
            self.status_label.setText(f"最近项目不存在：{path}")
            return
        try:
            self.project = load_project(path)
        except Exception as exc:
            self.show_error("打开最近项目失败", exc)
            return
        self.project_path = path
        self.remember_current_project()
        self.current_index = 0 if self.project.cues else None
        self.refresh_view()
        self.autosave_project()
        self.status_label.setText(f"已打开项目：{path.name}")

    def remember_current_project(self) -> None:
        if self.project_path is None:
            return
        remember_project(self.project_path)
        self.refresh_recent_projects()

    def offer_autosave_restore(self) -> None:
        path = autosave_project_path()
        if not path.exists():
            return
        answer = QMessageBox.question(
            self,
            "恢复自动保存",
            "SubLight 找到一个自动保存的项目，是否恢复？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.project = load_project(path)
        except Exception as exc:
            self.show_error("恢复自动保存失败", exc)
            return
        self.project_path = None
        self.current_index = 0 if self.project.cues else None
        self.refresh_view()
        self.status_label.setText(f"已恢复自动保存：{path.name}")

    def refresh_recent_projects(self) -> None:
        self.recent_combo.blockSignals(True)
        self.recent_combo.clear()
        self.recent_combo.addItem("最近项目")
        for item in load_recent_projects():
            path = Path(item)
            self.recent_combo.addItem(path.name, str(path))
        self.recent_combo.blockSignals(False)

    def select_cue(self, row: int) -> None:
        if row < 0 or row >= len(self.project.cues):
            self.current_index = None
            return
        self.current_index = row
        self.focus_cue_in_highlight_view(row)
        self.refresh_style_preview()

    def set_active_style_from_combo(self, index: int) -> None:
        style_name = self.style_combo.itemData(index)
        if not style_name:
            return
        self.set_active_style(str(style_name))

    def set_active_style(self, style_name: str) -> None:
        self.project.active_style = style_name
        self.load_style_into_editor(self.current_style())
        self.refresh_style_preview()
        self.autosave_project()

    def connect_style_editor_signals(self) -> None:
        for line_edit in (
            self.font_input,
            self.primary_color_input,
            self.highlight_color_input,
            self.outline_color_input,
            self.keyword_outline_color_input,
            self.back_color_input,
        ):
            line_edit.textChanged.connect(self.refresh_style_preview)
        for spin in (
            self.font_size_spin,
            self.margin_v_spin,
            self.max_line_width_spin,
            self.back_alpha_spin,
            self.alignment_spin,
            self.border_style_spin,
            self.keyword_scale_spin,
            self.outline_spin,
            self.keyword_outline_spin,
            self.shadow_spin,
        ):
            spin.valueChanged.connect(self.refresh_style_preview)
        self.bold_check.toggled.connect(self.refresh_style_preview)
        self.keyword_bold_check.toggled.connect(self.refresh_style_preview)

    def update_style_combo_items(self) -> None:
        current = self.project.active_style
        names = sorted(set(STYLE_PRESETS) | set(self.project.custom_styles))
        self.style_combo.blockSignals(True)
        self.style_combo.clear()
        current_index = 0
        for index, name in enumerate(names):
            self.style_combo.addItem(style_display_name(name), name)
            if name == current:
                current_index = index
        if names:
            self.style_combo.setCurrentIndex(current_index)
        self.style_combo.blockSignals(False)

    def current_style(self) -> StylePreset:
        if self.project.active_style in self.project.custom_styles:
            return merge_style_preset(
                preset_name="bold-yellow",
                overrides=self.project.custom_styles[self.project.active_style],
            )
        return merge_style_preset(preset_name=self.project.active_style)

    def load_style_into_editor(self, preset: StylePreset) -> None:
        self.font_input.setText(preset.font)
        self.font_size_spin.setValue(preset.font_size)
        self.margin_v_spin.setValue(preset.margin_v)
        self.max_line_width_spin.setValue(preset.max_line_width)
        self.primary_color_input.setText(preset.primary_color)
        self.highlight_color_input.setText(preset.highlight_color)
        self.outline_color_input.setText(preset.outline_color)
        self.keyword_outline_color_input.setText(preset.keyword_outline_color)
        self.back_color_input.setText(preset.back_color)
        self.back_alpha_spin.setValue(preset.back_alpha)
        self.bold_check.setChecked(preset.bold)
        self.keyword_bold_check.setChecked(preset.keyword_bold)
        self.keyword_scale_spin.setValue(preset.keyword_scale)
        self.outline_spin.setValue(preset.outline)
        self.keyword_outline_spin.setValue(preset.keyword_outline)
        self.shadow_spin.setValue(preset.shadow)
        self.alignment_spin.setValue(preset.alignment)
        self.border_style_spin.setValue(preset.border_style)
        self.refresh_style_preview()

    def refresh_style_preview(self, *args: object) -> None:
        del args
        preset = self.style_from_editor()
        sample = "SubLight 让关键词更醒目"
        if self.current_index is not None and self.current_index < len(self.project.cues):
            sample = self.project.cues[self.current_index].text
        if not sample.strip():
            sample = "SubLight 让关键词更醒目"
        keyword = next((rule.text for rule in self.project.keyword_rules if rule.enabled), "")
        if not keyword or keyword not in sample:
            keyword = sample[: max(1, min(3, len(sample)))]
        text = html.escape(sample)
        escaped_keyword = html.escape(keyword)
        highlighted = (
            f"<span style='color: {preset.highlight_color}; "
            f"font-weight: {700 if preset.keyword_bold else 500};'>"
            f"{escaped_keyword}</span>"
        )
        if escaped_keyword in text:
            text = text.replace(escaped_keyword, highlighted, 1)
        font_size = max(16, min(34, int(preset.font_size * 0.48)))
        weight = 700 if preset.bold else 500
        self.style_preview_label.setText(
            "<div style='"
            f"font-family: {html.escape(preset.font)};"
            f"font-size: {font_size}px;"
            f"font-weight: {weight};"
            f"color: {preset.primary_color};"
            f"text-shadow: 0 0 {preset.shadow}px {preset.outline_color};"
            "'>"
            f"{text}"
            "</div>"
        )
        self.refresh_subtitle_document()

    def style_from_editor(self) -> StylePreset:
        return StylePreset(
            font=self.font_input.text().strip() or "STHeiti",
            font_size=self.font_size_spin.value(),
            margin_v=self.margin_v_spin.value(),
            max_line_width=self.max_line_width_spin.value(),
            primary_color=self.primary_color_input.text().strip() or "#FFFFFF",
            highlight_color=self.highlight_color_input.text().strip() or "#FFD400",
            outline_color=self.outline_color_input.text().strip() or "#000000",
            keyword_outline_color=self.keyword_outline_color_input.text().strip()
            or "#000000",
            back_color=self.back_color_input.text().strip() or "#000000",
            back_alpha=self.back_alpha_spin.value(),
            bold=self.bold_check.isChecked(),
            keyword_bold=self.keyword_bold_check.isChecked(),
            keyword_scale=self.keyword_scale_spin.value(),
            outline=self.outline_spin.value(),
            keyword_outline=self.keyword_outline_spin.value(),
            shadow=self.shadow_spin.value(),
            alignment=self.alignment_spin.value(),
            border_style=self.border_style_spin.value(),
        )

    def refresh_subtitle_document(self) -> None:
        if not hasattr(self, "subtitle_highlight_view"):
            return
        view = self.subtitle_highlight_view
        scrollbar_value = view.verticalScrollBar().value()
        cursor_position = view.textCursor().position()
        view.blockSignals(True)
        view.clear()
        self.cue_document_ranges = {}

        preset = self.style_from_editor()
        base_format = self.subtitle_text_format(preset, highlighted=False)
        highlight_format = self.subtitle_text_format(preset, highlighted=True)
        prefix_format = QTextCharFormat(base_format)
        prefix_format.setForeground(QColor("#8f969c"))
        prefix_format.setFontWeight(QFont.Bold)

        cursor = QTextCursor(view.document())
        for index, cue in enumerate(self.project.cues):
            prefix = f"{index + 1:03d}  "
            cursor.insertText(prefix, prefix_format)
            text_start = cursor.position()
            cursor.insertText(cue.text, base_format)
            text_end = cursor.position()
            self.cue_document_ranges[index] = (text_start, text_end)

            for span in cue.manual_highlights:
                start = max(0, min(span.start, len(cue.text)))
                end = max(0, min(span.end, len(cue.text)))
                if start >= end:
                    continue
                span_cursor = QTextCursor(view.document())
                span_cursor.setPosition(text_start + start)
                span_cursor.setPosition(text_start + end, QTextCursor.KeepAnchor)
                span_cursor.mergeCharFormat(highlight_format)

            if index < len(self.project.cues) - 1:
                cursor.setPosition(text_end)
                cursor.insertText("\n\n", base_format)

        restored_cursor = QTextCursor(view.document())
        restored_cursor.setPosition(min(cursor_position, len(view.toPlainText())))
        view.setTextCursor(restored_cursor)
        view.verticalScrollBar().setValue(scrollbar_value)
        view.blockSignals(False)

    def subtitle_text_format(
        self,
        preset: StylePreset,
        *,
        highlighted: bool,
    ) -> QTextCharFormat:
        display_size = max(13, min(28, int(preset.font_size * 0.42)))
        text_format = QTextCharFormat()
        text_format.setFontFamily(preset.font)
        text_format.setFontPointSize(
            max(13, min(34, display_size * preset.keyword_scale))
            if highlighted
            else display_size
        )
        text_format.setForeground(
            QColor(preset.highlight_color if highlighted else preset.primary_color)
        )
        text_format.setFontWeight(
            QFont.Bold
            if (preset.keyword_bold if highlighted else preset.bold)
            else QFont.Normal
        )
        return text_format

    def toggle_document_selection_highlight(self, selection_start: int, selection_end: int) -> None:
        if selection_start == selection_end:
            return
        ranges_by_cue = self.cue_ranges_for_document_selection(selection_start, selection_end)
        if not ranges_by_cue:
            self.status_label.setText("请拖选字幕正文，不要只选择序号或空白。")
            return

        removing = all(
            ranges_are_covered(
                self.project.cues[index].manual_highlights,
                ranges,
                text_length=len(self.project.cues[index].text),
            )
            for index, ranges in ranges_by_cue.items()
        )

        changed_indexes: list[int] = []
        for index, ranges in ranges_by_cue.items():
            cue = self.project.cues[index]
            spans = (
                remove_manual_spans(
                    cue.manual_highlights,
                    ranges,
                    text_length=len(cue.text),
                )
                if removing
                else add_manual_spans(
                    cue.manual_highlights,
                    ranges,
                    text_length=len(cue.text),
                )
            )
            if spans != cue.manual_highlights:
                self.project.cues[index] = replace(cue, manual_highlights=spans)
                changed_indexes.append(index)

        if not changed_indexes:
            self.status_label.setText("高亮没有变化")
            return

        self.current_index = changed_indexes[0]
        self.refresh_subtitle_items(changed_indexes)
        self.refresh_subtitle_document()
        self.focus_cue_in_highlight_view(self.current_index)
        self.autosave_project()
        action = "取消高亮" if removing else "添加高亮"
        self.status_label.setText(f"已{action}：{len(changed_indexes)} 条字幕")

    def cue_ranges_for_document_selection(
        self,
        selection_start: int,
        selection_end: int,
    ) -> dict[int, list[tuple[int, int]]]:
        start = min(selection_start, selection_end)
        end = max(selection_start, selection_end)
        ranges_by_cue: dict[int, list[tuple[int, int]]] = {}
        for index, (text_start, text_end) in self.cue_document_ranges.items():
            overlap_start = max(start, text_start)
            overlap_end = min(end, text_end)
            if overlap_start >= overlap_end:
                continue
            ranges_by_cue.setdefault(index, []).append(
                (overlap_start - text_start, overlap_end - text_start)
            )
        return ranges_by_cue

    def sync_current_cue_from_document_cursor(self) -> None:
        position = self.subtitle_highlight_view.textCursor().position()
        index = self.cue_index_at_document_position(position)
        if index is None or index == self.current_index:
            return
        self.current_index = index
        self.subtitle_list.blockSignals(True)
        self.subtitle_list.setCurrentRow(index)
        self.subtitle_list.blockSignals(False)
        self.refresh_style_preview()

    def cue_index_at_document_position(self, position: int) -> int | None:
        for index, (start, end) in self.cue_document_ranges.items():
            if start <= position <= end:
                return index
        return None

    def focus_cue_in_highlight_view(self, index: int) -> None:
        if index not in self.cue_document_ranges:
            return
        text_start, _ = self.cue_document_ranges[index]
        cursor = QTextCursor(self.subtitle_highlight_view.document())
        cursor.setPosition(text_start)
        self.subtitle_highlight_view.setTextCursor(cursor)
        self.subtitle_highlight_view.ensureCursorVisible()

    def save_custom_style(self) -> None:
        name = self.custom_style_name.text().strip()
        if not name:
            self.status_label.setText("请先输入自定义样式名称")
            return
        self.project.custom_styles[name] = asdict(self.style_from_editor())
        self.project.active_style = name
        self.update_style_combo_items()
        self.style_combo.setCurrentText(name)
        self.autosave_project()
        self.status_label.setText(f"已保存样式：{name}")

    def import_style_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入样式 JSON",
            "",
            "JSON 文件 (*.json)",
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            preset = merge_style_preset(preset_name="bold-yellow", overrides=data)
        except Exception as exc:
            self.show_error("导入样式失败", exc)
            return
        name = Path(path).stem
        self.project.custom_styles[name] = asdict(preset)
        self.project.active_style = name
        self.update_style_combo_items()
        self.load_style_into_editor(preset)
        self.autosave_project()
        self.status_label.setText(f"已导入样式：{name}")

    def export_style_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出样式 JSON",
            f"{self.project.active_style}.json",
            "JSON 文件 (*.json)",
        )
        if not path:
            return
        try:
            Path(path).write_text(
                json.dumps(asdict(self.style_from_editor()), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
        except Exception as exc:
            self.show_error("导出样式失败", exc)
            return
        self.status_label.setText(f"已导出样式：{Path(path).name}")

    def highlight_selection(self) -> None:
        cursor = self.subtitle_highlight_view.textCursor()
        if not cursor.hasSelection():
            self.status_label.setText("请直接在字幕高亮区拖选文字")
            return
        self.toggle_document_selection_highlight(cursor.selectionStart(), cursor.selectionEnd())

    def clear_cue_highlights(self) -> None:
        index = self.require_current_cue()
        if index is None:
            return
        cue = self.project.cues[index]
        self.project.cues[index] = replace(cue, manual_highlights=())
        self.refresh_subtitle_item(index)
        self.refresh_subtitle_document()
        self.autosave_project()
        self.status_label.setText("已清空当前字幕高亮")

    def apply_selection_globally(self) -> None:
        cursor = self.subtitle_highlight_view.textCursor()
        selected = cursor.selectedText().strip()
        if not selected:
            self.status_label.setText("请先拖选一个词或短语")
            return
        if not any(rule.text == selected for rule in self.project.keyword_rules):
            self.project.keyword_rules.append(KeywordRule(text=selected))
        self.autosave_project()
        self.status_label.setText(f"已添加全局关键词：{selected}")

    def refresh_keyword_suggestions(self) -> None:
        self.keyword_suggestions.clear()
        if not self.project.cues:
            self.status_label.setText("请先导入字幕")
            return
        existing = {rule.text for rule in self.project.keyword_rules}
        suggestions = [
            keyword
            for keyword in auto_keywords(self.project.cues, limit=24)
            if keyword not in existing
        ]
        for keyword in suggestions:
            self.keyword_suggestions.addItem(keyword)
        self.status_label.setText(f"已推荐 {len(suggestions)} 个关键词")

    def add_selected_keyword_suggestions(self) -> None:
        selected = [item.text() for item in self.keyword_suggestions.selectedItems()]
        if not selected:
            self.status_label.setText("请先选择推荐关键词")
            return
        existing = {rule.text for rule in self.project.keyword_rules}
        added = 0
        for keyword in selected:
            if keyword not in existing:
                self.project.keyword_rules.append(KeywordRule(text=keyword))
                existing.add(keyword)
                added += 1
        self.ignore_selected_keyword_suggestions(update_status=False)
        self.autosave_project()
        self.status_label.setText(f"已添加 {added} 条关键词规则")

    def ignore_selected_keyword_suggestions(
        self,
        checked: bool = False,
        *,
        update_status: bool = True,
    ) -> None:
        del checked
        rows = sorted(
            {
                self.keyword_suggestions.row(item)
                for item in self.keyword_suggestions.selectedItems()
            },
            reverse=True,
        )
        if not rows:
            if update_status:
                self.status_label.setText("请先选择推荐关键词")
            return
        for row in rows:
            self.keyword_suggestions.takeItem(row)
        if update_status:
            self.status_label.setText(f"已忽略 {len(rows)} 个推荐词")

    def export_ass(self) -> None:
        if not self.project.cues:
            self.status_label.setText("请先导入字幕")
            return
        default_path = Path(self.project.srt_path or "subtitles.srt").with_suffix(".ass")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 ASS 字幕",
            str(default_path),
            "ASS 字幕 (*.ass)",
        )
        if not path:
            return
        try:
            self.write_ass_output(Path(path))
        except Exception as exc:
            self.show_error("导出 ASS 失败", exc)
            return
        self.status_label.setText(f"已导出 ASS：{Path(path).name}")

    def export_green_overlay(self) -> None:
        if not self.project.cues:
            self.status_label.setText("请先导入字幕")
            return
        if not self.ensure_ffmpeg_ready():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出绿幕字幕层",
            "subtitle-overlay.mov",
            "MOV 视频 (*.mov)",
        )
        if not path:
            return
        try:
            ass_path = Path(path).with_suffix(".ass")
            self.write_ass_output(ass_path)
            width, height = self.export_size()
            duration = self.export_duration()
            self.start_export(
                "正在导出绿幕字幕层...",
                lambda runner: render_overlay(
                    ass_path,
                    Path(path),
                    width=width,
                    height=height,
                    duration=duration,
                    fps=int(self.project.export_settings.get("fps", 30)),
                    runner=runner.run,
                ),
                f"已导出字幕层：{Path(path).name}",
            )
        except Exception as exc:
            self.show_error("导出字幕层失败", exc)

    def export_selected_presets(self) -> None:
        if not self.project.cues:
            self.status_label.setText("请先导入字幕")
            return
        if not self.ensure_ffmpeg_ready():
            return
        style_names = [
            str(item.data(Qt.UserRole) or item.text())
            for item in self.batch_styles_list.selectedItems()
        ]
        if not style_names:
            self.status_label.setText("请先选择一个或多个批量导出预设")
            return
        directory = QFileDialog.getExistingDirectory(self, "批量导出字幕层", "")
        if not directory:
            return
        try:
            self.commit_editor_text()
            output_dir = Path(directory)
            width, height = self.export_size()
            duration = self.export_duration()
            fps = int(self.project.export_settings.get("fps", 30))
            cues = list(self.project.cues)
            keywords = [rule.text for rule in self.project.keyword_rules if rule.enabled]
            base_name = Path(self.project.srt_path or "subtitles.srt").stem

            for style_name in style_names:
                preset = merge_style_preset(preset_name=style_name)
                ass_path = output_dir / f"{base_name}.{style_name}.ass"
                overlay_path = output_dir / f"{base_name}.{style_name}.mov"

                def job(
                    runner: FfmpegRunner,
                    *,
                    style_preset: StylePreset = preset,
                    ass_output: Path = ass_path,
                    overlay_output: Path = overlay_path,
                ) -> None:
                    write_ass(
                        cues,
                        keywords,
                        ass_output,
                        width=width,
                        height=height,
                        preset=style_preset,
                    )
                    write_keyword_report(keywords, ass_output.with_suffix(".keywords.md"), cues)
                    render_overlay(
                        ass_output,
                        overlay_output,
                        width=width,
                        height=height,
                        duration=duration,
                        fps=fps,
                        runner=runner.run,
                    )

                self.enqueue_export(
                    f"字幕层预设：{style_display_name(style_name)}",
                    job,
                    f"已导出字幕层预设：{style_display_name(style_name)}",
                )
            self.status_label.setText(f"已加入 {len(style_names)} 个预设字幕层导出任务")
            self.start_next_queued_export()
        except Exception as exc:
            self.show_error("导出选中预设失败", exc)

    def export_burned_video(self) -> None:
        if not self.project.video_path:
            self.status_label.setText("请先导入视频")
            return
        if not self.ensure_ffmpeg_ready():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "烧录到视频",
            "highlighted.mp4",
            "MP4 视频 (*.mp4)",
        )
        if not path:
            return
        try:
            ass_path = Path(path).with_suffix(".ass")
            self.write_ass_output(ass_path)
            self.start_export(
                "正在把字幕烧录到视频...",
                lambda runner: burn_video(
                    Path(self.project.video_path),
                    ass_path,
                    Path(path),
                    runner=runner.run,
                ),
                f"已导出烧录视频：{Path(path).name}",
            )
        except Exception as exc:
            self.show_error("烧录视频失败", exc)

    def export_preview_segment(self) -> None:
        if not self.project.video_path:
            self.status_label.setText("请先导入视频")
            return
        if not self.ensure_ffmpeg_ready():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 5 秒预览",
            "preview.highlighted.mp4",
            "MP4 视频 (*.mp4)",
        )
        if not path:
            return
        try:
            ass_path = Path(path).with_suffix(".ass")
            self.write_ass_output(ass_path)
            start_seconds = 0.0
            if self.current_index is not None and self.current_index < len(self.project.cues):
                start_seconds = max(self.project.cues[self.current_index].start_ms / 1000 - 1, 0)
            self.start_export(
                "正在导出预览片段...",
                lambda runner: burn_preview_segment(
                    Path(self.project.video_path),
                    ass_path,
                    Path(path),
                    start_seconds=start_seconds,
                    duration_seconds=5.0,
                    runner=runner.run,
                ),
                f"已导出预览：{Path(path).name}",
            )
        except Exception as exc:
            self.show_error("导出预览失败", exc)

    def write_ass_output(self, path: Path) -> None:
        self.commit_editor_text()
        width, height = self.export_size()
        preset = self.style_from_editor()
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
        return

    def autosave_project(self) -> None:
        if not self.project.cues and not self.project.srt_path and not self.project.video_path:
            return
        try:
            save_project(self.project, autosave_project_path())
        except Exception:
            return

    def refresh_view(self) -> None:
        self.subtitle_list.blockSignals(True)
        self.subtitle_list.clear()
        for index, cue in enumerate(self.project.cues):
            self.subtitle_list.addItem(self.item_for_cue(index, cue))
        self.subtitle_list.blockSignals(False)

        self.refresh_subtitle_document()

        if self.current_index is not None and self.project.cues:
            self.subtitle_list.setCurrentRow(self.current_index)
            self.focus_cue_in_highlight_view(self.current_index)

        self.update_style_combo_items()
        self.video_label.setText(
            f"视频：{Path(self.project.video_path).name}"
            if self.project.video_path
            else "未导入视频"
        )
        self.project_label.setText(
            self.project_path.name if self.project_path else "未命名项目"
        )
        self.refresh_style_preview()

    def refresh_subtitle_item(self, index: int) -> None:
        if index < 0 or index >= len(self.project.cues):
            return
        self.subtitle_list.blockSignals(True)
        self.subtitle_list.takeItem(index)
        self.subtitle_list.insertItem(index, self.item_for_cue(index, self.project.cues[index]))
        self.subtitle_list.setCurrentRow(index)
        self.subtitle_list.blockSignals(False)

    def refresh_subtitle_items(self, indexes: list[int]) -> None:
        for index in indexes:
            self.refresh_subtitle_item(index)

    def item_for_cue(self, index: int, cue: Cue) -> QListWidgetItem:
        highlight_marker = " *" if cue.manual_highlights else ""
        label = f"{index + 1:03d}{highlight_marker}  {cue.text[:58]}"
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, cue.index)
        return item

    def require_current_cue(self) -> int | None:
        if self.current_index is None or self.current_index >= len(self.project.cues):
            self.status_label.setText("请先选择一条字幕")
            return None
        return self.current_index

    def ensure_ffmpeg_ready(self) -> bool:
        try:
            require_ffmpeg_tools()
        except Exception as exc:
            self.show_error("未找到 ffmpeg", exc)
            return False
        return True

    def enqueue_export(
        self,
        label: str,
        job: Callable[[FfmpegRunner], None],
        success_message: str,
    ) -> None:
        self.export_queue.append(ExportQueueItem(label, job, success_message))
        self.refresh_export_queue()

    def refresh_export_queue(self) -> None:
        self.export_queue_list.clear()
        for index, item in enumerate(self.export_queue, start=1):
            self.export_queue_list.addItem(f"{index:02d}  {item.label}")

    def clear_export_queue(self) -> None:
        self.export_queue.clear()
        self.refresh_export_queue()
        self.status_label.setText("已清空待导出任务")

    def start_next_queued_export(self) -> None:
        if self.export_thread is not None:
            self.status_label.setText("已有导出任务正在运行")
            return
        if not self.export_queue:
            self.status_label.setText("导出队列为空")
            return
        item = self.export_queue.pop(0)
        self.refresh_export_queue()
        self.start_export(f"正在导出：{item.label}", item.job, item.success_message)

    def start_export(
        self,
        status: str,
        job: Callable[[FfmpegRunner], None],
        success_message: str,
    ) -> None:
        if self.export_thread is not None:
            self.status_label.setText("已有导出任务正在运行")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.cancel_export_button.setEnabled(True)
        self.status_label.setText(status)

        self.export_thread = QThread()
        self.active_ffmpeg_runner = FfmpegRunner()
        runner = self.active_ffmpeg_runner
        self.export_worker = ExportWorker(lambda: job(runner), success_message)
        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(self.export_worker.run)
        self.export_worker.finished.connect(self.export_finished)
        self.export_worker.failed.connect(self.export_failed)
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.failed.connect(self.export_thread.quit)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        self.export_thread.start()

    def cancel_export(self) -> None:
        if self.active_ffmpeg_runner is None:
            return
        self.active_ffmpeg_runner.cancel()
        self.cancel_export_button.setEnabled(False)
        self.status_label.setText("正在取消导出...")

    def export_finished(self, message: str) -> None:
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 1)
        self.cancel_export_button.setEnabled(False)
        self.status_label.setText(message)
        self.export_thread = None
        self.export_worker = None
        self.active_ffmpeg_runner = None
        if self.export_queue:
            self.start_next_queued_export()

    def export_failed(self, message: str) -> None:
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 1)
        self.cancel_export_button.setEnabled(False)
        if "cancelled" in message.lower():
            self.status_label.setText("导出已取消")
        else:
            self.status_label.setText(f"导出失败：{message}")
            QMessageBox.critical(self, "导出失败", message)
        self.export_thread = None
        self.export_worker = None
        self.active_ffmpeg_runner = None

    def show_error(self, title: str, exc: Exception) -> None:
        QMessageBox.critical(self, title, str(exc))
        self.status_label.setText(f"{title}: {exc}")
