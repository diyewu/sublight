# Commercial Readiness Checklist

This document tracks what SubLight needs before it can be considered usable by normal creators without maintainer support.

## Current Position

SubLight has a working CLI, reusable core modules, a desktop GUI MVP, project files, editable styles, style preview, asynchronous cancellable exports, keyword suggestion controls, queued preset overlay export, best-effort autosave recovery, sample assets, a static landing page, a generated tutorial video, packaging scaffolding, and public contribution templates.

The product is still alpha. It should be treated as an open-source prototype moving toward commercial quality, not a finished paid product.

## Must-Have Before Public Beta

- Reliable macOS desktop build from GitHub Releases.
- Reliable Windows desktop build from GitHub Releases.
- Verified GUI smoke test on at least one macOS machine and one Windows machine.
- Clear `ffmpeg` setup path for non-technical users.
- Export validation that warns when video dimensions or durations are missing.
- Tutorial video showing one complete workflow.
- More complete GUI tests for project editing and style editing.

## Should-Have Before Paid or Commercial Distribution

- Installer signing or notarization plan for macOS.
- Windows code signing plan.
- Crash/error reporting policy that respects local creator files.
- Privacy policy explaining that local files stay local.
- Versioned project file migration tests.
- Preset library designed around creator use cases.
- Clear support channel and response expectations.

## Release Quality Gates

Each public release should pass:

- Unit tests.
- Python compile check.
- CLI smoke test.
- GUI launch smoke test.
- ASS export test.
- Preview segment export test with ffmpeg.
- Green overlay export test with ffmpeg.
- Burned video export test with ffmpeg.
- Fresh install test in a clean virtual environment.
- Desktop artifact build on GitHub Actions.

## Known Product Risks

- Alpha MOV transparency is inconsistent across editors.
- `ffmpeg` setup is still technical for many users.
- GUI coverage is limited when PySide6 is not installed in CI.
- Manual highlight ranges can become stale if cue text is edited heavily.
- Cross-platform font names may render differently.
- Long video exports need stronger progress reporting and cancellation.

## Feedback Channels

Use GitHub Issues for now:

- Bug reports: https://github.com/diyewu/sublight/issues/new?template=bug_report.yml
- Feature requests: https://github.com/diyewu/sublight/issues/new?template=feature_request.yml

Future channels can include a landing-page form, Discord/WeChat community, or in-app feedback export bundle.
