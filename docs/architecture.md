# SubLight Architecture

SubLight should be built as a reusable subtitle engine with multiple interfaces on top. The CLI and GUI should both call the same core modules.

## Architecture Goals

- Keep subtitle parsing, highlighting, styling, and exporting testable without a GUI.
- Keep ffmpeg command generation isolated from UI code.
- Support both batch CLI workflows and interactive GUI workflows.
- Make project files stable enough to survive app upgrades.
- Make style presets portable through JSON.

## Proposed Package Layout

```text
src/sublight/
  __init__.py
  cli.py
  core/
    models.py
    srt.py
    highlights.py
    keywords.py
    project.py
  styles/
    presets.py
    ass.py
    schema.py
  exporters/
    ass_exporter.py
    ffmpeg.py
    video_exporter.py
  gui/
    app.py
    main_window.py
    subtitle_list.py
    style_panel.py
    preview_panel.py
    export_dialog.py
```

The current `cli.py` contains most of the engine logic. Milestone 1 should move that logic into `core`, `styles`, and `exporters` while keeping the CLI behavior compatible.

## Data Model

### `SubtitleCue`

Represents one subtitle cue.

Fields:

- `id`
- `index`
- `start_ms`
- `end_ms`
- `text`
- `manual_highlights`

### `HighlightSpan`

Represents an explicit highlight range.

Fields:

- `start`
- `end`
- `style_role`
- `source`

`source` can be `manual`, `keyword`, or `auto`.

### `KeywordRule`

Represents global keyword matching.

Fields:

- `text`
- `case_sensitive`
- `match_whole_word`
- `enabled`
- `style_role`

### `StylePreset`

Represents render styling.

Fields should match the existing CLI style model:

- `font`
- `font_size`
- `keyword_font_size`
- `margin_v`
- `max_line_width`
- `primary_color`
- `highlight_color`
- `outline_color`
- `keyword_outline_color`
- `back_color`
- `back_alpha`
- `bold`
- `keyword_bold`
- `keyword_scale`
- `outline`
- `keyword_outline`
- `shadow`
- `alignment`
- `border_style`

### `Project`

Represents a full SubLight project.

Fields:

- `version`
- `srt_path`
- `video_path`
- `cues`
- `keyword_rules`
- `active_style`
- `custom_styles`
- `export_settings`

Project files should use JSON and a `.sublight.json` suffix.

## Core Modules

### `core.srt`

Responsibilities:

- Read SRT files with UTF-8 / UTF-8 BOM / GB18030 fallback.
- Parse cue timings.
- Serialize cue edits back to SRT if needed.

### `core.highlights`

Responsibilities:

- Apply keyword rules to subtitle text.
- Merge manual and global highlights.
- Resolve overlapping highlight spans.
- Preserve manual highlights as highest priority.

### `core.keywords`

Responsibilities:

- Auto-suggest keywords.
- Score repeated terms.
- Filter stopwords.
- Return auditable keyword candidates with counts.

### `core.project`

Responsibilities:

- Save and load `.sublight.json`.
- Migrate older project versions.
- Resolve relative media paths.

## Style Modules

### `styles.presets`

Responsibilities:

- Store built-in style presets.
- List presets.
- Merge preset + custom JSON + command-line overrides.

### `styles.ass`

Responsibilities:

- Convert `SubtitleCue`, highlight spans, and `StylePreset` into ASS.
- Escape ASS text.
- Generate inline ASS tags.
- Wrap long lines.

## Export Modules

### `exporters.ass_exporter`

Responsibilities:

- Write `.ass` files.
- Write keyword reports.

### `exporters.ffmpeg`

Responsibilities:

- Locate `ffmpeg` and `ffprobe`.
- Probe video duration and dimensions.
- Run ffmpeg commands.
- Parse progress output.
- Return structured errors.

### `exporters.video_exporter`

Responsibilities:

- Render green-screen overlays.
- Render alpha overlays.
- Burn subtitles into videos.
- Export short preview segments.

## GUI Architecture

Recommended first GUI stack:

```text
PySide6 + Python core + ffmpeg
```

Reasons:

- Reuses the current Python engine.
- Cross-platform enough for macOS and Windows.
- Faster to build than rewriting the engine for a web stack.
- Native desktop packaging is achievable with PyInstaller.

The GUI should communicate with export jobs through a worker thread or process, so the UI stays responsive while ffmpeg runs.

## GUI Views

### Main Window

- Project title
- Import buttons
- Export button
- Recent project access

### Subtitle List

- Cue index
- Time range
- Subtitle text preview
- Highlight indicator

### Cue Editor

- Full subtitle text
- Select text to add highlight
- Remove highlight
- Apply keyword to all cues

### Style Panel

- Built-in preset selector
- Font size
- Main color
- Highlight color
- Outline
- Shadow
- Caption box
- Bottom margin
- Save custom preset

### Preview Panel

- Render current cue as image preview.
- If video imported, show video frame with subtitle overlay.
- Jump to cue time.

### Export Dialog

- ASS
- Green-screen overlay
- Alpha overlay
- Burned-in MP4
- Preview segment
- Progress bar
- Error details

## Export Reliability Notes

Alpha video support differs across editors and versions. SubLight should treat alpha overlays as optional, not primary.

Recommended priority:

1. Burned-in MP4 for delivery.
2. Green-screen overlay for editor workflows.
3. Alpha MOV overlay for editors that preserve transparency.
4. ASS for advanced users.

## Testing Strategy

Core tests:

- SRT parse edge cases.
- Keyword matching.
- Manual highlight span merging.
- ASS escaping.
- Style preset merging.
- Project save/load migrations.

Export tests:

- ffmpeg command construction.
- Smoke render a tiny ASS overlay.
- Verify green-screen frame contains visible text.
- Verify burned-in frame contains visible text.

GUI tests can start as manual smoke tests until the core stabilizes.
