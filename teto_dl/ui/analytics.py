"""
TetoDL Analytics / Wrap System
Visualizing Registry Data - Clean & Professional Style
"""
import re
import time
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box
import questionary

# Import Registry & Utils
from ..constants import RuntimeConfig, HISTORY_DISPLAY_LIMIT
from ..core.registry import registry
from ..core.history import calculate_stats, load_history, get_history_stats, reset_history
from ..utils.styles import clear, menu_style, format_duration, format_duration_digital, console
from ..utils.processing import get_platform_badge

def render_analytics_view():
    """Hanya menampilkan output Visual Analytics (Tanpa Loop/Clear)"""
    
    if not registry.data:
        console.print(Panel("[red]Registry database is empty. Download something first![/red]", title="No Data", border_style="red"))
        return False

    data = calculate_stats()

    # --- HEADER SECTION ---
    console.print()
    console.rule("[bold cyan]TETODL WRAP & DOWNLOAD ANALYTICS[/bold cyan]", style="dim cyan")
    console.print()

    # --- SUMMARY GRID ---
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)

    def big_stat(value, label):
        return f"[bold white]{value}[/]\n[cyan]{label}[/]"

    grid.add_row(
        big_stat(data['total_audio'], "Audio Files"),
        big_stat(data['total_files'], "Total Library"),
        big_stat(data['total_video'], "Video Files")
    )
    
    console.print(Panel(grid, box=box.MINIMAL, border_style="dim"))
    console.print()

    # --- TOP ARTISTS TABLE ---
    t_artist = Table(title="TOP ARTISTS", box=box.SQUARE, expand=True, title_style="bold cyan", header_style="bold cyan", border_style="dim white", show_edge=True, pad_edge=True)
    t_artist.add_column("#", justify="right", style="dim", width=3)
    t_artist.add_column("ARTIST", style="white", ratio=3) 
    t_artist.add_column("COUNT", justify="left", style="white", width=10)
    t_artist.add_column("DISTRIBUTION", ratio=2, style="cyan") 

    top_artists = data['artists'].most_common(5)
    max_count_art = top_artists[0][1] if top_artists else 1

    for idx, (artist, count) in enumerate(top_artists, 1):
        bar_len = int((count / max_count_art) * 20)
        t_artist.add_row(str(idx), artist, str(count), "━" * bar_len)

    # --- TOP ALBUMS TABLE ---
    t_album = Table(title="TOP ALBUMS", box=box.SQUARE, expand=True, title_style="bold cyan", header_style="bold cyan", border_style="dim white", show_edge=True, pad_edge=True)
    t_album.add_column("#", justify="right", style="dim", width=3)
    t_album.add_column("ALBUM", style="white", ratio=3) 
    t_album.add_column("COUNT", justify="left", style="white", width=10)
    t_album.add_column("DISTRIBUTION", style="cyan", ratio=2)

    top_albums = data['albums'].most_common(5)
    max_count_alb = top_albums[0][1] if top_albums else 1

    if not top_albums:
        t_album.add_row("-", "[dim]No album data[/dim]", "-", "-")
    else:
        for idx, (album, count) in enumerate(top_albums, 1):
            bar_len = int((count / max_count_alb) * 20)
            t_album.add_row(str(idx), album, str(count), "━" * bar_len)

    console.print(t_artist)
    console.print() 
    console.print(t_album)
    console.print()

    if data['most_played_path']:
        console.print(Align.center(f"[dim]Most Redownloaded:[/dim] [white]{data['most_played_path']}[/white] [cyan]({data['most_played_count']}x)[/cyan]"))
    
    return True

