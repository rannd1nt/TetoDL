import os
import sys
import io
import asyncio
import time
import uuid
import threading
import html as htmlmod
import urllib.parse
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

from .models import DownloadRequest, PreviewRequest
from .discovery import MDNSBroadcaster
from ..ui.entry.dispatch import execute_cli_context
from ..constants import RuntimeConfig
from ..core import config as config_mgr
from ..utils.display import get_free_space
from ..utils.files import TempManager
from ..utils.share import list_entries, stream_file, create_share_router, SVG as _SHARE_SVG
from ..utils.time_parser import get_cut_seconds
from ..utils.processing import parse_playlist_items
from ..utils.network import find_free_port, get_best_ip
from ..utils.styles import console as rich_console

share_launchers = {}

active_tasks = {}
broadcaster = None

# --- BACKGROUND WORKERS ---
async def cleanup_worker():
    while True:
        # Ambil interval dari config (default 3600 detik / 1 jam)
        interval = getattr(RuntimeConfig, 'DAEMON_CLEANUP_INTERVAL', 3600)
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
    
    global broadcaster
    port = int(os.getenv("TETODL_PORT", 7370))
    broadcaster = MDNSBroadcaster(port=port)
    broadcaster.start()
    
    yield
    
    if broadcaster:
        broadcaster.stop()
    cleanup_task.cancel()

# --- APP INITIALIZATION ---
app = FastAPI(
    title="TetoDL Service API", 
    version="1.3.0", 
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

app.mount("/web", StaticFiles(directory=str(STATIC_DIR), html=True), name="static_web")

@app.get("/")
@app.get("/web")
async def root():
    return RedirectResponse(url="/web/")

# Mount Folder Media untuk Streaming Lokal
app.mount("/media/music", StaticFiles(directory=RuntimeConfig.MUSIC_ROOT), name="music_media")
app.mount("/media/videos", StaticFiles(directory=RuntimeConfig.VIDEO_ROOT), name="video_media")
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

def background_task_runner(task_id: str, context: dict):
    log_buf = io.StringIO()
    task_data = {
        "status": "processing",
        "details": context.get('url', 'Task Queued'),
        "title": context.get('task_title', ''),
        "file_path": None,
        "logs": "",
    }
    active_tasks[task_id] = task_data

    old_stdout = sys.stdout
    old_console_file = getattr(rich_console, 'file', old_stdout)
    tee = _LogTee(old_stdout, log_buf, task_data)

    sys.stdout = tee
    try:
        rich_console.file = tee
    except Exception:
        pass

    try:
        result = execute_cli_context(context) or {}
        task = active_tasks[task_id]
        task["status"] = "completed"
        if isinstance(result, dict):
            fp = result.get('file_path')
            if fp:
                fp_abs = os.path.abspath(fp)
                task["file_path"] = fp_abs
                task["is_dir"] = os.path.isdir(fp_abs)
                if task["is_dir"]:
                    task["dir_path"] = fp_abs
                else:
                    task["dir_path"] = os.path.dirname(fp_abs)
            fc = result.get('file_count')
            if fc:
                task["file_count"] = fc
    except Exception as e:
        active_tasks[task_id]["status"] = f"error: {str(e)}"
        active_tasks[task_id]["file_path"] = None
    finally:
        sys.stdout = old_stdout
        try:
            rich_console.file = old_console_file
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
            "music_free_space": get_free_space(RuntimeConfig.MUSIC_ROOT),
            "video_free_space": get_free_space(RuntimeConfig.VIDEO_ROOT)
        }
    }

@app.get("/api/v1/config")
async def get_current_config():
    """Membaca konfigurasi yang tersimpan (termasuk setting Daemon)"""
    config_mgr.load_config()
    return {
        "audio_quality": RuntimeConfig.AUDIO_QUALITY,
        "video_container": RuntimeConfig.VIDEO_CONTAINER,
        "max_resolution": RuntimeConfig.MAX_VIDEO_RESOLUTION,
        "daemon_default_temp": getattr(RuntimeConfig, 'DAEMON_DEFAULT_TEMP', True),
        "daemon_cleanup_interval": getattr(RuntimeConfig, 'DAEMON_CLEANUP_INTERVAL', 3600),
        "smart_cover_mode": RuntimeConfig.SMART_COVER_MODE,
        "lyrics_mode": RuntimeConfig.LYRICS_MODE,
    }

