# TetoDL Packaging & Cross-Platform Refactor

> **Branch:** `feat/packaging`
> **Status:** Planning
> **Goal:** TetoDL v2.0.0 — cross-platform (Linux + Windows), pip-installable, optionally compilable to standalone binary, with CI/CD.

---

## Table of Contents

1. [Goal](#goal)
2. [Constraints](#constraints)
3. [Architecture Overview](#architecture-overview)
4. [Phase A — Code Refactor](#phase-a--code-refactor-source-compat)
5. [Phase B — Build & CI/CD](#phase-b--build--cicd)
6. [Phase C — Installer & Distribution](#phase-c--installer--distribution)
7. [Installation Methods](#installation-methods)
8. [Update Mechanism](#update-mechanism)
9. [Feature Separation](#feature-separation)
10. [Complete File Change Summary](#complete-file-change-summary)
11. [Out of Scope](#out-of-scope)

---

## Goal

TetoDL harus bisa:

- **Jalan di Windows** (native, bukan WSL), tanpa mengurangi fitur apapun
- **Jalan di Linux** dengan cara yang sama seperti sekarang
- **Satu sumber kode** — tidak ada cabang per-platform
- **Dikompilasi jadi binary** via PyInstaller — bundle Python runtime + library + ffmpeg.exe
- **Binary bisa jalan tanpa Python/Git/ffmpeg** — cocok untuk user awam
- **Diinstall dengan satu perintah**:
  - Windows: `iwr "https://install.tetodl.dev" | iex` — download binary
  - Linux: `bash <(curl -s https://install.tetodl.dev)` — download binary
- **Pip-installable**: `pip install tetodl` → `tetodl` command global (untuk developer)
- **Bisa di-update** tanpa kehilangan data pengguna

---

## Constraints

| # | Constraint | Alasan |
|---|-----------|--------|
| 1 | **No Git required** | User Windows gak mau ribet install Git cuma buat clone |
| 2 | **No manual FFmpeg PATH** | Thumbnail processing pake PyAV. yt-dlp's internal ffmpeg needs di-solve via **bundled ffmpeg.exe** di binary. Di pip mode, user tetap perlu ffmpeg (winget/install manual) |
| 3 | **yt-dlp harus bisa update** | Baik di source mode, pip mode, maupun compiled binary |
| 4 | **Feature parity** | Semua fitur yang ada di Linux harus ada di Windows (CLI, TUI, Daemon, smart-cover, lyrics, share, --cut, --zip, --m3u, dll) |
| 5 | **Feature separation** | User bisa pilih: CLI-only, CLI+TUI, Full (CLI+TUI+Daemon) |
| 6 | **Zero regression** | Semua fitur Linux yang udah jalan harus tetap jalan |
| 7 | **Satu branch** | Cross-platform dari satu source tree, gak ada fork |
| 8 | **Binary no-dependency** | Compiled binary di Windows harus jalan **tanpa Python, Git, maupun ffmpeg manual** — semua sudah ter-bundle |

---

## Architecture Overview

### Layer Architecture (Existing — No Change)

```
utils/ ← core/ ← pipeline/ ← [cli/, ui/, daemon/]
```

Lapisan ini tidak berubah. Yang berubah hanya implementasi di dalamnya untuk mendukung Windows.

### Dual FFmpeg / PyAV Layer (Thumbnail Processing Only)

PyAV hanya menggantikan **panggilan ffmpeg langsung dari kode TetoDL** (thumbnail crop & convert). Ini cuma 2 fungsi: `crop_thumbnail_to_square()` dan `convert_thumbnail_format()` di `utils/thumbnail.py`.

```
Thumbnail / Cover Processing
│
├── Linux (IS_LINUX)
│   └── subprocess ffmpeg         ← existing, no change
│       crop_thumbnail_to_square()
│       convert_thumbnail_format()
│
└── Windows (IS_WINDOWS)
    └── PyAV (import av)          ← new implementation
        _crop_with_pyav()
        _convert_with_pyav()
```

### Bundled FFmpeg (yt-dlp Internal Usage)

Ada 4 fitur yang depend on ffmpeg **di dalam yt-dlp**, bukan kode TetoDL:

| Fitur | Flag | yt-dlp mechanism |
|-------|------|-----------------|
| Audio conversion | `-f mp3/m4a/opus` | Post-processor `FFmpegExtractAudio` |
| Video codec | `-c h264/h265` | `postprocessor_args` via ffmpeg |
| Video/audio merge | default download | `FFmpegMerger` |
| Audio trim | `--cut` | `download_ranges` + ffmpeg |

Ini semua gak bisa diganti PyAV karena yt-dlp punya internal post-processor chain yang pake ffmpeg binary. Solusinya:
- **Compiled binary Windows**: bundle `ffmpeg.exe` ke dalam PyInstaller build (~40 MB tambahan). yt-dlp dapet `ffmpeg_location` → semua fitur jalan.
- **Pip install Windows**: user perlu install ffmpeg via winget (`winget install ffmpeg`) atau manual.
- **Linux**: system ffmpeg (seperti sekarang).

`FFMPEG_CMD` di Windows detection:
```python
if IS_WINDOWS:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        FFMPEG_CMD = os.path.join(sys._MEIPASS, 'ffmpeg.exe')  # Bundled
    else:
        FFMPEG_CMD = shutil.which('ffmpeg')  # Dari PATH, bisa None
```

### Hybrid yt-dlp Update (Compiled Binary)

```
Binary Startup Sequence:
  1. Cek ~/.cache/TetoDL/ytdlp-override/
  2. Ada folder yt-dlp-{version}?
     ├── Yes → sys.path.insert(0, override_path)
     │         ← yt_dlp di-load dari sini, bukan bundled
     └── No  → pake yt_dlp yg ter-bundle di binary
  3. Background thread: cek PyPI untuk versi baru
  4. User setuju update?
     ├── Yes → download wheel dari PyPI
     │         extract ke ~/.cache/TetoDL/ytdlp-override/
     │         console.ok("Updated! Restart to use new version")
     └── No  → lanjut
```

Ini works karena `import yt_dlp` ngecek `sys.path` urut. Override path di index 0 didahulukan dari bundled `_internal` punya PyInstaller.

### Search API Rewrite

```
search.py
  SEBELUM: subprocess.run(["yt-dlp", "--dump-json", ...])
  SESUDAH: yt_dlp.YoutubeDL({"extract_flat": True}).extract_info(...)
```

Penting karena:
- Di binary PyInstaller, subprocess ke `yt-dlp` gak bisa (binary gak ngespawn dirinya sendiri sebagai module)
- Pake Python API works di semua mode (source, pip, binary)
- Lebih cepat (gak perlu spawn process)

### Daemon — Platform-Specific

```
daemon/service.py
│
├── Linux (not IS_WINDOWS)
│   └── systemd (existing) — tetodl.service
│
└── Windows (IS_WINDOWS)
    └── Stub — print "Coming soon"
        (Fase berikutnya: pywin32 Windows Service)
```

### Feature-Specific Flags (Lazy Detection)

Setiap binary variant (CLI, TUI, Daemon, Full) hanya punya akses ke fitur yang sesuai. Implementasinya pake **lazy import detection** di `cli/parser.py` — bukan preprocessor, bukan compile-time flag.

```python
# cli/parser.py

def _has_tui():
    """TUI tersedia kalo rich + questionary bisa di-import."""
    try:
        import rich, questionary  # noqa: F401
        return True
    except ImportError:
        return False

def _has_daemon():
    """Daemon tersedia kalo fastapi + uvicorn bisa di-import."""
    try:
        import fastapi, uvicorn  # noqa: F401
        return True
    except ImportError:
        return False

def cli():
    parser = argparse.ArgumentParser(...)
    
    # ─── Core flags — ALWAYS ada (CLI only) ───
    dl = parser.add_argument_group("Download Options")
    dl.add_argument("-a", "--audio", ...)
    dl.add_argument("-v", "--video", ...)
    # ... semua core download dan utility flags
    
    # ─── TUI flags — HANYA kalo rich/questionary terinstall ───
    if _has_tui():
        tui = parser.add_argument_group("TUI Options")
        tui.add_argument("--header", ...)
        tui.add_argument("--progress-style", ...)
    
    # ─── Daemon subcommand — HANYA kalo fastapi/uvicorn terinstall ───
    if _has_daemon():
        daemon = parser.add_subparsers().add_parser("daemon")
        daemon.add_argument("--run", ...)
        daemon.add_argument("--display", ...)
    
    return parser
```

Binary variants menghasilkan:

| Binary | `rich`/`questionary` | `fastapi`/`uvicorn` | Flags di --help |
|--------|---------------------|---------------------|-----------------|
| `tetodl-cli` | ❌ (not bundled) | ❌ (not bundled) | Core only |
| `tetodl-tui` | ✅ | ❌ | Core + TUI |
| `tetodl-daemon` | ❌ | ✅ | Core + Daemon |
| `tetodl` (full) | ✅ | ✅ | Core + TUI + Daemon |

**Source code 100% sama.** Tidak ada `#ifdef`, tidak ada branch compile. PyInstaller build script yang menentukan library mana yang masuk ke bundle.

### Graceful Library Degradation

Semua `import` terhadap library opsional (TUI/Daemon) harus di-wrap dengan try/except di seluruh kode — bukan cuma di parser:

```python
# utils/console/themes.py
try:
    import rich
except ImportError:
    rich = None

def get_theme():
    if rich is None:
        return PlainTheme()       # fallback ASCII-only
    return RichTheme()            # full color

# ui/entry/menu.py
try:
    import questionary
except ImportError:
    questionary = None

def show_main_menu():
    if questionary is None:
        return _simple_menu()     # fallback: print + input()
    return _questionary_menu()    # full TUI
```

Ini memastikan:
- **CLI-only binary**: TUI functions fallback ke simple print/input — gak crash
- **Daemon-only binary**: panggil menu TUI → fallback ke simple mode
- **Source code langsung `python main.py`**: kalo user gak install optional deps, app tetep jalan (dengan fitur terbatas)

## Phase A — Code Refactor (Source Compat)

Semua perubahan di source code biar jalan di Linux + Windows.

### A1. `pyproject.toml` — Project Packaging

**Before:** Placeholder build-system only, no `[project]` section.

**After:**

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "tetodl"
version = "2.0.0"
description = "YouTube Media Downloader — CLI, TUI & Daemon"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "rannd1nt"}]
requires-python = ">=3.9"

dependencies = [
    "yt-dlp>=2026.2.4",
    "requests>=2.32.5",
    "beautifulsoup4>=4.14.3",
    "mutagen>=1.47.0",
    "colorama>=0.4.6",
    "pydantic>=2.13.4",
]

[project.optional-dependencies]
tui = [
    "rich>=13.9.4",
    "questionary>=2.1.1",
    "qrcode>=8.2",
]
daemon = [
    "fastapi>=0.136.3",
    "uvicorn>=0.48.0",
    "zeroconf>=0.2.0",
]
windows = [
    "av>=14.0",        # PyAV — menggantikan ffmpeg subprocess
]
full = [
    "tetodl[tui,daemon]",
]
all = [
    "tetodl[full,windows]",
]

[project.urls]
Homepage = "https://github.com/rannd1nt/TetoDL"

[project.scripts]
tetodl = "tetodl.__main__:main"

[tool.pytest.ini_options]
testpaths = ["tetodl/tests"]
pythonpath = ["tetodl"]
filterwarnings = ["ignore::DeprecationWarning"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "network: marks tests that require network access",
    "daemon: marks tests requiring daemon mode",
    "tui: marks tests requiring questionary/rich TUI",
    "windows: marks tests specific to Windows platform",
]
```

### A2. `tetodl/__main__.py` — New Entry Point

**New file:**

```python
"""Entry point for `python -m tetodl` and `tetodl` command."""
from tetodl.ui.entry.app import app

app.run()
```

### A3. `tetodl/constants.py` — Platform Detection Rewrite

| Line | Before | After |
|------|--------|-------|
| 10 | `os.path.exists("/data/data/com.termux")` | Same (TERMUX check, safe) |
| 17-18 | `if hasattr(os, "uname") and "microsoft" in os.uname().release.lower()` | Wrapped in `if not IS_WINDOWS:` — `os.uname()` doesn't exist on Windows |
| 21 | `open("/proc/version", "r")` | Same guard — `/proc/version` is Linux-only |
| 108-112 | Hardcoded `/usr/bin/ffmpeg`, `sys.prefix/bin/ffmpeg` | Gated behind `if not IS_WINDOWS:` |
| 115 | `sys.prefix/bin/spotdl` | Same guard |
| 132 | `SERVICE_PATH = .../systemd/...` | Gated: only defined if `not IS_WINDOWS` |
| 172 | `if not IS_WINDOWS: CONFIG_DIR.mkdir(...)` | **Hapus guard** — Windows juga perlu bikin folder |

Windows path branch (sudah ada, lines 46-54):
```python
elif IS_WINDOWS:
    home = Path.home()  # C:\Users\...
    BASE_PATH = home / "Downloads" / APP_NAME
    CONFIG_DIR = home / ".config" / APP_NAME  # → C:\Users\rannd1nt\.config\TetoDL
    DATA_DIR = home / ".local" / "share" / APP_NAME
    CACHE_DIR = home / ".cache" / APP_NAME
    TEMP_DIR = CACHE_DIR / "temp"
    FFMPEG_CMD = None  # Pakai PyAV — fallback ke subprocess kalo user punya ffmpeg
```

`FFMPEG_CMD` di Windows:
```python
elif IS_WINDOWS:
    # ...
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        FFMPEG_CMD = os.path.join(sys._MEIPASS, 'ffmpeg.exe')  # Bundled di binary
    else:
        FFMPEG_CMD = shutil.which('ffmpeg')  # Bisa None kalo gak ada
```

Semua kode yang make `FFMPEG_CMD` harus handle `None`:
- `pipeline/steps/download.py:220,270` — kalo `None`, yt-dlp cari ffmpeg sendiri di PATH (atau skip post-processing)
- `utils/thumbnail.py` — pake PyAV path kalo `FFMPEG_CMD is None`

### A4. `core/dependency.py` — Critical Fixes

| Line | Before | After |
|------|--------|-------|
| 88-93 | `subprocess.run(['which', command])` | `return shutil.which(command) is not None` — cross-platform |
| 99-140 | `check_ffmpeg()` — wajib ada | Di Windows: skip (gak required, pake PyAV) |
| 225-226 | `if IS_WINDOWS: return False` | **Dihapus** |
| 328 | `'ffmpeg': check_ffmpeg()` | `'ffmpeg': True if IS_WINDOWS else check_ffmpeg()` |

### A5. `ui/verifier.py` — Remove Windows Exit

| Line | Before | After |
|------|--------|-------|
| 85-92 | Panggil `verify_platform_compatibility()` → exit kalo Windows | **Dihapus** — gak perlu cek platform |

### A6. `utils/thumbnail.py` — Dual Implementation

```python
from ..constants import FFMPEG_CMD, IS_WINDOWS

def crop_thumbnail_to_square(thumbnail_path):
    if IS_WINDOWS:
        return _crop_with_pyav(thumbnail_path)
    return _crop_with_ffmpeg(thumbnail_path)

def _crop_with_pyav(thumbnail_path):
    """Crop thumbnail using PyAV (Windows)."""
    try:
        import av
        with av.open(thumbnail_path) as container:
            frame = next(container.decode(video=0))
            img = frame.to_image()
            size = min(img.size)
            left = (img.size[0] - size) // 2
            top = (img.size[1] - size) // 2
            cropped = img.crop((left, top, left + size, top + size))
            cropped.save(thumbnail_path)
        return True
    except Exception as e:
        console.err(...)
        return False

def _crop_with_ffmpeg(thumbnail_path):
    """Crop thumbnail using ffmpeg subprocess (Linux)."""
    # ... existing code unchanged ...

def convert_thumbnail_format(thumbnail_path, target_format="jpg"):
    if IS_WINDOWS:
        return _convert_with_pyav(thumbnail_path, target_format)
    return _convert_with_ffmpeg(thumbnail_path, target_format)
```

### A7. `core/search.py` — Rewrite to Python API

**Before:**
```python
yt_dlp_cmd = "yt-dlp"
if not shutil.which(yt_dlp_cmd): ...
cmd = [yt_dlp_cmd, "--flat-playlist", "--dump-json", ...]
result = subprocess.run(cmd, ...)
```

**After:**
```python
try:
    from yt_dlp import YoutubeDL
except ImportError:
    console.err(...)
    return None

search_query = f"ytsearch{limit}:{query}"
with YoutubeDL({
    "quiet": True,
    "extract_flat": True,
    "no_warnings": True,
}) as ydl:
    info = ydl.extract_info(search_query, download=False)
```

Ini penting untuk kompatibilitas dengan compiled binary.

### A8. `core/maintenance.py` — No Git, No Bash

**`perform_update()`** — dual mode:

```python
import sys
import os
import shutil
import requests
from pathlib import Path

def _is_binary() -> bool:
    """Detect if running as compiled PyInstaller binary."""
    return getattr(sys, 'frozen', False)

def perform_update() -> bool:
    if _is_binary():
        return _update_binary()
    return _update_pip()

def _update_pip() -> bool:
    """Pip mode: upgrade via pip install --upgrade."""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--upgrade", "tetodl", "yt-dlp"
        ])
        console.ok(Keys.maint.update_successful)
        return True
    except subprocess.CalledProcessError as e:
        console.err(Keys.maint.update_failed(error=e))
        return False
    except FileNotFoundError:
        console.err(Keys.maint.pip_not_found)
        return False

def _update_binary() -> bool:
    """
    Binary mode: self-destructive update.
    Download new binary, swap, restart.
    Pattern: sama seperti uv, mise, pip.
    """
    is_win = os.name == 'nt'
    current = Path(sys.argv[0]).resolve()
    temp = current.with_suffix(current.suffix + ".new")
    
    # Tentukan URL download sesuai platform + variant
    platform = "windows" if is_win else "linux"
    variant = _detect_variant()  # cli / tui / daemon / full
    ext = ".exe" if is_win else ""
    name = f"tetodl{'-' + variant if variant != 'full' else ''}{ext}"
    url = f"https://github.com/rannd1nt/TetoDL/releases/latest/download/{name}"
    
    console.proc(f"Downloading {name}...")
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(temp, "wb") as f:
            shutil.copyfileobj(r.raw, f)
    except Exception as e:
        console.err(f"Download failed: {e}")
        return False
    
    if is_win:
        # Windows: rename → spawn update script → exit
        _win_replace_and_restart(current, temp)
        return True
    else:
        # Linux: replace langsung + restart
        os.replace(temp, current)
        os.chmod(current, 0o755)
        os.execv(current, sys.argv)
        return True  # unreachable

def _win_replace_and_restart(current: Path, temp: Path):
    """Windows: rename exe + spawn .bat untuk replace."""
    old = current.with_suffix(current.suffix + ".old")
    bat = current.with_suffix(current.suffix + ".update.bat")
    
    bat_content = f"""@echo off
ping 127.0.0.1 -n 2 > nul
del "{old}" 2>nul
move /y "{temp}" "{current}" > nul
start "" "{current}" --version
del "%~f0"
"""
    bat.write_text(bat_content)
    subprocess.Popen([str(bat)], shell=True)
    sys.exit(0)
```

**`perform_uninstall()`** — ganti `bash uninstall.sh` jadi pure Python:
```python
def perform_uninstall():
    # Data cleanup (existing logic, lines 116-144) — pindahin ke fungsi sendiri
    _cleanup_user_data(wipe_mode)
    
    # Hapus symlink (Linux) — skip kalo Windows
    if not IS_WINDOWS:
        _remove_symlink()
    
    print()
    console.warn("Also run: pip uninstall tetodl")
    console.warn("To remove all: rm -rf ~/.config/TetoDL ~/.local/share/TetoDL ~/.cache/TetoDL")
```

### A9. `utils/network.py` — URL Opening

```python
def open_url(url: str) -> bool:
    try:
        if IS_TERMUX:
            subprocess.run(["am", "start", ...])
            return True
        elif IS_WINDOWS:
            os.startfile(url)       # Windows native
            return True
        else:
            # Linux (existing)
            subprocess.run(["xdg-open", url], ...)
            return True
    except Exception:
        try:
            webbrowser.open(url)    # Cross-platform fallback
            return True
        except Exception:
            return False
```

### A10. `daemon/service.py` — Platform Guard

```python
from ...constants import IS_WINDOWS

def setup_systemd(host: str, port: int):
    if IS_WINDOWS:
        console.warn("Daemon service is not yet available on Windows.")
        console.warn("Run 'tetodl daemon --run' to start manually.")
        return
    # ... existing systemd code ...

def remove_systemd():
    if IS_WINDOWS:
        console.warn("Daemon service is not installed.")
        return
    # ... existing systemd code ...
```

### A11. `daemon/display.py` — Platform Guard

```python
def get_daemon_status():
    if IS_WINDOWS:
        return "unknown (Windows)"
    try:
        subprocess.check_output(["systemctl", "--user", "is-active", "tetodl.service"])
        return "active"
    except:
        return "inactive"
```

### A12. Test Files — Cross-Platform Paths

Ganti semua hardcoded `/tmp/foo.mp3` dengan `tmp_path` fixture pytest:

```python
# Before:
def test_something():
    path = "/tmp/test.mp3"
    
# After:
def test_something(tmp_path):
    path = str(tmp_path / "test.mp3")
```

Files affected (dari hasil scan):
- `tetodl/tests/conftest.py`
- `tetodl/tests/daemon/conftest.py`
- `tetodl/tests/pipeline/conftest.py`
- `tetodl/tests/pipeline/test_handlers.py`
- `tetodl/tests/pipeline/test_pipeline.py`
- `tetodl/tests/pipeline/steps/test_classify.py`
- `tetodl/tests/pipeline/steps/test_cover.py`
- `tetodl/tests/pipeline/steps/test_finalize.py`
- `tetodl/tests/pipeline/steps/test_lyrics.py`
- `tetodl/tests/cli/test_dispatch.py`
- `tetodl/tests/core/test_history.py`
- `tetodl/tests/core/test_models.py`
- `tetodl/tests/core/conftest.py`
- `tetodl/tests/core/test_registry.py`

---

## Phase B — Build & CI/CD

### B1. PyInstaller Packaging

File **`tetodl.spec`** di root repo:

```python
# -*- mode: python ; coding: utf-8 -*-

import platform
import sys
from pathlib import Path

is_windows = platform.system() == "Windows"

block_cipher = None

# Base analysis — common for all variants
common_excludes = [
    "tkinter", "unittest", "email", "http.server",
    "pydoc", "test", "distutils", "lib2to3",
]

# Detect platform
IS_WINDOWS_BUILD = platform.system() == "Windows"

# Helper: download ffmpeg for Windows build
if IS_WINDOWS_BUILD:
    import urllib.request
    import zipfile
    FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    FFMPEG_ZIP = "ffmpeg.zip"
    if not os.path.exists("ffmpeg.exe"):
        print("Downloading ffmpeg.exe...")
        urllib.request.urlretrieve(FFMPEG_URL, FFMPEG_ZIP)
        with zipfile.ZipFile(FFMPEG_ZIP) as z:
            for f in z.namelist():
                if f.endswith("ffmpeg.exe"):
                    with z.open(f) as src, open("ffmpeg.exe", "wb") as dst:
                        dst.write(src.read())
                    break
        os.remove(FFMPEG_ZIP)

binaries = []
datas = [("tetodl/locales/*.json", "tetodl/locales"), ("assets/*.txt", "assets")]

if IS_WINDOWS_BUILD and os.path.exists("ffmpeg.exe"):
    binaries.append(("ffmpeg.exe", "."))

a = Analysis(
    ["tetodl/__main__.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "yt_dlp",
        "yt_dlp.extractor",
        "yt_dlp.postprocessor",
        "mutagen",
        "mutagen.mp3",
        "mutagen.mp4",
        "mutagen.flac",
        "mutagen.id3",
        "pydantic",
        "requests",
        "bs4",
        "colorama",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=common_excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# TUI-specific imports
tui_hidden = ["rich", "questionary", "qrcode"]
daemon_hidden = ["fastapi", "uvicorn", "zeroconf"]

# Build variants
if "CLI_ONLY" not in os.environ:
    a.binaries += [x for x in tui_hidden if x not in a.binaries]

if "DAEMON" in os.environ.get("BUILD_VARIANT", ""):
    a.binaries += daemon_hidden
elif "FULL" in os.environ.get("BUILD_VARIANT", "FULL"):
    a.binaries += tui_hidden + daemon_hidden

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="tetodl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

Build commands:
```bash
# CLI only
BUILD_VARIANT=CLI_ONLY pyinstaller tetodl.spec

# Full
BUILD_VARIANT=FULL pyinstaller tetodl.spec
```

### B2. GitHub Actions Workflow

#### 3-Tier Testing Strategy

```
Push ke feat/packaging / PR ke main
│
├── Tier 1: Unit Tests (~30 detik) — setiap push
│   ├── pytest -m "not slow and not network"
│   ├── Linux ✅ + Windows ✅ (matrix: py3.9, py3.12)
│   └── Tests: parser, config, models, pipeline steps (fully mocked)
│
├── Tier 2: Mocked Integration Tests (~3 menit) — setiap push
│   ├── pytest -m "integration" (new marker)
│   ├── Linux ✅ + Windows ✅
│   └── Fake yt-dlp + fake ffmpeg + fake HTTP
│       Test SEMUA kombinasi flag dari README Command Reference
│
└── Tier 3: Build Test (~5 menit) — setiap push ke main
    ├── PyInstaller compile → tetodl.exe + tetodl binary
    └── Binary smoke test: --help, --version
```

#### Tier 2 — Flag Combination Test Matrix

Ini daftar lengkap test cases dari README `Command Reference` + `CLI Mode Usage`:

```python
# tetodl/tests/test_flag_combinations.py

FLAG_COMBINATIONS = [
    # ===== 1. Core Download & Quality =====
    # Section "Basic & High Performance"
    ("url", [],                                   "default auto-detect"),
    ("url", ["-a"],                               "audio mode"),
    ("url", ["-v"],                               "video mode"),
    ("url", ["-a", "--async"],                    "async playlist audio"),
    ("url", ["-a", "--quiet"],                    "quiet audio"),
    
    # ===== 2. Audio Processing & Metadata =====
    # Section "Music Mode (M4A + Smart Metadata)"
    ("url", ["-a", "-f", "m4a", "--smart-cover", "--lyrics"],
                                                  "audio + smart-cover + lyrics"),
    ("url", ["-a", "-f", "mp3"],                  "audio mp3 format"),
    ("url", ["-a", "-f", "opus"],                 "audio opus format"),
    ("url", ["-a", "--no-cover"],                 "raw audio no cover"),
    ("url", ["-a", "--smart-cover", "--force-crop"],
                                                  "audio + force crop"),
    ("url", ["-a", "--lyrics", "--romaji"],       "audio + romanized lyrics"),
    
    # ===== 3. Video & Asset Extraction =====
    # Section "Power User Video Mode"
    ("url", ["-v", "-f", "mkv", "-r", "1080p", "-c", "h264"],
                                                  "video full control"),
    ("url", ["-v", "-r", "720p"],                 "video 720p"),
    ("url", ["-v", "-c", "h265"],                 "video h265"),
    ("url", ["-v", "-f", "mp4"],                  "video mp4 container"),
    ("url", ["-v", "-o", "/tmp/videos"],          "video custom output"),
    
    # ===== Thumbnail Extraction =====
    ("url", ["--thumbnail-only"],                 "thumbnail default"),
    ("url", ["--thumbnail-only", "-f", "png"],    "thumbnail as png"),
    ("url", ["--thumbnail-only", "-f", "webp"],   "thumbnail as webp"),
    ("url", ["--thumbnail-only", "--smart-cover", "-f", "jpg"],
                                                  "smart thumbnail"),
    
    # ===== 4. Precision Editing (Cut) =====
    ("url", ["-a", "--cut", "1:30-2:00"],         "cut range"),
    ("url", ["-a", "--cut", "1:30-"],             "cut from start"),
    ("url", ["-a", "--cut", "-2:00"],             "cut to end"),
    
    # ===== 5. Interactive Discovery =====
    (None,  ["--search", "test query"],           "search default"),
    (None,  ["--search", "test", "-a", "-f", "m4a", "--smart-cover", "--lyrics"],
                                                  "search + audio + metadata"),
    (None,  ["--search", "test", "-l", "10"],     "search limit 10"),
    
    # ===== 6. Organization =====
    ("url", ["-a", "--group", "My Playlist"],     "group named"),
    ("url", ["-a", "--group"],                    "group auto-name"),
    ("url", ["-a", "--group", "--m3u"],           "group + m3u"),
    ("url", ["-a", "--group", "P", "--m3u"],      "group named + m3u"),
    ("url", ["-a", "--group", "P", "--zip"],      "group + zip"),
    ("url", ["-a", "--items", "1,3,5-7"],         "playlist items"),
    
    # ===== 7. Network Sharing =====
    ("/tmp/share", ["--share"],                   "share local path"),
    ("url",       ["-a", "--share-temp"],         "share temp download"),
    ("url",       ["-a", "--share-temp", "--zip"],"share temp + zip"),
    ("url",       ["-a", "--share"],              "staging share"),
    ("url",       ["-a", "--share", "--zip"],     "staging + zip"),
    ("url",       ["-a", "--group", "P", "--share"],
                                                  "collection share"),
    ("url",       ["-a", "--group", "P", "--share", "--zip"],
                                                  "collection archive"),
    
    # ===== 8. Utility & Maintenance =====
    ("url", ["--info"],                           "system info"),
    ("url", ["--wrap"],                           "analytics wrap"),
    (None,  ["--history"],                        "show history"),
    (None,  ["--history", "50"],                  "history limit 50"),
    (None,  ["--history", "--reverse"],           "history reversed"),
    (None,  ["--history", "--find", "song"],     "history filtered"),
    (None,  ["--reset", "cache"],                "reset cache"),
    (None,  ["--reset", "history", "cache"],       "reset multiple"),
    (None,  ["--recheck"],                        "force recheck"),
    
    # ===== 9. Configuration =====
    (None,  ["--lang", "id"],                     "set language"),
    (None,  ["--progress-style", "modern"],       "progress modern"),
    (None,  ["--progress-style", "classic"],      "progress classic"),
    (None,  ["--delay", "3"],                     "set delay"),
    (None,  ["--retries", "5"],                   "set retries"),
    (None,  ["--header", "classic"],              "set header"),
]
```

Setiap test case:

```python
@pytest.mark.integration
@pytest.mark.parametrize("url,args,desc", FLAG_COMBINATIONS)
def test_flag_combination(url, args, desc, tmp_path, mocker):
    """Test that every documented flag combination works as expected."""
    # 1. Mock yt-dlp (gak perlu network)
    fake_info = {...}  # fake video/playlist info dict
    mocker.patch("yt_dlp.YoutubeDL.extract_info", return_value=fake_info)
    mocker.patch("yt_dlp.YoutubeDL.__enter__", ...)
    
    # 2. Mock HTTP (smart-cover, genius, itunes)
    mocker.patch("requests.get", return_value=MockResponse(200, b"fake"))
    
    # 3. Mock ffmpeg/PyAV (thumbnail crop)
    mocker.patch("tetodl.utils.thumbnail.crop_thumbnail_to_square", return_value=True)
    
    # 4. Mock subprocess calls
    mocker.patch("subprocess.run", return_value=MockCompletedProcess())
    
    # 5. Run via CLI parser + dispatcher
    sys.argv = ["tetodl"] + ([url] if url else []) + args
    from tetodl.cli.parser import cli
    handled, result = cli.parse()
    
    # 6. Verify expected outcome
    if "history" in args or "reset" in args or "info" in args:
        assert handled == True  # early-exit commands
    else:
        # Download/search commands → verify pipeline was invoked
        assert isinstance(result, (CliDownload, CliSearch, CliMenu))
```

#### File `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [main, "feat/**"]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      release:
        description: "Create release?"
        type: boolean
        default: false

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff mypy
      - run: ruff check tetodl/
      - run: mypy tetodl/ --ignore-missing-imports

  test-unit:
    name: Unit (py${{ matrix.python }}, ${{ matrix.os }})
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ["3.9", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install -e ".[full,windows]"
      - run: pytest -m "not slow and not network and not integration" -v

  test-integration:
    name: Integration (${{ matrix.os }})
    needs: [lint]
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[full,windows]"
      - run: pytest -m "integration" -v --tb=short
        env:
          TETODL_CI: "1"

  build:
    name: Build (${{ matrix.os }})
    needs: [test-unit, test-integration]
    if: github.ref == 'refs/heads/main'
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pyinstaller
      - run: pip install -e ".[full,windows]"
      - run: pyinstaller tetodl.spec
      - name: Smoke test
        run: |
          if [[ "${{ matrix.os }}" == "windows-latest" ]]; then
            ./dist/tetodl.exe --version
            ./dist/tetodl.exe --help
          else
            ./dist/tetodl --version
            ./dist/tetodl --help
          fi
      - uses: actions/upload-artifact@v4
        with:
          name: tetodl-${{ matrix.os == 'ubuntu-latest' && 'linux' || 'windows' }}
          path: dist/tetodl*

  test-distros:
    name: Linux (${{ matrix.distro }})
    needs: [lint]
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    strategy:
      fail-fast: false
      matrix:
        distro:
          - ubuntu:20.04
          - ubuntu:22.04
          - ubuntu:24.04
          - debian:11
          - debian:12
          - archlinux:latest
          - fedora:40
          - fedora:41
          - alpine:latest
          - nixos/nix:latest
    runs-on: ubuntu-latest
    container:
      image: ${{ matrix.distro }}
    steps:
      - uses: actions/checkout@v4
      - name: Install Python + ffmpeg
        run: |
          case "${{ matrix.distro }}" in
            ubuntu*|debian*)
              apt-get update -qq
              apt-get install -y -qq python3-pip ffmpeg ;;
            archlinux*)
              pacman -Sy --noconfirm python python-pip ffmpeg ;;
            fedora*)
              dnf install -y python3-pip python3-devel ffmpeg-free ;;
            alpine*)
              apk add python3 py3-pip ffmpeg ;;
            nixos*)
              nix-shell -p python3 python3Packages.pip ffmpeg-headless
              --run "pip install -e .[full]" ;;
          esac
      - name: Test pip install
        run: |
          pip install -e ".[full]"
          tetodl --version
          tetodl --help
      - name: Test binary
        run: |
          pip install pyinstaller
          pyinstaller tetodl.spec --clean
          ./dist/tetodl --version

  e2e:
    name: E2E (Nightly)
    if: github.event_name == 'schedule' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[full]"
      - name: Real download test
        run: |
          tetodl "https://youtu.be/dQw4w9WgXcQ" -a -f m4a --smart-cover --lyrics -o /tmp/test-dl
          test -f /tmp/test-dl/*.m4a
          tetodl "https://youtu.be/dQw4w9WgXcQ" --thumbnail-only -f jpg -o /tmp/test-dl
          test -f /tmp/test-dl/*.jpg

  release:
    name: Release
    if: github.event_name == 'workflow_dispatch' && inputs.release
    needs: [build]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
      - name: Generate tag
        id: tag
        run: echo "tag=v$(date +'%Y.%m.%d')" >> $GITHUB_OUTPUT
      - uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.tag.outputs.tag }}
          files: |
            tetodl-linux/tetodl
            tetodl-windows/tetodl.exe
```

**Free tier GitHub Actions cukup karena:**
- Unlimited minutes untuk **public** repositori
- Satu run penuh: ~10-15 menit (lint + unit(4) + integrasi(2) + build(2))
- E2E cuma jalan **nightly** (schedule), bukan tiap push
- Tests pake mock, gak perlu YouTube API key

---

## Phase C — Installer & Distribution

### C1. `install.ps1` — Windows Installer (Binary Download)

**New file: `install.ps1`** — URL: `https://install.tetodl.dev`

```
One-liner: iwr "https://install.tetodl.dev" | iex
TETAP INTERAKTIF: Read-Host, Write-Host jalan setelah script selesai di-download.
```

Script ini **download pre-compiled binary** dari GitHub Releases. User **tidak perlu Python, Git, atau ffmpeg**.

```powershell
<#
.SYNOPSIS
    TetoDL Windows Installer — Binary Edition
.DESCRIPTION
    Downloads pre-compiled TetoDL binary from GitHub Releases.
    No Python, Git, or ffmpeg required.
    Usage: iwr "https://install.tetodl.dev" | iex
#>

param(
    [switch]$Force,
    [ValidateSet("cli", "full")]
    [string]$Variant = ""
)

# ─────────────────────────────────────────────────
# 1. Welcome
# ─────────────────────────────────────────────────
$Host.UI.RawUI.WindowTitle = "TetoDL Installer"

Write-Host "╔══════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       TetoDL Installer           ║" -ForegroundColor Cyan
Write-Host "║          (Windows)               ║" -ForegroundColor Cyan
Write-Host "║  One binary. No dependencies.    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─────────────────────────────────────────────────
# 2. Feature selection
# ─────────────────────────────────────────────────
if (-not $Variant) {
    Write-Host "Select variant:" -ForegroundColor Cyan
    Write-Host "  [1] tetodl-cli.exe (~25 MB) — CLI only"
    Write-Host "  [2] tetodl.exe (~70 MB) — Full: CLI + TUI + Daemon"
    Write-Host ""
    $choice = Read-Host "Choice (1/2)"
    switch ($choice) {
        "1" { $Variant = "cli" }
        default { $Variant = "full" }
    }
}

# ─────────────────────────────────────────────────
# 3. Detect architecture
# ─────────────────────────────────────────────────
$arch = switch ([Environment]::Is64BitOperatingSystem) {
    $true  { "x86_64" }
    $false { "i686" }
}
$binaryName = if ($Variant -eq "cli") { "tetodl-cli.exe" } else { "tetodl.exe" }
$downloadUrl = "https://github.com/rannd1nt/TetoDL/releases/latest/download/$binaryName"

# ─────────────────────────────────────────────────
# 4. Download binary
# ─────────────────────────────────────────────────
$installDir = "$env:LOCALAPPDATA\TetoDL"
$binPath = "$installDir\tetodl.exe"

if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

Write-Host "Downloading TetoDL..." -ForegroundColor Cyan
try {
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($downloadUrl, $binPath)
    Write-Host "[OK] Saved to $binPath" -ForegroundColor Green
} catch {
    Write-Host "[!] Download failed: $_" -ForegroundColor Red
    exit 1
}

# Mark as executable (Windows doesn't need this but for completeness)
Unblock-File $binPath -ErrorAction SilentlyContinue

# ─────────────────────────────────────────────────
# 5. Add to PATH (User-level)
# ─────────────────────────────────────────────────
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$installDir*") {
    $newPath = "$installDir;$currentPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "[OK] Added to PATH" -ForegroundColor Green
}

# ─────────────────────────────────────────────────
# 6. Done!
# ─────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Installation Complete!           ║" -ForegroundColor Green
Write-Host "║                                   ║" -ForegroundColor Green
Write-Host "║  Restart your terminal, then:     ║" -ForegroundColor Green
Write-Host "║                                   ║" -ForegroundColor Green
Write-Host "║     tetodl --help                 ║" -ForegroundColor Green
Write-Host "║     tetodl -a 'URL'              ║" -ForegroundColor Green
Write-Host "║                                   ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Refresh PATH for current session
$env:Path = "$installDir;$env:Path"
```

### C2. `tetodl.sh` — Linux Installer (Binary / Pip)

```
One-liner: bash <(curl -s https://install.tetodl.dev)
TETAP INTERAKTIF: membaca input user.
```

Dua mode install:
1. **Binary mode** (default): download pre-compiled `tetodl` binary dari GitHub Releases → no deps
2. **Pip mode** (opsional): `pip install tetodl[full]` — butuh Python

```bash
#!/usr/bin/env bash
# TetoDL Linux Installer
# Usage: bash <(curl -s https://install.tetodl.dev)

# ─────────────────────────────────────────────────
# 1. Welcome
# ─────────────────────────────────────────────────
echo "╔══════════════════════════════════╗"
echo "║       TetoDL Installer           ║"
echo "║          (Linux)                 ║"
echo "╚══════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────
# 2. Select installation method
# ─────────────────────────────────────────────────
echo "Select installation method:"
echo "  [1] Binary (fast, ~50 MB, no Python needed)"
echo "  [2] Pip (requires Python + ffmpeg)"
echo ""
read -p "Choice (1/2): " method

case "$method" in
    2)
        # Pip mode
        pip install tetodl[full]
        echo "Done! Run 'tetodl' from anywhere."
        ;;
    *)
        # Binary mode (default)
        echo "Select variant:"
        echo "  [1] tetodl-cli (~25 MB) — CLI only"
        echo "  [2] tetodl (~50 MB) — Full: CLI + TUI + Daemon"
        read -p "Choice (1/2): " variant
        BIN="tetodl"
        [ "$variant" = "1" ] && BIN="tetodl-cli"
        
        echo "Downloading $BIN..."
        curl -L "https://github.com/rannd1nt/TetoDL/releases/latest/download/$BIN-linux" \
             -o "$HOME/.local/bin/$BIN"
        chmod +x "$HOME/.local/bin/$BIN"
        
        # Add to PATH if needed
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            echo "Added ~/.local/bin to PATH"
        fi
        
        echo ""
        echo "╔══════════════════════════════════╗"
        echo "║  Installation Complete!           ║"
        echo "║                                   ║"
        echo "║  Run 'tetodl' from terminal.      ║"
        echo "╚══════════════════════════════════╝"
        ;;
esac
```

**`tetodl.sh` yang lama:** dideprekasi. Fungsinya diganti oleh script installer ini dan `pip install tetodl`.

### C3. Distribution via `install.tetodl.dev`

Satu URL, auto-detect OS:
```
Request → https://install.tetodl.dev/
  │
  ├── User-Agent: Windows → 302 redirect → https://github.com/.../install.ps1
  │                        atau serve langsung
  │
  └── User-Agent: Linux   → 302 redirect → https://github.com/.../tetodl.sh
```

Implementasi simpel: **Cloudflare Worker** (gratis) atau **GitHub Pages** + JS redirect.

Atau pake URL terpisah:
- `https://install.tetodl.dev/windows`
- `https://install.tetodl.dev/linux`

### C4. PyPI Release

```bash
# Build
python -m build

# Upload
twine upload dist/*

# Done — user tinggal:
pip install tetodl
```

Persyaratan akun PyPI: daftar di https://pypi.org/ (gratis).

---

## Installation Methods

TetoDL v2.0 mendukung 3 metode instalasi yang berbeda, tergantung kebutuhan user.

### Method 1: One-liner Binary (Recommended — No Dependencies)

**Cocok untuk user awam.** Download pre-compiled binary dari GitHub Releases. Binary sudah bundle Python runtime + semua library + ffmpeg.exe. **Tidak perlu Python, Git, atau ffmpeg.**

| Platform | Command |
|----------|---------|
| **Windows** | `iwr "https://install.tetodl.dev" \| iex` |
| **Linux** | `bash <(curl -s https://install.tetodl.dev)` |

Kedua installer **tetap interaktif** (tanya fitur, konfirmasi PATH, dll) — karena script di-download dulu semua, baru di-run.

Binary sizes:
| Variant | Windows | Linux |
|---------|---------|-------|
| `tetodl` (Full: CLI+TUI+Daemon) | ~70 MB | ~50 MB |
| `tetodl-cli` (CLI only) | ~25 MB | ~20 MB |

### Method 2: Pip Install (Python Environment)

**Cocok untuk developer atau pengguna Python.** TetoDL terinstall sebagai Python package. Butuh Python 3.9+ dan ffmpeg di PATH.

```bash
# Minimal
pip install tetodl                          # CLI only

# + TUI (rich, questionary, QR)
pip install tetodl[tui]                    # CLI + TUI

# Full
pip install tetodl[full]                   # CLI + TUI + Daemon

# Windows specific (PyAV instead of ffmpeg subprocess)
pip install tetodl[full,windows]           # Full + PyAV
pip install tetodl[all]                    # Full + PyAV + Daemon
```

Pip mode di Windows **tetap butuh ffmpeg.exe** untuk yt-dlp internal features. Install via:
```powershell
winget install ffmpeg
```

### Method 3: Direct Download

Download langsung dari GitHub Releases tanpa installer interaktif:
- Windows: `https://github.com/rannd1nt/TetoDL/releases/latest/download/tetodl.exe`
- Linux: `https://github.com/rannd1nt/TetoDL/releases/latest/download/tetodl-linux`

### Summary Perbandingan

| Aspect | Binary (iwr/curl) | Pip install | Direct download |
|--------|-------------------|-------------|-----------------|
| Butuh Python? | ❌ | ✅ | ❌ |
| Butuh Git? | ❌ | ❌ | ❌ |
| Butuh ffmpeg? | ❌ (bundled) | ✅ (system/winget) | ❌ (bundled) |
| Interaktif? | ✅ | ❌ | ❌ |
| Update app | Download ulang | `pip install --upgrade` | Download ulang |
| Update yt-dlp | Built-in override | `pip install --upgrade` | Built-in override |
| Size | ~25-70 MB | ~15 MB + Python | ~25-70 MB |

---

## Update Mechanism

### Source / Pip Mode

| Komponen | Command |
|----------|---------|
| App | `pip install --upgrade tetodl` |
| yt-dlp | `pip install --upgrade yt-dlp` (via `--update` flag / menu) |
| Data | Otomatis — config, history, cache di `~/.config/TetoDL/` dll |

### Compiled Binary Mode

| Komponen | Mechanism |
|----------|-----------|
| App | Self-destructive update: download binary baru → replace → restart |
| yt-dlp | Download wheel dari PyPI → extract ke `~/.cache/TetoDL/ytdlp-override/` |

**App update flow (self-destructive):**
```
Binary startup dengan --update flag
  ↓
Detect platform (windows/linux) + variant (cli/tui/daemon/full)
  ↓
Download {binary}.new dari GitHub Releases
  ↓
Windows:
  ├── rename tetodl.exe → tetodl.exe.old
  ├── rename tetodl.exe.new → tetodl.exe
  ├── spawn tetodl.exe --version
  └── hapus .old di startup berikutnya

Linux:
  ├── os.replace(temp, current)
  ├── os.chmod(current, 0o755)
  └── os.execv(current, sys.argv)  # restart langsung
```

**Windows .bat update script:**
```batch
@echo off
ping 127.0.0.1 -n 2 > nul
del "%~dp0tetodl.exe.old" 2>nul
move /y "%~dp0tetodl.exe.new" "%~dp0tetodl.exe" > nul
start "" "%~dp0tetodl.exe" --version
del "%~f0"
```

Pattern ini sama persis dengan yang dipake `uv`, `mise`, `pip`, `rustup` — sudah battle-tested.

**yt-dlp update flow di binary:**
```
User pilih update yt-dlp
  → download wheel dari PyPI
  → extract ke ~/.cache/TetoDL/ytdlp-override/
  → console.warn("Restart to apply")
  → next startup: sys.path.insert(0, override_dir)
  → import yt_dlp → pakai versi baru
```

---

## Feature Separation

### Pip Extras

```toml
[project.optional-dependencies]
tui = ["rich>=13.9.4", "questionary>=2.1.1", "qrcode>=8.2"]
daemon = ["fastapi>=0.136.3", "uvicorn>=0.48.0", "zeroconf>=0.2.0"]
windows = ["av>=14.0"]  # PyAV for thumbnail processing
full = ["tetodl[tui,daemon]"]
all = ["tetodl[full,windows]"]
```

Setiap extra hanya install library yang diperlukan. Tidak ada overhead:

```bash
# CLI only — 5 deps (yt-dlp, requests, bs4, mutagen, colorama, pydantic)
pip install tetodl

# + TUI — tambah 3 deps (rich, questionary, qrcode)
pip install tetodl[tui]

# + Daemon — tambah 3 deps (fastapi, uvicorn, zeroconf)
pip install tetodl[tui,daemon]

# CLI + Daemon (no TUI) — hanya Daemon extra
pip install "tetodl[daemon] @ git+https://github.com/rannd1nt/TetoDL"

# Full — semua extra
pip install tetodl[all]
```

### Binary Variants

| Binary Name | Content | Size (Win) | Size (Linux) | Flags in --help |
|-------------|---------|-----------|-------------|-----------------|
| `tetodl-cli.exe` | Core only | ~25 MB | ~20 MB | Core CLI flags |
| `tetodl-tui.exe` | Core + TUI | ~40 MB | ~35 MB | Core + TUI flags |
| `tetodl-daemon.exe` | Core + Daemon | ~45 MB | ~40 MB | Core + Daemon flags |
| `tetodl.exe` / `tetodl-linux` | Full (Core+TUI+Daemon) | ~70 MB | ~50 MB | All flags |

### Graceful Degradation Matrix

| Code Path | CLI-only binary | CLI+TUI binary | CLI+Daemon binary | Full binary |
|-----------|----------------|----------------|-------------------|-------------|
| `import rich` | ❌ → PlainTheme | ✅ | ❌ → PlainTheme | ✅ |
| `import questionary` | ❌ → simple input() | ✅ | ❌ → simple input() | ✅ |
| `import fastapi` | ❌ → "Daemon unavailable" | ❌ → "Daemon unavailable" | ✅ | ✅ |
| `import av` (Windows) | ❌ → fallback subprocess | ❌ → fallback subprocess | ❌ → fallback subprocess | ✅ |

Semua fallback memastikan **app tidak crash** — hanya fitur yang tidak tersedia.

---

## Complete File Change Summary

| # | File | Status | Change |
|---|------|--------|--------|
| 1 | `pyproject.toml` | Modified | Full `[project]` + extras + scripts + pytest markers |
| 2 | `tetodl/__main__.py` | **New** | Entry point for `python -m tetodl` & CLI command |
| 3 | `tetodl/constants.py` | Modified | Platform detection rewrite, Windows paths init, bundled ffmpeg detection |
| 4 | `tetodl/core/dependency.py` | Modified | Remove Win block, `which`→`shutil.which()`, ffmpeg optional on Windows |
| 5 | `tetodl/ui/verifier.py` | Modified | Remove `verify_platform_compatibility()` call |
| 6 | `tetodl/utils/thumbnail.py` | Modified | Dual PyAV/ffmpeg implementation (crop + convert) |
| 7 | `tetodl/core/search.py` | Modified | Subprocess `yt-dlp` CLI → Python `yt_dlp.YoutubeDL` API |
| 8 | `tetodl/core/maintenance.py` | Modified | `git pull` → `pip install --upgrade`, `bash` uninstall → pure Python |
| 9 | `tetodl/utils/network.py` | Modified | `os.startfile()` for Windows URL opening |
| 10 | `tetodl/daemon/service.py` | Modified | IS_WINDOWS guard on systemd functions |
| 11 | `tetodl/daemon/display.py` | Modified | IS_WINDOWS guard on systemctl check |
| 12 | `tetodl.spec` | **New** | PyInstaller config with ffmpeg bundling + build variants |
| 13 | `.github/workflows/ci.yml` | **New** | Full CI/CD: lint → unit test → integration test → build → release |
| 14 | `install.ps1` | **New** | Windows binary installer (interactive, one-liner, no deps) |
| 15 | `tetodl.sh` | Deprecated | Replaced by pip install + Linux binary installer |
| 16 | `install.sh` | **New** | Linux binary installer (interactive, one-liner) |
| 17 | Test files (14+ files) | Modified | `/tmp/` → `tmp_path` fixture, add `integration` marker |
| 18 | `tetodl/tests/test_flag_combinations.py` | **New** | Parametrized integration tests for all README flag combinations |
| 19 | `.github/workflows/nightly.yml` | **New** | Nightly E2E test with real YouTube URLs |
| 20 | `plan/README.md` | **New** | This document |

---

## Out of Scope

Hal-hal ini **tidak** termasuk dalam branch `feat/packaging`:

| Feature | Alasan |
|---------|--------|
| **Desktop app (GUI)** | Butuh framework terpisah (Tauri/Electron) — nanti aja |
| **Windows Daemon (`pywin32`)** | Service stub dulu, implementasi penuh nanti |
| **macOS support** | Belum ada permintaan, infrastructure bisa nanti |
| **`install.tetodl.dev` URL hosting** | Sementara pake GitHub Releases langsung |
| **Android/Termux refactor** | Tetap jalan seperti sekarang |
| **ARM64 build** | Nanti kalo ada permintaan |
| **Portable mode (USB)** | Nanti |

---

## Timeline

```
Fase A (Code Refactor)    → 2-3 hari
Fase B (Build & CI/CD)    → 1-2 hari
Fase C (Installer)        → 1 hari
─────────────────────────────────
Total                     → ~5 hari
```

---

*Document version: 2.0 — Last updated: 2026-07-21*
