# Quality Check Script for Boring-Gemini
# Windows PowerShell version
# Run this before committing to ensure all quality gates pass

$ErrorActionPreference = "Continue"

Write-Host "🔍 Running Quality Checks for Boring-Gemini..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check if in project root
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Please run this script from the project root" -ForegroundColor Red
    exit 1
}

# Track overall status
$script:OVERALL_STATUS = 0

function Print-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "━━━ $Title ━━━" -ForegroundColor Yellow
}

function Print-Status {
    param(
        [bool]$Success,
        [string]$Message
    )
    if ($Success) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
        $script:OVERALL_STATUS = 1
    }
}

# =============================================================================
# TIER 1: Fast Checks
# =============================================================================
Print-Section "TIER 1: Linting & Formatting"

Write-Host "Running version consistency check..."
$versionCheck = python scripts/verify_version.py
Print-Status ($LASTEXITCODE -eq 0) "Version consistency"

Write-Host "Running Ruff linter..."
$ruffCheck = ruff check src/ tests/ --output-format=github
Print-Status ($LASTEXITCODE -eq 0) "Ruff linting"

Write-Host "Running Ruff formatter..."
$ruffFormat = ruff format --check src/ tests/
Print-Status ($LASTEXITCODE -eq 0) "Code formatting"

Write-Host "Running Mypy type checker..."
$mypyCheck = mypy src/boring/ --config-file=pyproject.toml
Print-Status ($LASTEXITCODE -eq 0) "Type checking"

# =============================================================================
# TIER 2: Security Checks
# =============================================================================
Print-Section "TIER 2: Security Scanning"

Write-Host "Running Bandit security scan..."
$banditCheck = bandit -r src/ -ll -ii
Print-Status ($LASTEXITCODE -eq 0) "Security scan"

Write-Host "Checking for dependency vulnerabilities..."
$pipAudit = pip-audit --desc
Print-Status ($LASTEXITCODE -eq 0) "Dependency vulnerabilities"

# =============================================================================
# TIER 3: Tests & Coverage
# =============================================================================
Print-Section "TIER 3: Tests & Code Quality"

Write-Host "Checking code complexity..."
$radonCheck = radon cc src/boring/ -a -nb --total-average
Print-Status ($LASTEXITCODE -eq 0) "Code complexity"

Write-Host "Checking docstring coverage..."
$interrogate = interrogate -vv --fail-under=80 src/boring/ --ignore-init-module --ignore-magic
Print-Status ($LASTEXITCODE -eq 0) "Docstring coverage"

Write-Host "Running unit tests with coverage..."
$pytest = pytest tests/unit/ `
    --cov=src/boring `
    --cov-report=term-missing `
    --cov-fail-under=49 `
    -v --tb=short
Print-Status ($LASTEXITCODE -eq 0) "Unit tests and coverage"

# =============================================================================
# Summary
# =============================================================================
Print-Section "Summary"

if ($OVERALL_STATUS -eq 0) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "✅ All quality checks passed!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can safely commit your changes:"
    Write-Host "  git add ."
    Write-Host "  git commit -m `"your message`""
    exit 0
} else {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
    Write-Host "❌ Some quality checks failed" -ForegroundColor Red
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the issues above before committing."
    Write-Host ""
    Write-Host "Quick fixes:"
    Write-Host "  - Format code:  ruff format src/ tests/"
    Write-Host "  - Fix linting:  ruff check src/ tests/ --fix"
    Write-Host "  - Add docstrings to increase coverage"
    Write-Host "  - Add tests to increase test coverage"
    exit 1
}
