"""
TetoDL Analytics / Wrap System
Visualizing Registry Data - Clean & Professional Style
"""
import time

from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box
import questionary

# Import Registry
from ..constants import RuntimeConfig, HISTORY_DISPLAY_LIMIT
from ..core.registry import registry
from ..core.history import calculate_stats
from ..core.history import load_history, get_history_stats, reset_history
from ..utils.styles import clear, menu_style, format_duration, format_duration_digital, console
from ..utils.processing import get_platform_badge

def show_analytics():
    """Menampilkan UI TetoDL Wrap / Analytics"""
    while True:
        clear()
        
        if not registry.data:
            console.print(Panel("[red]Registry database is empty.[/red]", title="Error"))
            questionary.press_any_key_to_continue().ask()
            return

        data = calculate_stats()

        # --- 1. HEADER SECTION (Clean Rule) ---
        console.print()
        console.rule("[bold cyan]TETODL WRAP & DOWNLOAD ANALYTICS[/bold cyan]", style="dim cyan")
        console.print()

        # --- 2. SUMMARY GRID (Minimalist) ---
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)

        # Helper untuk angka besar
        def big_stat(value, label):
            return f"[bold white]{value}[/]\n[cyan]{label}[/]"

        grid.add_row(
            big_stat(data['total_audio'], "Audio Files"),
            big_stat(data['total_files'], "Total Library"),
            big_stat(data['total_video'], "Video Files")
        )
        
        # Bungkus grid dalam Panel invisible biar ada spacing atas-bawah yang enak
        console.print(Panel(grid, box=box.MINIMAL, border_style="dim"))
        console.print()

        # --- 3. TOP ARTISTS TABLE ---
        t_artist = Table(
            title="TOP ARTISTS",
            box=box.SQUARE,
            expand=True,
            title_style="bold cyan",
            header_style="bold cyan",
            border_style="dim white",
            show_edge=True,
            pad_edge=True
        )
        # Struktur: Dim ID, White Content, Cyan Bar
        t_artist.add_column("#", justify="right", style="dim", width=3)
        t_artist.add_column("ARTIST", style="white", ratio=3) 
        t_artist.add_column("DOWNLOAD COUNT", justify="left", style="white", width=16)
        t_artist.add_column("DISTRIBUTION", ratio=2, style="cyan") 

        top_artists = data['artists'].most_common(5)
        max_count_art = top_artists[0][1] if top_artists else 1

        for idx, (artist, count) in enumerate(top_artists, 1):
            bar_len = int((count / max_count_art) * 20)
            bar_visual = f"{'━' * bar_len}" 
            
            t_artist.add_row(
                str(idx),
                artist,
                str(count),
                bar_visual
            )

        # --- 4. TOP ALBUMS TABLE (Updated Distribution) ---
        t_album = Table(
            title="TOP ALBUMS", 
            box=box.SQUARE, 
            expand=True,
            title_style="bold cyan",
            header_style="bold cyan",
            border_style="dim white",
            show_edge=True,
            pad_edge=True
        )

        t_album.add_column("#", justify="right", style="dim", width=3)
        t_album.add_column("ALBUM", style="white", ratio=3) 
        t_album.add_column("DOWNLOAD COUNT", justify="left", style="white", width=16)
        t_album.add_column("DISTRIBUTION", style="cyan", ratio=2) # Kolom Distribusi

        # Ambil data album dulu untuk hitung max count
        top_albums = data['albums'].most_common(5)
        max_count_alb = top_albums[0][1] if top_albums else 1

        if not top_albums:
            # Placeholder harus 4 kolom juga biar tabel gak rusak
            t_album.add_row("-", "[dim]No album data available[/dim]", "-", "-")
        else:
            for idx, (album, count) in enumerate(top_albums, 1):
                # Logic Bar Chart (Sama dengan artist)
                bar_len = int((count / max_count_alb) * 20)
                bar_visual = f"{'━' * bar_len}"
                
                t_album.add_row(
                    str(idx), 
                    album, 
                    str(count), 
                    bar_visual # Masukkan bar visual ke kolom ke-4
                )

        # Render Tables
        console.print(t_artist)
        console.print() 
        console.print(t_album)
        console.print()

        # Footer Info (Most Played) - Simple Text centered
        if data['most_played_path']:
            console.print(
                Align.center(
                    f"[dim]Most Redownloaded:[/dim] [white]{data['most_played_path']}[/white] "
                    f"[cyan]({data['most_played_count']}x)[/cyan]"
                )
            )

        # --- 5. NAVIGATION (Invisible Prompt) ---
        choice = questionary.select(
            message="",
            choices=[
                "Back to History",
            ],
            style=menu_style(),
            qmark=" ",
            pointer=">",
            use_indicator=False,
            instruction=" "
        ).ask()

        if choice == "Back to History" or choice is None:
            break


def display_history():
    """Display history using Rich"""
    while True: # Loop utama menu history   
        clear()
        
        # 1. Tampilkan Header Statistik (Existing Code)
        stats = get_history_stats()
        console.print()
        console.print(f"[bold white]=== TetoDL Download History ===[/bold white]", justify="center")
        console.print(
            f"[dim]Video: {stats['yt_video']} | Audio: {stats['yt_audio']} | Music: {stats['yt_music']} | Spotify: {stats['spotify']} | "
            f"Total: {format_duration(stats['total_duration'])}[/dim]\n",
            justify="center"
        )

        valid_history = [x for x in RuntimeConfig.DOWNLOAD_HISTORY if x.get('success', True)]

        if not valid_history:
            console.print("[yellow]Belum ada riwayat download sukses.[/yellow]", justify="center")
            # Kalau kosong tetep kasih menu balik
            console.print("\n")
        else:
            # 2. Setup Tabel Rich (Existing Code)
            table = Table(box=box.SIMPLE, expand=True, header_style="bold cyan")
            
            table.add_column("No", justify="right", style="dim", width=3)
            table.add_column("Date", style="blue", no_wrap=True)
            table.add_column("Code", justify="center", width=8)
            table.add_column("Title", style="white", ratio=1)
            table.add_column("Duration", justify="right", width=9)

            recent = valid_history[-HISTORY_DISPLAY_LIMIT:]
            
            for idx, entry in enumerate(reversed(recent), 1):
                plat = entry.get('platform', 'Unknown')
                dtype = entry.get('download_type', '')
                duration_sec = entry.get('duration', 0)
                
                title_raw = entry.get('title', 'No Title') or "No Title"
                date_raw = entry.get('date_display', '-')

                table.add_row(
                    str(idx),
                    date_raw,
                    get_platform_badge(plat, dtype),
                    title_raw.strip(),
                    format_duration_digital(duration_sec)
                )

            console.print(table)
        
        # Navigation
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

        if choice == "back" or choice is None:
            break
            
        elif choice == "analytics":
            show_analytics()
            
        elif choice == "refresh":
            load_history()
            continue
            
        elif choice == "clear":
            confirm = questionary.confirm(
                "Are you sure you want to clear the History logs?",
                style=menu_style(),
                qmark=' ',
                default=False
            ).ask()
            
            if confirm:
                reset_history()
                console.print("[green]History cleared.[/green]")
                time.sleep(1)