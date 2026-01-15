# Quality Gates - CI/CD Integration

> Built-in multi-tier verification gates for CI/CD pipelines. Fail fast, fail safe.

---

## 🚦 Gate Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Quality Gates                         │
├─────────────────────────────────────────────────────────┤
│  Tier 1: Lint & Format    ━━━━▶ Fast feedback (~10s)   │
│  Tier 2: Security Scan    ━━━━▶ Vulnerability check    │
│  Tier 3: Unit Tests       ━━━━▶ Coverage validation    │
│  Tier 4: Integration      ━━━━▶ Full system test       │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    ✅ Deploy or ❌ Block
```

---

## 📋 Tier Breakdown

### Tier 1: Lint & Format (~10 seconds)

```yaml
- name: Lint & Format
  run: |
    ruff check --output-format=github .
    ruff format --check .
```

**Tools**: Ruff (Python), ESLint (JS/TS), golangci-lint (Go)

### Tier 2: Security Scan (~30 seconds)

```yaml
- name: Security Scan
  run: |
    bandit -r src/ --severity-level medium
    pip-audit --strict
```

**Tools**: Bandit (SAST), pip-audit (dependencies), Safety

### Tier 3: Unit Tests (~2-5 minutes)

```yaml
- name: Unit Tests
  run: |
    pytest --cov=src --cov-fail-under=40
```

**Thresholds**: 40% minimum coverage by default

### Tier 4: Integration Tests (main branch only)

```yaml
- name: Integration Tests
  if: github.ref == 'refs/heads/main'
  run: |
    pytest tests/integration/ -v
```

---

## ⚙️ Configuration

### Project Settings (.boring.toml)

```toml
[boring.quality_gates]
min_coverage = 40           # Minimum test coverage %
max_complexity = 15         # Maximum cyclomatic complexity
max_file_lines = 500        # Maximum lines per file
max_function_lines = 50     # Maximum lines per function

[boring.linter_configs]
ruff_line_length = 100
eslint_max_warnings = 0

[boring.security]
bandit_severity = "medium"  # low|medium|high
dependency_scan = true
secret_scan = true
```

### GitHub Actions (.github/workflows/quality-gates.yml)

```yaml
name: Quality Gates

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff
      - run: ruff check --output-format=github .
      - run: ruff format --check .

  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit pip-audit
      - run: bandit -r src/ -ll
      - run: pip-audit

  test:
    runs-on: ubuntu-latest
    needs: security
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src --cov-fail-under=40

  integration:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -v
```

---

## 🛠️ MCP Tool Integration

### Verify Command

```bash
# Quick syntax check
boring verify --level BASIC

# Standard with linting
boring verify --level STANDARD --incremental

# Full with tests
boring verify --level FULL

# AI semantic review
boring verify --level SEMANTIC
```

#### ✨ Vibe Coder CLI
```bash
# Natural language verification
boring-route "verify my code"
# 🎯 boring_verify (STANDARD)

boring-route "do a full check"
# 🎯 boring_verify (FULL)
```

### Background Task

```python
# Run verification in background
task_id = boring_task(
    action="start",
    task_type="verify",
    level="FULL"
)

# Check status
boring_task(action="status", task_id=task_id)
```

---

## 🔄 Git Hooks

### Installation

```bash
# Install all hooks
boring hooks install

# Check status
boring hooks status

# Uninstall
boring hooks uninstall
```

### Hook Levels

| Hook | Trigger | Level |
|------|---------|-------|
| pre-commit | Every commit | STANDARD |
| pre-push | Every push | FULL |
| quick-check | Save (optional) | BASIC |

---

## 📊 Quality Trend

### View History

```bash
boring_quality_trend --days 30
```

### Fail on Regression

```python
# In CI
if current_score < historical_average - 0.5:
    fail("Quality regression detected")
```

---

## 🏢 Enterprise Patterns

### Branch Protection Rules

```yaml
# GitHub branch protection
required_status_checks:
  strict: true
  checks:
    - lint
    - security
    - test
```

### Multi-Environment Gates

```yaml
# Different gates per environment
staging:
  min_coverage: 60
  security_level: high

production:
  min_coverage: 80
  security_level: critical
  require_integration: true
```

---

## See Also

- [Performance](./performance.md) - Optimization
- [Git Hooks](../guides/git-hooks.md) - Local hooks
- [Pro Tips](../guides/pro-tips.md) - Best practices
