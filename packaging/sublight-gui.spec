# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path.cwd()


a = Analysis(
    ["src/sublight/gui/app.py"],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[(str(ROOT / "assets"), "assets")],
    hiddenimports=[
        "sublight.cli",
        "sublight.core.highlights",
        "sublight.core.keywords",
        "sublight.core.models",
        "sublight.core.project",
        "sublight.core.srt",
        "sublight.exporters.ass_exporter",
        "sublight.exporters.ffmpeg",
        "sublight.exporters.video_exporter",
        "sublight.gui.main_window",
        "sublight.styles.ass",
        "sublight.styles.presets",
        "sublight.styles.schema",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SubLight",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SubLight",
)
