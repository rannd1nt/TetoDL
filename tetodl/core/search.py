import json
import subprocess
import shutil
import questionary
from questionary import Choice

from ..constants import IS_TERMUX
# Import helper formatting yang sudah ada
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..utils.formatters import (
    color, 
    search_style, 
    truncate_title, 
    format_duration_digital
)


def perform_youtube_search(query, limit=5):
    """
    Search YouTube via yt-dlp and return interactive selection.
    Returns: Selected Video URL or None
    """
    yt_dlp_cmd = "yt-dlp"
    if not shutil.which(yt_dlp_cmd):
        console.err(Keys.search.ytdlp_not_found)
        return None

    try:
        search_query = f"ytsearch{limit}:{query}"
        
        cmd = [
            yt_dlp_cmd,
            "--flat-playlist", 
            "--dump-json",
            "--no-warnings",
            "--quiet",
            "--no-colors", 
            search_query
        ]
        
        with console.spin(f"Searching YouTube for '{query}'..."):
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            console.err(Keys.search.search_failed)
            return None

        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        'title': data.get('title', 'Unknown Title'),
                        'id': data.get('id'),
                        'duration': data.get('duration'),
                        'uploader': data.get('uploader', 'Unknown'),
                        'url': data.get('url') or f"https://www.youtube.com/watch?v={data.get('id')}"
                    })
                except json.JSONDecodeError:
                    pass
        
        if not videos:
            console.warn(Keys.search.no_results_found)
            return None

        formatted_query = color(query, 'c') 
        console.ok(f"Search Results for '{formatted_query}':")

        choices = []
        for vid in videos:
            dur_str = format_duration_digital(vid.get('duration'))
            clean_title = truncate_title(vid['title'], max_chars=50)
            label = f"- {clean_title} >> | Dur: {dur_str} | Up: {vid['uploader']} |"
            choices.append(Choice(title=label, value=vid['url']))
        
        choices.append(Choice(title="- Cancel", value="CANCEL"))

        if not IS_TERMUX:
            selection = questionary.select(
                message="Select one to download:",
                choices=choices,
                style=search_style(),
                qmark='',
                pointer=">",
                use_indicator=False,
                instruction=' '
            ).ask()
        else:
            for i, vid in enumerate(videos):
                d_str = format_duration_digital(vid.get('duration'))
                t_str = truncate_title(vid['title'], max_chars=35)
                print(f"{i+1}. {t_str} [{d_str}] | {vid['uploader']}")
                
            print("c. Cancel")
            
            try:
                idx = input("Select > ").strip().lower()
            except KeyboardInterrupt:
                return None

            if idx == 'c' or not idx.isdigit(): return "CANCEL"
            idx = int(idx) - 1
            if 0 <= idx < len(videos): selection = videos[idx]['url']
            else: selection = "CANCEL"

        if selection == "CANCEL":
            return None
            
        return selection

    except Exception as e:
        console.err(Keys.search.search_error(error=e))
        return None