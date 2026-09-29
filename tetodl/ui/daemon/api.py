# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import html as htmlmod
import io
import os
import re
import sys
import threading
import time
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from ..cli.dispatch import execute_download
from ...constants import APP_VERSION
from ...utils.console import console
from ...utils.i18n_keys import Keys
from ...core.domain import config as cfg
from ...core.domain import config as config_mgr
from ...core.domain.env import env
from ...core.domain.models import DownloadResult, DownloadSession
from ...core.domain.server_config import get_server_config
from ...utils.display import get_free_space
from ...utils.files import TempManager
from ...utils.formatters import color
from ...utils.console.themes import PlainTheme
from ...utils.processing import parse_playlist_items
from ...utils.time_parser import get_cut_seconds
from .auth import (
    clear_auth_cookies,
    issue_token_pair,
    set_auth_cookies,
    verify_admin_password,
    verify_request_auth,
)
from .display import daemon_urls
from .models import AuthVerifyRequest, DownloadRequest, PreviewRequest

active_tasks: dict[str, Any] = {}

# --- BACKGROUND WORKERS ---
async def cleanup_worker():
    while True:
        # Ambil interval dari config (default 3600 detik / 1 jam)
        interval = getattr(cfg, 'daemon_cleanup_interval', 3600)
        temp_dir = TempManager.get_temp_dir()
        current_time = time.time()

        if temp_dir.exists():
            for file_path in temp_dir.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > interval:
                        try:
                            file_path.unlink()
                            print(f"[Daemon] Auto-cleaned temp file: {file_path.name}")
                        except Exception:
                            pass
        
        # Cek setiap 5 menit (300 detik)
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(TempManager.get_temp_dir(), exist_ok=True)
    cleanup_task = asyncio.create_task(cleanup_worker())
    yield
    cleanup_task.cancel()

