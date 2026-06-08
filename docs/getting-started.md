# Getting Started with SubLight

SubLight helps creators turn normal SRT subtitles into highlighted subtitle files, overlay videos, or burned-in videos.

## What You Need

- Python 3.10 or newer for the CLI.
- Optional PySide6 dependency for the desktop GUI.
- `ffmpeg` and `ffprobe` for video export.
- An `.srt` subtitle file.
- Optional matching video file.

## Install

CLI only:

```bash
pipx install git+https://github.com/diyewu/sublight.git
```

GUI:

```bash
pipx install "git+https://github.com/diyewu/sublight.git[gui]"
```

Install `ffmpeg` on macOS:

```bash
brew install ffmpeg
```

## GUI Workflow

1. Run `sublight-gui`.
2. Click `Import SRT` and choose your subtitle file.
3. Optionally click `Import Video` and choose the matching video.
4. Select a subtitle cue in the list.
5. Select a word or phrase in the cue editor.
6. Click `Highlight Selection` for a manual highlight.
7. Click `Apply Selection Globally` if the phrase should be highlighted everywhere.
8. Use `Suggest` to review automatic keyword candidates, then add or ignore selected suggestions.
9. Choose or edit a style preset.
10. Export one of these outputs:
   - `Export ASS`
   - `Export Green Overlay`
   - `Export 5s Preview`
   - `Export Selected Presets`
   - `Burn Video`

Project files can be saved as `.sublight.json` and reopened later. SubLight also keeps a best-effort autosave in the user config directory.

## CLI Workflow

Generate highlighted ASS subtitles:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --output input.highlighted.ass
```

Auto-suggest keywords:

```bash
sublight input.srt --auto-keywords 20
```

Render a green-screen overlay:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --overlay-output subtitle-overlay.mov \
  --width 1280 --height 720
```

Burn subtitles into a video:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --video input.mp4 \
  --burn-output final.highlighted.mp4
```

## Try the Example Assets

The repository includes:

- `examples/sample.srt`
- `examples/sample-video.mp4`
- `examples/sample.sublight.json`
- `examples/cyan-style.json`

Use them to smoke-test the CLI or GUI before trying your own files.

## Choosing Export Modes

- Use `ASS` when you want an editable subtitle file.
- Use `Green Overlay` when your editor supports chroma key. This is often the most reliable overlay workflow.
- Use `Burn Video` when you want a final MP4 with subtitles already included.
- Use `5s Preview` before a long export.

Alpha MOV overlays are useful in some editors, but transparency support varies. If your editor shows a black background, use green overlay with chroma key or burn the video directly.

## Where Files Are Stored

On macOS, recent projects and autosave live under:

```text
~/Library/Application Support/SubLight/
```

On Windows, they live under:

```text
%APPDATA%/SubLight/
```

On Linux, they live under:

```text
~/.config/SubLight/
```

## Troubleshooting

If exports fail, first check that `ffmpeg` and `ffprobe` are available:

```bash
ffmpeg -version
ffprobe -version
```

If subtitles are invisible in an editor, try the green-screen overlay mode and remove the green background with chroma key.
