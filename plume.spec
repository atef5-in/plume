# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["plume/gui_entry.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "plyer.platforms.win.notification",
        "pystray._win32",
        "PIL._tkinter_finder",
        "tkinter",
        "tkinter.messagebox",
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
    name="plume",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # no terminal window
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="plume",
)
