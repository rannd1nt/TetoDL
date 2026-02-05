#!/bin/bash
# TetoDL - Universal Installer
# by rannd1nt

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    clear
    echo -e "${RED}[FATAL ERROR] RESTRICTED ENVIRONMENT DETECTED${NC}"
    echo "-----------------------------------------------------"
    echo -e "Current Environment : ${YELLOW}$OSTYPE (Windows Native)${NC}"
    echo -e "Required Environment: ${GREEN}Linux (WSL2), Android (Termux), or macOS${NC}"
    echo ""
    echo "REASON:"
    echo "This script requires a genuine Linux kernel and package manager"
    echo "(apt/pacman/dnf) which are missing in Git Bash/MinGW."
    echo ""
    echo "SOLUTION:"
    echo "1. Enable WSL2 on Windows."
    echo "2. Install Ubuntu from Microsoft Store."
    echo "3. Run this script inside the Ubuntu terminal."
    echo "-----------------------------------------------------"
    exit 1
fi

# Global Variables
IS_TERMUX=false
IS_LINUX=false
PYTHON_CMD="python"
PIP_CMD="pip"
PKG_MANAGER=""
INSTALL_CMD=""
VENV_DIR=".venv"

print_header() {
    clear
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${BLUE}         TetoDL - Dependency Auto Installer       ${NC}"
    echo -e "${BLUE}==================================================${NC}"
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

detect_environment() {
    if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
        IS_TERMUX=true
        print_info "Platform: Android (Termux)"
        return
    fi

    IS_LINUX=true
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        INSTALL_CMD="sudo apt install -y"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
        print_info "Platform: Linux / WSL (Debian/Ubuntu)"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --needed --noconfirm"
        print_info "Platform: Linux (Arch/Manjaro)"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="sudo dnf install -y"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
        print_info "Platform: Linux (Fedora/RHEL)"
    else
        clear
        echo -e "${RED}[FATAL ERROR] UNSUPPORTED OPERATING SYSTEM${NC}"
        echo "-----------------------------------------------------"
        echo -e "Detected OS Type : ${YELLOW}$OSTYPE${NC}"
        echo "Missing Tools    : apt, pacman, or dnf"
        echo ""
        echo "This installer only supports:"
        echo "1. Debian/Ubuntu based (inc. WSL2)"
        echo "2. Arch Linux based"
        echo "3. Fedora/RHEL based"
        echo "4. Android (Termux)"
        echo "-----------------------------------------------------"
        exit 1
    fi
}

# Parse arguments
LITE_MODE=false
if [[ "$1" == "--lite" ]]; then
    LITE_MODE=true
fi

# ==== MAIN EXECUTION START ====
print_header
detect_environment

# Step 1: System Update & Dependencies
print_step "Step 1/5: Checking System Dependencies..."

if [ "$IS_TERMUX" = true ]; then
    print_info "Updating Termux repositories..."
    pkg update -y > /dev/null 2>&1
    DEPENDENCIES="python ffmpeg termux-api termux-tools"
    if [ "$LITE_MODE" = false ]; then
        DEPENDENCIES="$DEPENDENCIES rust binutils build-essential git"
    fi
    pkg install -y $DEPENDENCIES

elif [ "$IS_LINUX" = true ]; then
    if [ "$PKG_MANAGER" == "apt" ]; then
        SYS_DEPS="python3-pip python3-venv ffmpeg build-essential"
        print_info "Requesting SUDO access for system dependencies..."
        $INSTALL_CMD $SYS_DEPS
    elif [ "$PKG_MANAGER" == "pacman" ]; then
        SYS_DEPS="python-pip ffmpeg base-devel"
        print_info "Requesting SUDO access for system dependencies..."
        $INSTALL_CMD $SYS_DEPS
    elif [ "$PKG_MANAGER" == "dnf" ]; then
        SYS_DEPS="python3-pip ffmpeg gcc"
        print_info "Requesting SUDO access for system dependencies..."
        $INSTALL_CMD $SYS_DEPS
    fi
fi

print_success "System dependencies ready."

# Step 2: Python Environment (VENV)
print_step "Step 2/5: Preparing Python Environment..."

if [ "$IS_LINUX" = true ]; then
    # -- LINUX: MANDATORY VENV --
    print_info "Linux detected: Creating Virtual Environment (PEP 668 Compliant)..."

    # Clean old venv if broken
    if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/python" ]; then
        rm -rf "$VENV_DIR"
    fi

    if [ ! -d "$VENV_DIR" ]; then
        $PYTHON_CMD -m venv "$VENV_DIR"
        print_success "Virtual Environment created at ./$VENV_DIR"
    else
        print_info "Using existing Virtual Environment."
    fi

    # Override CMD to use VENV binary
    PYTHON_EXEC="./$VENV_DIR/bin/python"
    PIP_EXEC="./$VENV_DIR/bin/pip"

    # Update pip inside venv
    $PIP_EXEC install --upgrade pip > /dev/null 2>&1

else
    # -- TERMUX: GLOBAL --
    print_info "Termux detected: Using Global Python Environment"
    PYTHON_EXEC=$PYTHON_CMD
    PIP_EXEC="$PYTHON_CMD -m pip"

    $PIP_EXEC install --upgrade pip > /dev/null 2>&1 || print_info "Pip upgrade skipped (minor error)"
fi

# Step 3: Install Project Requirements
print_step "Step 3/5: Installing Python Libraries..."

if [ "$LITE_MODE" = true ]; then
    print_info "MODE: LITE (No Spotify)"
    if $PIP_EXEC install -r requirements-lite.txt; then
        print_success "Dependencies installed."
    else
        print_error "Failed to install dependencies."
        exit 1
    fi
else
    print_info "MODE: FULL (With Spotify)"
    print_info "Compiling and installing dependencies..."
    if $PIP_EXEC install -r requirements.txt; then
        print_success "Dependencies installed."
    else
        print_error "Failed to install dependencies."
        print_info "Tip: Try checking requirements.txt versions or use --lite mode."
        exit 1
    fi
fi

# Step 4: Storage & Config
print_step "Step 4/5: Finalizing Configuration..."

if [ "$IS_TERMUX" = true ]; then
    termux-setup-storage
    sleep 2
else
    mkdir -p "$HOME/Downloads/TetoDL"
fi

# Step 5: Create Launcher (Run Script)
print_step "Step 5/5: Finalizing Setup..."

chmod +x main.py
INSTALL_DIR=$(pwd)

if [ "$IS_LINUX" = true ]; then
    cat > run.sh <<EOL
#!/bin/bash
cd "$INSTALL_DIR"
./$VENV_DIR/bin/python main.py "\$@"
EOL
    chmod +x run.sh
    print_success "Created launcher: ./run.sh"

    # --- B. Bikin Global Shortcut ---
    USER_BIN="$HOME/.local/bin"
    TARGET_LINK="$USER_BIN/tetodl"

    if [ ! -d "$USER_BIN" ]; then mkdir -p "$USER_BIN"; fi
    if [ -f "$TARGET_LINK" ]; then rm -f "$TARGET_LINK"; fi
    
    ln -sf "$INSTALL_DIR/run.sh" "$TARGET_LINK"
    print_success "Global command set: 'tetodl'"

    SHELL_CONFIG="$HOME/.bashrc"
    if [ -n "$ZSH_VERSION" ]; then SHELL_CONFIG="$HOME/.zshrc"; fi

    if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
        print_info "Configuring PATH automatically..."
        
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_CONFIG"; then
            echo "" >> "$SHELL_CONFIG"
            echo '# Added by TetoDL Installer' >> "$SHELL_CONFIG"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
            print_success "Added configuration to $SHELL_CONFIG"
        else
            print_info "Configuration already exists in $SHELL_CONFIG"
        fi
        
        NEED_RESTART=true
    else
        NEED_RESTART=false
    fi

    # Create Uninstaller Script
    cat > uninstall.sh <<EOL
#!/bin/bash
echo "Uninstalling TetoDL..."
if [ -f "$TARGET_LINK" ]; then
    rm "$TARGET_LINK"
    echo "✓ Global shortcut removed"
fi

if [ -d "$INSTALL_DIR/$VENV_DIR" ]; then
    rm -rf "$INSTALL_DIR/$VENV_DIR"
    echo "✓ Virtual environment removed"
fi

if [ -f "$INSTALL_DIR/run.sh" ]; then
    rm "$INSTALL_DIR/run.sh"
    echo "✓ Launcher script removed"
fi

rm -f "$INSTALL_DIR/uninstall.sh"
echo "✓ Cleanup complete."
echo "You can now delete this folder manually."
EOL
    chmod +x uninstall.sh
    print_success "Created uninstaller: ./uninstall.sh"
    
    if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
        echo ""
        print_info "WARNING: $USER_BIN is not in your PATH."
        echo "Add this to your .bashrc / .zshrc to use 'tetodl' command everywhere:"
        echo -e "${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi
fi

# Summary
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}          INSTALLATION COMPLETE!         ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

if [ "$IS_LINUX" = true ]; then
    if [ "$NEED_RESTART" = true ]; then
        echo -e "${YELLOW}[IMPORTANT] Setup is done, but one last step needed:${NC}"
        echo "Because we updated your shell configuration, please either:"
        echo "1. Close and reopen this terminal, OR"
        echo -e "2. Run this command now: ${GREEN}source $SHELL_CONFIG${NC}"
        echo ""
    else
        echo "You can now run TetoDL from anywhere!"
    fi
    echo -e "Try command: ${GREEN}tetodl${NC}"
else
    echo -e "Run with: ${GREEN}./main.py${NC}"
fi