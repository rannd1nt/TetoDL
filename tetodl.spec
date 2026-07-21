# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — single binary with all features.
"""

import platform
import time
import urllib.request
import zipfile
from pathlib import Path

IS_WIN_BUILD = platform.system() == "Windows"

# ── Binary naming ──────────────────────────────────────────────
suffix = ".exe" if IS_WIN_BUILD else ""
platform_tag = "" if IS_WIN_BUILD else "-linux"
binary_name = f"tetodl{platform_tag}{suffix}"

# ── Platform-specific binaries ─────────────────────────────────
binaries = []
if IS_WIN_BUILD:
    bundled_ffmpeg = Path("ffmpeg.exe")
    if not bundled_ffmpeg.exists():
        print("[spec] Downloading ffmpeg.exe for Windows bundle...")
        URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        for attempt in range(3):
            try:
                urllib.request.urlretrieve(URL, "ffmpeg.zip")
                break
            except Exception:
                if attempt == 2:
                    raise
                print(f"[spec] Download failed (attempt {attempt+1}/3), retrying in 3s...")
                time.sleep(3)
        with zipfile.ZipFile("ffmpeg.zip") as z:
            for f in z.namelist():
                if f.endswith("ffmpeg.exe"):
                    with z.open(f) as src, open("ffmpeg.exe", "wb") as dst:
                        dst.write(src.read())
                    break
        Path("ffmpeg.zip").unlink()
    _ffmpeg_data = "ffmpeg.exe"

# ── Hidden imports (all features) ──────────────────────────────
HIDDEN = [
    "yt_dlp", "yt_dlp.extractor", "yt_dlp.postprocessor",
    "mutagen", "mutagen.mp3", "mutagen.mp4", "mutagen.flac", "mutagen.id3",
    "pydantic", "requests", "bs4", "colorama", "rich",
    "questionary", "qrcode",
    "fastapi", "uvicorn", "zeroconf",
]

# ── Excludes ───────────────────────────────────────────────────
EXCLUDES = [
    "tkinter", "unittest", "http.server", "pydoc", "test",
    "venv", "ensurepip",
]
if not IS_WIN_BUILD:
    EXCLUDES += ["av", "win32api", "win32con", "pywin32"]

# ── Data files ─────────────────────────────────────────────────
ROOT = Path(__spec__.origin).resolve().parent if __spec__ else Path.cwd()
datas = []
if IS_WIN_BUILD and _ffmpeg_data:
    datas.append((_ffmpeg_data, "."))
for pattern, dest in [("tetodl/locales/*.json", "tetodl/locales"),
                       ("tetodl/utils/share_static/*", "tetodl/utils/share_static"),
                       ("tetodl/daemon/static/*", "tetodl/daemon/static"),
                       ("assets/*", "assets")]:
    for f in ROOT.glob(pattern):
        if f.is_file():
            datas.append((str(f), dest))

# ── Analysis ───────────────────────────────────────────────────
a = Analysis(
    ["tetodl/__main__.py"],
    binaries=binaries,
    datas=datas,
    hiddenimports=HIDDEN,
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
