# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# customtkinter ships JSON theme files + asset PNGs that PyInstaller does not
# pick up automatically — without this, the .exe crashes on first dialog open.
ctk_datas = collect_data_files("customtkinter")

a = Analysis(
    ["plume/gui_entry.py"],
    pathex=["."],
    binaries=[],
    datas=[("plume.ico", ".")] + ctk_datas,
    hiddenimports=[
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "plyer.platforms.win.notification",
        "pystray._win32",
        "PIL._tkinter_finder",
        "tkinter",
        "tkinter.messagebox",
        "customtkinter",
        "darkdetect",  # customtkinter dependency for system theme detection
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
    icon="plume.ico",
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
