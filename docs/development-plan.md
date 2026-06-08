# SubLight Development Plan

SubLight is being built in seven milestones. Each milestone should leave the project in a usable state and should be committed separately.

## Milestone Strategy

The build order is:

1. Stabilize the reusable subtitle engine.
2. Add project persistence.
3. Add the desktop GUI workflow.
4. Make styles product-grade.
5. Make exports reliable and understandable.
6. Package the app for normal users.
7. Prepare the open-source project for public and commercial iteration.

## M1: Core Engine

Status: implemented.

Purpose: separate subtitle parsing, keyword logic, style rendering, and ffmpeg export from the CLI.

Key outputs:

- Reusable `sublight.core` modules.
- Reusable `sublight.styles` modules.
- Reusable `sublight.exporters` modules.
- Thin CLI entry point.
- Unit tests for core subtitle behavior.

## M2: Project Persistence

Status: implemented.

Purpose: let users save and reopen work instead of re-highlighting subtitles every session.

Key outputs:

- `.sublight.json` project format.
- Cue-level manual highlight spans.
- Global keyword rules.
- Active built-in style and custom style storage.
- Migration version field.

## M3: Desktop GUI MVP

Status: implemented.

Purpose: make the main workflow accessible without terminal commands.

Key outputs:

- PySide6 GUI entry point.
- SRT and video import.
- Subtitle cue list.
- Cue editor.
- Manual highlight selection.
- Global keyword selection.
- Basic style selection.
- ASS, overlay, and burned video exports.

## M4: Style Editor

Status: implemented.

Purpose: give creators control over common subtitle style parameters.

Key outputs:

- Editable style fields.
- Built-in preset selector.
- Save custom style.
- Import/export style JSON.
- Export uses the edited style state.

## M5: Export UX

Status: implemented.

Purpose: reduce export confusion and avoid freezing the GUI during long ffmpeg jobs.

Key outputs:

- `ffmpeg` and `ffprobe` detection.
- Async GUI export worker.
- Progress indicator.
- Preview segment export.
- Readable export errors.

## M6: Desktop Packaging

Status: implemented and release-validated for alpha builds.

Purpose: make installable app artifacts possible through repeatable packaging.

Key outputs:

- PyInstaller spec.
- GitHub Actions release workflow.
- App icon asset.
- Recent project config.
- Example project and style files.
- Validated `v0.1.0-alpha.3` GitHub Release with macOS and Windows zip artifacts.

## M7: Commercial Readiness

Status: implemented as alpha-readiness foundations.

Purpose: make the project understandable, recoverable, and contribution-friendly for public users.

Key outputs:

- Getting-started guide.
- Static product landing page.
- Commercial readiness checklist.
- Contribution guide.
- Issue templates.
- Pull request template.
- Best-effort autosave and restore prompt.
- Keyword suggestion accept/ignore controls.
- Batch overlay export for selected built-in presets.
- Style preview panel.
- Export cancellation for ffmpeg jobs.
- Export queue for selected preset overlays.
- Example SRT, project, style, and tiny sample video.
- Generated tutorial video and storyboard.

## Next Product Slices

The next useful slices after M7 are:

- Smoke-test the downloaded macOS and Windows desktop artifacts on real machines.
- Improve `ffmpeg` onboarding for non-technical users.
- Add GUI regression tests for project editing, style editing, and export queue behavior.