@app.patch("/api/v1/config")
async def update_config(request: Request):
    """Menerima setting baru dari HP dan menyimpannya ke config.json secara permanen"""
    data = await request.json()
    config_mgr.load_config()
    
    # Petakan request JSON ke objek konfigurasi
    if "daemon_default_temp" in data: RuntimeConfig.DAEMON_DEFAULT_TEMP = data["daemon_default_temp"]
    if "daemon_cleanup_interval" in data: RuntimeConfig.DAEMON_CLEANUP_INTERVAL = data["daemon_cleanup_interval"]
    if "audio_quality" in data: RuntimeConfig.AUDIO_QUALITY = data["audio_quality"]
    if "max_resolution" in data: RuntimeConfig.MAX_VIDEO_RESOLUTION = data["max_resolution"]
    if "smart_cover_mode" in data: RuntimeConfig.SMART_COVER_MODE = data["smart_cover_mode"]
    if "lyrics_mode" in data: RuntimeConfig.LYRICS_MODE = data["lyrics_mode"]
    
    config_mgr.save_config() # Simpan ke disk
    return {"status": "success", "message": "Configuration updated persistently."}


# --- 2. ORCHESTRATION (THE BIG BRAIN) ---
@app.post("/api/v1/download")
async def process_download(req: DownloadRequest, bg_tasks: BackgroundTasks):
    if not req.url and not req.search_query:
        raise HTTPException(status_code=400, detail="Must provide 'url' or 'search_query'")

    task_id = str(uuid.uuid4())[:8]
    overrides = {'simple_mode': True}

    if req.url: overrides['url'] = req.url
    if req.audio_only: overrides['type'] = 'audio'
    if req.video_only: overrides['type'] = 'video'
    if req.thumbnail_only: overrides['thumbnail_only'] = True

    if req.format: overrides['format'] = req.format
    if req.resolution: overrides['resolution'] = req.resolution
    if req.codec: overrides['codec'] = req.codec

    if req.async_mode: overrides['async'] = True
    if req.cut_time:
        overrides['cut_raw'] = req.cut_time
        try:
            start, end = get_cut_seconds(req.cut_time)
            overrides['cut_range'] = (start, end)
        except ValueError:
            pass
    if req.items:
        overrides['items_raw'] = req.items
        try:
            overrides['playlist_items'] = parse_playlist_items(req.items)
        except ValueError:
            pass
    if req.group: overrides['group'] = req.group
    if req.m3u: overrides['m3u'] = True
    if req.smart_cover: overrides['smart_cover'] = True
    if req.no_cover: overrides['no_cover'] = True
    if req.force_crop: overrides['force_crop'] = True

    # Explicit set semua boolean (biar gak ada state leakage antar request)
    overrides['lyrics'] = req.lyrics
    overrides['romaji'] = req.romaji

    if req.title:
        overrides['task_title'] = req.title

    # --- TEMP VS PERMANENT STORAGE LOGIC ---
    if req.share_temp:
        is_temp = True
    elif req.share:
        is_temp = False
    else:
        is_temp = getattr(RuntimeConfig, 'DAEMON_DEFAULT_TEMP', True)

    if is_temp:
        task_dir = Path(str(TempManager.get_temp_dir())) / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        overrides['output_path'] = str(task_dir)

    context = {
        'mode': 'cli_download' if req.url else 'cli_search',
        'is_temp_session': False,
        'overrides': overrides,
        'task_title': req.title or '',
    }
        
    # CATATAN PENTING: Di mode Daemon, `is_temp_session` sengaja False.
    # Biarkan auto-cleanup worker yang hapus file lama, jangan `TempManager.cleanup()`.
    # (Itu langsung hapus file sebelum sempat di-streaming).

    bg_tasks.add_task(background_task_runner, task_id, context)

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

    try:
        import yt_dlp as yt
        loop = _asyncio.get_event_loop()
        with yt.YoutubeDL({
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }) as ydl:
            try:
                info = await _asyncio.wait_for(
                    loop.run_in_executor(None, lambda: ydl.extract_info(req.url, download=False)),
                    timeout=45.0,
                )
            except _asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail="Preview timed out. The URL may point to a very large playlist. Try a single video URL."
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction failed: {e}")

    formats = []
    resolutions = set()
    for f in info.get('formats', []):
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


