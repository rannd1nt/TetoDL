"""
Folder navigation system
"""
import os
import time
from ..constants import RuntimeConfig
from ..utils.i18n import get_text as _
from ..utils.colors import print_error, print_info, clear, color, Colors as C
from ..utils.file_utils import create_nomedia_file
from ..core.config import save_config, cleanup_ghost_subfolders


def navigate_folders(start_path, title="Pilih Folder", restrict_to_start=True):
    """
    Recursive folder navigation system
    restrict_to_start: if True, cannot go above start_path
    """
    current_path = start_path
    
    while True:
        clear()
        print(color(f'=== {title} ===', 'c'))
        print(f"\n{color(_('download.navigation.current_location'), 'c')} {color(current_path, 'lgrn')}\n")

        try:
            # Get all folders in current dir
            entries = []
            for item in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    entries.append(item)
        except Exception as e:
            print_error(f"Tidak bisa membaca folder: {e}")
            input("Tekan Enter untuk kembali...")
            return None

        # Display choices
        for i, folder in enumerate(entries, start=1):
            f_name = f'{i}) {folder}/'
            print(color(f_name, 'lgrn'))
        
        # Display option to go to parent if not restricted or not at restricted root
        
        print(C.CYAN)
        if not restrict_to_start or current_path != start_path:
            print(f"0) {_('download.navigation.go_up')}")
        
        print(f"99) {_('download.navigation.select_this')} ")
        print(f"100) {_('common.cancel')}")
        
        print(C.RESET)
        choice = input(f"{_('common.choose')}").strip()
        
        if choice == "0" and (not restrict_to_start or current_path != start_path):
            # Go to parent directory
            parent = os.path.dirname(current_path.rstrip("/"))
            if parent and os.path.exists(parent):
                # Check if not exceeding start_path boundary
                if not restrict_to_start or (parent.startswith(start_path) and len(parent) >= len(start_path)):
                    current_path = parent
                else:
                    print_info("Tidak bisa naik di atas folder root")
                    time.sleep(0.6)
            else:
                print_info("Tidak bisa naik lebih tinggi")
                time.sleep(0.6)
                
        elif choice == "99":
            # Select current folder
            return current_path
            
        elif choice == "100":
            # Cancel
            return None
            
        elif choice.isdigit() and 1 <= int(choice) <= len(entries):
            # Enter selected subfolder
            selected_folder = entries[int(choice) - 1]
            current_path = os.path.join(current_path, selected_folder)
            
        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)


def select_download_folder(root_dir, type_key):
    """
    Download folder selection with full i18n
    """

    if RuntimeConfig.SIMPLE_MODE:
        return root_dir
        
    cleanup_ghost_subfolders()
    
    while True:
        clear()
        print(f"\n=== {color(_('download.folder.select_location', type=type_key), 'c')} ===\n")
        print(f"{color(_('download.folder.root', path=color(root_dir, 'lgrn')), 'c')}\n")

        # Display user-created subfolders
        user_subfolders = RuntimeConfig.USER_SUBFOLDERS.get(type_key, [])
        for i, name in enumerate(user_subfolders, start=1):
            print(color(f"{i}) {name}", "c"))

        option_index = len(user_subfolders) + 1
        print(f"{color(f'{option_index}) {_('download.folder.create_new')}', 'c')}")
        option_index += 1
        print(f"{color(f'{option_index}) {_('download.folder.browse_system')}', 'c')}")
        print(f"{color(f'0) {_('download.folder.save_to_root')}', 'c')}")
        print(f"{color(f'100) {_('common.cancel')}', 'c')}\n")

        choice = input(_('common.choose')).strip()

        # Save to root
        if choice == "0":
            return root_dir

        # Cancel
        elif choice == "100":
            return None

        # Create new subfolder
        elif choice == str(len(user_subfolders) + 1):
            name = input(_('download.folder.enter_name')).strip()
            if not name:
                continue

            new_path = os.path.join(root_dir, name)

            try:
                os.makedirs(new_path, exist_ok=True)
                create_nomedia_file(new_path)

                if name not in RuntimeConfig.USER_SUBFOLDERS[type_key]:
                    RuntimeConfig.USER_SUBFOLDERS[type_key].append(name)
                    save_config()

                return new_path

            except Exception as e:
                print_error(_('download.folder.create_failed', error=e))
                time.sleep(1)
                continue

        # System subfolders
        elif choice == str(len(user_subfolders) + 2):
            selected_path = navigate_folders(
                root_dir,
                f"System Subfolders ({type_key})",
                restrict_to_start=True
            )
            if selected_path:
                return selected_path
            continue

        # Select existing user subfolder
        elif choice.isdigit() and 1 <= int(choice) <= len(user_subfolders):
            selected_folder = user_subfolders[int(choice) - 1]
            selected_path = os.path.join(root_dir, selected_folder)

            if not os.path.exists(selected_path):
                print_info(_('download.folder.not_found', name=selected_folder))
                RuntimeConfig.USER_SUBFOLDERS[type_key].remove(selected_folder)
                save_config()
                print_info(_('download.folder.choose_again'))
                time.sleep(1.5)
                continue

            return selected_path

        else:
            print_error(_('error.invalid_input'))
            time.sleep(0.6)