import os
import time
import questionary
from rich import box
from rich.table import Table
from questionary import Choice, Separator

from ..core.cache import get_cache_size
from ..ui.navigation import navigate_folders, remove_nomedia_file
from ..utils.console import console
from ..utils.formatters import (
    clear, color, menu_style, colored_switch, console as rich_console
)
from ..utils.i18n import get_language_display_name, get_available_languages, get_text as _
from ..utils.i18n_keys import Keys
from ..utils.display import formatted_video_codec
from ..constants import AUDIO_QUALITY_OPTIONS, VALID_RESOLUTIONS, VALID_CODECS
from ..core import config as cfg
from ..utils.files import get_free_space
from ..core.config import (
    save_config, reset_to_defaults, toggle_video_container,
    toggle_simple_mode, toggle_skip_existing, set_video_resolution,
    clear_cache, get_language_name, update_language, toggle_audio_quality,
    get_audio_quality_info, toggle_smart_cover, set_video_codec
)


def menu_audio_quality():
    """Menu for audio quality settings"""
    while True:
        clear()
        current_quality = cfg.audio_quality
        quality_info = AUDIO_QUALITY_OPTIONS[current_quality]

        print(color(f"\n======== {_('menu.audio_quality.title')} ========\n", "c"))
        print(_('menu.audio_quality.current',
                format=color(quality_info['ext'].upper(), 'lgrn'),
                bitrate=color(quality_info['bitrate'], 'g')))
        print()
        print(_('menu.audio_quality.select'))
        print()

        # MP3 Option
        selected_mp3 = f" {color(' [✓]', 'lgrn')}" if current_quality == "mp3" else ""
        print(color(f"1) {_('menu.audio_quality.mp3_title')}{selected_mp3}", "c"))
        print(f"   {_('menu.audio_quality.mp3_desc_1')}")
        print(f"   {_('menu.audio_quality.mp3_desc_2')}")
        print(f"   {_('menu.audio_quality.mp3_desc_3')}\n")

        # M4A Option
        selected_m4a = f" {color(' [✓]', 'lgrn')}" if current_quality == "m4a" else ""
        print(color(f"2) {_('menu.audio_quality.m4a_title')}{selected_m4a}", "c"))
        print(f"   {_('menu.audio_quality.m4a_desc_1')}")
        print(f"   {_('menu.audio_quality.m4a_desc_2')}")
        print(f"   {_('menu.audio_quality.m4a_desc_3')}\n")

        # OPUS Option
        selected_opus = f" {color(' [✓]', 'lgrn')}" if current_quality == "opus" else ""
        print(color(f"3) {_('menu.audio_quality.opus_title')}{selected_opus}", "c"))
        print(f"   {_('menu.audio_quality.opus_desc_1')}")
        print(f"   {_('menu.audio_quality.opus_desc_2')}")
        print(f"   {_('menu.audio_quality.opus_desc_3')}\n")

        try:
            choice = input(_('common.choose_info', info=_('common.zero_enter'))).strip()
        except KeyboardInterrupt:
            return

        if choice == "1":
            toggle_audio_quality("mp3")
            console.ok(Keys.menu.audio_quality.changed(format=color("MP3", 'lgrn')))
            time.sleep(1)
        elif choice == "2":
            toggle_audio_quality("m4a")
            console.ok(Keys.menu.audio_quality.changed(format=color("M4A", 'lgrn')))
            time.sleep(1)
        elif choice == "3":
            toggle_audio_quality("opus")
            console.ok(Keys.menu.audio_quality.changed(format=color("OPUS", 'lgrn')))
            time.sleep(1)
        elif choice == "0" or choice == '':
            return
        else:
            console.err(Keys.error.invalid_input)
            time.sleep(0.6)

