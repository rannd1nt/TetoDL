"""
FastAPI-based file sharing & media player for TetoDL.
Replaces the legacy http.server implementation (server_styles.py).
"""
import html
import os
import re
import urllib.parse
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse

_STATIC_DIR = Path(__file__).parent / "share_static"

with open(_STATIC_DIR / "styles.css") as f:
    _CSS = f.read()
with open(_STATIC_DIR / "player.js") as f:
    _JS = f.read()

SVG = {
    'folder': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    'back': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
    'audio': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
    'video': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="17" x2="22" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/></svg>',
    'image': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
    'archive': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>',
    'code': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    'doc': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    'app': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>',
    'file': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>',
    'download': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    'play': '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
    'pause': '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
}

AUDIO_EXTS = {'.mp3', '.m4a', '.wav', '.flac', '.opus'}
VIDEO_EXTS = {'.mp4', '.mkv', '.webm', '.avi', '.mov'}
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}
ARCHIVE_EXTS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
CODE_EXTS = {'.py', '.js', '.html', '.css', '.json', '.c', '.rs'}
DOC_EXTS = {'.pdf', '.txt', '.md', '.doc', '.docx'}
APP_EXTS = {'.apk', '.exe', '.msi'}


def _resolve_path(root: str, subpath: str) -> str:
    root = os.path.abspath(root)
    safe = urllib.parse.unquote(subpath)
    full = os.path.normpath(os.path.join(root, safe))
    if not full.startswith(root):
        raise HTTPException(403, "Path traversal denied")
    return full


def _classify(ext: str):
    if ext in AUDIO_EXTS:
        return 'audio', SVG['audio']
    if ext in VIDEO_EXTS:
        return 'video', SVG['video']
    if ext in IMAGE_EXTS:
        return 'image', SVG['image']
    if ext in ARCHIVE_EXTS:
        return 'archive', SVG['archive']
    if ext in CODE_EXTS:
        return 'code', SVG['code']
    if ext in DOC_EXTS:
        return 'doc', SVG['doc']
    if ext in APP_EXTS:
        return 'app', SVG['app']
    return 'file', SVG['file']


def _human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size/1024:.1f} KB"
    return f"{size/(1024**2):.1f} MB"


def render_dir_listing(serve_root: str, display_path: str, entries: list) -> str:
    displaypath = html.escape(display_path, quote=False)
    r = []
    r.append('<!DOCTYPE html><html lang="en">')
    r.append(f'<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"><title>TetoDL Share</title><style>{_CSS}</style></head>')
    r.append('<body><div class="branding"><h1>TetoDL Local Share</h1><p>by <span>rannd1nt</span></p></div><div class="glass-container">')
    r.append('<div class="header-section">')
    r.append(f'<div class="path-header">{SVG["folder"]} <span>{displaypath}</span></div>')
    r.append('<input type="text" id="searchInput" class="search-box" onkeyup="filterList()" placeholder="Type to search...">')
    r.append('</div><div class="scroll-area"><ul class="file-list" id="fileList">')

    rel = display_path.replace(serve_root, "").lstrip("/")
    if rel:
        parent = os.path.dirname(rel)
        if not parent:
            parent_route = "/"
        else:
            parent_route = "/" + urllib.parse.quote(parent)
        r.append(f'<li class="file-item parent-dir"><a class="file-link" href="{parent_route}">')
        r.append(f'<div class="icon-box">{SVG["back"]}</div><div class="info"><span class="name">Go Back</span><span class="meta">Parent Directory</span></div></a></li>')

    entries.sort(key=lambda e: (not e['is_dir'], e['name'].lower()))
    for e in entries:
        name = e['name']
        url = urllib.parse.quote(e['name'])
        if e['is_dir']:
            url += "/"
        type_class = "type-folder" if e['is_dir'] else f"type-{_classify(os.path.splitext(name)[1].lower())[0]}"
        icon = SVG['folder'] if e['is_dir'] else _classify(os.path.splitext(name)[1].lower())[1]
        meta = "Directory" if e['is_dir'] else e.get('size_str', '')

        r.append(f'<li class="file-item {type_class}"><a class="file-link" href="{url}">')
        r.append(f'<div class="icon-box">{icon}</div><div class="info"><span class="name">{html.escape(name)}</span><span class="meta">{meta}</span></div></a></li>')

    r.append('</ul></div></div><div class="footer">Hybrid CLI/TUI Media Suite</div>')
    r.append(f'<script>{_JS}</script>')
    r.append('</body></html>')
    return ''.join(r)


def render_player_page(file_path: str, serve_root: str) -> str:
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    is_audio = ext in AUDIO_EXTS

    rel = os.path.relpath(file_path, serve_root)
    src_url = urllib.parse.quote(rel) + "?raw=true"
    dl_url = urllib.parse.quote(rel) + "?dl=1"

    icon = SVG['audio'] if is_audio else SVG['video']

    if is_audio:
        media_html = f'<div id="mediaCover" class="media-cover">{icon}</div><audio id="mediaElement" src="{src_url}" preload="metadata"></audio>'
    else:
        media_html = f'<div class="video-container"><video id="mediaElement" class="video-element" src="{src_url}" playsinline preload="metadata"></video></div>'

    dir_url = "/" + urllib.parse.quote(os.path.dirname(rel)) if os.path.dirname(rel) else "/"

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>Playing - {filename}</title>
    <style>{_CSS}</style>
