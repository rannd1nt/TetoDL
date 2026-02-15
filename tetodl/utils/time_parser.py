"""
Time parsing utilities for TetoDL.
Handles flexible formats like HH:MM:SS, MM:SS, or SS.
"""
from typing import Optional, Tuple, List, Union

def time_to_seconds(t_str: str) -> float:
    """
    Converts a time string into total seconds (float).

    Supports standard 'HH:MM:SS' formats as well as loose formatting 
    (e.g., '1:2:9' becomes 1h 2m 9s). It strictly validates that minutes 
    and seconds do not exceed 59.

    Args:
        t_str (str): Time string (e.g., "1:02:30", "1:5", "120", "start", "end").

    Returns:
        float: Total duration in seconds. Returns 0.0 for 'start' and inf for 'end'.

    Raises:
        ValueError: If format is invalid or values exceed time limits (>=60).
    """
    t_str = t_str.strip().lower()
    
    if t_str in ['start', '0']: return 0.0
    if t_str in ['end', 'inf']: return float('inf')
    if not t_str: return 0.0

    try:
        parts: List[float] = [float(p) for p in reversed(t_str.split(':'))]

        if len(parts) > 3:
            raise ValueError("Format too long (Max HH:MM:SS)")
            
        seconds = parts[0]
        minutes = parts[1] if len(parts) > 1 else 0
        hours = parts[2] if len(parts) > 2 else 0
        
        if seconds >= 60:
            raise ValueError(f"Seconds cannot be >= 60 (got {int(seconds)})")
        if minutes >= 60:
            raise ValueError(f"Minutes cannot be >= 60 (got {int(minutes)})")
            
        return seconds + (minutes * 60) + (hours * 3600)

    except ValueError as e:
        if "could not convert" in str(e):
            raise ValueError(f"Invalid number format in '{t_str}'")
        raise e

def get_cut_seconds(cut_str: str) -> Optional[Tuple[float, float]]:
    """
    Parses the '--cut' argument string into a start and end tuple.

    Handles various range formats:
    - Explicit range: "58:09-1:02:12" (Start to End)
    - Open-ended start: "58:09-" (Start to End of video)
    - Open-ended end: "-1:02:12" (Start of video to End)
    - Loose formatting: "58:9-1:2:12" (Single digits allowed)

    Returns:
        Optional[Tuple[float, float]]: A tuple (start_seconds, end_seconds).
    """
    if not cut_str:
        return None
        
    cut_str = cut_str.strip().lower()
    
    if '-' in cut_str:
        parts = cut_str.split('-')
        if len(parts) != 2:
            raise ValueError("Invalid format. Use only one '-' separator (e.g. 'start-end').")
        
        raw_start, raw_end = parts[0].strip(), parts[1].strip()
    else:
        # Fallback: if no dash, treat input as start time until end
        raw_start, raw_end = cut_str, "inf"

    start_sec = time_to_seconds(raw_start) if raw_start else 0.0
    end_sec = time_to_seconds(raw_end) if raw_end else float('inf')

    if end_sec != float('inf') and start_sec >= end_sec:
        raise ValueError(f"Start time ({start_sec}s) cannot be greater than End time ({end_sec}s)")

    return start_sec, end_sec