def menu_video_resolution():
    """Menu for video resolution settings"""
    while True:
        clear()
        current_res = cfg.max_video_resolution
        print(current_res)

        print(color(f"\n======== {_('menu.video_resolution.title')} ========\n", "c"))
        print(_('menu.video_resolution.select') + "\n")

        res_info = {
            "4320p": {"title": "8K Ultra HD", "desc": "menu.video_resolution.4320p_desc"},
            "2160p": {"title": "4K Ultra HD", "desc": "menu.video_resolution.2160p_desc"},
            "1440p": {"title": "2K Quad HD",  "desc": "menu.video_resolution.1440p_desc"},
            "1080p": {"title": "Full HD",     "desc": "menu.video_resolution.1080p_desc"},
            "720p":  {"title": "HD",          "desc": "menu.video_resolution.720p_desc"},
            "480p":  {"title": "SD",          "desc": "menu.video_resolution.480p_desc"}
        }

        for idx, res in enumerate(VALID_RESOLUTIONS, 1):
            info = res_info.get(res, {"title": "Unknown", "desc": ""})
            
            is_selected = f" {color(' [✓]', 'lgrn')}" if current_res == res else ""
            
            print(color(f"{idx}) {res} - {info['title']}{is_selected}", "c"))
            
            description = _(info['desc'])
            if description:
                print(f"{description}")
            print()

        back_idx = 0

        try:
            choice = input(_('common.choose_info', info=_('common.zero_enter'))).strip()
        except KeyboardInterrupt:
            return

        # Logic Selection
        if choice.isdigit():
            choice_int = int(choice)
            
            if 1 <= choice_int <= len(VALID_RESOLUTIONS):
                selected_res = VALID_RESOLUTIONS[choice_int - 1]
                set_video_resolution(selected_res)
                console.ok(Keys.config.resolution_changed(resolution=color(selected_res, 'lgrn')))
                time.sleep(1)
            elif choice_int == back_idx:
                return
            else:
                console.err(Keys.error.invalid_input)
                time.sleep(0.6)
        elif choice == '':
            return
        else:
            console.err(Keys.error.invalid_input)
            time.sleep(0.6)

def menu_video_codec():
    """Menu for video codec settings"""
    while True:
        clear()
        current_codec = cfg.video_codec
        
        print(color(f"\n======== {_('menu.video_codec.title')} ========\n", "c"))
        print(_('menu.video_codec.select') + "\n")

        # Dictionary info codec
        codec_info = {
            "default": {
                "title": _("menu.video_codec.default_title"), 
                "desc": "menu.video_codec.default_desc"
            },
            "h264": {
                "title": _("menu.video_codec.h264_title"), 
                "desc": "menu.video_codec.h264_desc"
            },
            "h265": {
                "title": _("menu.video_codec.h265_title"), 
                "desc": "menu.video_codec.h265_desc"
            }
        }

        for idx, codec in enumerate(VALID_CODECS, 1):
            info = codec_info.get(codec, {"title": "Unknown", "desc": ""})
            is_selected = f" {color(' [✓]', 'lgrn')}" if current_codec == codec else ""
            
            print(color(f"{idx}) {info['title']}{is_selected}", "c"))
            
            description = _(info['desc'])
            if description:
                print(f"{description}")
            print()

        back_idx = 0

        try:
            choice = input(_('common.choose_info', info=_('common.zero_enter'))).strip()
        except KeyboardInterrupt:
            return

        if choice.isdigit():
            choice_int = int(choice)
            
            if 1 <= choice_int <= len(VALID_CODECS):
                selected_codec = VALID_CODECS[choice_int - 1]
                set_video_codec(selected_codec)
                
                console.ok(Keys.config.codec_changed(codec=color(formatted_video_codec(selected_codec), 'lgrn')))
                time.sleep(1)
            elif choice_int == back_idx:
                return
            else:
                console.err(Keys.error.invalid_input)
                time.sleep(0.6)
        elif choice == '':
            return
        else:
            console.err(Keys.error.invalid_input)
            time.sleep(0.6)

