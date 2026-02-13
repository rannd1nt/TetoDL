# tetodl/utils/server_ui.py
import os
import html
import io
import urllib.parse
from http.server import SimpleHTTPRequestHandler

# --- LIQUID GLASS CSS (Brutal & Aesthetic) ---
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');

    :root {
        --glass-surface: rgba(20, 20, 35, 0.4);
        --glass-border: rgba(255, 255, 255, 0.1);
        --glass-highlight: rgba(255, 255, 255, 0.05);
        
        --item-bg: rgba(0, 0, 0, 0.4);
        --item-border: rgba(255, 255, 255, 0.08);
        
        --text-main: #ffffff;
        --text-muted: #94a3b8;
        --accent: #00d2ff; /* Cyan Neon */
        --accent-glow: rgba(0, 210, 255, 0.4);
    }
    
    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    
    body {
        font-family: 'Outfit', -apple-system, sans-serif;
        background: #0f172a;
        /* Animated Liquid Background */
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        background-size: 200% 200%;
        animation: liquidMove 15s ease infinite;
        color: var(--text-main);
        min-height: 100vh;
        padding: 20px;
        padding-top: 40px;
    }

    @keyframes liquidMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* --- BRANDING --- */
    .branding {
        text-align: center;
        margin-bottom: 25px;
        position: relative;
        z-index: 10;
    }
    
    .branding h1 {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #fff 0%, #00d2ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 10px 30px rgba(0, 210, 255, 0.3);
        margin-bottom: 2px;
    }
    
    .branding p {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 500;
    }
    
    .branding p span { color: var(--accent); }

    /* --- MAIN CONTAINER (The Liquid Glass) --- */
    .glass-container {
        max_width: 700px;
        margin: 0 auto;
        position: relative;
        
        background: var(--glass-surface);
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 20px;
        box-shadow: 
            0 20px 40px rgba(0,0,0,0.4),
            inset 0 0 0 1px rgba(255,255,255, 0.05);
        overflow: hidden;
    }
    
    /* Glossy Shine Effect on top left */
    .glass-container::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        pointer-events: none;
        z-index: 0;
    }

    .content-wrapper { position: relative; z-index: 1; }

    /* --- PATH HEADER --- */
    .path-header {
        font-size: 0.9rem;
        color: var(--accent);
        background: rgba(0, 210, 255, 0.1);
        border: 1px solid rgba(0, 210, 255, 0.2);
        padding: 10px 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        word-break: break-all;
        font-family: monospace;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* --- SEARCH BOX --- */
    .search-box {
        width: 100%;
        padding: 16px 20px;
        border-radius: 16px;
        border: 1px solid var(--glass-border);
        background: rgba(0, 0, 0, 0.3); /* Dark hole feel */
        color: white;
        font-size: 1rem;
        font-family: inherit;
        outline: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 20px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
    }
    .search-box:focus {
        border-color: var(--accent);
        box-shadow: 
            inset 0 2px 4px rgba(0,0,0,0.5),
            0 0 0 2px var(--accent-glow);
    }

    /* --- FILE LIST --- */
    .file-list { 
        list-style: none; 
        display: flex; 
        flex-direction: column; 
        gap: 12px; 
        padding-bottom: 10px;
    }
    
    .file-item {
        /* ITEM SEPARATION LOGIC */
        background: var(--item-bg);
        border: 1px solid var(--item-border);
        border-radius: 16px;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s, background 0.2s, border-color 0.2s;
    }
    
    .file-item:active { transform: scale(0.98); }
    
    .file-link {
        display: flex;
        align-items: center;
        padding: 16px;
        text-decoration: none;
        color: inherit;
        position: relative;
        z-index: 2;
    }
    
    /* Icon Styling */
    .icon-box {
        width: 48px; height: 48px;
        display: flex; align-items: center; justify-content: center;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        font-size: 1.5rem;
        margin-right: 15px;
        flex-shrink: 0;
    }
    
    .info { flex: 1; min-width: 0; }
    
    .name { 
        display: block; 
        font-weight: 600; 
        font-size: 1rem;
        color: #f1f5f9;
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        margin-bottom: 4px;
        letter-spacing: 0.3px;
    }
    
    .meta { 
        display: block; 
        font-size: 0.75rem; 
        color: var(--text-muted); 
        font-weight: 500;
    }

    /* Back Button Special Style */
    .parent-dir {
        background: rgba(0, 210, 255, 0.08);
        border-color: rgba(0, 210, 255, 0.2);
    }
    .parent-dir .icon-box {
        background: rgba(0, 210, 255, 0.2);
    }
    .parent-dir .name { color: var(--accent); }

    .footer {
        text-align: center;
        margin-top: 30px;
        font-size: 0.75rem;
        opacity: 0.5;
        letter-spacing: 1px;
    }
</style>
"""

JS = """
<script>
    function filterList() {
        const input = document.getElementById('searchInput');
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
    def log_message(self, format, *args):
        pass

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
        
        # --- BRANDING HEADER ---
        r.append('<div class="branding">')
        r.append('<h1>TetoDL Local Share</h1>')
        r.append('<p>by <span>rannd1nt</span></p>')
        r.append('</div>')
        
        # --- GLASS CONTAINER ---
        r.append('<div class="glass-container"><div class="content-wrapper">')
        
        # Path
        r.append(f'<div class="path-header">📂 {displaypath}</div>')
        
        # Search
        r.append('<input type="text" id="searchInput" class="search-box" onkeyup="filterList()" placeholder="Type to search files...">')
        
        r.append('<ul class="file-list" id="fileList">')

        # Back Button
        if self.path != '/':
            r.append('<li class="file-item parent-dir">')
            r.append('<a class="file-link" href="../">')
            r.append('<div class="icon-box">⬅️</div>')
            r.append('<div class="info"><span class="name">Go Back</span><span class="meta">Parent Directory</span></div>')
            r.append('</a></li>')

        for name in list_dir:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            
            is_dir = os.path.isdir(fullname)
            if is_dir:
                displayname = name + "/"
                linkname = name + "/"
                icon = "📁"
                meta_text = "Directory"
            else:
                ext = os.path.splitext(name)[1].lower()
                if ext in ['.mp3', '.m4a', '.wav', '.flac', '.opus']: icon = "🎵"
                elif ext in ['.mp4', '.mkv', '.webm', '.avi']: icon = "🎬"
                elif ext in ['.jpg', '.png', '.webp', '.jpeg']: icon = "🖼️"
                elif ext in ['.zip', '.rar', '.7z', '.tar']: icon = "📦"
                elif ext in ['.pdf', '.txt', '.md', '.json', '.py']: icon = "📄"
                elif ext in ['.exe', '.msi', '.apk']: icon = "📲"
                else: icon = "📃"

                try:
                    size = os.path.getsize(fullname)
                    if size < 1024: size_str = f"{size} B"
                    elif size < 1024**2: size_str = f"{size/1024:.1f} KB"
                    else: size_str = f"{size/(1024**2):.1f} MB"
                    meta_text = size_str
                except:
                    meta_text = "-"

            r.append('<li class="file-item">')
            r.append(f'<a class="file-link" href="{urllib.parse.quote(linkname)}">')
            r.append(f'<div class="icon-box">{icon}</div>')
            r.append(f'<div class="info"><span class="name">{html.escape(displayname)}</span>')
            r.append(f'<span class="meta">{meta_text}</span></div>')
            r.append('</a></li>')

        r.append('</ul>')
        r.append('</div></div>')
        
        r.append('<div class="footer">A Hybrid CLI/TUI Media Suite</div>')
        
        r.append(JS)
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