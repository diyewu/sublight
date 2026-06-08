# SubLight Product Plan

SubLight is evolving from a subtitle-processing CLI into a commercial-grade subtitle highlighting app for short-video creators, educators, and content teams.

The product goal is simple: import subtitles, choose or edit highlighted words, preview the result, pick a style, and export a usable video or subtitle layer without touching complex subtitle formats manually.

## Target Users

- Short-video creators who want key terms to stand out in talking-head videos.
- Educators and tutorial makers who need repeated terminology highlighted.
- Content teams that batch-produce videos from scripts, recordings, and SRT files.
- Editors using Jianying, CapCut, Premiere, DaVinci Resolve, or similar tools.

## Core User Workflow

1. Import an `.srt` file.
2. Optionally import the matching video.
3. Review subtitle lines in a timeline-aware list.
4. Select words or phrases to highlight.
5. Optionally use automatic keyword suggestions.
6. Choose a built-in style preset or edit a custom style.
7. Preview the visual result.
8. Export one or more outputs:
   - `.ass` subtitle file
   - green-screen subtitle layer
   - alpha subtitle layer
   - burned-in final video
   - keyword report / project JSON

## MVP Scope

The first GUI version should focus on completing one reliable workflow end to end:

- Import SRT.
- Display all subtitle cues.
- Allow manual word/phrase highlighting per cue.
- Apply global keywords across all cues.
- Choose one built-in style preset.
- Export ASS.
- Export green-screen overlay.
- Burn subtitles into a video if a video is imported.
- Save and reopen a project.

The MVP does not need advanced video editing, cloud sync, AI selection, or template marketplaces.

## Product Principles

- Keep the subtitle text editable and auditable.
- Make every automatic choice reversible.
- Prefer reliable exports over clever but fragile editor integrations.
- Keep the core engine independent from the GUI.
- Support batch workflows from the CLI even after the GUI exists.
- Do not modify proprietary editor draft files.

## Highlight Model

SubLight should support two highlight modes:

- Global keyword highlights: every occurrence of a keyword is highlighted.
- Manual cue highlights: specific ranges in specific subtitle cues are highlighted.

Manual cue highlights should take priority over global keyword rules. This allows users to avoid accidental highlights when a word appears in the wrong context.

## Style System

Built-in styles should cover common creator needs:

- `bold-yellow`: white text, yellow keywords, strong black outline.
- `clean-blue`: clean tutorial look with cyan-blue keywords.
- `warm-orange`: warm creator/teaching style.
- `large-focus`: larger emphasis for short clips and mobile-first videos.
- `soft-box`: semi-transparent caption box for complex backgrounds.
- `minimal-white`: clean white captions with subtle outline.
- `dark-box`: black-box caption style for maximum readability.

Custom styles should support:

- Font family
- Font size
- Main text color
- Highlight color
- Outline color
- Outline thickness
- Keyword outline color
- Keyword outline thickness
- Keyword scale
- Bold / non-bold text
- Shadow
- Caption box color
- Caption box opacity
- Alignment
- Bottom margin
- Max line width
- Line wrapping

## Export Modes

SubLight should support these export modes:

- ASS only: fastest, editable, useful for power users.
- Green-screen overlay: most reliable editor-compatible overlay.
- Alpha MOV overlay: useful when editors preserve transparency.
- Burned-in MP4: simplest delivery format.
- Preview segment: short test export before rendering the whole video.

## Commercial Readiness Goals

Before calling SubLight commercially usable, it should have:

- A desktop GUI for macOS and Windows.
- Clear import/export flows.
- Project save files.
- Style presets and custom styles.
- Progress bars and readable export errors.
- ffmpeg detection and setup guidance.
- Example projects.
- Basic crash-safe autosave.
- Release builds through GitHub Actions.
- A public documentation site or polished README.

## Non-Goals

- Editing video timelines.
- Replacing full video editors.
- Directly editing encrypted Jianying/CapCut draft files.
- Cloud account systems in the first commercial version.
- Paid license enforcement before product-market fit is clearer.
