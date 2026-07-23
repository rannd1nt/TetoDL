"""
Folder navigation system
"""
import os
import time

import questionary
from questionary import Choice, Separator
from rich.padding import Padding
from rich.text import Text

from ..core import config as cfg
from ..core.config import cleanup_ghost_subfolders, save_config
from ..ui.components import header
from ..utils.console import console
from ..utils.files import remove_nomedia_file
from ..utils.formatters import clear, menu_style
from ..utils.formatters import console as rich_console
from ..utils.i18n import get_text as _
from ..utils.i18n_keys import Keys


def navigate_folders(start_path, title="Pilih Folder", restrict_to_start=True):
    """
    Interactive folder navigation using arrow keys & filtering.
    """
    current_path = os.path.abspath(start_path)

    while True:
        clear()
        rich_console.print()
        rich_console.print(Padding(title, (0, 3)), style='bright_cyan')

        loc_text = Text.assemble(
            (_('download.navigation.current_location'), "bright_cyan"),
            (" ", "default"),
            (current_path, "green")
        )

        rich_console.print() 
        rich_console.print(Padding(loc_text, (0, 3)))
        rich_console.print()

        # 1. Ambil list folder
        try:
            all_items = sorted(os.listdir(current_path), key=str.lower)
            folders = [
                item for item in all_items 
                if os.path.isdir(os.path.join(current_path, item))
            ]
        except PermissionError:
            console.err(Keys.ui.access_denied_to(path=current_path))
            current_path = os.path.dirname(current_path)
            time.sleep(1)
            continue
        except Exception as e:
            console.err(Keys.ui.error_reading_folder(error=str(e)))
            return None

        choices: list[Choice | Separator] = []

        can_go_up = True
        if restrict_to_start:
            if current_path == start_path:
                can_go_up = False
        
        if os.path.dirname(current_path) == current_path:
            can_go_up = False

        if can_go_up:
            choices.append(Choice(
                title=f"- {_('download.navigation.go_up')} (..)", 
                value="__UP__"
            ))

        choices.append(Choice(
            title=f"- {_('download.navigation.select_this')}", 
            value="__SELECT__"
        ))

        choices.append(Separator("-" * 30))

        if not folders:
            choices.append(Choice(title="   (Empty Folder)", value="__NONE__", disabled="—"))
        else:
            for folder in folders:
                choices.append(Choice(
                    title=f" 📁 {folder}", 
                    value=folder
                ))

        choices.append(Separator("-" * 30))
        choices.append(Choice(title=f"- {_('common.cancel')}", value="__CANCEL__"))

        selection = questionary.select(
            message="",
            choices=choices,
            style=menu_style(),
            qmark='',
            pointer=">",
            use_indicator=False, 
            instruction=' ' 
        ).ask()

        if selection is None:
            return None

        if selection == "__UP__":
            current_path = os.path.dirname(current_path)
        
        elif selection == "__SELECT__":
            return current_path
        
        elif selection == "__CANCEL__":
            return None
            
        elif selection == "__NONE__":
            continue
            
        else:
            next_path = os.path.join(current_path, selection)
            current_path = next_path


def select_download_folder(root_dir, type_key='Unknown'):
    """
    Download folder selection yang terikat pada PATH (root_dir).
    Menggunakan Questionary & Rich UI.
    """
    if cfg.simple_mode:
        return root_dir
        
    cleanup_ghost_subfolders()

    root_key = os.path.abspath(root_dir)

    while True:
        clear()
        header()
        
        def path_info():
            rich_console.print(Padding(
                Text.assemble(
                    (_('download.folder.select_location', type=type_key), "bright_cyan"),
                    ("\nBase: ", "bright_cyan"),
                    (root_dir, "bright_green")
                ),
                (0, 1)
            ))

        path_info()
        current_subfolders = cfg.user_subfolders.get(root_key, [])
        
        choices: list[Choice | Separator] = []

        choices.append(Separator("--- TetoDL Subfolders ---"))
        if current_subfolders:
            for folder in current_subfolders:
                choices.append(Choice(
                    title=f"📁 {folder}",
                    value=folder
                ))
            choices.append(Separator(' '))
        else:
            choices.append(Choice(
                title=_('download.folder.no_subfolder'), 
                disabled="—"
            ))
        
        choices.append(Separator("-------- Action ---------"))
        choices.append(Choice(
            title=f"- {_('download.folder.save_to_root')}", 
            value="__ROOT__"
        ))
        
        choices.append(Choice(
            title=f"- {_('download.folder.create_new')}", 
            value="__NEW__"
        ))
        
        choices.append(Choice(
            title=f"- {_('download.folder.browse_system')}", 
            value="__BROWSE__"
        ))
        
        choices.append(Separator("-------------------------"))
        choices.append(Choice(title=f"- {_('common.cancel')}", value="__CANCEL__"))

        selection = questionary.select(
            message='',
            choices=choices,
            style=menu_style(),
            qmark='',
            pointer=">",
            use_indicator=False,
            instruction=' '
        ).ask()

        
        # 1. Cancel
        if selection == "__CANCEL__" or selection is None:
            clear()
            header()
            path_info()
            print()
            return None

        # 2. Save to Root
        elif selection == "__ROOT__":
            return root_dir

        # 3. Create New Folder
        elif selection == "__NEW__":
            clear()
            header()
            path_info()
            print()
            name = questionary.text(
                message=_('download.folder.enter_name'),
                style=menu_style(),
                qmark=''
            ).ask()

            if not name or not name.strip():
                continue

            new_path = os.path.join(root_dir, name.strip())

            try:
                os.makedirs(new_path, exist_ok=True)
                remove_nomedia_file(new_path)

                if root_key not in cfg.user_subfolders:
                    cfg.user_subfolders[root_key] = []
                
                if name.strip() not in cfg.user_subfolders[root_key]:
                    cfg.user_subfolders[root_key].append(name.strip())
                    save_config()

                return new_path

            except Exception as e:
                console.err(Keys.download.folder.create_failed(error=str(e)))
                time.sleep(1.5)
                continue

        # 4. Browse System (Navigasi Bebas)
        elif selection == "__BROWSE__":
            selected_path = navigate_folders(
                root_dir,
                f"{_('download.folder.browse_title')} ({os.path.basename(root_dir)})",
                restrict_to_start=False
            )
            if selected_path:
                return selected_path
            continue

        # 5. User Shortcut (Folder yang dipilih)
        else:
            selected_folder = selection
            selected_path = os.path.join(root_dir, selected_folder)

            # Validasi apakah folder fisik masih ada?
            if not os.path.exists(selected_path):
                console.warn(Keys.download.folder.not_found(name=selected_folder))
                
                # Hapus shortcut mati ini dari config
                if root_key in cfg.user_subfolders:
                    try:
                        cfg.user_subfolders[root_key].remove(selected_folder)
                        # Hapus key dictionary jika list jadi kosong (bersih-bersih)
                        if not cfg.user_subfolders[root_key]:
                            del cfg.user_subfolders[root_key]
                        save_config()
                    except ValueError:
                        pass # Sudah terhapus duluan
                
                console.warn(Keys.download.folder.choose_again)
                time.sleep(1.5)
                continue # Refresh menu

            return selected_path