def render_history_view(limit=20, reverse_order=False, search_query=None):
    """
    Menampilkan history dengan opsi sorting, filtering, dan highlighting.
    
    Args:
        limit (int): Jumlah item maksimal yang ditampilkan.
        reverse_order (bool): Jika True, tampilkan dari yang TERLAMA (Oldest). 
                            Jika False, tampilkan dari yang TERBARU (Latest).
        search_query (str): Kata kunci untuk filter judul (case-insensitive).
    """
    
    raw_history = RuntimeConfig.DOWNLOAD_HISTORY
    valid_history = [x for x in raw_history if x.get('success', True)]

    # === FILTERING (SEARCH) ===
    if search_query:
        query_pattern = re.compile(re.escape(search_query), re.IGNORECASE)

        filtered_data = [
            x for x in valid_history 
            if x.get('title') and query_pattern.search(x.get('title'))
        ]
        
        if not filtered_data:
            console.print(f"\n[yellow]No history found matching query: [bold]'{search_query}'[/bold][/yellow]\n")
            return

        valid_history = filtered_data
        filter_status = f" [dim yellow](Filter: '{search_query}')[/dim yellow]"
    else:
        filter_status = ""
        
        if not valid_history:
            console.print("\n[yellow]No download history found.[/yellow]\n")
            return

    # === HEADER STATS ===
    stats = get_history_stats()
    console.print()
    console.print(f"[bold white]=== TetoDL Download History{filter_status} ===[/bold white]", justify="center")
    console.print(
        f"[dim]Video: {stats['yt_video']} | Audio: {stats['yt_audio']} | Music: {stats['yt_music']} | Spotify: {stats['spotify']} | "
        f"Total Duration: {format_duration(stats['total_duration'])}[/dim]\n",
        justify="center"
    )

    # === SORTING & LIMITING ===
    
    if reverse_order:
        # OLDEST FIRST
        target_data = valid_history[:limit]
        order_desc = "Oldest"
    else:
        # LATEST FIRST
        if limit >= len(valid_history):
            target_data = list(reversed(valid_history))
        else:
            target_data = list(reversed(valid_history[-limit:]))
        order_desc = "Latest"

    # === BUILD TABLE ===
    table = Table(box=box.SIMPLE, expand=True, header_style="bold cyan")
    table.add_column("No", justify="right", style="dim", width=3)
    table.add_column("Date", style="blue", no_wrap=True)
    table.add_column("Type", justify="left", width=8)
    table.add_column("Title", style="white", ratio=1, justify="left")
    table.add_column("Duration", justify="center", width=9)

    console.print(f"[dim]Showing {order_desc} {len(target_data)} items[/dim]", justify="center")

    # === RENDER ROWS ===
    for idx, entry in enumerate(target_data, 1):
        plat = entry.get('platform', 'Unknown')
        dtype = entry.get('download_type', '')
        duration_sec = entry.get('duration', 0)
        title_raw = entry.get('title', 'No Title') or "No Title"
        date_raw = entry.get('date_display', '-')

        title_display = title_raw.strip()
        if search_query:
            title_display = query_pattern.sub(
                lambda m: f"[u yellow]{m.group(0)}[/]", 
                title_display
            )

        table.add_row(
            str(idx),
            date_raw,
            get_platform_badge(plat, dtype),
            title_display,
            format_duration_digital(duration_sec)
        )

    console.print(table)
    console.print()


# ==========================================
# TUI WRAPPERS
# ==========================================

def show_analytics():
    """Interactive TUI for Analytics"""
    while True:
        clear()
        
        has_data = render_analytics_view()
        
        if not has_data:
            questionary.press_any_key_to_continue().ask()
            return

        choice = questionary.select(
            message="",
            choices=["Back to History"],
            style=menu_style(),
            qmark=" ",
            pointer=">",
            use_indicator=False,
            instruction=" "
        ).ask()

        if choice == "Back to History" or choice is None:
            break

def display_history():
    """Interactive TUI for History"""
    while True:   
        clear()
        
        render_history_view(limit=HISTORY_DISPLAY_LIMIT)
        
        choice = questionary.select(
            message="",
            choices=[
                questionary.Choice(title="[<] Back to Main Menu", value="back"),
                questionary.Choice(title="[!] TetoDL Wrap / Analytics", value="analytics"),
                questionary.Choice(title="[R] Refresh History", value="refresh"),
                questionary.Choice(title="[x] Clear History Log", value="clear"),
            ],
            style=menu_style(),
            qmark="",
            pointer=">",
            use_indicator=False,
            instruction=" "
        ).ask()

        if choice == "back" or choice is None: break
        elif choice == "analytics": show_analytics()
        elif choice == "refresh": load_history(); continue
        elif choice == "clear":
            if questionary.confirm("Clear history logs?", style=menu_style(), qmark=' ').ask():
                reset_history()
                console.print("[green]History cleared.[/green]")
                time.sleep(1)