# -*- mode: python ; coding: utf-8 -*-
"""
Single PyInstaller spec — 8 binary variants (4 variant × 2 platform).

Usage (Windows build machine):
  set BUILD_VARIANT=full && pyinstaller tetodl.spec   → tetodl.exe
  set BUILD_VARIANT=cli  && pyinstaller tetodl.spec   → tetodl-cli.exe

Usage (Linux build machine):
  BUILD_VARIANT=full pyinstaller tetodl.spec           → tetodl-linux
  BUILD_VARIANT=cli  pyinstaller tetodl.spec           → tetodl-cli-linux

Variants: cli, tui, daemon, full
"""

import os
import platform
import sys
import urllib.request
import zipfile
from pathlib import Path

IS_WIN_BUILD = platform.system() == "Windows"
IS_LINUX_BUILD = not IS_WIN_BUILD
BUILD_VARIANT = os.environ.get("BUILD_VARIANT", "full").lower()

# ── Binary naming ──────────────────────────────────────────────
suffix = ".exe" if IS_WIN_BUILD else ""
platform_tag = "" if IS_WIN_BUILD else "-linux"
variant_tag = "" if BUILD_VARIANT == "full" else f"-{BUILD_VARIANT}"
binary_name = f"tetodl{variant_tag}{platform_tag}{suffix}"

# ── Platform-specific binaries ─────────────────────────────────
binaries = []
if IS_WIN_BUILD:
    bundled_ffmpeg = Path("ffmpeg.exe")
    if not bundled_ffmpeg.exists():
        print("[spec] Downloading ffmpeg.exe for Windows bundle...")
        URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        urllib.request.urlretrieve(URL, "ffmpeg.zip")
        with zipfile.ZipFile("ffmpeg.zip") as z:
            for f in z.namelist():
                if f.endswith("ffmpeg.exe"):
                    with z.open(f) as src, open("ffmpeg.exe", "wb") as dst:
                        dst.write(src.read())
                    break
        Path("ffmpeg.zip").unlink()
    binaries.append(("ffmpeg.exe", "."))

# ── Variant-specific hidden imports ────────────────────────────
CORE_HIDDEN = [
    "yt_dlp", "yt_dlp.extractor", "yt_dlp.postprocessor",
    "mutagen", "mutagen.mp3", "mutagen.mp4", "mutagen.flac", "mutagen.id3",
    "pydantic", "requests", "bs4", "colorama",
]
TUI_HIDDEN = ["rich", "questionary", "qrcode"]
DAEMON_HIDDEN = ["fastapi", "uvicorn", "zeroconf"]

hidden = list(CORE_HIDDEN)
if BUILD_VARIANT in ("tui", "full"):
    hidden += TUI_HIDDEN
if BUILD_VARIANT in ("daemon", "full"):
    hidden += DAEMON_HIDDEN

# ── Exclude unused feature libraries ───────────────────────────
EXCLUDES = [
    "tkinter", "unittest", "http.server", "pydoc", "test",
    "venv", "ensurepip",
]
if BUILD_VARIANT == "cli":
    EXCLUDES += TUI_HIDDEN + DAEMON_HIDDEN
elif BUILD_VARIANT == "tui":
    EXCLUDES += DAEMON_HIDDEN
elif BUILD_VARIANT == "daemon":
    EXCLUDES += TUI_HIDDEN

# Linux never needs PyAV or Windows-specific DLLs
if IS_LINUX_BUILD:
    EXCLUDES += ["av", "win32api", "win32con", "pywin32"]

# ── Data files ─────────────────────────────────────────────────
datas = []
for pattern, dest in [("tetodl/locales/*.json", "tetodl/locales"),
                       ("assets/*", "assets")]:
    matches = [str(f) for f in Path().glob(pattern) if f.is_file()]
    datas += [(m, dest) for m in matches]

# ── Analysis ───────────────────────────────────────────────────
a = Analysis(
    ["tetodl/__main__.py"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name=binary_name, console=True, upx=True,
)
