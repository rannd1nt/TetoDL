import questionary
from questionary import Choice

from ..constants import IS_TERMUX
from ..utils.console import console
from ..utils.i18n_keys import Keys
from ..utils.formatters import (
    color,
    search_style,
    truncate_title,
    format_duration_digital
)

try:
    import yt_dlp as yt
except ImportError:
    yt = None


def perform_youtube_search(query, limit=5):
    """
    Search YouTube via yt_dlp Python API and return interactive selection.
    Returns: Selected Video URL or None
    """
    if yt is None:
        console.err(Keys.search.ytdlp_not_found)
        return None

    try:
        with yt.YoutubeDL({
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }) as ydl:
            search_query = f"ytsearch{limit}:{query}"
            info = ydl.extract_info(search_query, download=False)

        if not info or 'entries' not in info:
            console.warn(Keys.search.no_results_found)
            return None

        videos = []
        for entry in info['entries']:
            if entry:
                videos.append({
                    'title': entry.get('title', 'Unknown Title'),
                    'id': entry.get('id'),
                    'duration': entry.get('duration'),
                    'uploader': entry.get('uploader', 'Unknown'),
                    'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                })

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

            if idx == 'c' or not idx.isdigit():
                return "CANCEL"
            chosen = int(idx) - 1
            if 0 <= chosen < len(videos):
                selection = videos[chosen]['url']
            else:
                selection = "CANCEL"

        if selection == "CANCEL":
            return None

        return selection

    except Exception as e:
        console.err(Keys.search.search_error(error=e))
        return None
