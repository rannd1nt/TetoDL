"""
Time parsing utilities for TetoDL.
Handles format: HH:MM:SS, MM:SS, or SS.
"""

def time_to_seconds(t_str: str) -> float:
    """
    Mengkonversi string waktu ke total detik (float).
    Mendukung format '1:2:9' (otomatis dianggap 1 jam 2 menit 9 detik).
    Validasi ketat: Menit dan Detik tidak boleh >= 60.
    
    Args:
        t_str: String waktu (e.g., "1:02:30", "05:00", "120", "start", "end")
    
    Returns:
        float: Total detik.
        
    Raises:
        ValueError: Jika format salah atau angka tidak valid.
    """
    t_str = t_str.strip().lower()
    
    # Handle Keyword Magic
    if t_str in ['start', '0']: return 0.0
    if t_str in ['end', 'inf']: return float('inf')
    if not t_str: return 0.0 # Empty string dianggap 0 (awal)

    try:
        parts = t_str.split(':')
        
        # Validasi panjang (Max HH:MM:SS)
        if len(parts) > 3:
            raise ValueError("Format too long (Max HH:MM:SS)")
            
        # Konversi ke float/int untuk validasi nilai
        # Kita membalik urutan biar selalu [Detik, Menit, Jam]
        parts = [float(p) for p in reversed(parts)]
        
        seconds = parts[0]
        minutes = parts[1] if len(parts) > 1 else 0
        hours = parts[2] if len(parts) > 2 else 0
        
        # Validasi Logika Waktu (60-base check)
        if seconds >= 60:
            raise ValueError(f"Seconds cannot be >= 60 (got {int(seconds)})")
        if minutes >= 60:
            raise ValueError(f"Minutes cannot be >= 60 (got {int(minutes)})")
            
        # Hitung Total Detik
        total_seconds = seconds + (minutes * 60) + (hours * 3600)
        return total_seconds

    except ValueError as e:
        # Re-raise dengan pesan yang lebih jelas jika itu error konversi angka
        if "could not convert" in str(e):
            raise ValueError(f"Invalid number format in '{t_str}'")
        raise e

def get_cut_seconds(cut_str: str):
    """
    Main parser untuk flag --cut.
    Mengubah input range menjadi tuple (start_sec, end_sec).
    
    Supported Formats:
    - "1:02:23-1:05:45" (Start to End)
    - "03:02-end"       (Start to End keyword)
    - "03:02-"          (Start to End implicit)
    - "start-13:20"     (Start keyword to End)
    - "-13:20"          (Start implicit to End)
    
    Returns:
        tuple[float, float]: (start_seconds, end_seconds)
    """
    if not cut_str:
        return None
        
    cut_str = cut_str.strip().lower()
    
    # Pisahkan berdasarkan '-'
    if '-' in cut_str:
        parts = cut_str.split('-')
        if len(parts) != 2:
            raise ValueError("Invalid format. Use only one '-' separator (e.g. 'start-end').")
        
        raw_start, raw_end = parts[0].strip(), parts[1].strip()
    else:
        raw_start, raw_end = cut_str, "inf"

    start_sec = time_to_seconds(raw_start) if raw_start else 0.0
    end_sec = time_to_seconds(raw_end) if raw_end else float('inf')

    # Validasi Logika Range
    if end_sec != float('inf') and start_sec >= end_sec:
        raise ValueError(f"Start time ({start_sec}s) cannot be greater than End time ({end_sec}s)")

    return start_sec, end_sec