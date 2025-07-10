#!/bin/bash
# install.sh

set -e

REPO_URL="https://github.com/relaycli/relay"
PACKAGE_NAME="relaycli"
MIN_PYTHON_VERSION="3.10"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi
    
    local python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local required_version="3.10"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
        error "Python ${MIN_PYTHON_VERSION}+ is required, but ${python_version} is installed"
    fi
    
    log "Python ${python_version} detected ✓"
}

# Install UV if not present
install_uv() {
    if command -v uv &> /dev/null; then
        log "UV already installed ✓"
        return
    fi
    
    log "Installing UV package manager..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
        if command -v curl &> /dev/null; then
            curl -LsSf https://astral.sh/uv/install.sh | sh
        elif command -v wget &> /dev/null; then
            wget -qO- https://astral.sh/uv/install.sh | sh
        elif command -v pip &> /dev/null; then
            pip install uv
        else
            error "Neither curl nor wget is available. Please install one of them first."
        fi
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    if ! command -v uv &> /dev/null; then
        error "Failed to install UV"
    fi
    
    log "UV installed successfully ✓"
}

# Install the package
install_package() {
    log "Installing ${PACKAGE_NAME}..."
    
    if ! uv pip install --system "${PACKAGE_NAME}"; then
        error "Failed to install ${PACKAGE_NAME}"
    fi
    
    log "${PACKAGE_NAME} installed successfully ✓"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    if ! command -v relay &> /dev/null; then
        error "relay command not found in PATH"
    fi
    
    if ! relay --help &> /dev/null; then
        error "relay command failed to run"
    fi
    
    log "Installation verified ✓"
}

main() {
    log "Installing Relay CLI..."
    
    check_python
    install_uv
    install_package
    verify_installation
    
    log ""
    log "🎉 Relay CLI installed successfully!"
    log "Run 'relay account add' to get started"
    log "Documentation: https://docs.relaycli.com"
}

main "$@"