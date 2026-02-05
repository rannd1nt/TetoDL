# utils/hooks.py
import sys
from ..utils.spinner import Spinner

# --- LOGGER ---
_ACTIVE_RICH = None

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg):
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()
        
        global _ACTIVE_RICH
        if _ACTIVE_RICH is not None:
            try:
                _ACTIVE_RICH.stop()
            except:
                pass

        if "403" in msg or "Forbidden" in msg:
            return 
        print(msg)

# --- HOOK IMPLEMENTATIONS ---

def _hook_minimal(d):
    """Output teks simple"""
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', 'N/A').strip()
        eta = d.get('_eta_str', 'N/A').strip()
        size = d.get('_total_bytes_str') or d.get('_total_bytes_estimate_str') or 'N/A'
        
        sys.stdout.write(f"\r\033[K[TetoDL] {p} of {size} at {speed} ETA {eta} ")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

def _hook_classic(d):
    """Output bar pendek"""
    if d['status'] == 'downloading':
        try:
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percent = downloaded / total if total > 0 else 0
            
            bar_len = 20 
            filled = int(bar_len * percent)
            
            if filled >= bar_len:
                bar = '=' * bar_len
            else:
                bar = '=' * filled + '>' + ' ' * (bar_len - filled - 1)
            
            percent_str = f"{percent:.1%}"
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            
            # Output: [=========>          ] 50.0% | 2MB/s | ETA 00:10
            msg = f"\r\033[K[{bar}] {percent_str} | {speed} | ETA {eta}"
            sys.stdout.write(msg)
            sys.stdout.flush()
        except:
            pass
    elif d['status'] == 'finished':
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

# --- RICH HOOK (MODERN) ---
try:
    from rich.progress import Progress, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn
    
    class RichProgressManager:
        def __init__(self):
            self.progress = None
            self.task_id = None
            global _ACTIVE_RICH
            _ACTIVE_RICH = self
        
        def stop(self):
            """Method manual buat matikan bar dari luar"""
            if self.progress:
                self.progress.stop()
                self.progress = None

        def __call__(self, d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                
                if not self.progress:
                    self.progress = Progress(
                        TextColumn("[bold cyan][TetoDL]", justify="right"),
                        BarColumn(bar_width=None),
                        "[progress.percentage]{task.percentage:>3.1f}%",
                        "•",
                        TransferSpeedColumn(),
                        "•",
                        TimeRemainingColumn(),
                        transient=True 
                    )
                    self.progress.start()
                    self.task_id = self.progress.add_task("Download", total=total)
                
                self.progress.update(self.task_id, completed=downloaded, total=total)
            
            elif d['status'] == 'finished':
                if self.progress:
                    self.progress.stop()
                    self.progress = None

    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

class EncodingSpinnerHook:
    """
    Hook khusus untuk menangani loading state saat FFmpeg/Post-processor berjalan.
    """
    def __init__(self, text):
        self.text = text
        self.spinner = None
        self.is_running = False 

    def __call__(self, d):
        """
        d['status'] -> 'started' | 'finished'
        d['postprocessor'] -> 'FFmpegFixupM4a', 'Merger', etc.
        """
        if d['status'] == 'started':
            if not self.is_running:
                # Instansiasi Spinner baru tiap kali start
                self.spinner = Spinner(self.text)
                self.spinner.start()
                self.is_running = True
                
        elif d['status'] == 'finished':
            if self.is_running and self.spinner:
                self.spinner.stop()
                self.spinner = None
                self.is_running = False


# --- FACTORY / SELECTOR ---
def get_progress_hook(style_name='minimal'):
    """Factory function untuk memilih style hook"""
    if style_name == 'modern' and _HAS_RICH:
        return RichProgressManager()
    elif style_name == 'minimal':
        return _hook_minimal
    else:
        return _hook_classic # Default
    
def get_postprocessor_hook(text_message):
    """Factory untuk post-processor hook"""
    return EncodingSpinnerHook(text_message)