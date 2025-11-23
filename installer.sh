#!/bin/bash
# AIO Downloader - Auto Installer for Termux
# by rannd1nt

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo ""
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}            TetoDL - Installer ${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[→]${NC} $1"
}

# Parse arguments
LITE_MODE=false
if [[ "$1" == "--lite" ]]; then
    LITE_MODE=true
fi

print_header

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_error "Script ini harus dijalankan di Termux!"
    exit 1
fi

print_success "Termux terdeteksi"

# Step 1: Update packages
print_step "Step 1/6: Update package list..."
if pkg update -y > /dev/null 2>&1; then
    print_success "Package list updated"
else
    print_error "Gagal update package list"
    exit 1
fi

# Step 2: Install system dependencies
print_step "Step 2/6: Install system dependencies..."
print_info "Installing: python, ffmpeg, git"

if pkg install -y python ffmpeg git > /dev/null 2>&1; then
    print_success "System dependencies installed"
else
    print_error "Gagal install system dependencies"
    exit 1
fi

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    print_success "FFmpeg: $(ffmpeg -version | head -n1 | cut -d' ' -f3)"
else
    print_error "FFmpeg tidak terdeteksi"
    exit 1
fi

# Check Python
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    print_success "Python: $PYTHON_VERSION"
else
    print_error "Python tidak terdeteksi"
    exit 1
fi

# Step 3: Upgrade pip
print_step "Step 3/6: Upgrade pip..."
if pip install --upgrade pip > /dev/null 2>&1; then
    print_success "pip upgraded"
else
    print_info "pip upgrade skipped (not critical)"
fi

# Step 4: Install Python dependencies
print_step "Step 4/6: Install Python dependencies..."

if [ "$LITE_MODE" = true ]; then
    print_info "Lite mode: Installing without Spotify support"
    print_info "This will be much faster!"
    
    if pip install -r requirements-lite.txt; then
        print_success "Lite dependencies installed"
    else
        print_error "Gagal install lite dependencies"
        exit 1
    fi
else
    print_info "Full mode: Installing with Spotify support"
    print_info "WARNING: This may take 30-60 minutes due to Rust compilation!"
    print_info "Press Ctrl+C now if you want to use --lite mode instead"
    sleep 5
    
    if pip install -r requirements.txt; then
        print_success "Full dependencies installed"
    else
        print_error "Gagal install full dependencies"
        print_info "Tip: Gunakan --lite mode jika instalasi terlalu lama"
        exit 1
    fi
fi

# Step 5: Setup storage permission
print_step "Step 5/6: Setup storage permission..."
print_info "Izinkan permission saat popup muncul!"
termux-setup-storage
sleep 2
print_success "Storage permission setup complete"

# Step 6: Set permissions
print_step "Step 6/6: Set file permissions..."
chmod +x main.py
print_success "File permissions set"

# Summary
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

if [ "$LITE_MODE" = true ]; then
    print_info "Installed: Lite version (without Spotify)"
    print_info "Menu Spotify akan hidden di aplikasi"
else
    print_info "Installed: Full version (with Spotify)"
fi

echo ""
print_step "Installed components:"
echo "  ✓ Python $(python --version 2>&1 | cut -d' ' -f2)"
echo "  ✓ FFmpeg $(ffmpeg -version | head -n1 | cut -d' ' -f3)"
echo "  ✓ yt-dlp"
echo "  ✓ requests"

if [ "$LITE_MODE" = false ]; then
    if command -v spotdl &> /dev/null; then
        echo "  ✓ spotdl"
    else
        echo "  ✗ spotdl (failed)"
    fi
fi

echo ""
print_success "Ready to use!"
echo ""
print_step "Run dengan:"
echo "  ${GREEN}python main.py${NC}"
echo "  atau"
echo "  ${GREEN}./main.py${NC}"
echo ""

print_info "Tip: Program akan melakukan dependency verification saat pertama kali dijalankan"
echo ""