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

Status: implemented as build scaffolding.

Purpose: make installable app artifacts possible through repeatable packaging.

Key outputs:

- PyInstaller spec.
- GitHub Actions release workflow.
- App icon asset.
- Recent project config.
- Example project and style files.

## M7: Commercial Readiness

Status: implemented as alpha-readiness foundations.

Purpose: make the project understandable, recoverable, and contribution-friendly for public users.

Key outputs:

- Getting-started guide.
- Commercial readiness checklist.
- Contribution guide.
- Issue templates.
- Pull request template.
- Best-effort autosave and restore prompt.

## Next Product Slices

The next useful slices after M7 are:

- Autosave recovery prompt on GUI launch.
- Real style preview panel.
- Keyword suggestion accept/reject UI.
- Export queue and cancel button.
- Bundled sample SRT and sample video.
- GitHub Releases artifact validation.
- Landing page and tutorial video.
