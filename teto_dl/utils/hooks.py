"""
Hooks Utility
Provides logging handlers and progress hooks for different UI styles.
"""
import sys
from typing import Any, Dict, Optional, Union, Callable
from ..utils.spinner import Spinner

_ACTIVE_RICH: Optional['RichProgressManager'] = None

class QuietLogger:
    """Handles logging with minimal output and interruption management."""
    
    def debug(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()
        
        global _ACTIVE_RICH
        if _ACTIVE_RICH is not None:
            try:
                _ACTIVE_RICH.stop()
            except Exception:
                pass

        if "403" in msg or "Forbidden" in msg:
            return 
        print(msg)

def _hook_minimal(d: Dict[str, Any]) -> None:
    """Provides a simple text-based progress output."""
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

def _hook_classic(d: Dict[str, Any]) -> None:
    """Provides a classic progress bar output."""
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
            
            msg = f"\r\033[K[{bar}] {percent_str} | {speed} | ETA {eta}"
            sys.stdout.write(msg)
            sys.stdout.flush()
        except Exception:
            pass
    elif d['status'] == 'finished':
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

try:
    from rich.progress import Progress, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn
    
    class RichProgressManager:
        """Manages modern progress bars using the Rich library."""
        
        def __init__(self) -> None:
            self.progress: Optional[Progress] = None
            self.task_id: Any = None
            global _ACTIVE_RICH
            _ACTIVE_RICH = self
        
        def stop(self) -> None:
            """Manually stops the progress display."""
            if self.progress:
                self.progress.stop()
                self.progress = None

        def __call__(self, d: Dict[str, Any]) -> None:
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
    Hook to manage loading states during FFmpeg or post-processing operations.
    """
    def __init__(self, text: str) -> None:
        self.text = text
        self.spinner: Optional[Spinner] = None
        self.is_running: bool = False 

    def __call__(self, d: Dict[str, Any]) -> None:
        if d['status'] == 'started':
            if not self.is_running:
                self.spinner = Spinner(self.text)
                self.spinner.start()
                self.is_running = True
                
        elif d['status'] == 'finished':
            if self.is_running and self.spinner:
                self.spinner.stop()
                self.spinner = None
                self.is_running = False

def get_progress_hook(style_name: str = 'minimal') -> Union[Callable[[Dict[str, Any]], None], 'RichProgressManager']:
    """Factory function to select the progress hook style."""
    if style_name == 'modern' and _HAS_RICH:
        return RichProgressManager()
    elif style_name == 'minimal':
        return _hook_minimal
    else:
        return _hook_classic
    
def get_postprocessor_hook(text_message: str) -> EncodingSpinnerHook:
    """Factory function to create a post-processor hook."""
    return EncodingSpinnerHook(text_message)