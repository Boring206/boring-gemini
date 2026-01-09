#!/usr/bin/env bash
# Quality Check Script for Boring-Gemini
# Run this before committing to ensure all quality gates pass

set -e  # Exit on error

echo "🔍 Running Quality Checks for Boring-Gemini..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

# Function to print section
print_section() {
    echo ""
    echo -e "${YELLOW}━━━ $1 ━━━${NC}"
}

# Check if in project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Please run this script from the project root${NC}"
    exit 1
fi

# Track overall status
OVERALL_STATUS=0

# =============================================================================
# TIER 1: Fast Checks
# =============================================================================
print_section "TIER 1: Linting & Formatting"

echo "Running Ruff linter..."
if ruff check src/ tests/ --output-format=github; then
    print_status 0 "Ruff linting passed"
else
    print_status 1 "Ruff linting failed"
    OVERALL_STATUS=1
fi

echo "Running Ruff formatter..."
if ruff format --check src/ tests/; then
    print_status 0 "Code formatting is correct"
else
    print_status 1 "Code formatting failed (run: ruff format src/ tests/)"
    OVERALL_STATUS=1
fi

echo "Running Mypy type checker..."
if mypy src/boring/ --config-file=pyproject.toml; then
    print_status 0 "Type checking passed"
else
    print_status 1 "Type checking failed"
    OVERALL_STATUS=1
fi

# =============================================================================
# TIER 2: Security Checks
# =============================================================================
print_section "TIER 2: Security Scanning"

echo "Running Bandit security scan..."
if bandit -r src/ -ll -ii; then
    print_status 0 "Security scan passed"
else
    print_status 1 "Security scan found issues"
    OVERALL_STATUS=1
fi

echo "Checking for dependency vulnerabilities..."
if pip-audit --desc; then
    print_status 0 "No dependency vulnerabilities found"
else
    print_status 1 "Dependency vulnerabilities detected"
    OVERALL_STATUS=1
fi

# =============================================================================
# TIER 3: Tests & Coverage
# =============================================================================
print_section "TIER 3: Tests & Code Quality"

echo "Checking code complexity..."
if radon cc src/boring/ -a -nb --total-average; then
    print_status 0 "Code complexity acceptable"
else
    print_status 1 "Code complexity too high"
    OVERALL_STATUS=1
fi

echo "Checking docstring coverage..."
if interrogate -vv --fail-under=80 src/boring/ --ignore-init-module --ignore-magic; then
    print_status 0 "Docstring coverage ≥ 80%"
else
    print_status 1 "Docstring coverage < 80%"
    OVERALL_STATUS=1
fi

echo "Running unit tests with coverage..."
if pytest tests/unit/ \
    --cov=src/boring \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v --tb=short; then
    print_status 0 "Tests passed with ≥ 80% coverage"
else
    print_status 1 "Tests failed or coverage < 80%"
    OVERALL_STATUS=1
fi

# =============================================================================
# Summary
# =============================================================================
print_section "Summary"

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ All quality checks passed!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "You can safely commit your changes:"
    echo "  git add ."
    echo "  git commit -m \"your message\""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Some quality checks failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Please fix the issues above before committing."
    echo ""
    echo "Quick fixes:"
    echo "  - Format code:  ruff format src/ tests/"
    echo "  - Fix linting:  ruff check src/ tests/ --fix"
    echo "  - Add docstrings to increase coverage"
    echo "  - Add tests to increase test coverage"
    exit 1
fi