# --- APP INITIALIZATION ---
app = FastAPI(
    title="TetoDL Service API", 
    version=APP_VERSION, 
    description="Full-Featured Web Services for TetoDL",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATIC FILES & ROUTING ---
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.is_dir():
    app.mount("/web", StaticFiles(directory=str(STATIC_DIR), html=True), name="static_web")

@app.get("/")
@app.get("/web")
async def root():
    return RedirectResponse(url="/web/")

# Mount Folder Media untuk Streaming Lokal
app.mount("/media/music", StaticFiles(directory=cfg.music_root), name="music_media")
app.mount("/media/videos", StaticFiles(directory=cfg.video_root), name="video_media")
app.mount("/media/temp", StaticFiles(directory=TempManager.get_temp_dir()), name="temp_media")


# --- CORE LOGIC WRAPPER (with realtime log capture) ---
class _LogTee:
    """Tee: tulis ke original stdout AND buffer, update task logs live."""
    def __init__(self, original, buf, task_ref):
        self.original = original
        self.buf = buf
        self.task_ref = task_ref

    def write(self, data):
        self.original.write(data)
        self.buf.write(data)
        self.task_ref["logs"] = self.buf.getvalue()[-8000:]

    def flush(self):
        self.original.flush()
        self.buf.flush()

    def isatty(self):
        return False

def background_task_runner(task_id: str, session: DownloadSession, mode: str = 'cli_download', task_title: str = ''):
    log_buf = io.StringIO()
    task_data = {
        "status": "processing",
        "details": session.url or 'Task Queued',
        "title": task_title or '',
        "file_path": None,
        "logs": "",
    }
    active_tasks[task_id] = task_data

    old_stdout = sys.stdout
    old_console_file = getattr(console.rich, 'file', old_stdout)
    tee = _LogTee(old_stdout, log_buf, task_data)

    sys.stdout = tee
    try:
        console.rich.file = tee  # type: ignore[assignment]
    except Exception:
        pass

    try:
        result = execute_download(session) or DownloadResult(success=False)
        task = active_tasks[task_id]
        task["status"] = "completed"
        if isinstance(result, DownloadResult):
            fp = result.file_path
            if fp:
                fp_abs = os.path.abspath(fp)
                task["file_path"] = fp_abs
                task["is_dir"] = os.path.isdir(fp_abs)
                if task["is_dir"]:
                    task["dir_path"] = fp_abs
                else:
                    task["dir_path"] = os.path.dirname(fp_abs)
            fc = result.file_count
            if fc:
                task["file_count"] = fc
    except Exception as e:
        active_tasks[task_id]["status"] = f"error: {e!s}"
        active_tasks[task_id]["file_path"] = None
    finally:
        sys.stdout = old_stdout
        try:
            console.rich.file = old_console_file
        except Exception:
            pass
        task_data["logs"] = log_buf.getvalue()[-8000:]


# ==========================================
#              API ENDPOINTS
# ==========================================

# --- 1. SYSTEM & CONFIG ---
@app.get("/api/v1/system/status")
async def get_system_status():
    return {
        "status": "online",
        "storage": {
            "music_free_space": get_free_space(cfg.music_root),
            "video_free_space": get_free_space(cfg.video_root)
        }
    }

@app.get("/api/v1/config")
async def get_current_config():
    """Membaca konfigurasi yang tersimpan (termasuk setting Daemon)"""
    config_mgr.load_config()
    return {
        "audio_quality": cfg.audio_quality,
        "video_container": cfg.video_container,
        "max_resolution": cfg.max_video_resolution,
        "daemon_default_temp": getattr(cfg, 'daemon_default_temp', True),
        "daemon_cleanup_interval": getattr(cfg, 'daemon_cleanup_interval', 3600),
        "lyrics_mode": cfg.lyrics_mode,
    }


# --- AUTH ENDPOINTS ---
@app.post("/api/v1/auth/verify")
async def auth_verify(req: AuthVerifyRequest, response: Response):
    """Verify admin password (teto_password) and issue HttpOnly Dual-Token cookies."""
    server_cfg = get_server_config()
    if not server_cfg.teto_password:
        raise HTTPException(
            status_code=400,
            detail="Admin password (teto_password) is not configured in tetodl.conf",
        )
    if not verify_admin_password(req.password, server_cfg):
        raise HTTPException(status_code=401, detail="Invalid admin password")

    access_tok, refresh_tok = issue_token_pair(server_cfg)
    set_auth_cookies(response, access_token=access_tok, refresh_token=refresh_tok, cfg=server_cfg)
    return {"status": "ok", "authenticated": True}


@app.get("/api/v1/auth/status")
async def auth_status(request: Request, response: Response):
    """Check current authentication status, performing silent refresh if needed."""
    server_cfg = get_server_config()
    is_auth, source = verify_request_auth(request, response, server_cfg)
    return {
        "authenticated": is_auth,
        "password_configured": bool(server_cfg.teto_password),
        "source": source,
    }


@app.post("/api/v1/auth/logout")
async def auth_logout(response: Response):
    """Clear authentication cookies."""
    clear_auth_cookies(response)
    return {"status": "ok", "authenticated": False}


# --- 2. ORCHESTRATION (THE BIG BRAIN) ---
@app.post("/api/v1/download")
async def process_download(
    req: DownloadRequest,
    request: Request,
    response: Response,
    bg_tasks: BackgroundTasks,
):
    if not req.url and not req.search_query:
        raise HTTPException(status_code=400, detail="Must provide 'url' or 'search_query'")

    task_id = str(uuid.uuid4())[:8]

    # --- TEMP VS PERMANENT STORAGE LOGIC ---
    if req.share:
        is_auth, _ = verify_request_auth(request, response)
        if not is_auth:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Saving to permanent library requires admin authorization (teto_password).",
            )
        is_temp = False
    elif req.share_temp:
        is_temp = True
    else:
        default_temp = getattr(cfg, 'daemon_default_temp', True)
        if not default_temp:
            is_auth, _ = verify_request_auth(request, response)
            is_temp = not is_auth
        else:
            is_temp = True

    output_path: str | None = None
    if is_temp:
        task_dir = Path(str(TempManager.get_temp_dir())) / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(task_dir)

    media_type: Literal['audio', 'video', 'thumbnail'] = 'audio'
    if req.video_only:
        media_type = 'video'
    elif req.thumbnail_only:
        media_type = 'thumbnail'

    cut_range: tuple[float, float] | None = None
    if req.cut_time:
        try:
            cut_range = get_cut_seconds(req.cut_time)
        except ValueError:
            pass

    playlist_items: set[int] | None = None
    if req.items:
        try:
            playlist_items = parse_playlist_items(req.items)
        except ValueError:
            pass

    from ...utils.network import is_spotify_url
    is_spotify = bool(req.spotify or (req.url and is_spotify_url(req.url)))

    session = DownloadSession(
        url=req.url or '',
        media_type=media_type,
        output_path=output_path,
        format=req.format or None,
        resolution=req.resolution or None,
        codec=req.codec or None,
        cut_range=cut_range,
        playlist_items=playlist_items,
        group_folder=req.group or False,
        m3u=req.m3u or False,
        zip=req.zip or False,
        cover=req.cover or False,
        metadata=req.metadata or False,
        no_enrich=req.no_enrich or False,
        lyrics=req.lyrics,
        romaji=req.romaji,
        async_mode=req.async_mode or False,
        is_temp_session=False,
        is_spotify=is_spotify,
    )

    mode = 'cli_download' if req.url else 'cli_search'

    bg_tasks.add_task(background_task_runner, task_id, session, mode, req.title or '')

    target_loc = "Temporary Storage" if is_temp else "Permanent Library"
    return {
        "status": "queued",
        "task_id": task_id,
        "message": f"Download task dispatched. Target: {target_loc}"
    }

