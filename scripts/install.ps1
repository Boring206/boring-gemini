
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

# 1. Check Prerequisites (Python & UV)
Write-Step "Checking Prerequisites..."

# Check for uv (The game changer)
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    $HAS_UV = $true
    Write-Host "🚀 UV detected! Engaging Turbo Mode..." -ForegroundColor Magenta
} else {
    $HAS_UV = $false
    Write-Host "🐢 UV not found. Using standard Python (Slower but reliable)..." -ForegroundColor Yellow
}

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
    if ($HAS_UV) {
        Write-Host "Creating Virtual Environment (UV)..." -ForegroundColor Gray
        uv venv $VENV_DIR
    } else {
        Write-Host "Creating Virtual Environment (Standard)..." -ForegroundColor Gray
        & $PYTHON_CMD -m venv $VENV_DIR
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to create venv."
        exit 1
    }
} else {
    Write-Host "Using existing Virtual Environment." -ForegroundColor Gray
}

# 3. Install/Update Boring
Write-Step "Checking for Updates..."

# Get installed version
$INSTALLED_VER = ""
$PIP_LIST_CMD = if ($HAS_UV) { 
    $VENV_PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"
    "uv pip list --python $VENV_PYTHON" 
} else { 
    $PIP_CMD = Join-Path $VENV_DIR "Scripts\pip.exe"
    "$PIP_CMD list" 
}

try {
    $INSTALLED_VER = iex "$PIP_LIST_CMD" | Select-String "boring-aicoding\s+([\d\.]+)" | ForEach-Object { $_.Matches.Groups[1].Value }
} catch {
    $INSTALLED_VER = ""
}

if ($INSTALLED_VER) {
    Write-Host "Currently installed: v$INSTALLED_VER" -ForegroundColor Gray
} else {
    Write-Host "New installation detected." -ForegroundColor Gray
}

# Simple check: If already installed, we could skip long update unless forced
# For Vibe Coder, let's always ensure we at least try --upgrade but quietly
# V11.2.7 'Brain Map Evolution' (Stabilized)

Write-Step "Syncing Boring (Latest)..."

if ($HAS_UV) {
    $VENV_PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"
    uv pip install --python $VENV_PYTHON --upgrade boring-aicoding --quiet
} else {
    $PIP_CMD = Join-Path $VENV_DIR "Scripts\pip.exe"
    & $PIP_CMD install --upgrade boring-aicoding --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to sync boring-aicoding."
    exit 1
}
Write-Success "Boring is up to date."

# 4. Launch Wizard
Write-Step "Launching Configuration Wizard..."
$BORING_CMD = Join-Path $VENV_DIR "Scripts\boring.exe"

# Pass through to the wizard
& $BORING_CMD wizard

Write-Host "`n✨ Setup Phase Complete. Happy Coding!" -ForegroundColor Magenta
