#!/usr/bin/env bash
#
# Installation script for jestsay
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
PREFIX="${PREFIX:-$HOME/.local}"
INSTALL_DIR="${INSTALL_DIR:-$PREFIX/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/jestsay"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Install jestsay to your system.

OPTIONS:
    -p, --prefix DIR      Installation prefix (default: ~/.local)
    -d, --data-dir DIR    Data directory (default: ~/.local/share/jestsay)
    -s, --system          Install system-wide (requires sudo)
    -f, --force           Overwrite existing installation
    -h, --help            Show this help message

ENVIRONMENT:
    PREFIX                Installation prefix
    INSTALL_DIR           Binary installation directory
    XDG_DATA_HOME         XDG data directory (used to determine data location)

EXAMPLES:
    # Install to ~/.local (default)
    $0

    # Install system-wide
    sudo $0 --system

    # Install to custom location
    PREFIX=/opt/jestsay $0
EOF
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is required but not installed"
        echo "Please install Python 3 and try again."
        exit 1
    fi
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--prefix)
                PREFIX="$2"
                INSTALL_DIR="$PREFIX/bin"
                shift 2
                ;;
            -d|--data-dir)
                DATA_DIR="$2"
                shift 2
                ;;
            -s|--system)
                PREFIX="/usr/local"
                INSTALL_DIR="/usr/local/bin"
                DATA_DIR="/usr/local/share/jestsay"
                shift
                ;;
            -f|--force)
                FORCE=1
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage >&2
                exit 1
                ;;
        esac
    done
}

confirm_system_install() {
    if [[ "$DATA_DIR" == /usr/local/share/* || "$INSTALL_DIR" == /usr/local/bin ]]; then
        if [[ $EUID -ne 0 ]]; then
            log_error "System-wide installation requires root privileges"
            echo "Run with sudo or use --prefix for user installation"
            exit 1
        fi
    fi
}

check_existing_installation() {
    if [[ -f "$INSTALL_DIR/jestsay" && "${FORCE:-0}" -ne 1 ]]; then
        log_warn "jestsay is already installed at $INSTALL_DIR/jestsay"
        echo "Use --force to overwrite"
        exit 0
    fi
}

create_directories() {
    log_info "Creating directories..."
    
    # Try to create directories, with fallback for permission issues
    if ! mkdir -p "$INSTALL_DIR" 2>/dev/null; then
        log_error "Cannot create $INSTALL_DIR"
        echo "Check permissions or use sudo for system-wide install"
        exit 1
    fi
    
    if ! mkdir -p "$DATA_DIR" 2>/dev/null; then
        log_error "Cannot create $DATA_DIR"
        exit 1
    fi
}

install_files() {
    log_info "Installing jestsay..."
    
    # Install main script (strip .py extension)
    cp "$SCRIPT_DIR/jestsay.py" "$INSTALL_DIR/jestsay"
    chmod +x "$INSTALL_DIR/jestsay"
    log_info "Installed binary to $INSTALL_DIR/jestsay"
    
    # Install data files
    cp "$SCRIPT_DIR/assets/quips.txt" "$DATA_DIR/"
    cp "$SCRIPT_DIR/assets/senior.txt" "$DATA_DIR/"
    cp "$SCRIPT_DIR/assets/commands.txt" "$DATA_DIR/"
    cp "$SCRIPT_DIR/assets/pixpop_bubble_long.ans" "$DATA_DIR/"
    cp "$SCRIPT_DIR/assets/pixpop_bubble_short.ans" "$DATA_DIR/"
    log_info "Installed data files to $DATA_DIR"
}

check_path() {
    local in_path=0
    case ":$PATH:" in
        *":$INSTALL_DIR:"*) in_path=1 ;;
    esac
    
    if [[ $in_path -eq 0 && "$INSTALL_DIR" != "/usr/local/bin" ]]; then
        log_warn "$INSTALL_DIR is not in your PATH"
        echo "Add the following to your shell configuration:"
        echo "    export PATH=\"$INSTALL_DIR:\$PATH\""
    fi
}

print_summary() {
    echo
    log_info "Installation complete!"
    echo
    echo "Binary: $INSTALL_DIR/jestsay"
    echo "Data:   $DATA_DIR"
    echo
    echo "Usage:"
    echo "    jestsay                  # Show random quip with jester"
    echo "    jestsay --quips /path/file   # Use custom quips file"
    echo "    jestsay --jester /path/art   # Use custom ANSI art"
    echo
}

main() {
    check_dependencies
    parse_args "$@"
    confirm_system_install
    check_existing_installation
    create_directories
    install_files
    check_path
    print_summary
}

main "$@"
