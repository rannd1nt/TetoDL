import os
import html
import io
import urllib.parse
from http.server import SimpleHTTPRequestHandler

# --- ICONS (SVG DATA) ---
SVG_ICONS = {
    'folder': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>''',
    'back': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>''',
    'audio': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>''',
    'video': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg>''',
    'image': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>''',
    'archive': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>''',
    'code': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>''',
    'doc': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>''',
    'app': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>''',
    'file': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>''',
    'download': '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>''',
    'play': '''<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>''',
    'pause': '''<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>'''
}

# --- CSS  ---
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');

    :root {
        --glass-surface: rgba(20, 20, 35, 0.65);
        --glass-border: rgba(255, 255, 255, 0.1);
        --item-bg: rgba(0, 0, 0, 0.3);
        --item-border: rgba(255, 255, 255, 0.06);
        --text-main: #ffffff;
        --text-muted: #94a3b8;
        --accent: #00d2ff;
        
        --c-folder: #fbbf24;
        --c-audio: #00d2ff;
        --c-video: #a855f7;
        --c-image: #f43f5e;
        --c-archive: #f97316;
        --c-code: #10b981;
        --c-doc: #94a3b8;
    }
    
    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    
    body {
        font-family: 'Outfit', -apple-system, sans-serif;
        background: #0f172a;
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        background-size: 200% 200%;
        animation: liquidMove 15s ease infinite;
        color: var(--text-main);
        height: 100dvh; 
        overflow: hidden;
        display: flex; flex-direction: column;
        padding: 20px; padding-top: 30px;
    }

    @keyframes liquidMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .branding {
        text-align: center; margin-bottom: 20px; flex-shrink: 0; z-index: 10;
    }
    .branding h1 {
        font-size: 1.8rem; font-weight: 800; letter-spacing: -1px;
        background: linear-gradient(135deg, #fff 0%, #00d2ff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 10px 30px rgba(0, 210, 255, 0.3); margin: 0;
    }
    .branding p {
        font-size: 0.7rem; color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase; letter-spacing: 2px; font-weight: 500; margin-top: 5px;
    }
    .branding p span { color: var(--accent); }

    .glass-container {
        width: 100%; max_width: 600px; margin: 0 auto;
        flex: 1; min-height: 0; 
        display: flex; flex-direction: column;
        background: var(--glass-surface);
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 24px; padding: 15px; 
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        margin-bottom: 10px;
        overflow: hidden;
    }

    .header-section { flex-shrink: 0; z-index: 2; margin-bottom: 10px; }
    .path-header {
        font-size: 0.85rem; color: var(--accent);
        background: rgba(0, 210, 255, 0.1); border: 1px solid rgba(0, 210, 255, 0.2);
        padding: 10px 14px; border-radius: 12px; margin-bottom: 10px;
        word-break: break-all; font-family: monospace;
        display: flex; align-items: center; gap: 8px;
    }
    .path-header svg { width: 18px; height: 18px; min-width: 18px; }

    .search-box {
        width: 100%; padding: 12px 16px; border-radius: 12px;
        border: 1px solid var(--glass-border); background: rgba(0, 0, 0, 0.3);
        color: white; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
    }
    .search-box:focus { border-color: var(--accent); }

    .scroll-area {
        flex-grow: 1; overflow-y: auto; -webkit-overflow-scrolling: touch;
        position: relative; z-index: 1; padding-bottom: 10px;
        scrollbar-width: none; -ms-overflow-style: none;
    }
    .scroll-area::-webkit-scrollbar { display: none; }

    .file-list { list-style: none; display: flex; flex-direction: column; gap: 8px; }
    .file-item {
        background: var(--item-bg); border: 1px solid var(--item-border);
        border-radius: 14px; position: relative; overflow: hidden;
        transition: background 0.1s; content-visibility: auto; 
    }
    @media (hover: hover) {
        .file-item:hover { background: rgba(255, 255, 255, 0.05); border-color: rgba(255,255,255,0.1); }
    }
    .file-item:active { transform: scale(0.99); background: rgba(255, 255, 255, 0.1); }
    .file-link {
        display: flex; align-items: center; padding: 12px; text-decoration: none;
        color: inherit; position: relative; z-index: 2; width: 100%;
    }
    .icon-box {
        width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
        background: rgba(255,255,255,0.03); border-radius: 10px; margin-right: 12px;
        flex-shrink: 0; color: var(--text-muted);
    }
    .icon-box svg { width: 20px; height: 20px; stroke-width: 2; }
    .type-folder .icon-box { color: var(--c-folder); background: rgba(251, 191, 36, 0.1); }
    .type-audio .icon-box { color: var(--c-audio); background: rgba(0, 210, 255, 0.1); }
    .type-video .icon-box { color: var(--c-video); background: rgba(168, 85, 247, 0.1); }
    .type-image .icon-box { color: var(--c-image); background: rgba(244, 63, 94, 0.1); }
    .type-archive .icon-box { color: var(--c-archive); background: rgba(249, 115, 22, 0.1); }
    .type-code .icon-box { color: var(--c-code); background: rgba(16, 185, 129, 0.1); }
    .info { flex: 1; min-width: 0; }
    .name { 
        display: block; font-weight: 600; font-size: 0.95rem; color: #f1f5f9;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px;
    }
    .meta { display: block; font-size: 0.7rem; color: var(--text-muted); font-weight: 500; }
    .parent-dir {
        position: sticky; top: 0; z-index: 10;
        background: #141724; border: 1px solid rgba(0, 210, 255, 0.3);
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .parent-dir .file-link { padding: 10px 12px; }
    .parent-dir .icon-box { color: var(--accent); background: rgba(0, 210, 255, 0.15); width: 32px; height: 32px; }
    .parent-dir .name { color: var(--accent); }
    .footer { text-align: center; margin-top: auto; padding: 5px; font-size: 0.7rem; opacity: 0.4; flex-shrink: 0; }

    /* PLAYER STYLES */
    .player-layout { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
    .player-content {
        flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch;
        display: flex; flex-direction: column; align-items: center;
        padding-top: 10px; scrollbar-width: none;
    }
    .player-content::-webkit-scrollbar { display: none; }
    video, audio { display: none; }
    .media-cover {
        width: 140px; height: 140px; display: flex; align-items: center; justify-content: center;
        background: rgba(0, 0, 0, 0.2); border-radius: 30px; margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 0 40px rgba(0, 210, 255, 0.15);
        flex-shrink: 0; position: relative;
    }
    .media-cover svg { width: 60px; height: 60px; color: var(--accent); }
    .media-cover.playing { animation: pulse 2s infinite; border-color: var(--accent); }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 210, 255, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(0, 210, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 210, 255, 0); }
    }
    .media-title-large {
        font-size: 1.2rem; font-weight: 700; margin-bottom: 5px; padding: 0 10px;
        color: white; text-align: center;
    }
    .custom-controls {
        width: 100%; margin-top: 20px; background: rgba(0,0,0,0.2);
        padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 20px;
    }
    
    /* --- FIXED SLIDER CSS --- */
    input[type=range] {
        -webkit-appearance: none; 
        width: 100%; 
        background: rgba(255, 255, 255, 0.1); /* Background jalur yang belum dilewati */
        border-radius: 3px;
        height: 6px;
        margin-bottom: 10px; 
        cursor: pointer;
        
        /* Gradient untuk jalur yang SUDAH dilewati (Kiri) */
        /* JS akan mengubah background-size untuk 'mengisi' jalur ini */
        background-image: linear-gradient(var(--accent), var(--accent));
        background-size: 0% 100%; 
        background-repeat: no-repeat;
    }
    
    input[type=range]:focus { outline: none; }

    /* WebKit Track (Transparan biar background Input yg kelihatan) */
    input[type=range]::-webkit-slider-runnable-track {
        width: 100%; height: 6px; cursor: pointer;
        background: transparent; border: none;
    }
    /* WebKit Thumb */
    input[type=range]::-webkit-slider-thumb {
        -webkit-appearance: none; 
        height: 16px; width: 16px; border-radius: 50%;
        background: white; 
        margin-top: -5px; /* Center thumb */
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    
    /* Firefox Support (Firefox punya pseudo element sendiri buat progress) */
    input[type=range]::-moz-range-track {
        width: 100%; height: 6px; cursor: pointer;
        background: rgba(255,255,255,0.1); border-radius: 3px;
    }
    input[type=range]::-moz-range-progress {
        background-color: var(--accent); height: 6px; border-radius: 3px;
    }
    input[type=range]::-moz-range-thumb {
        height: 16px; width: 16px; border: none; border-radius: 50%;
        background: #ffffff; cursor: pointer;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }

    .time-labels {
        display: flex; justify-content: space-between;
        font-size: 0.75rem; color: var(--text-muted); font-family: monospace;
        margin-bottom: 15px;
    }
    .btn-row { display: flex; align-items: center; justify-content: center; gap: 20px; }
    .btn-control {
        background: none; border: none; color: white; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: transform 0.1s;
    }
    .btn-control:active { transform: scale(0.9); }
    .btn-play {
        width: 60px; height: 60px; background: var(--accent);
        border-radius: 50%; color: #0f172a; box-shadow: 0 5px 20px rgba(0, 210, 255, 0.4);
    }
    .btn-play svg { width: 24px; height: 24px; fill: currentColor; }
    .btn-dl {
        color: var(--text-muted); text-decoration: none;
        display: flex; flex-direction: column; align-items: center;
        font-size: 0.7rem; gap: 4px;
    }
    .btn-dl svg { width: 20px; height: 20px; }
    .video-container {
        width: 100%; border-radius: 16px; overflow: hidden;
        margin-bottom: 20px; background: black; position: relative; flex-shrink: 0;
    }
    .video-element { width: 100%; display: block; max-height: 50vh; object-fit: contain; }
</style>
"""

JS_PLAYER = """
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const media = document.getElementById('mediaElement');
        const playBtn = document.getElementById('playBtn');
        const progressBar = document.getElementById('progressBar');
        const currTime = document.getElementById('currTime');
        const totalTime = document.getElementById('totalTime');
        const cover = document.getElementById('mediaCover');
        const playIcon = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none" width="24" height="24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
        const pauseIcon = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none" width="24" height="24"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';

        if(!media) return;

        function togglePlay() {
            if (media.paused) {
                media.play();
                playBtn.innerHTML = pauseIcon;
                if(cover) cover.classList.add('playing');
            } else {
                media.pause();
                playBtn.innerHTML = playIcon;
                if(cover) cover.classList.remove('playing');
            }
        }
        playBtn.addEventListener('click', togglePlay);

        function updateSliderFill(value) {
            progressBar.style.backgroundSize = value + '% 100%';
        }

        media.addEventListener('timeupdate', function() {
            if(media.duration) {
                const percent = (media.currentTime / media.duration) * 100;
                progressBar.value = percent;
                
                updateSliderFill(percent);
                
                currTime.innerText = formatTime(media.currentTime);
                totalTime.innerText = formatTime(media.duration);
            }
        });

        progressBar.addEventListener('input', function() {
            updateSliderFill(this.value);
            
            if(media.duration) {
                const seekTime = (this.value / 100) * media.duration;
                media.currentTime = seekTime;
            }
        });

        function formatTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            
            const sStr = (s < 10 ? '0' : '') + s;
            
            if (h > 0) {
                const mStr = (m < 10 ? '0' : '') + m;
                return h + ':' + mStr + ':' + sStr;
            } else {
                return m + ':' + sStr;
            }
        }

        media.play().then(() => {
            playBtn.innerHTML = pauseIcon;
            if(cover) cover.classList.add('playing');
        }).catch(() => {
            playBtn.innerHTML = playIcon;
        });
        
        if(media.tagName === 'VIDEO') {
            media.addEventListener('click', togglePlay);
        }
    });

    function filterList() {
        const input = document.getElementById('searchInput');
        if (!input) return;
        const filter = input.value.toLowerCase();
        const li = document.getElementsByClassName('file-item');

        for (let i = 0; i < li.length; i++) {
            if (li[i].classList.contains('parent-dir')) continue;
            const nameSpan = li[i].getElementsByClassName("name")[0];
            if (nameSpan) {
                const txtValue = nameSpan.textContent || nameSpan.innerText;
                if (txtValue.toLowerCase().indexOf(filter) > -1) {
                    li[i].style.display = "";
                } else {
                    li[i].style.display = "none";
                }
            }
        }
    }
