<div align="center">

  <img src="docs/TETOTETOTETO.gif" alt="TetoDL Banner" width="100%">

  <br>
  <h1>TetoDL - TUI & CLI Media Downloader</h1>

  <p>
    <img src="https://img.shields.io/badge/MADE_WITH-PYTHON-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/PLATFORM-LINUX_%7C_WSL_%7C_TERMUX-green?style=for-the-badge&logo=linux&logoColor=white" alt="Platform">
    <img src="https://img.shields.io/badge/LICENSE-MIT-purple?style=for-the-badge" alt="License">
  </p>
  
  <p>
    <a href="https://github.com/rannd1nt/TetoDL/issues">
      <img src="https://img.shields.io/badge/Maintained%3F-Yes-238636?style=flat-square" alt="Maintenance">
    </a>
    <img src="https://img.shields.io/badge/Version-1.1.1-orange?style=flat-square" alt="Version">
  </p>

</div>

**TetoDL** is a powerful, hybrid **CLI & TUI** media downloader built for Linux, WSL, and Android (Termux). It combines the speed of command-line tools with the aesthetics of a Terminal User Interface.

Focusing on **Smart Metadata**, TetoDL ensures your music library is always tidy with correct cover arts, artist names, and albums even from YouTube sources.

---

## Features

* **Hybrid Interface:** Use simple CLI commands for quick downloads or the TUI for a visual menu.
* **Smart Metadata:** Auto-embeds cover art and metadata (via iTunes).
* **Smart Subfolder System:** Intelligently manages download paths. It remembers your created subfolders (e.g., for Albums/Playlists) and auto-cleans "ghost" folders from the menu if they are deleted from the disk.
* **TetoDL Analytics (Wrap):** visualize your download habits (Top Artists, Albums, Total Duration) directly in your terminal.
* **Advanced History:** Searchable logs with filtering and sorting capabilities.
* **System Diagnostics:** Built-in tools to check system health, storage usage, and configuration.
* **Cross-Platform:** Optimized for **Linux & WSL**. (Legacy support for Termux available).

---

## Installation

### Prerequisites
* **Linux / WSL:** `git`, `python3`, `ffmpeg`
* **Termux:** `git`, `python`, `ffmpeg`

### Quick Install
Clone the repository and run the universal installer:

```bash
# 1. Clone Repository
git clone https://github.com/rannd1nt/TetoDL.git
cd TetoDL
```
```bash
# 2. Run Full Installer (Auto-detects OS & installs dependencies)
bash tetodl.sh
```
OR
```bash
# Without Spotdl Installation
bash tetodl.sh --lite
```

**Note for Termux Users:** The current `main` branch is optimized for Linux/WSL. <br>If you want the old stable version specifically designed for Android/Termux mobile interface, please use the legacy tag:
```bash
git clone --branch legacy-termux-v1 https://github.com/rannd1nt/TetoDL.git
```

---

## TUI Mode Visual Tour
Experience the interactive menu by simply running `tetodl` without arguments.

### Main Menu Appearance
![Screenshoot](docs/main-menu.png)

### Download Location Selection
![Screenshoot](docs/output-path.png)

### Download Progress Log
![Screenshoot](docs/download-process.png)

### Download History
![Screenshoot](docs/history.png)

### Download Wrap
![Screenshoot](docs/wrap.png)

---

## TetoDL CLI Mode Usage
> **WARNING:** When using the CLI mode, ALWAYS wrap your URLs in quotes. Terminals interpret the `&` symbol (common in YouTube URLs) as a background command.<br><br>
**Recommended Usage:** `tetodl "https://youtube.com/watch?v=..."`<br>
**Not Recommended Usage:** `tetodl https://youtube.com/watch?v=...`


### Common Scenarios

* **Default Download (Auto-Detect):** 
    Without any flags, TetoDL automatically detects the content type from the link. It relies on your saved configuration (defined in `config.json` or **TUI settings**) to determine the download path and quality preferences.
    ```bash
    tetodl "https://youtu.be/url"
    ```

* **Audio Only (Music Mode):**
    Download audio extraction specifically. The `-a` flag enables audio mode, while `-f m4a` forces the output to **M4A (AAC)** format, which is ideal for maintaining metadata in music libraries.
    ```bash
    tetodl "https://youtu.be/url" -a -f m4a
    ```