# --- 4. SHARE BROWSE (JSON directory listing) ---
@app.get("/api/v1/share/browse")
async def share_browse(path: str = ""):
    display_path = path or "/"
    try:
        from ..constants import DEFAULT_MUSIC_ROOT, DEFAULT_VIDEO_ROOT
        root_map = {
            "MUSIC": DEFAULT_MUSIC_ROOT,
            "VIDEO": DEFAULT_VIDEO_ROOT,
            "TEMP": str(TempManager.get_temp_dir()),
        }
        quick = {k: os.path.abspath(v) for k, v in root_map.items()}

        if path.startswith("quick:"):
            key = path.replace("quick:", "")
            real = quick.get(key)
            if not real:
                raise HTTPException(400, f"Unknown quick path: {key}")
            entries = list_entries(real)
            return {"path": real, "display": key, "entries": entries, "quick": list(quick.keys())}

        real = os.path.abspath(path) if path else "/"
        if not os.path.isdir(real):
            raise HTTPException(400, "Not a directory")
        entries = list_entries(real)
        return {"path": real, "display": display_path, "entries": entries, "quick": list(quick.keys())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Browse error: {e}")


# --- 5. SHARE STREAM (raw file serving, no HTML) ---
@app.get("/api/v1/share/stream")
async def share_stream(request: Request):
    path = request.query_params.get("path", "")
    if not path:
        raise HTTPException(400, "Missing 'path' query param")
    real = os.path.abspath(path)
    if not os.path.isfile(real):
        raise HTTPException(404, "File not found")
    range_header = request.headers.get("range")
    dl = request.query_params.get("dl")
    response = await stream_file(real, range_header)
    if dl is not None:
        filename = os.path.basename(real)
        safe = filename.replace('\\', '\\\\').replace('"', '\\"')
        response.headers["Content-Disposition"] = f'attachment; filename="{safe}"'
    return response


# --- 6. SHARE BROWSER HTML (dir listing, same glassmorphism as TetoDL Share) ---

def _icon(ext: str):
    if ext in ('.mp3','.m4a','.wav','.flac','.opus'): return _SHARE_SVG['audio']
    if ext in ('.mp4','.mkv','.webm','.avi','.mov'): return _SHARE_SVG['video']
    if ext in ('.jpg','.jpeg','.png','.webp','.gif','.svg'): return _SHARE_SVG['image']
    if ext in ('.zip','.rar','.7z','.tar','.gz'): return _SHARE_SVG['archive']
    if ext in ('.py','.js','.html','.css','.json','.c'): return _SHARE_SVG['code']
    if ext in ('.pdf','.txt','.md'): return _SHARE_SVG['doc']
    return _SHARE_SVG['file']

def _size_str(size: int) -> str:
    if size < 1024: return f"{size} B"
    if size < 1024**2: return f"{size/1024:.1f} KB"
    return f"{size/(1024**2):.1f} MB"

@app.get("/api/v1/share/browse_html")
async def share_browse_html(request: Request):
    path = request.query_params.get("path", "")
    root_raw = request.query_params.get("root") or path
    real = os.path.abspath(path) if path else ""
    root_abs = os.path.abspath(root_raw)
    if not real or not os.path.isdir(real):
        raise HTTPException(404, "Not a directory")

    css = _player_css()
    dirname = htmlmod.escape(os.path.basename(real) or real)

    entries = []
    for name in sorted(os.listdir(real), key=str.lower):
        full = os.path.join(real, name)
        is_dir = os.path.isdir(full)
        ext = os.path.splitext(name)[1].lower()
        if is_dir:
            meta = "Directory"
            icon = _SHARE_SVG['folder']
            link = f"/api/v1/share/browse_html?path={urllib.parse.quote(os.path.abspath(full))}&root={urllib.parse.quote(root_abs)}"
        else:
            sz = 0
            try: sz = os.path.getsize(full)
            except: pass
            meta = _size_str(sz)
            icon = _icon(ext)
            link = f"/api/v1/share/player?path={urllib.parse.quote(os.path.abspath(full))}"
        entries.append((name, icon, link, meta))

    rows = ""
    is_root = os.path.normpath(real) == os.path.normpath(root_abs)
    if not is_root:
        parent = os.path.normpath(os.path.dirname(real))
        if not parent.startswith(root_abs + os.sep) and parent != root_abs:
            parent = root_abs
        p_enc = urllib.parse.quote(parent)
        rows += f'<li class="file-item parent-dir"><a class="file-link" href="/api/v1/share/browse_html?path={p_enc}&root={urllib.parse.quote(root_abs)}"><div class="icon-box">{_SHARE_SVG["back"]}</div><div class="info"><span class="name">Go Back</span><span class="meta">Parent Directory</span></div></a></li>'
    else:
        rows += f'<li class="file-item parent-dir"><a class="file-link" href="/web/"><div class="icon-box">{_SHARE_SVG["back"]}</div><div class="info"><span class="name">Back to Orchestrator</span><span class="meta">Return to task panel</span></div></a></li>'

    for name, icon, link, meta in entries:
        rows += f'<li class="file-item"><a class="file-link" href="{link}"><div class="icon-box">{icon}</div><div class="info"><span class="name">{htmlmod.escape(name)}</span><span class="meta">{meta}</span></div></a></li>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>{dirname} - TetoDL</title>
<style>{css}</style>
</head>
<body>
<div class="branding"><h1>TetoDL Download</h1><p>Task Results</p></div>
<div class="glass-container">
<div class="header-section">
<div class="path-header">{_SHARE_SVG["folder"]} <span>{dirname}</span></div>
<input type="text" class="search-box" onkeyup="filterList()" placeholder="Type to search...">
</div>
<div class="scroll-area"><ul class="file-list" id="fileList">{rows}</ul></div>
</div>
<div class="footer">TetoDL Orchestrator — Task Results</div>
<script>{_player_js()}</script>
</body>
</html>"""
    return HTMLResponse(html)


# --- 7. SHARE PLAYER (full HTML player page with metadata) ---

_SVG_BACK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'
_SVG_PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>'
_SVG_PAUSE = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
_SVG_DOWNLOAD = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'
_SVG_MUSIC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>'

def _player_css() -> str:
    p = Path(__file__).resolve().parent.parent / "utils" / "share_static" / "styles.css"
    return p.read_text() if p.exists() else ""

def _player_js() -> str:
    p = Path(__file__).resolve().parent.parent / "utils" / "share_static" / "player.js"
    return p.read_text() if p.exists() else ""

def _get_meta(path: str) -> dict:
    import base64
    meta = {"title": "", "artist": "", "album": "", "cover_b64": "", "cover_mime": "image/jpeg"}
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".mp3":
            from mutagen.mp3 import MP3
            from mutagen.id3 import APIC
            a = MP3(path)
            meta["title"] = str(a.tags.get("TIT2", "")) if a.tags else ""
            meta["artist"] = str(a.tags.get("TPE1", "")) if a.tags else ""
            meta["album"] = str(a.tags.get("TALB", "")) if a.tags else ""
            if a.tags:
                for t in a.tags.values():
                    if isinstance(t, APIC):
                        meta["cover_b64"] = base64.b64encode(t.data).decode()
                        meta["cover_mime"] = t.mime
                        break
        elif ext == ".m4a":
            from mutagen.mp4 import MP4
            a = MP4(path)
            meta["title"] = a.get("\xa9nam", [""])[0]
            meta["artist"] = a.get("\xa9ART", [""])[0]
            meta["album"] = a.get("\xa9alb", [""])[0]
            if "covr" in a:
                d = a["covr"][0]
                if isinstance(d, bytes):
                    meta["cover_b64"] = base64.b64encode(d).decode()
                    meta["cover_mime"] = "image/png" if d[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
        elif ext == ".flac":
            from mutagen.flac import FLAC
            a = FLAC(path)
            meta["title"] = a.get("title", [""])[0]
            meta["artist"] = a.get("artist", [""])[0]
            meta["album"] = a.get("album", [""])[0]
            if a.pictures:
                meta["cover_b64"] = base64.b64encode(a.pictures[0].data).decode()
                meta["cover_mime"] = a.pictures[0].mime
        elif ext == ".opus":
            from mutagen.oggopus import OggOpus
            a = OggOpus(path)
            meta["title"] = a.get("title", [""])[0]
            meta["artist"] = a.get("artist", [""])[0]
            meta["album"] = a.get("album", [""])[0]
    except Exception:
        pass 
    return meta

@app.get("/api/v1/share/player")
async def share_player(request: Request):
    path = request.query_params.get("path", "")
    if not path:
        raise HTTPException(400, "Missing 'path' query param")
    real = os.path.abspath(path)
    if not os.path.isfile(real):
        raise HTTPException(404, "File not found")

    filename = os.path.basename(real)
    ext = os.path.splitext(filename)[1].lower()
    AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".opus"}
    VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}
    is_video = ext in VIDEO_EXTS
    is_audio = ext in AUDIO_EXTS
    stream_url = f"/api/v1/share/stream?path={urllib.parse.quote(real)}"
    back_url = request.headers.get("referer", "/web/")

    meta = _get_meta(real) if is_audio else {}
    title = htmlmod.escape(meta.get("title") or filename)
    artist = htmlmod.escape(meta.get("artist") or "")
    album = htmlmod.escape(meta.get("album") or "")
    cover_b64 = meta.get("cover_b64", "")

    if is_video:
        media_html = f'<div class="video-container"><video id="mediaElement" class="video-element" src="{stream_url}" playsinline preload="metadata"></video></div>'
    elif is_audio and cover_b64:
        mime = meta.get("cover_mime", "image/jpeg")
        media_html = f'<div id="mediaCover" class="media-cover" style="background-image:none"><img src="data:{mime};base64,{cover_b64}" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:30px"></div><audio id="mediaElement" src="{stream_url}" preload="metadata"></audio>'
    elif is_audio:
        media_html = f'<div id="mediaCover" class="media-cover">{_SVG_MUSIC}</div><audio id="mediaElement" src="{stream_url}" preload="metadata"></audio>'
    else:
        media_html = f'<div class="video-container"><video id="mediaElement" class="video-element" src="{stream_url}" playsinline preload="metadata"></video></div>'

    meta_lines = ""
    if title and title != htmlmod.escape(filename):
        meta_lines += f'<div class="media-title-large">{title}</div>'
    if artist:
        meta_lines += f'<div class="media-artist">{artist}</div>'
    if album:
        meta_lines += f'<div class="media-album">{album}</div>'

    css = _player_css()
    js = _player_js()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>{htmlmod.escape(filename)} - TetoDL</title>
<style>{css}</style>
</head>
<body>
<div class="branding"><h1>TetoDL Player</h1><p>Secured Stream</p></div>
<div class="glass-container">
<div class="player-layout">
<div class="header-section">
<div class="path-header">
<a href="{htmlmod.escape(back_url)}" style="text-decoration:none;color:inherit;display:flex;align-items:center;gap:8px;width:100%">
{_SVG_BACK} <span>Back to Orchestrator</span>
</a>
</div>
</div>
<div class="player-content">
{media_html}
{meta_lines if meta_lines else f'<div class="media-title-large">{htmlmod.escape(filename)}</div>'}
<div class="custom-controls">
<input type="range" id="progressBar" min="0" max="100" value="0" step="0.1">
<div class="time-labels"><span id="currTime">0:00</span><span id="totalTime">0:00</span></div>
<div class="btn-row">
<a href="{stream_url}&dl=1" download class="btn-dl">{_SVG_DOWNLOAD}<span>Save</span></a>
<button id="playBtn" class="btn-control btn-play">{_SVG_PLAY}</button>
<div style="width:20px"></div>
</div>
</div>
</div>
</div>
</div>
<div class="footer">TetoDL Orchestrator - Secure Stream</div>
<script>{js}</script>
</body>
</html>"""
    return HTMLResponse(html)


# --- 7. SHARE LAUNCH (start background uvicorn on new port) ---
@app.post("/api/v1/share/launch")
async def share_launch(request: Request):
    data = await request.json()
    path = data.get("path", "")
    norm = os.path.abspath(path) if path else ""

    if not norm or not os.path.exists(norm):
        raise HTTPException(400, "Path not found")

    if norm in share_launchers:
        return {"url": share_launchers[norm]["url"]}

    if os.path.isfile(norm):
        serve_root = os.path.dirname(norm)
        serve_file = os.path.basename(norm)
    elif os.path.isdir(norm):
        serve_root = norm
        serve_file = None
    else:
        raise HTTPException(400, "Not a file or directory")

    ip = get_best_ip()
    share_app = FastAPI()
    share_app.include_router(create_share_router(serve_root))

    port = find_free_port(8989)
    if port is None:
        raise HTTPException(500, "No free ports available")

    def _run():
        try:
            uvicorn.run(share_app, host="0.0.0.0", port=port, log_level="error")
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    url = f"http://{ip}:{port}/{urllib.parse.quote(serve_file)}" if serve_file else f"http://{ip}:{port}/"

    # Tunggu server siap (max 5 detik)
    import urllib.request as _ureq, urllib.error as _uerr
    import time as _time
    deadline = _time.time() + 5
    ready = False
    while _time.time() < deadline:
        try:
            _ureq.urlopen(f"http://127.0.0.1:{port}/", timeout=1)
            ready = True
            break
        except (_uerr.URLError, ConnectionRefusedError, OSError):
            _time.sleep(0.15)
    if not ready:
        raise HTTPException(500, "Server failed to start in time")

    share_launchers[norm] = {"url": url, "thread": t, "port": port}
    return {"url": url, "port": port, "ip": ip}


def run_server(host: str, port: int):
    """Fungsi entry point untuk uvicorn dari CLI"""
    os.environ["TETODL_PORT"] = str(port)
    uvicorn.run(app, host=host, port=port)