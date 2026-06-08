# SubLight Tutorial Video Script

This is the short tutorial shipped with the alpha project. The generated video is a compact, no-voice walkthrough that can be replaced later by a recorded product demo.

Generate it with:

```bash
python scripts/create_tutorial_video.py --output examples/tutorial-video.mp4
```

## Storyboard

1. Import SRT
   Open subtitles and attach the matching video.

2. Pick Keywords
   Mark text manually or accept suggested keywords.

3. Tune Style
   Preview fonts, colors, outlines, and caption boxes.

4. Queue Exports
   Render multiple presets without babysitting ffmpeg.

5. Back To Editor
   Use green overlays or burned MP4s in your workflow.

## Future Recorded Demo

A polished public beta tutorial should show the live GUI:

- Import `examples/sample.srt`.
- Import `examples/sample-video.mp4`.
- Use keyword suggestions.
- Edit one style field and check preview.
- Queue two preset overlays.
- Export a 5-second preview.
- Open the rendered video in a video editor.