* **Video Only (Video Mode):**
    Uses `-v` for video mode, forces the **.mp4** container for maximum compatibility, and caps the resolution at **720p**.
    ```bash
    tetodl "https://youtu.be/url" -v -f mp4 -r 720p
    ```

* **Power User Mode**
    Full control over the download. Fetches high-quality video in **.mkv** with a maximum resolution limit of **1080p**, enforces the **h264** codec for compatibility, and saves the file to a specific custom directory using the `-o` flag.
    ```bash
    tetodl "https://youtu.be/url" -v -f mkv -r 1080p -c h264 -o "/home/user/Videos/Collection"
    ```

---

## Command Reference

**1. Download Options:** Basic flags for downloading media.

| Flag | Argument | Description |
|:-----|:-----|:-----|
| `-a`, `--audio` | - | Download as Audio. |
| `-v`, `--video` | - | Download as Video (Default). |
| `-f`, `--format`| FORMAT | Force format: `mp3`, `m4a`, `opus` (audio) or `mp4`, `mkv` (video). |
|`-r`, `--resolution`| RES | Max video resolution limit: `480p`, `720p`, `1080p`, `2k`, `4k`, `8k`. |
| `-c`, `--codec` | CODEC | Set video codec: `default` (speed), `h264` (compat), `h265` (size).|
|`-o`, `--output`| PATH | Save to a custom output directory (Overrides TUI Base Path). |

**2. Utility, Maintance & History:** Manage data, view statistics, and perform system maintenance.
| Flag | Argument | Description |
|:-----|:-----|:-----|
|`--info`| - | Show current configuration, system paths, and storage usage. |
|`--wrap`| - | Show TetoDL Analytics (Top Artists, Albums, & Total Duration). |
|`--history`| LIMIT | Show download history (default last 20). Ex: tetodl --history 50. |
|`--reverse`| - | **(Requires `--history`)** Show oldest downloads first. |
| `--search` | QUERY | **(Requires `--history`)** Filter history by title (case-insensitive). |
|`--recheck`| - | Force dependency integrity check (ffmpeg, spotdl, etc). |
|`--reset`| TARGET | Reset data. Targets: `history`, `cache`, `config`, `registry`, `all`. |
|`--update`| - | Update TetoDL to latest version (Git Pull). |
|`--uninstall`| - | Remove TetoDL symlink, launcher, and cleanup user data. |

**3. Configuration:** Advanced settings that are often hidden from the TUI.
| Flag | Argument | Description |
|:-----|:-----|:-----|
|`--header`| NAME |Set TUI app header (`default`, `classic` or `filename` in `assets/`). |
|`--progress-style`| STYLE | Set progress bar: `minimal`, `classic`, `modern`. |
| `--lang` | CODE | Set language: `en` (English) or `id` (Indonesia).|
| `--delay`| SEC | Set delay between downloads (seconds). |
| `--retries` | NUM | Set max download retries. |
| `--media-scanner` | on/off | Enable/Disable Android Media Scanner (Termux Only). |

### **CLI vs TUI Configuration**

1. **TUI (Interactive Mode - Persistent):**  
    Use the **TUI** to configure your **Global Defaults**. Any changes made here are saved permanently to `config.json` and will be used automatically for future downloads. This includes:
   - **Base Path:** Default download locations for Music and Video.
   - **Video Preferences:** Default Resolution (e.g., Max 
   1080p), Container (MP4/MKV), and Codec.
   - **Audio Preferences:** Default Quality/Format (M4A/MP3/Opus).
2. **CLI (Command Line - Runtime):**
   - **One-Time Overrides:** Flags like `-r 4k`, `-f mp3`, or `-o /tmp` only apply to the current command. They temporarily override your TUI defaults but do not change them permanently.
     and do not change global settings.
   - **Advanced Maintenance:** System-level settings like `--retries`, `--delay`, `--media-scanner` and `--reset` are exclusive to the CLI to prevent accidental changes in the TUI menu.

---

## Localization (i18n)
TetoDL supports two languages:
- `en` — English
- `id` — Indonesian


## Acknowledgments
- Built on top [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [ffmpeg](https://www.ffmpeg.org/)
- Inspired by various open-source downloader tools for YouTube and Spotify

## License
Distributed under the MIT License. See `LICENSE` for more information.