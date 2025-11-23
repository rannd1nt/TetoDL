"""
Folder navigation system
"""
import os
import time
from ..constants import RuntimeConfig
from ..utils.colors import print_error, print_info
from ..utils.file_utils import create_nomedia_file
from ..core.config import save_config, cleanup_ghost_subfolders


def navigate_folders(start_path, title="Pilih Folder", restrict_to_start=True):
    """
    Recursive folder navigation system
    restrict_to_start: if True, cannot go above start_path
    """
    current_path = start_path
    
    while True:
        os.system("clear")
        print(f"=== {title} ===")
        print(f"Lokasi sekarang:\n{current_path}\n")

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
            print(f"{i}) {folder}/")
        
        # Display option to go to parent if not restricted or not at restricted root
        if not restrict_to_start or current_path != start_path:
            print("0) Naik ke folder sebelumnya")
        
        print("99) Pilih folder ini")
        print("100) Batal")

        choice = input("\nPilih > ").strip()

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
    Download folder selection:
    1) user subfolders
    2) create new subfolder
    3) view and use system subfolders
    0) save to root
    100) cancel
    """
    # If simple mode is active, directly return root_dir
    if RuntimeConfig.SIMPLE_MODE:
        return root_dir
        
    # Clean ghost subfolders before showing choices
    cleanup_ghost_subfolders()
    
    while True:
        os.system("clear")
        print(f"\n=== Pilih Lokasi Penyimpanan ({type_key}) ===\n")
        print(f"Root: {root_dir}\n")

        # Display user-created subfolders
        user_subfolders = RuntimeConfig.USER_SUBFOLDERS.get(type_key, [])
        for i, name in enumerate(user_subfolders, start=1):
            print(f"{i}) {name}")

        option_index = len(user_subfolders) + 1
        print(f"{option_index}) Buat subfolder baru")
        option_index += 1
        print(f"{option_index}) Lihat dan gunakan subfolder sistem")
        print("0) Simpan di root folder ini")
        print("100) Batal\n")

        choice = input("Pilihan > ").strip()

        # Save to root
        if choice == "0":
            return root_dir
        # Cancel
        elif choice == "100":
            return None
        # Create new subfolder
        elif choice == str(len(user_subfolders)+1):
            name = input("Nama subfolder baru: ").strip()
            if not name:
                continue
            new_path = os.path.join(root_dir, name)
            try:
                os.makedirs(new_path, exist_ok=True)
                # Remove .nomedia from new folder to show in gallery
                create_nomedia_file(new_path)
                if name not in RuntimeConfig.USER_SUBFOLDERS[type_key]:
                    RuntimeConfig.USER_SUBFOLDERS[type_key].append(name)
                    save_config()
                return new_path
            except Exception as e:
                print_error(f"Gagal membuat folder: {e}")
                time.sleep(1)
                continue
        # View and use system subfolders (limited)
        elif choice == str(len(user_subfolders)+2):
            selected_path = navigate_folders(
                root_dir, 
                f"Subfolder Sistem ({type_key})",
                restrict_to_start=True  # Limit navigation only within root_dir
            )
            if selected_path:
                return selected_path
            # If cancelled, continue loop
            continue
            
        # Select user subfolder
        elif choice.isdigit() and 1 <= int(choice) <= len(user_subfolders):
            selected_folder = user_subfolders[int(choice)-1]
            selected_path = os.path.join(root_dir, selected_folder)
            
            # Double check: ensure folder still exists
            if not os.path.exists(selected_path):
                print_info(f"Subfolder '{selected_folder}' tidak ditemukan, menghapus dari config...")
                RuntimeConfig.USER_SUBFOLDERS[type_key].remove(selected_folder)
                save_config()
                print_info("Silakan pilih lagi.")
                time.sleep(1.5)
                continue
                
            return selected_path
        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)