def prompt_language_selection(force_selection=False):
    """
    Helper function to show language selection list.
    Args:
        force_selection (bool): If True, 'Back' option will be hidden.
    """
    available_codes = get_available_languages()
    choices = []

    choices.append(Separator())
    for code in available_codes:
        display_name = get_language_display_name(code)
        choices.append(Choice(title=f"- {display_name}", value=code))

    choices.append(Separator())
    
    if not force_selection:
        choices.append(Choice(title=f"- {_('common.back')}", value="back")) 

    return questionary.select(
        message=_('menu.language.choose'),
        qmark="",
        choices=choices,
        style=menu_style(),
        instruction=" ",
        pointer=">"
    ).ask()

def language_setting():
    """Menu for selecting language using Questionary"""
    while True:
        clear()
        
        current_code = cfg.language
        current_display = get_language_display_name(current_code)
        
        print(color(f"\n ======== {_('menu.language.title')} ========\n", "c"))
        print(" " + _('menu.language.current', lang=color(current_display, 'lgrn')) + "\n")
        
        answer = prompt_language_selection(force_selection=False)

        if not answer or answer == "back":
            return

        update_language(answer)


def menu_folder():
    """Menu for managing root download folders with Rich display"""
    while True:
        clear()
        
        def path_info():
            print(color(f"\n   {_('menu.root_folder.title')}\n", "c"))

            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            
            # Kolom: Label, Path, Free Space
            table.add_column("Type", style="bold cyan")
            table.add_column("Path", style="green")
            table.add_column("Space", style="dim white", justify="right")

            # Music Row
            music_space = get_free_space(cfg.music_root)
            table.add_row(
                "Music Path:", 
                cfg.music_root, 
                music_space
            )

            # Video Row
            video_space = get_free_space(cfg.video_root)
            table.add_row(
                "Video Path:", 
                cfg.video_root, 
                video_space
            )

            # Render table ke layar
            rich_console.print(table)

        path_info()

        # 3. Questionary Menu
        choices = [
            Choice(title=f"- {_('menu.root_folder.change_music', default='Change music root')}", value="1"),
            Choice(title=f"- {_('menu.root_folder.change_video', default='Change video root')}", value="2"),
            Separator(line="-"*30),
            Choice(title=f"- {_('menu.root_folder.reset')}", value="3"),
            Choice(title=f"- {_('common.back')}", value="4"),
        ]

        selection = questionary.select(
            message="",
            choices=choices,
            style=menu_style(),
            qmark='',
            pointer=">",
            use_indicator=False,
            instruction=' ',
        ).ask()

        if selection is None: return
        choice = selection

        if choice == "1":
            new_dir = navigate_folders(cfg.music_root, _('download.navigation.title'), restrict_to_start=False)
            if new_dir:
                cfg.music_root = new_dir
                os.makedirs(cfg.music_root, exist_ok=True)
                remove_nomedia_file(cfg.music_root)
                save_config()

        elif choice == "2":
            new_dir = navigate_folders(cfg.video_root, _('download.navigation.title'), restrict_to_start=False)
            if new_dir:
                cfg.video_root = new_dir
                os.makedirs(cfg.video_root, exist_ok=True)
                remove_nomedia_file(cfg.video_root)
                save_config()

        elif choice == "3":
            reset_to_defaults()
            clear()
            path_info()
            console.ok(Keys.config.reset_default)
            time.sleep(1)

        elif choice == "4":
            return

