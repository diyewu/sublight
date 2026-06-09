# SubLight

SubLight is an open-source subtitle highlighting tool for creators who want key words to pop automatically in short videos, tutorials, and talking-head content.

It turns ordinary `.srt` subtitles into keyword-highlighted `.ass` subtitles, green-screen subtitle overlays, alpha-capable overlay videos, or burned-in final videos.

## Features

- Parse `.srt` subtitles.
- Highlight selected keywords inline.
- Auto-pick candidate keywords from subtitle text.
- Generate `.ass` subtitles with ASS inline styles.
- Render green-screen subtitle layers for editors such as Jianying/CapCut.
- Render alpha-capable overlay videos for workflows that support transparency.
- Burn highlighted subtitles directly into a final video.
- Switch visual styles with built-in presets.
- Override styles with JSON.
- Review suggested keywords in the GUI and add selected terms globally.
- Batch-export green-screen overlays from multiple built-in presets.
- Preview style edits directly in the GUI.
- Cancel long-running ffmpeg exports from the GUI.

## Requirements

SubLight uses Python for subtitle processing and `ffmpeg` for video rendering.

Install `ffmpeg` on macOS:

```bash
brew install ffmpeg
```

Check it:

```bash
ffmpeg -version
```

## Install

From GitHub:

```bash
pipx install git+https://github.com/diyewu/sublight.git
```

For local development:

```bash
git clone https://github.com/diyewu/sublight.git
cd sublight
python -m pip install -e .
```

Then run:

```bash
sublight --help
```

Install the optional desktop GUI dependencies:

```bash
pipx install "git+https://github.com/diyewu/sublight.git[gui]"
```

Run the GUI:

```bash
sublight-gui
```

The GUI can import SRT/video files, mark manual highlights, edit styles, export ASS, render overlays, burn final videos, and export short preview segments.

## Desktop Builds

SubLight includes a PyInstaller spec for desktop packaging:

```bash
python -m pip install -e ".[gui,build]"
pyinstaller packaging/sublight-gui.spec --noconfirm
```

GitHub Actions builds macOS and Windows artifacts from tags matching `v*` or manual workflow runs.

Latest validated prerelease:

- [v0.1.0-alpha.5](https://github.com/diyewu/sublight/releases/tag/v0.1.0-alpha.5)
- `SubLight-macOS.zip`
- `SubLight-Windows.zip`

Current packaging strategy:

- The app bundles SubLight and PySide6.
- `ffmpeg` is not bundled yet.
- Users should install `ffmpeg` separately or make it available on `PATH`.
- Future releases may ship managed ffmpeg binaries per platform.

## Quick Start

Generate an ASS subtitle file:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --output input.highlighted.ass
```

Auto-pick keywords:

```bash
sublight input.srt --auto-keywords 20
```

Render a green-screen subtitle overlay:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --style-preset bold-yellow \
  --overlay-output subtitle-overlay.mov \
  --width 1280 --height 720
```

Burn subtitles into a final video:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --video input.mp4 \
  --burn-output final.highlighted.mp4
```

## Style Presets

List built-in presets:

```bash
sublight --list-style-presets
```

Current presets:

- `bold-yellow`: default short-video style, white text with yellow keywords.
- `clean-blue`: lighter outline with cyan-blue keywords.
- `warm-orange`: warm tutorial style with orange keywords.
- `large-focus`: larger high-impact captions.
- `soft-box`: captions with a semi-transparent box.

Use a preset:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --style-preset clean-blue
```

Batch render several styles:

```bash
for style in bold-yellow clean-blue warm-orange large-focus soft-box; do
  sublight input.srt \
    --keywords "Codex,knowledge base,workflow" \
    --style-preset "$style" \
    --overlay-output "subtitle.$style.mov" \
    --width 1280 --height 720
done
```

## Custom Style JSON

You can override any style preset with a JSON file:

```json
{
  "font_size": 58,
  "keyword_font_size": 66,
  "margin_v": 72,
  "max_line_width": 30,
  "primary_color": "#FFFFFF",
  "highlight_color": "#00E5FF",
  "outline_color": "#000000",
  "keyword_outline_color": "#001018",
  "outline": 3.2,
  "keyword_outline": 4.8,
  "keyword_scale": 1.0
}
```

Use it:

```bash
sublight input.srt \
  --keywords "Codex,knowledge base,workflow" \
  --style-preset bold-yellow \
  --style-json my-style.json
```

Supported style fields:

```text
font
font_size
keyword_font_size
margin_v
max_line_width
primary_color
highlight_color
outline_color
keyword_outline_color
back_color
back_alpha
bold
keyword_bold
keyword_scale
outline
keyword_outline
shadow
alignment
border_style
```

## Jianying / CapCut Workflow

Recommended workflow:

1. Export subtitles as `.srt`.
2. Run SubLight to generate a highlighted layer or burned-in video.
3. In Jianying/CapCut, use one of these options:
   - Import the burned-in video if you want the simplest result.
   - Import the green-screen overlay and use chroma key on green.
   - Import the alpha overlay if your editor correctly supports alpha.

In practice, the burned-in video and green-screen overlay are often more reliable than alpha videos across different editor versions.

## Notes

- SubLight does not edit Jianying/CapCut draft files.
- Newer Jianying/CapCut draft files may be encoded or encrypted, so external subtitle layers are safer.
- The generated `.ass` file is useful for previewing, burning, or further manual editing.

## Roadmap

SubLight is moving from a CLI prototype toward a commercial-ready desktop app.

- [Getting started](docs/getting-started.md)
- [Landing page](site/index.html)
- [Tutorial video script](docs/tutorial-video-script.md)
- [Product plan](docs/product-plan.md)
- [Architecture](docs/architecture.md)
- [Development plan](docs/development-plan.md)
- [Commercial readiness](docs/commercial-readiness.md)
- [Roadmap](ROADMAP.md)

## Contributing

Bug reports, feature requests, tests, docs, and focused pull requests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
