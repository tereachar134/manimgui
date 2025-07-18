#!/bin/bash

# Manim GUI Editor Installer
# For YouTube Channel: Dimensional Algebra
# GitHub: https://github.com/tereachar134/manimgui

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${RED}Error: Do not run this script as root.${NC}"
    exit 1
fi

# Check requirements
check_requirements() {
    local missing=()
    
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    if ! command -v pip3 &> /dev/null; then
        missing+=("pip3")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}Missing dependencies:${NC} ${missing[*]}"
        echo -e "Install them with:"
        echo -e "  Ubuntu/Debian: ${YELLOW}sudo apt install python3 python3-pip${NC}"
        echo -e "  macOS: ${YELLOW}brew install python${NC}"
        exit 1
    fi
}

# Main installation
install_manimgui() {
    echo -e "${GREEN}>>> Installing Manim GUI Editor${NC}"
    echo -e "${YELLOW}By Dimensional Algebra${NC}"
    echo -e "YouTube: https://www.youtube.com/@D-Algebra"
    echo -e "GitHub: https://github.com/tereachar134/manimgui\n"

    # Create installation directory
    INSTALL_DIR="$HOME/manimgui"
    echo -e "${GREEN}[1/4] Creating installation directory...${NC}"
    mkdir -p "$INSTALL_DIR" || {
        echo -e "${RED}Failed to create directory: $INSTALL_DIR${NC}"
        exit 1
    }

    # Download files
    echo -e "${GREEN}[2/4] Downloading files...${NC}"
    cd "$INSTALL_DIR" || exit 1
    
    # Download main script
    curl -sL -o "manimgui.py" "https://raw.githubusercontent.com/tereachar134/manimgui/main/manimgui.py" || {
        echo -e "${RED}Failed to download manimgui.py${NC}"
        exit 1
    }

    # Download requirements
    curl -sL -o "requirements.txt" "https://raw.githubusercontent.com/tereachar134/manimgui/main/requirements.txt" || {
        echo -e "${RED}Failed to download requirements.txt${NC}"
        exit 1
    }

    # Create virtual environment
    echo -e "${GREEN}[3/4] Setting up virtual environment...${NC}"
    python3 -m venv venv || {
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    }

    # Install dependencies
    echo -e "${GREEN}[4/4] Installing dependencies...${NC}"
    source venv/bin/activate
    pip install --upgrade pip wheel || {
        echo -e "${RED}Failed to upgrade pip${NC}"
        exit 1
    }
    
    pip install -r requirements.txt || {
        echo -e "${RED}Failed to install dependencies${NC}"
        exit 1
    }
    deactivate

    # Create desktop shortcut (Linux only)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "\n${GREEN}Creating desktop shortcut...${NC}"
        DESKTOP_FILE="$HOME/.local/share/applications/manimgui.desktop"
        cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Manim GUI Editor
Comment=GUI for Manim animations (Dimensional Algebra)
Exec=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/manimgui.py
Icon=applications-science
Terminal=false
Categories=Education;Science;Math;
EOL
        
        if command -v update-desktop-database &> /dev/null; then
            update-desktop-database ~/.local/share/applications
        fi
    fi

    # Installation complete
    echo -e "\n${GREEN}Installation complete!${NC}"
    echo -e "Run the GUI with:"
    echo -e "  ${YELLOW}cd $INSTALL_DIR && ./venv/bin/python manimgui.py${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "Or find 'Manim GUI Editor' in your applications menu"
    fi
}

# Run installation
check_requirements
install_manimgui
