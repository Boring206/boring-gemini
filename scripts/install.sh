#!/bin/bash
# Boring Implementation Bootstrapper (Linux/macOS)
# "The One-Click Setup for Vibe Coders"

set -e  # Exit on error

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

log_step() {
    echo -e "\n${CYAN}🔮 $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Check Python
log_step "Checking Prerequisites..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Verify version is 3.x
    PY_VER=$(python --version 2>&1)
    if [[ $PY_VER == *"Python 3"* ]]; then
        PYTHON_CMD="python"
    else
        log_error "Python 3 is required. Found $PY_VER"
        exit 1
    fi
else
    log_error "Python 3 not found! Please install via 'brew install python' or your package manager."
    exit 1
fi

echo "Found $($PYTHON_CMD --version)"

# 2. Setup Venv
HOME_DIR="$HOME"
BORING_DIR="$HOME_DIR/.boring"
VENV_DIR="$BORING_DIR/env"

mkdir -p "$BORING_DIR"

log_step "Preparing Environment at $VENV_DIR..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Virtual Environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
else
    echo "Using existing Virtual Environment."
fi

# 3. Install/Update Boring
log_step "Installing Boring (Latest)..."
PIP_CMD="$VENV_DIR/bin/pip"

"$PIP_CMD" install --upgrade boring-aicoding --quiet
log_success "Boring installed successfully."

# 4. Launch Wizard
log_step "Launching Configuration Wizard..."
BORING_CMD="$VENV_DIR/bin/boring"

# Pass through to the wizard
exec "$BORING_CMD" wizard