@app.get("/api/v1/tasks")
async def get_active_tasks():
    return active_tasks

@app.get("/api/v1/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    task = active_tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"logs": task.get("logs", ""), "status": task["status"]}


# --- 3. PREVIEW (via yt-dlp extract_info) ---
@app.post("/api/v1/preview")
async def preview_media(req: PreviewRequest):
    import asyncio as _asyncio

    console.proc(f"Previewing metadata for: {req.url}")

    # --- Spotify preview path ---
    from ...utils.network import is_spotify_url
    if req.url and is_spotify_url(req.url):
        from ...core.clients.spotify import SpotifyResolver
        resolver = SpotifyResolver()
        try:
            container_name, tracks = await _asyncio.wait_for(
                _asyncio.to_thread(resolver.resolve_meta, req.url),
                timeout=15.0,
            )
        except _asyncio.TimeoutError:
            console.err("Spotify metadata request timed out (15s)")
            raise HTTPException(status_code=504, detail="Spotify metadata request timed out (15s). Please check network connection.")
        except Exception as e:
            console.err(f"Spotify extraction failed: {e}")
            raise HTTPException(status_code=400, detail=f"Spotify extraction failed: {e}")

        if not tracks:
            raise HTTPException(status_code=400, detail="No tracks found")

        console.ok(f"Spotify metadata resolved: {container_name or tracks[0].title}")

        entries = [
            {
                "id": t.spotify_id,
                "title": t.title,
                "artist": t.artist,
                "artists": t.artists,
                "album": t.album,
                "duration": t.duration_ms // 1000,
                "thumbnail": t.cover_url,
            }
            for t in tracks
        ]

        return {
            "id": container_name or tracks[0].spotify_id,
            "title": container_name or f"{tracks[0].title} - {tracks[0].artist}",
            "duration": sum(t.duration_ms for t in tracks) // 1000,
            "uploader": tracks[0].artist if tracks else None,
            "thumbnail": tracks[0].cover_url or None,
            "description": None,
            "webpage_url": req.url,
            "formats": [],
            "is_playlist": len(tracks) > 1,
            "available_resolutions": [],
            "entries": entries,
            "source": "spotify",
        }

    # --- YouTube / general preview path ---
    try:
        import yt_dlp as yt

        def _extract():
            with yt.YoutubeDL({
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
                'cachedir': env.get('ytdlp_cache_dir'),
            }) as ydl:
                return ydl.extract_info(req.url, download=False)

        info = await _asyncio.wait_for(
            _asyncio.to_thread(_extract),
            timeout=25.0,
        )
    except _asyncio.TimeoutError:
        console.err(f"Preview timed out for URL: {req.url}")
        raise HTTPException(
            status_code=504,
            detail="Preview timed out (25s). The URL may point to a very large playlist or YouTube is slow."
        )
    except HTTPException:
        raise
    except Exception as e:
        console.err(f"Extraction failed: {e}")
        raise HTTPException(status_code=400, detail=f"Extraction failed: {e}")

    console.ok(f"Media metadata resolved: {info.get('title')}")

    formats = []
    resolutions = set()
    for f in info.get('formats', []):  # type: ignore[union-attr]
        fmt = {
            'format_id': f.get('format_id'),
            'ext': f.get('ext'),
            'resolution': f.get('resolution'),
            'filesize': f.get('filesize'),
            'abr': f.get('abr'),
            'vbr': f.get('vbr'),
            'fps': f.get('fps'),
            'format_note': f.get('format_note'),
            'vcodec': f.get('vcodec'),
            'acodec': f.get('acodec'),
            'height': f.get('height'),
            'width': f.get('width'),
        }
        formats.append(fmt)
        vc = f.get('vcodec')
        h = f.get('height')
        if vc and vc != 'none' and h:
            resolutions.add(h)

    thumbnails = info.get('thumbnails', [])
    thumbnail = thumbnails[-1].get('url') if thumbnails else None

    is_playlist = info.get('_type') == 'playlist' or 'entries' in info

    return {
        'id': info.get('id'),
        'title': info.get('title'),
        'duration': info.get('duration'),
        'uploader': info.get('uploader'),
        'thumbnail': thumbnail,
        'description': (info.get('description') or '')[:500],
        'webpage_url': info.get('webpage_url'),
        'formats': formats,
        'is_playlist': is_playlist,
        'available_resolutions': sorted(resolutions, reverse=True),
    }


# --- 4. SECURE DELIVERABLE DOWNLOADS ---
@app.get("/api/v1/download/file/{task_id}")
async def download_deliverable(task_id: str, request: Request, response: Response):
    """Serve completed download deliverable with path-jailing."""
    task = active_tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.get("status") != "completed":
        raise HTTPException(400, "Task is not completed yet")
    file_path = task.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(404, "Deliverable file not found on disk")

    real = Path(file_path).resolve()
    temp_dir = Path(TempManager.get_temp_dir()).resolve()

    # Deliverables outside temp directory require admin authentication
    if not real.is_relative_to(temp_dir):
        is_auth, _ = verify_request_auth(request, response)
        if not is_auth:
            raise HTTPException(
                401,
                "Access denied: Downloading permanent library files requires authorization",
            )

    if real.is_dir():
        raise HTTPException(
            400,
            "Target is a folder. Enable zip mode to download as an archive.",
        )

    filename = real.name
    safe_name = filename.encode("ascii", "ignore").decode("ascii") or "download"
    encoded_name = urllib.parse.quote(filename, safe="")
    return FileResponse(
        str(real),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_name}'
        },
    )


