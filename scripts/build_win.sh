#!/usr/bin/env bash
# ==============================================================================
# build_win.sh — Local Zero-Bandwidth Windows Build & Deploy Pipeline for TetoDL
#
# Builds the standalone tetodl.exe binary natively using an isolated, hermetic
# uv runtime triggered from WSL/Linux. Reuses cached binaries to minimize
# bandwidth and prevents accidental overwrites of existing installations.
#
# Usage:
#   ./scripts/build_win.sh [OPTIONS]
#
# Options:
#   -f, --force         Force overwrite if an active installation is detected
#   -s, --skip-install  Compile binary only (dist/tetodl.exe); do not install
#   -c, --clean         Clean build cache, dist directories, and venv
#   -t, --test          Run post-build smoke verification tests
#   -h, --help          Show this help message and exit
# ==============================================================================
set -euo pipefail

# ANSI color codes
CLR_RESET="\033[0m"
CLR_BOLD="\033[1m"
CLR_RED="\033[1;31m"
CLR_GREEN="\033[1;32m"
CLR_YELLOW="\033[1;33m"
CLR_BLUE="\033[1;34m"
CLR_CYAN="\033[1;36m"
CLR_GRAY="\033[0;90m"

log_info()    { printf "${CLR_BLUE}[*]${CLR_RESET} %s\n" "$*"; }
log_success() { printf "${CLR_GREEN}[+]${CLR_RESET} %s\n" "$*"; }
log_warn()    { printf "${CLR_YELLOW}[-]${CLR_RESET} %s\n" "$*"; }
log_error()   { printf "${CLR_RED}[!]${CLR_RESET} %s\n" "$*"; }
log_fatal()   { printf "${CLR_RED}[!] FATAL:${CLR_RESET} %s\n" "$*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default flags
FORCE=false
SKIP_INSTALL=false
CLEAN=false
RUN_TEST=false

show_help() {
    echo -e "${CLR_BOLD}TetoDL Local Windows Build Pipeline${CLR_RESET}
Usage: $(basename "$0") [OPTIONS]

${CLR_BOLD}Options:${CLR_RESET}
  -f, --force         Overwrite existing TetoDL installation without aborting
  -s, --skip-install  Compile binary only to dist/tetodl.exe (skip install to AppData)
  -c, --clean         Clean PyInstaller build caches, dist/ folder, and venv
  -t, --test          Execute smoke tests on the compiled binary (--version, --help)
  -h, --help          Show this help message and exit

${CLR_BOLD}Examples:${CLR_RESET}
  $(basename "$0")                      # Safe build & install (aborts if already installed)
  $(basename "$0") --force              # Build and overwrite existing active installation
  $(basename "$0") --skip-install -t    # Build to dist/tetodl.exe and run smoke tests
  $(basename "$0") --clean --force      # Clean rebuild and force install"
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--force)
            FORCE=true
            shift
            ;;
        -s|--skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -t|--test)
            RUN_TEST=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unrecognized argument: $1"
            show_help
            exit 1
            ;;
    esac
done

printf "\n"
printf "${CLR_CYAN}======================================================${CLR_RESET}\n"
printf "${CLR_BOLD}   TetoDL Local Windows Build & Deploy Engine        ${CLR_RESET}\n"
printf "${CLR_CYAN}======================================================${CLR_RESET}\n\n"

log_info "Workspace root: $ROOT_DIR"

# ------------------------------------------------------------------------------
# 1. Environment & Interop Discovery
# ------------------------------------------------------------------------------
log_info "Detecting Windows host environment..."

POWERSHELL_BIN=""
for candidate in powershell.exe pwsh.exe /mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe; do
    if command -v "$candidate" >/dev/null 2>&1; then
        POWERSHELL_BIN="$candidate"
        break
    fi
done

if [[ -z "$POWERSHELL_BIN" ]]; then
    log_fatal "Windows PowerShell executable not found. Ensure Windows interop is enabled in WSL (/etc/wsl.conf)."
fi
log_success "Found Windows PowerShell: $POWERSHELL_BIN"

if ! command -v wslpath >/dev/null 2>&1; then
    log_fatal "'wslpath' utility is required to translate WSL and Windows paths."
fi

# ------------------------------------------------------------------------------
# 2. Locate Windows LocalAppData & Target Installation
# ------------------------------------------------------------------------------
TARGET_WIN_EXE=""
TARGET_WSL_EXE=""

