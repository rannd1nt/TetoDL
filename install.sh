#!/usr/bin/env bash
#
# TetoDL Linux Installer — Binary Edition
# Downloads pre-compiled TetoDL binary from GitHub Releases.
# No Python, Git, or ffmpeg required.
#
# Usage:
#   bash <(curl -sL "https://rannd1nt.github.io/TetoDL/install.sh")
#

set -e

# ─────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

# ─────────────────────────────────────────────────
# 1. Detect platform
# ─────────────────────────────────────────────────
UNAME_M=$(uname -m)
case "$UNAME_M" in
    x86_64|amd64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="aarch64" ;;
    *) echo -e "${RED}Unsupported architecture: $UNAME_M${NC}"; exit 1 ;;
esac

echo ""
echo -e "${CYAN}╔══════════════════════════════════╗${NC}"
echo -e "${CYAN}║       TetoDL Installer           ║${NC}"
echo -e "${CYAN}║         (Linux $ARCH)               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════╝${NC}"
echo ""

BINARY_NAME="tetodl-linux"

# ─────────────────────────────────────────────────
# 2. Install directory
# ─────────────────────────────────────────────────
INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

# ─────────────────────────────────────────────────
# 3. Fetch latest release
# ─────────────────────────────────────────────────
REPO="rannd1nt/tetodl"
API_URL="https://api.github.com/repos/${REPO}/releases/latest"

echo -e "${YELLOW}  Fetching latest release...${NC}"

if command -v curl &>/dev/null; then
    TAG=$(curl -sL "$API_URL" | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": "//; s/".*//')
elif command -v wget &>/dev/null; then
    TAG=$(wget -qO- "$API_URL" | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": "//; s/".*//')
else
    echo -e "${RED}  [!] curl or wget is required${NC}"
    exit 1
fi

if [ -z "$TAG" ]; then
    echo -e "${RED}  [!] Failed to fetch release info${NC}"
    echo -e "${YELLOW}  Download manually from: https://github.com/${REPO}/releases${NC}"
    exit 1
fi
echo -e "${GREEN}  Latest version: $TAG${NC}"

# ─────────────────────────────────────────────────
# 4. Download binary
# ─────────────────────────────────────────────────
DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${TAG}/${BINARY_NAME}"
OUTPUT_PATH="${INSTALL_DIR}/tetodl"

echo -e "${YELLOW}  Downloading ${BINARY_NAME} ...${NC}"
if command -v curl &>/dev/null; then
    curl -sL "$DOWNLOAD_URL" -o "$OUTPUT_PATH"
elif command -v wget &>/dev/null; then
    wget -q "$DOWNLOAD_URL" -O "$OUTPUT_PATH"
fi

chmod +x "$OUTPUT_PATH"

# ─────────────────────────────────────────────────
# 5. Add to PATH
# ─────────────────────────────────────────────────
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
        bash)
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "${HOME}/.bashrc"
            echo -e "${GREEN}  Added to PATH in ~/.bashrc${NC}"
            ;;
        zsh)
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "${HOME}/.zshrc"
            echo -e "${GREEN}  Added to PATH in ~/.zshrc${NC}"
            ;;
        fish)
            mkdir -p "${HOME}/.config/fish/conf.d"
            echo "set -gx PATH \$PATH $INSTALL_DIR" >> "${HOME}/.config/fish/conf.d/tetodl.fish"
            echo -e "${GREEN}  Added to PATH in ~/.config/fish/conf.d/tetodl.fish${NC}"
            ;;
        *)
            echo -e "${YELLOW}  Please add $INSTALL_DIR to your PATH manually${NC}"
            ;;
    esac
    export PATH="$PATH:$INSTALL_DIR"
fi

echo ""
echo -e "${GREEN}  TetoDL installed successfully!${NC}"
echo -e "  ${GRAY}Location: $OUTPUT_PATH${NC}"
echo ""
echo -e "${CYAN}  Run 'tetodl --help' to get started.${NC}"
echo -e "${CYAN}  (You may need to restart your terminal or run 'source ~/.bashrc')${NC}"

# ─────────────────────────────────────────────────
# 6. Post-install prompt
# ─────────────────────────────────────────────────
if [ "$TETODL_FORCE" != "1" ] && [ -t 0 ]; then
    echo ""
    read -r -p "  Run tetodl --help now? (Y/n) " run_now
    if [ "$run_now" != "n" ]; then
        "$OUTPUT_PATH" --help
    fi
fi