</head>
<body>
    <div class="branding"><h1>TetoDL Player</h1><p>Secured Stream</p></div>
    <div class="glass-container">
        <div class="player-layout">
            <div class="header-section">
                <div class="path-header">
                    <a href="{dir_url}" style="text-decoration:none;color:inherit;display:flex;align-items:center;gap:8px;width:100%">
                        {SVG["back"]} <span>Back to Directory</span>
                    </a>
                </div>
            </div>
            <div class="player-content">
                {media_html}
                <div class="media-title-large">{html.escape(filename)}</div>
                <div class="custom-controls">
                    <input type="range" id="progressBar" min="0" max="100" value="0" step="0.1">
                    <div class="time-labels"><span id="currTime">0:00</span><span id="totalTime">0:00</span></div>
                    <div class="btn-row">
                        <a href="{dl_url}" download class="btn-dl">{SVG['download']}<span>Save</span></a>
                        <button id="playBtn" class="btn-control btn-play">{SVG['play']}</button>
                        <div style="width:20px"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="footer">Hybrid CLI/TUI Media Suite</div>
    <script>{_JS}</script>
</body>
</html>'''
    return html_content


def list_entries(real_path: str) -> list:
    """Return JSON-serializable list of directory entries."""
    entries = []
    for name in sorted(os.listdir(real_path), key=str.lower):
        full = os.path.join(real_path, name)
        is_dir = os.path.isdir(full)
        entry = {'name': name, 'is_dir': is_dir}
        if not is_dir:
            try:
                size = os.path.getsize(full)
                entry['size'] = size
                entry['size_str'] = _human_size(size)
            except OSError:
                entry['size'] = 0
                entry['size_str'] = ''
        entries.append(entry)
    return entries


async def stream_file(full_path: str, range_header: str | None = None):
    """Async generator for streaming file with byte-range support."""
    file_size = os.path.getsize(full_path)
    start, end = 0, file_size - 1
    content_length = file_size
    status_code = 200
    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Type': _guess_mime(full_path),
    }

    if range_header:
        match = re.match(r'bytes=(\d*)-(\d*)', range_header)
        if match:
            start = int(match.group(1)) if match.group(1) else 0
            end = int(match.group(2)) if match.group(2) else file_size - 1
            if start >= file_size:
                raise HTTPException(416)
            content_length = end - start + 1
            status_code = 206
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'

    headers['Content-Length'] = str(content_length)

    async def _gen():
        with open(full_path, 'rb') as f:
            f.seek(start)
            remaining = content_length
            chunk_size = 65536
            while remaining > 0:
                to_read = min(chunk_size, remaining)
                data = f.read(to_read)
                if not data:
                    break
                yield data
                remaining -= len(data)

    return StreamingResponse(_gen(), status_code=status_code, headers=headers)


def _guess_mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mimes = {
        '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.wav': 'audio/wav',
        '.flac': 'audio/flac', '.opus': 'audio/opus',
        '.mp4': 'video/mp4', '.mkv': 'video/webm', '.webm': 'video/webm',
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.webp': 'image/webp', '.gif': 'image/gif', '.svg': 'image/svg+xml',
        '.pdf': 'application/pdf', '.zip': 'application/zip',
        '.json': 'application/json', '.html': 'text/html', '.css': 'text/css',
        '.js': 'application/javascript',
    }
    return mimes.get(ext, 'application/octet-stream')


def create_share_router(serve_root: str) -> APIRouter:
    """Create an APIRouter that serves the given directory (file browser + player)."""
    serve_root = os.path.abspath(serve_root)
    if not os.path.isdir(serve_root):
        raise ValueError(f"Not a directory: {serve_root}")

    router = APIRouter()

    @router.get("/")
    async def share_index():
        entries = list_entries(serve_root)
        html_content = render_dir_listing(serve_root, "/", entries)
        return HTMLResponse(html_content)

    @router.get("/{path:path}")
    async def share_serve(path: str, request: Request):
        full = _resolve_path(serve_root, path)

        if not os.path.exists(full):
            raise HTTPException(404)

        if os.path.isdir(full):
            entries = list_entries(full)
            rel_display = "/" + path if path else "/"
            html_content = render_dir_listing(serve_root, rel_display, entries)
            return HTMLResponse(html_content)

        ext = os.path.splitext(full)[1].lower()
        query_raw = request.query_params.get('raw')
        query_dl = request.query_params.get('dl')
        range_header = request.headers.get('range')

        if ext in MEDIA_EXTS and not query_raw and not query_dl and not range_header:
            html_content = render_player_page(full, serve_root)
            return HTMLResponse(html_content)

        return await stream_file(full, range_header)

    return router