# Scan /mnt/c/Users/*/AppData/Local/TetoDL/tetodl.exe
for user_dir in /mnt/c/Users/*; do
    candidate="$user_dir/AppData/Local/TetoDL/tetodl.exe"
    if [[ -f "$candidate" ]]; then
        TARGET_WSL_EXE="$candidate"
        TARGET_WIN_EXE="$(wslpath -w "$candidate" 2>/dev/null || true)"
        break
    fi
done

# If not found at specific path, check if any non-system user exists in /mnt/c/Users
if [[ -z "$TARGET_WSL_EXE" ]]; then
    for user_dir in /mnt/c/Users/*; do
        bname="$(basename "$user_dir")"
        if [[ "$bname" != "All Users" && "$bname" != "Default" && "$bname" != "Default User" && "$bname" != "Public" && "$bname" != "desktop.ini" && -d "$user_dir" ]]; then
            TARGET_WSL_EXE="$user_dir/AppData/Local/TetoDL/tetodl.exe"
            TARGET_WIN_EXE="$(wslpath -w "$TARGET_WSL_EXE" 2>/dev/null || true)"
            break
        fi
    done
fi

log_info "Resolved target binary location: ${TARGET_WIN_EXE:-Unknown}"

# ------------------------------------------------------------------------------
# 3. Pre-flight Safety Guard: Abort on Existing Installation
# ------------------------------------------------------------------------------
if [[ "$SKIP_INSTALL" = false && "$FORCE" = false ]]; then
    if [[ -n "$TARGET_WSL_EXE" && -f "$TARGET_WSL_EXE" ]]; then
        printf "\n"
        printf "${CLR_RED}╔════════════════════════════════════════════════════════════════════════════╗${CLR_RESET}\n"
        printf "${CLR_RED}║  ABORT: Active TetoDL installation detected!                              ║${CLR_RESET}\n"
        printf "${CLR_RED}╚════════════════════════════════════════════════════════════════════════════╝${CLR_RESET}\n"
        printf "Target path: ${CLR_YELLOW}%s${CLR_RESET}\n\n" "$TARGET_WIN_EXE"
        printf "To prevent configuration conflicts or corrupted states, the installer will\n"
        printf "not overwrite your existing installation automatically.\n\n"
        printf "Please perform one of the following actions:\n"
        printf "  1. Manually uninstall the existing version first:\n"
        printf "     ${CLR_CYAN}tetodl --uninstall${CLR_RESET}\n\n"
        printf "  2. Or rerun this build script with ${CLR_YELLOW}--force${CLR_RESET} (${CLR_YELLOW}-f${CLR_RESET}) to overwrite:\n"
        printf "     ${CLR_GREEN}%s --force${CLR_RESET}\n\n" "$0"
        exit 1
    fi
fi

# ------------------------------------------------------------------------------
# 4. Check for ffmpeg.exe cache to guarantee zero bandwidth
# ------------------------------------------------------------------------------
if [[ ! -f "$ROOT_DIR/ffmpeg.exe" ]]; then
    # Check Windows dev tools cache
    FOUND_FFMPEG=""
    for cache_dir in /mnt/c/Users/*/AppData/Local/tetodl-dev; do
        if [[ -f "$cache_dir/ffmpeg.exe" ]]; then
            FOUND_FFMPEG="$cache_dir/ffmpeg.exe"
            break
        fi
    done

    # Check PyInstaller runtime temp dirs (_MEI*) in Windows Temp
    if [[ -z "$FOUND_FFMPEG" ]]; then
        for mei_dir in /mnt/c/Users/*/AppData/Local/Temp/_MEI*; do
            if [[ -f "$mei_dir/ffmpeg.exe" ]]; then
                FOUND_FFMPEG="$mei_dir/ffmpeg.exe"
                break
            fi
        done
    fi

    # Check WinGet temp cache for already downloaded ffmpeg archives
    if [[ -z "$FOUND_FFMPEG" ]]; then
        for zip_file in /mnt/c/Users/*/AppData/Local/Temp/WinGet/*ffmpeg*/*.zip; do
            if [[ -f "$zip_file" ]]; then
                log_info "Found cached WinGet ffmpeg archive: $zip_file"
                log_info "Extracting ffmpeg.exe locally (0 bytes downloaded)..."
                if python3 -c "
import zipfile, sys
try:
    with zipfile.ZipFile(sys.argv[1]) as z:
        for name in z.namelist():
            if name.endswith('ffmpeg.exe'):
                with z.open(name) as src, open(sys.argv[2], 'wb') as dst:
                    dst.write(src.read())
                sys.exit(0)
except Exception:
    sys.exit(1)
sys.exit(1)
" "$zip_file" "$ROOT_DIR/ffmpeg.exe"; then
                    FOUND_FFMPEG="$ROOT_DIR/ffmpeg.exe"
                    break
                fi
            fi
        done
    fi

    if [[ -n "$FOUND_FFMPEG" ]]; then
        log_success "Found cached ffmpeg.exe at: $FOUND_FFMPEG"
        if [[ "$FOUND_FFMPEG" != "$ROOT_DIR/ffmpeg.exe" ]]; then
            log_info "Reusing cached ffmpeg.exe (saved ~100MB download)..."
            cp "$FOUND_FFMPEG" "$ROOT_DIR/ffmpeg.exe"
        fi
    else
        log_warn "No cached ffmpeg.exe found in local caches. Spec builder will retrieve it on first run."
    fi
else
    log_success "Local ffmpeg.exe already present in workspace root (0 bytes needed)."
fi

# ------------------------------------------------------------------------------
# 5. Invoke Windows PowerShell Worker
# ------------------------------------------------------------------------------
WIN_PROJECT_DIR="$(wslpath -w "$ROOT_DIR")"
WIN_PS_SCRIPT="$(wslpath -w "$SCRIPT_DIR/build_win.ps1")"

PS_ARGS=("-ProjectDir" "$WIN_PROJECT_DIR")
if [[ "$FORCE" = true ]]; then PS_ARGS+=("-Force"); fi
if [[ "$SKIP_INSTALL" = true ]]; then PS_ARGS+=("-SkipInstall"); fi
if [[ "$CLEAN" = true ]]; then PS_ARGS+=("-Clean"); fi
if [[ "$RUN_TEST" = true ]]; then PS_ARGS+=("-Test"); fi

log_info "Invoking Windows build worker via PowerShell interop..."
log_info "Command: $POWERSHELL_BIN -NoProfile -ExecutionPolicy Bypass -File $WIN_PS_SCRIPT ${PS_ARGS[*]}"
printf "\n"

"$POWERSHELL_BIN" -NoProfile -ExecutionPolicy Bypass -File "$WIN_PS_SCRIPT" "${PS_ARGS[@]}"
BUILD_STATUS=$?

if [[ $BUILD_STATUS -ne 0 ]]; then
    log_fatal "Windows build worker failed with exit code $BUILD_STATUS."
fi

printf "\n"
log_success "TetoDL Windows build pipeline finished successfully."