</script>
"""

class TetoHTTPHandler(SimpleHTTPRequestHandler):
    extensions_map = SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map.update({
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.mp4': 'video/mp4',
        '.mkv': 'video/webm', 
        '.webm': 'video/webm',
    })

    def log_message(self, format, *args):
        pass

    def copy_byte_range(self, infile, outfile, start, stop, bufsize=16*1024):
        if start is None: start = 0
        infile.seek(start)
        to_send = stop - start + 1
        while to_send > 0:
            read_size = min(bufsize, to_send)
            data = infile.read(read_size)
            if not data: break
            outfile.write(data)
            to_send -= len(data)

    def do_GET(self):
        self.path = urllib.parse.unquote(self.path)
        
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        
        ext = os.path.splitext(path)[1].lower()
        is_audio = ext in ['.mp3', '.m4a', '.wav', '.flac', '.opus']
        is_video = ext in ['.mp4', '.mkv', '.webm']
        
        range_header = self.headers.get('Range')
        
        if (is_audio or is_video) and 'raw' not in query and 'dl' not in query and not range_header:
            content = self.render_player_html(path, is_audio, is_video)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        
        if 'raw' in query or range_header:
            fs_path = self.translate_path(self.path) 
            
            if not os.path.exists(fs_path) or os.path.isdir(fs_path):
                self.send_error(404, "File not found")
                return

            file_size = os.path.getsize(fs_path)
            
            if range_header:
                try:
                    byte_range = range_header.replace('bytes=', '').split('-')
                    start = int(byte_range[0]) if byte_range[0] else 0
                    end = int(byte_range[1]) if byte_range[1] else file_size - 1
                    
                    if start >= file_size:
                        self.send_error(416, "Requested Range Not Satisfiable")
                        return
                    
                    chunk_len = end - start + 1
                    
                    self.send_response(206) # Partial Content
                    self.send_header("Content-Type", self.guess_type(fs_path))
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(chunk_len))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    
                    with open(fs_path, 'rb') as f:
                        self.copy_byte_range(f, self.wfile, start, end)
                    return
                    
                except Exception:
                    pass 

            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(fs_path))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes") 
            self.end_headers()
            
            with open(fs_path, 'rb') as f:
                self.copyfile(f, self.wfile)
            return

        return super().do_GET()

    def render_player_html(self, path, is_audio, is_video):
        filename = os.path.basename(path)
        
        src_url = urllib.parse.quote(path) + "?raw=true"
        dl_url = urllib.parse.quote(path) + "?dl=1"
        
        icon = SVG_ICONS['audio'] if is_audio else SVG_ICONS['video']
        
        if is_audio:
            media_html = f'''
            <div id="mediaCover" class="media-cover">{icon}</div>
            <audio id="mediaElement" src="{src_url}" preload="metadata"></audio>
            '''
        else:
            media_html = f'''
            <div class="video-container">
                <video id="mediaElement" class="video-element" src="{src_url}" playsinline preload="metadata"></video>
            </div>
            '''

        html_content = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
            <title>Playing - {filename}</title>
            {CSS}
        </head>
        <body>
            <div class="branding"><h1>TetoDL Player</h1><p>Secured Stream</p></div>
            
            <div class="glass-container">
                <div class="player-layout">
                    <div class="header-section">
                        <div class="path-header">
                            <a href="./" style="text-decoration:none; color:inherit; display:flex; align-items:center; gap:8px; width:100%">
                                {SVG_ICONS["back"]} <span>Back to Directory</span>
                            </a>
                        </div>
                    </div>

                    <div class="player-content">
                        {media_html}
                        
                        <div class="media-title-large">{html.escape(filename)}</div>
                        
                        <div class="custom-controls">
                            <input type="range" id="progressBar" min="0" max="100" value="0" step="0.1">
                            
                            <div class="time-labels">
                                <span id="currTime">0:00</span>
                                <span id="totalTime">0:00</span>
                            </div>
                            
                            <div class="btn-row">
                                <a href="{dl_url}" download class="btn-dl">
                                    {SVG_ICONS['download']}
                                    <span>Save</span>
                                </a>
                                
                                <button id="playBtn" class="btn-control btn-play">
                                    {SVG_ICONS['play']}
                                </button>
                                
                                <div style="width:20px"></div> 
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">Hybrid CLI/TUI Media Suite</div>
            {JS_PLAYER}
        </body>
        </html>
        '''
        return html_content.encode('utf-8', 'surrogateescape')

    def list_directory(self, path):
        try:
            list_dir = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        list_dir.sort(key=lambda a: (not os.path.isdir(os.path.join(path, a)), a.lower()))
        
        displaypath = html.escape(urllib.parse.unquote(self.path), quote=False)
        
        r = []
        r.append('<!DOCTYPE html>')
        r.append('<html lang="en">')
        r.append(f'<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"><title>TetoDL Share</title>{CSS}</head>')
        r.append('<body>')
        r.append('<div class="branding"><h1>TetoDL Local Share</h1><p>by <span>rannd1nt</span></p></div>')
        r.append('<div class="glass-container">')
        
        r.append('<div class="header-section">')
        r.append(f'<div class="path-header">{SVG_ICONS["folder"]} <span>{displaypath}</span></div>')
        r.append('<input type="text" id="searchInput" class="search-box" onkeyup="filterList()" placeholder="Type to search...">')
        r.append('</div>')
        
        r.append('<div class="scroll-area"><ul class="file-list" id="fileList">')

        if self.path != '/':
            r.append('<li class="file-item parent-dir"><a class="file-link" href="../">')
            r.append(f'<div class="icon-box">{SVG_ICONS["back"]}</div><div class="info"><span class="name">Go Back</span><span class="meta">Parent Directory</span></div></a></li>')

        for name in list_dir:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            svg_icon = SVG_ICONS['file']; type_class = ""; meta_text = "-"
            
            is_dir = os.path.isdir(fullname)
            if is_dir:
                displayname += "/"; linkname += "/"; svg_icon = SVG_ICONS['folder']; type_class = "type-folder"; meta_text = "Directory"
            else:
                ext = os.path.splitext(name)[1].lower()
                if ext in ['.mp3', '.m4a', '.wav', '.flac', '.opus']: svg_icon = SVG_ICONS['audio']; type_class = "type-audio"
                elif ext in ['.mp4', '.mkv', '.webm', '.avi', '.mov']: svg_icon = SVG_ICONS['video']; type_class = "type-video"
                elif ext in ['.jpg', '.png', '.webp', '.jpeg', '.gif', '.svg']: svg_icon = SVG_ICONS['image']; type_class = "type-image"
                elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']: svg_icon = SVG_ICONS['archive']; type_class = "type-archive"
                elif ext in ['.py', '.js', '.html', '.css', '.json', '.c', '.rs']: svg_icon = SVG_ICONS['code']; type_class = "type-code"
                elif ext in ['.pdf', '.txt', '.md', '.doc', '.docx']: svg_icon = SVG_ICONS['doc']; type_class = "type-doc"
                elif ext in ['.apk', '.exe', '.msi']: svg_icon = SVG_ICONS['app']; type_class = "type-code"
                
                try:
                    size = os.path.getsize(fullname)
                    if size < 1024: size_str = f"{size} B"
                    elif size < 1024**2: size_str = f"{size/1024:.1f} KB"
                    else: size_str = f"{size/(1024**2):.1f} MB"
                    meta_text = size_str
                except: pass

            r.append(f'<li class="file-item {type_class}"><a class="file-link" href="{urllib.parse.quote(linkname)}">')
            r.append(f'<div class="icon-box">{svg_icon}</div><div class="info"><span class="name">{html.escape(displayname)}</span><span class="meta">{meta_text}</span></div></a></li>')

        r.append('</ul></div></div>')
        r.append('<div class="footer">Hybrid CLI/TUI Media Suite</div>')
        r.append(JS_PLAYER)
        r.append('</body></html>')

        encoded = ''.join(r).encode('utf-8', 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f