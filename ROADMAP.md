# SubLight Roadmap

SubLight is currently an alpha desktop and CLI prototype. The next goal is to turn it into a commercial-ready desktop tool with a stable core engine, GUI workflow, style system, and reliable export pipeline.

See also:

- [Development plan](docs/development-plan.md)
- [Commercial readiness checklist](docs/commercial-readiness.md)

## M1: Core Engine Refactor

Status: implemented.

Goal: turn the current CLI script into reusable modules without breaking CLI behavior.

Deliverables:

- Move SRT parsing into `sublight.core.srt`.
- Move keyword extraction into `sublight.core.keywords`.
- Move highlight matching into `sublight.core.highlights`.
- Move style presets and ASS rendering into `sublight.styles`.
- Move ffmpeg logic into `sublight.exporters`.
- Keep the `sublight` CLI working.
- Add basic tests for parsing, matching, style merging, and ASS output.

Acceptance criteria:

- Existing CLI examples still work.
- Unit tests cover core subtitle and style logic.
- No GUI code depends on CLI internals.

## M2: Project Model

Status: implemented.

Goal: support saving and reopening user edits.

Deliverables:

- Define `Project`, `SubtitleCue`, `HighlightSpan`, `KeywordRule`, and `StylePreset` models.
- Save and load `.sublight.json` project files.
- Store manual highlight ranges per cue.
- Store global keyword rules.
- Store active style and custom styles.
- Add migration version field.

Acceptance criteria:

- A project can be saved, reopened, and exported with identical highlights.
- Manual cue highlights can coexist with global keyword highlights.

## M3: GUI MVP

Status: implemented.

Goal: let non-technical users complete the basic workflow in a desktop app.

Recommended stack:

```text
PySide6 + Python core + ffmpeg
```

Deliverables:

- Main desktop window.
- Import SRT.
- Display subtitle list.
- Edit one cue at a time.
- Select text and mark it as highlighted.
- Remove highlights.
- Choose built-in style preset.
- Export ASS.
- Export green-screen overlay.
- Burn subtitles into video if a video is imported.

Acceptance criteria:

- A user can import an SRT, manually highlight words, select a preset, and export a usable result without using the terminal.

## M4: Style Editor

Status: implemented.

Goal: make subtitle styling product-grade.

Deliverables:

- Style preset selector.
- Editable style fields:
  - Font
  - Font size
  - Main text color
  - Highlight color
  - Outline color
  - Outline thickness
  - Keyword outline color
  - Keyword outline thickness
  - Keyword scale
  - Shadow
  - Bottom margin
  - Max line width
  - Caption box color
  - Caption box opacity
- Save custom style.
- Import/export style JSON.
- Live style preview.

Acceptance criteria:

- A user can create a custom style, save it, reopen it, and export a video with that style.

## M5: Video Preview and Export UX

Status: implemented.

Goal: make export reliable and understandable.

Deliverables:

- Detect `ffmpeg` and `ffprobe`.
- Show clear setup guidance if missing.
- Show export progress.
- Show readable export errors.
- Render short preview segment.
- Jump preview to selected cue time.
- Optional video frame preview with subtitle overlay.
- Export queue for multiple style presets.

Acceptance criteria:

- Long exports do not freeze the GUI.
- Failed exports show actionable messages.
- Users can preview before exporting a full video.

## M6: Desktop Packaging

Status: implemented and release-validated for alpha builds.

Goal: ship installable builds for normal users.

Deliverables:

- macOS app build.
- Windows app build.
- App icon.
- User config directory.
- Recent projects.
- Example project.
- GitHub Actions release workflow.
- Decide whether to bundle ffmpeg or guide installation.
- Validated `v0.1.0-alpha.3` GitHub Release with macOS and Windows zip artifacts.

Acceptance criteria:

- A user can download an app from GitHub Releases and run it without cloning the repository.

## M7: Commercial Readiness

Status: implemented as alpha-readiness foundations.

Goal: polish SubLight for real public use.

Deliverables:

- Product landing page.
- Polished documentation.
- Tutorial video.
- Sample subtitle/video assets.
- Crash-safe autosave.
- Better keyword suggestion UX.
- Batch export.
- Feedback collection channel.
- Issue templates.
- Contribution guide.

Acceptance criteria:

- New users can understand the product, install it, complete a project, and report issues without direct maintainer support.

## Backlog

Possible future features:

- AI-assisted keyword selection.
- Multi-language subtitle support.
- Word-level subtitle timing from ASR output.
- Preset marketplace.
- Brand kit support.
- Team style libraries.
- Plugin integrations for editors.
- Direct upload to creator platforms.
- Template-based intro/outro caption animations.

## Current Priority

The current engineering priority is **Packaged App Smoke Testing**.

Download the `v0.1.0-alpha.3` macOS and Windows artifacts, smoke-test GUI launch/export on real machines, then tighten ffmpeg onboarding, signing/notarization, and GUI regression coverage before calling SubLight beta-ready.
