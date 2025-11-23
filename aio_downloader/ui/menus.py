"""
Menu system for AIO Downloader
"""
import os
import sys
import time
import threading
from ..constants import RuntimeConfig, DEFAULT_MUSIC_ROOT, DEFAULT_VIDEO_ROOT
from ..utils.colors import (
    print_process, print_info, print_success, 
    print_error, print_neutral, Colors
)
from ..core.config import (
    initialize_config, save_config, reset_to_defaults,
    toggle_simple_mode, toggle_skip_existing, toggle_video_resolution,
    clear_cache, clear_history
)
from ..core.history import display_history, load_history
from ..core.dependency import reset_verification
from ..utils.file_utils import create_nomedia_file
from ..ui.navigation import navigate_folders
from ..ui.display import (
    show_ascii, visit_instagram, visit_github, wait_and_clear_prompt
)
from ..downloaders.youtube import download_audio_youtube, download_video_youtube
from ..downloaders.spotify import download_spotify


def run_in_thread(fn, *args):
    """Run function in a separate thread"""
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()
    return t


def menu_folder():
    """Menu for managing root download folders"""
    while True:
        os.system("clear")
        print(f"\n{(Colors.LIGHT_GREEN)}=== Root Download Folder Settings ===\n")
        print(f"{(Colors.YELLOW)}1) Music root: {(Colors.GREEN)}{RuntimeConfig.MUSIC_ROOT}")
        print(f"{Colors.YELLOW}2) Video root: {(Colors.GREEN)}{RuntimeConfig.VIDEO_ROOT}\n")
        print(f"{(Colors.YELLOW)}3) Reset ke default")
        print(f"{Colors.YELLOW}4) Kembali{(Colors.RED)}\n")

        choice = input("Pilihan > ").strip()

        if choice == "1":
            new_dir = navigate_folders("/storage/emulated/0", "Pilih Folder Dasar", restrict_to_start=False)
            if new_dir:
                RuntimeConfig.MUSIC_ROOT = new_dir
                os.makedirs(RuntimeConfig.MUSIC_ROOT, exist_ok=True)
                create_nomedia_file(RuntimeConfig.MUSIC_ROOT)
                save_config()
                print_success(f"Music root diset ke: {RuntimeConfig.MUSIC_ROOT}")
                time.sleep(1)

        elif choice == "2":
            new_dir = navigate_folders("/storage/emulated/0", "Pilih Folder Dasar", restrict_to_start=False)
            if new_dir:
                RuntimeConfig.VIDEO_ROOT = new_dir
                os.makedirs(RuntimeConfig.VIDEO_ROOT, exist_ok=True)
                create_nomedia_file(RuntimeConfig.VIDEO_ROOT)
                save_config()
                print_success(f"Video root diset ke: {RuntimeConfig.VIDEO_ROOT}")
                time.sleep(1)

        elif choice == "3":
            reset_to_defaults()
            print_success("Reset ke default.")
            time.sleep(1)

        elif choice == "4":
            return

        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)


def menu_settings():
    """Menu for app settings"""
    while True:
        os.system("clear")
        print(f"\n{(Colors.LIGHT_GREEN)}======== TetoDL Settings ========\n")
        
        simple_mode_status = f"{Colors.GREEN}Aktif" if RuntimeConfig.SIMPLE_MODE else f"{Colors.RED}Nonaktif"
        print(f"{Colors.YELLOW}1) Simple Mode: {simple_mode_status}{Colors.WHITE}")
        print("→ Langsung download ke root folder, tanpa pilih subfolder\n")
        
        skip_status = f"{Colors.GREEN}Aktif" if RuntimeConfig.SKIP_EXISTING_FILES else f"{Colors.RED}Nonaktif"
        print(f"{Colors.YELLOW}2) Skip Existing Files: {skip_status}{Colors.WHITE}")
        print("→ Skip file yang sudah ada di folder tujuan\n")
        
        print(f"{Colors.YELLOW}3) Max Video Resolution: {Colors.GREEN}{RuntimeConfig.MAX_VIDEO_RESOLUTION}{Colors.WHITE}")
        print("→ Batas maksimal resolusi video (bukan fixed res)")
        print("→ Cek & pakai kualitas terbaik sampai batas ini\n")
        
        print(f"{Colors.YELLOW}4) Download History{Colors.WHITE}")
        print("→ Lihat riwayat download sebelumnya\n")
        
        print(f"{Colors.YELLOW}5) Clear Cache{Colors.WHITE}")
        print("→ Hapus cache metadata\n")
        
        print(f"{Colors.YELLOW}6) Clear History{Colors.WHITE}")
        print("→ Hapus riwayat download\n")
        
        print(f"{Colors.YELLOW}7) Reset Dependency Verification{Colors.WHITE}")
        print("→ Verify ulang dependencies saat run berikutnya\n")

        print(f"{Colors.YELLOW}8) Kembali\n{Colors.WHITE}")

        choice = input("Pilihan > ").strip()

        if choice == "1":
            toggle_simple_mode(not RuntimeConfig.SIMPLE_MODE)
            status = "diaktifkan" if RuntimeConfig.SIMPLE_MODE else "dinonaktifkan"
            print_success(f"Simple Mode {status}.")
            time.sleep(1)

        elif choice == "2":
            toggle_skip_existing(not RuntimeConfig.SKIP_EXISTING_FILES)
            status = "diaktifkan" if RuntimeConfig.SKIP_EXISTING_FILES else "dinonaktifkan"
            print_success(f"Skip Existing Files {status}.")
            time.sleep(1)   

        elif choice == "3":
            new_resolution = toggle_video_resolution()
            print_success(f"Max Video Resolution diubah ke: {new_resolution}")
            time.sleep(1)

        elif choice == "4":
            display_history()
            wait_and_clear_prompt()

        elif choice == "5":
            confirm = input("Yakin ingin menghapus cache? (y/n): ").strip().lower()
            if confirm == 'y':
                if clear_cache():
                    print_success("Cache berhasil dihapus")
                else:
                    print_info("Cache sudah kosong atau gagal dihapus")
            time.sleep(1)

        elif choice == "6":
            confirm = input("Yakin ingin menghapus history? (y/n): ").strip().lower()
            if confirm == 'y':
                if clear_history():
                    print_success("History berhasil dihapus")
                else:
                    print_info("History sudah kosong atau gagal dihapus")
            time.sleep(1)

        elif choice == "7":
            reset_verification()
            time.sleep(1)

        elif choice == "8":
            return

        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)


