# Git Hooks Integration

> Automate quality checks on every commit and push. Never push broken code again.

---

## 🚀 Quick Setup

### One-Command Installation

```bash
boring hooks install
```

This installs:
- **pre-commit** - Runs STANDARD verification
- **pre-push** - Runs FULL verification

---

## 📋 Hook Levels

| Hook | Trigger | Verification Level | Bypass |
|------|---------|-------------------|--------|
| pre-commit | `git commit` | STANDARD | `--no-verify` |
| pre-push | `git push` | FULL | `--no-verify` |

### What Each Level Checks

**STANDARD (pre-commit)**:
- ✅ Syntax errors
- ✅ Linting (ruff)
- ✅ Formatting
- ✅ Import sorting

**FULL (pre-push)**:
- Everything in STANDARD, plus:
- ✅ Unit tests
- ✅ Security scan
- ✅ Dependency audit

---

## ⚙️ Configuration

### Custom Hook Config (.boring.toml)

```toml
[boring.hooks]
pre_commit_level = "STANDARD"    # BASIC|STANDARD|FULL
pre_push_level = "FULL"          # STANDARD|FULL
auto_fix = true                  # Auto-fix linting issues
timeout_seconds = 300            # Max hook runtime

[boring.hooks.bypass_patterns]
# Skip verification for these file patterns
skip_files = ["*.md", "docs/*", "*.txt"]
```

### Manual Hook Scripts

If you prefer manual control, create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
boring verify --level STANDARD
exit $?
```

And `.git/hooks/pre-push`:

```bash
#!/bin/bash
boring verify --level FULL
exit $?
```

Make them executable:
```bash
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

---

## 🛠️ Commands

### Install Hooks
```bash
boring hooks install
```

### Check Status
```bash
boring hooks status

# Output:
# pre-commit: ✅ Installed (STANDARD)
# pre-push: ✅ Installed (FULL)
```

### Uninstall Hooks
```bash
boring hooks uninstall
```

### Upgrade Hooks
```bash
boring hooks install --force
```

---

## 🔄 Workflow Example

```bash
# Make changes
vim src/main.py

# Stage changes
git add src/main.py

# Commit triggers pre-commit hook
git commit -m "feat: add user authentication"
# ✅ Syntax Check: Passed
# ✅ Linting: Passed (3 auto-fixed)
# ✅ Formatting: Passed
# [main abc1234] feat: add user authentication

# Push triggers pre-push hook
git push origin main
# ✅ Syntax Check: Passed
# ✅ Linting: Passed
# ✅ Tests: 42 passed
# ✅ Security: No issues
# Pushing to origin...
```

---

## ⚡ Performance Tips

### Use Incremental Mode

Hooks automatically use incremental verification:
- Only checks **staged files** (pre-commit)
- Only checks **commits to push** (pre-push)

### Skip Heavy Checks

For quick commits during development:

```toml
# .boring.toml
[boring.hooks]
pre_commit_level = "BASIC"  # Fast syntax check only
pre_push_level = "STANDARD" # Save FULL for CI
```

### Bypass When Needed

```bash
# Skip hooks (use sparingly!)
git commit --no-verify -m "WIP: work in progress"
git push --no-verify
```

---

## 🏢 Team Configuration

### Shared Hook Config

Commit `.boring.toml` to share with team:

```bash
git add .boring.toml
git commit -m "Add team quality standards"
```

### Recommended Team Settings

```toml
# .boring.toml
[boring.hooks]
pre_commit_level = "STANDARD"
pre_push_level = "FULL"
auto_fix = true

[boring.quality_gates]
min_coverage = 40
max_complexity = 15
```

---

## 🔧 Troubleshooting

### Hook Not Running

```bash
# Check if hooks are installed
ls -la .git/hooks/

# Reinstall
boring hooks install --force
```

### Hook Too Slow

```toml
# .boring.toml
[boring.hooks]
pre_commit_level = "BASIC"  # Faster
timeout_seconds = 60        # Add timeout
```

### Tests Failing in Hook

```bash
# Run verification manually to see details
boring verify --level FULL --verbose
```

---

## See Also

- [Quality Gates](../features/quality-gates.md) - CI/CD integration
- [Performance](../features/performance.md) - Optimization
- [Pro Tips](./pro-tips.md) - Best practices
