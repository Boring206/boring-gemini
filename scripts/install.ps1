
# Boring Implementation Bootstrapper (Windows)
# "The One-Click Setup for Vibe Coders"

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n🔮 $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# 1. Check Python
Write-Step "Checking Prerequisites..."

if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command "py" -ErrorAction SilentlyContinue)) {
        Write-ErrorMsg "Python not found! Please install it via 'winget install Python.Python.3.12' or python.org"
        exit 1
    }
    $PYTHON_CMD = "py"
} else {
    $PYTHON_CMD = "python"
}

$PY_VER = & $PYTHON_CMD --version
Write-Host "Found $PY_VER" -ForegroundColor Gray

# 2. Setup Venv
$HOME_DIR = [System.Environment]::GetFolderPath("UserProfile")
$BORING_DIR = Join-Path $HOME_DIR ".boring"
$VENV_DIR = Join-Path $BORING_DIR "env"

if (-not (Test-Path $BORING_DIR)) {
    New-Item -ItemType Directory -Path $BORING_DIR -Force | Out-Null
}

Write-Step "Preparing Environment at $VENV_DIR..."

if (-not (Test-Path $VENV_DIR)) {
    Write-Host "Creating Virtual Environment..." -ForegroundColor Gray
    & $PYTHON_CMD -m venv $VENV_DIR
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to create venv."
        exit 1
    }
} else {
    Write-Host "Using existing Virtual Environment." -ForegroundColor Gray
}

# 3. Install/Update Boring
Write-Step "Installing Boring (Latest)..."
$PIP_CMD = Join-Path $VENV_DIR "Scripts\pip.exe"

& $PIP_CMD install --upgrade boring-aicoding --quiet
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to install boring-aicoding."
    exit 1
}
Write-Success "Boring installed successfully."

# 4. Launch Wizard
Write-Step "Launching Configuration Wizard..."
$BORING_CMD = Join-Path $VENV_DIR "Scripts\boring.exe"

# Pass through to the wizard
& $BORING_CMD wizard

Write-Host "`n✨ Setup Phase Complete. Happy Coding!" -ForegroundColor Magenta
