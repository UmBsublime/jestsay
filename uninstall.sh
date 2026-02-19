#!/usr/bin/env bash
#
# Uninstallation script for jestsay
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

Uninstall jestsay from your system.

OPTIONS:
    -p, --prefix DIR      Installation prefix (default: ~/.local)
    -d, --data-dir DIR    Data directory (default: ~/.local/share/jestsay)
    -s, --system          Uninstall system-wide (requires sudo)
    -y, --yes             Skip confirmation
    -h, --help            Show this help message
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
            -y|--yes)
                SKIP_CONFIRM=1
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

confirm_uninstall() {
    if [[ "${SKIP_CONFIRM:-0}" -eq 1 ]]; then
        return 0
    fi
    
    echo "This will remove:"
    echo "  - $INSTALL_DIR/jestsay"
    echo "  - $DATA_DIR"
    echo
    read -p "Continue? [y/N] " response
    
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            echo "Aborted."
            exit 0
            ;;
    esac
}

remove_files() {
    if [[ -f "$INSTALL_DIR/jestsay" ]]; then
        rm "$INSTALL_DIR/jestsay"
        log_info "Removed $INSTALL_DIR/jestsay"
    else
        log_warn "Binary not found at $INSTALL_DIR/jestsay"
    fi
    
    if [[ -d "$DATA_DIR" ]]; then
        rm -rf "$DATA_DIR"
        log_info "Removed $DATA_DIR"
    else
        log_warn "Data directory not found at $DATA_DIR"
    fi
}

main() {
    parse_args "$@"
    confirm_uninstall
    remove_files
    log_info "Uninstallation complete!"
}

main "$@"