def menu_settings():
    """Menu for app settings"""
    while True:
        clear()
        lang_name = get_language_name(cfg.language)
        audio_quality_info = get_audio_quality_info()
        current_container = getattr(cfg, 'video_container', 'mp4')
        current_codec = getattr(cfg, 'video_codec', 'default')

        rich_console.print("="*15, f"{_('menu.settings.title')}", "="*15, justify='center', end='\n\n')

        # Simple Mode
        simple_status = colored_switch(cfg.simple_mode, _('common.active'), _('common.inactive'))
        print(color(f"1) {_('menu.settings.simple_mode', status=simple_status)}", "c"))
        print(f"{_('menu.settings.simple_mode_desc')}\n")

        # Smart Cover Mode
        s_cover_status = colored_switch(cfg.smart_cover_mode, _('common.active'), _('common.inactive'))
        print(color(f"2) {_('menu.settings.smart_cover', status=s_cover_status)}", "c"))
        print(f"{_('menu.settings.smart_cover_desc_1')}")
        print(f"{_('menu.settings.smart_cover_desc_2')}")
        print(f"{_('menu.settings.smart_cover_desc_3')}\n")
        
        # Skip Existing
        skip_status = colored_switch(cfg.skip_existing_files, _('common.active'), _('common.inactive'))
        print(color(f"3) {_('menu.settings.skip_existing', status=skip_status)}", "c"))
        print(f"{_('menu.settings.skip_existing_desc')}\n")

        # Max Resolution
        print(color(f"4) {_('menu.settings.max_resolution', resolution=color(cfg.max_video_resolution, 'g'))}", "c"))
        print(f"{_('menu.settings.max_resolution_desc_2')}\n")

        # Video Container
        print(color(f"5) {_('menu.settings.video_container', container=color(current_container.upper(), 'g'))}", "c"))
        print(f"{_('menu.settings.video_container_desc')}\n")

        # Video Codec
        print(color(f"6) {_('menu.settings.video_codec',
                codec=color(formatted_video_codec(current_codec), 'g'))}", "c"))
        print(f"{_('menu.settings.video_codec_desc')}\n")

        # Audio Quality
        print(color(f"7) {_('menu.settings.audio_quality', format=color(audio_quality_info['ext'].upper(), 'g'))}", 'c'))
        print(f"{_('menu.settings.audio_quality_desc')}\n")
        
        # Language
        print(color(f"8) {_('menu.settings.language', lang=color(lang_name, 'g'))}", "c"))
        print(f"{_('menu.settings.language_desc')}\n")

        # Clear Cache
        print(color(f"9) {_('menu.settings.clear_cache')} {color(f'(Total Cache: {get_cache_size()})', 'g')}", "c"))
        print(f"{_('menu.settings.clear_cache_desc')}\n")


        try:
            choice = input(_('common.choose_info', info=_('common.zero_enter'))).strip()
        except KeyboardInterrupt:
            return

        if choice == "1":
            toggle_simple_mode(not cfg.simple_mode)
            status = _('config.simple_mode_enabled') if cfg.simple_mode else _('config.simple_mode_disabled')
            console.ok(status)
            time.sleep(1)

        elif choice == "2":
            toggle_smart_cover(not cfg.smart_cover_mode)
            status = _('config.smart_cover_enabled') if cfg.smart_cover_mode else _('config.smart_cover_disabled')
            console.ok(status)
            time.sleep(1)

        elif choice == "3":
            toggle_skip_existing(not cfg.skip_existing_files)
            status = _('config.skip_existing_enabled') if cfg.skip_existing_files else _('config.skip_existing_disabled')
            console.ok(status)
            time.sleep(1)

        elif choice == "4":
            menu_video_resolution()

        elif choice == "5":
            current = getattr(cfg, 'video_container', 'mp4')
            new_container = "mkv" if current == "mp4" else "mp4"
            
            if toggle_video_container(new_container):
                console.ok(Keys.config.container_changed(container=new_container.upper()))
            time.sleep(1)

        elif choice == "6":
            menu_video_codec()

        elif choice == "7":
            menu_audio_quality()
        
        elif choice == "8":
            language_setting()

        elif choice == "9":
            confirm = input(_('config.confirm_clear_cache')).strip().lower()
            if confirm == _('common.yes'):
                if clear_cache():
                    console.ok(Keys.config.cache_deleted)
                else:
                    console.warn(Keys.config.cache_empty)
            time.sleep(1)

        elif choice == "0" or choice == '':
            return

        else:
            console.err(Keys.error.invalid_input)
            time.sleep(0.6)