@app.get("/api/v1/share/download")
async def share_download(request: Request, response: Response):
    """Download a file with strict path jailing (sandboxed to temp unless authenticated)."""
    path_raw = request.query_params.get("path", "")
    if not path_raw:
        raise HTTPException(400, "Missing 'path' query param")
    real = Path(os.path.abspath(path_raw)).resolve()
    temp_dir = Path(TempManager.get_temp_dir()).resolve()

    if not real.is_relative_to(temp_dir):
        is_auth, _ = verify_request_auth(request, response)
        if not is_auth:
            raise HTTPException(403, "Access denied: Path is outside quarantined temporary storage")

    if not real.is_file():
        raise HTTPException(404, "File not found")

    filename = real.name
    safe_name = filename.encode("ascii", "ignore").decode("ascii") or "download"
    encoded_name = urllib.parse.quote(filename, safe="")
    return FileResponse(
        str(real),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_name}'
        },
    )



_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class _StripANSI:
    """Write a stream's output with ANSI escape sequences removed."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, data):
        self._stream.write(_ANSI_RE.sub("", data))
        return len(data)

    def flush(self):
        self._stream.flush()

    def isatty(self):
        return False

    def fileno(self):
        return self._stream.fileno()

    @property
    def encoding(self):
        return getattr(self._stream, "encoding", None)


class _Tee:
    """Duplicate writes to a live stream and an ANSI-stripped file."""

    def __init__(self, real, fh):
        self._real = real
        self._fh = fh

    def write(self, data):
        self._real.write(data)
        self._fh.write(_ANSI_RE.sub("", data))
        return len(data)

    def flush(self):
        self._real.flush()
        self._fh.flush()

    def isatty(self):
        return self._real.isatty()

    def fileno(self):
        return self._real.fileno()

    @property
    def encoding(self):
        return getattr(self._real, "encoding", None)


def _setup_output(log_file, interactive):
    """Route stdout/stderr according to interactivity and ``--log-file``."""
    if not interactive:
        console.theme = PlainTheme
    if not log_file:
        return
    fh = open(log_file, "a", encoding="utf-8", buffering=1)
    if interactive:
        sys.stdout = _Tee(sys.__stdout__, fh)
        sys.stderr = _Tee(sys.__stderr__, fh)
    else:
        sys.stdout = _StripANSI(fh)
        sys.stderr = _StripANSI(fh)


def _is_interactive():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _print_qr(url):
    try:
        import qrcode as _qr

        _qr_code = _qr.QRCode(version=1, box_size=1, border=1)
        _qr_code.add_data(url)
        _qr_code.make(fit=True)
        _qr_code.print_ascii(invert=True)
        print()
        console.warn(Keys.daemon.scan_qr_or_open_url)
    except ImportError:
        console.warn(Keys.daemon.open_url_in_browser(url=url))


def _announce(interactive, quiet, urls, port):
    """Print the startup banner (interactive) or one plain URL per line."""
    if interactive:
        if quiet:
            return
        print()
        for url in urls:
            console.ok(Keys.daemon.daemon_url(url=color(url, 'c')))
        console.warn(Keys.daemon.daemon_port(port=port))
        from ..cli.network import check_firewall_status
        check_firewall_status(port)
        print()
        _print_qr(urls[0])
        console.warn(Keys.daemon.press_ctrl_c_stop)
    else:
        for url in urls:
            print(f"TetoDL daemon listening at {url}")
        sys.stdout.flush()


def run_server(host: str, port: int, verbose: bool = False,
               quiet: bool = False, log_file: str | None = None,
               dev: bool = False):
    """Run the API server.

    Parameters
    ----------
    host : str
        Bind address.
    port : int
        Bind port.
    verbose : bool
        Show uvicorn request logs (default: quiet).
    quiet : bool
        Suppress the startup banner / QR output.
    log_file : str | None
        Tee (interactive) or redirect (non-interactive) output to a file.
    dev : bool
        Run uvicorn in reload mode for development.
    """
    interactive = _is_interactive()
    _setup_output(log_file, interactive)
    console.state.is_quiet = quiet or not interactive

    os.environ["TETODL_PORT"] = str(port)

    if env.get("is_windows"):
        from ..cli.network import ensure_windows_firewall_allow
        ensure_windows_firewall_allow(port)

    urls = daemon_urls(port)

    if dev:
        _announce(interactive, quiet, urls, port)
        uvicorn.run(app, host=host, port=port, reload=True,
                    log_level="warning" if not verbose else "info",
                    access_log=verbose)
        return

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning" if not verbose else "info",
        access_log=verbose,
    )
    server = uvicorn.Server(config)

    def _run():
        asyncio.run(server.serve())

    thread = threading.Thread(target=_run, name="uvicorn-server", daemon=True)
    thread.start()

    with console.spin(Keys.cli.starting_api_server(host=host, port=port)):
        while not server.started:
            time.sleep(0.05)

    _announce(interactive, quiet, urls, port)

    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        console.warn(Keys.daemon.shutting_down)
        server.should_exit = True
        thread.join(timeout=5)