def menu_about():
    """About menu"""
    while True:
        os.system("clear")
        print(f"\n{Colors.LIGHT_GREEN}> TetoDL v1.0, by rannd1nt <{Colors.WHITE}")
        print("The author kins Kasane Teto\n")
        print("1) View documentation >")
        print("2) Visit author's GitHub >")
        print("3) Visit author's Instagram >")
        print("4) Kembali")
        choice = input("\nPilihan > ").strip()

        if choice == "1":
            print_info("Dokumentasi belum tersedia.")
            time.sleep(1)
        elif choice == "2":
            visit_github()
        elif choice == "3":
            visit_instagram()
        elif choice == "4":
            break
        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)


def main_menu():
    """Main menu loop"""
    # Initialize configuration
    initialize_config()
    load_history()
    
    # Dependency verification (only on first run)
    if not RuntimeConfig.VERIFIED_DEPENDENCIES:
        from ..core.dependency import verify_dependencies
        if not verify_dependencies():
            # Core dependencies not met, exit
            sys.exit(1)
    
    while True:
        os.system("clear")
        show_ascii('teto-2')
        print(f"{Colors.LIGHT_GREEN}\n=== TetoDL by rannd1nt {Colors.RED}(ft. Kasane Teto){(Colors.LIGHT_GREEN)} ==={Colors.WHITE}")
        print("\nPilih:")
        print("1) YouTube Audio/YouTube Music → MP3")
        print(f"2) YouTube Video → MP4 (Max: {RuntimeConfig.MAX_VIDEO_RESOLUTION})")
        
        # Show Spotify menu only if available
        if RuntimeConfig.SPOTIFY_AVAILABLE:
            print("3) Spotify → MP3")
        else:
            print(f"3) Spotify → MP3 {Colors.RED}(tidak tersedia){Colors.WHITE}")
        print(f"4) Ubah Root Folder Download")
        print(f"5) Pengaturan")
        print(f"6) Tentang")
        print(f"7) Keluar\n")
        
        choice = input("Pilihan > ").strip()

        if choice == "1":
            url = input("Link YouTube/YouTube Music: ").strip()
            if RuntimeConfig.SIMPLE_MODE:
                print_process("Simple Mode: Memulai download...")
            t = run_in_thread(download_audio_youtube, url)
            t.join()
            wait_and_clear_prompt()

        elif choice == "2":
            url = input("Link YouTube: ").strip()
            if RuntimeConfig.SIMPLE_MODE:
                print_process("Simple Mode: Memulai download...")
            t = run_in_thread(download_video_youtube, url)
            t.join()
            wait_and_clear_prompt()

        elif choice == "3":
            if RuntimeConfig.SPOTIFY_AVAILABLE:
                url = input("Link Spotify: ").strip()
                if RuntimeConfig.SIMPLE_MODE:
                    print_process("Simple Mode: Memulai download...")
                download_spotify(url)
                wait_and_clear_prompt()
            else:
                print_error("Spotify tidak tersedia!")
                print_info("Install dengan: pip install spotdl")
                print_info("Atau reset verification di menu Pengaturan")
                time.sleep(3.5)

        elif choice == "4":
            menu_folder()

        elif choice == "5":
            menu_settings()

        elif choice == "5":
            menu_about()

        elif choice == "5":
            save_config()
            print_neutral("Keluar.", "[-]")
            break

        else:
            print_error("Input tidak valid!")
            time.sleep(0.6)