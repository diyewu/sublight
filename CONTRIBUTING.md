# Contributing to SubLight

Thanks for helping make subtitle highlighting easier for creators. SubLight is early, so the most valuable contributions are focused fixes, reproducible bug reports, test cases, documentation improvements, and small product-grade workflow improvements.

## Development Setup

```bash
git clone https://github.com/diyewu/sublight.git
cd sublight
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[gui,build]"
```

If you only need the CLI and tests, install the base package:

```bash
python -m pip install -e .
```

Install `ffmpeg` and `ffprobe` before testing video exports.

macOS:

```bash
brew install ffmpeg
```

## Useful Commands

```bash
python -m unittest discover -s tests
python -m py_compile $(find src tests -name '*.py' -print)
sublight --list-style-presets
sublight-gui
```

Build a local desktop app:

```bash
python -m pip install -e ".[gui,build]"
pyinstaller packaging/sublight-gui.spec --noconfirm
```

## Contribution Workflow

1. Open or pick an issue before starting larger work.
2. Keep changes scoped to one feature, bug fix, or documentation improvement.
3. Add or update tests when changing parsing, matching, project files, style rendering, ffmpeg commands, or GUI state behavior.
4. Run the test commands above before opening a pull request.
5. Explain the user-facing behavior change in the pull request.

## Code Guidelines

- Keep the subtitle engine independent from the GUI.
- Prefer dataclasses and typed functions for stable project data.
- Keep project JSON backward compatible. Add migration logic when changing saved fields.
- Keep ffmpeg command generation isolated in `sublight.exporters`.
- Keep GUI work asynchronous for long-running exports.
- Avoid direct modification of proprietary editor draft files.

## Reporting Bugs

Good bug reports include:

- Operating system and Python version.
- SubLight version or commit.
- Whether the CLI or GUI was used.
- The input SRT/video format if shareable.
- The exact export mode.
- The error message or a screenshot.
- A minimal sample file when possible.

Please remove private creator content before attaching files publicly.

