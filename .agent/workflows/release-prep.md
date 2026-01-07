---
description: Release Preparation Checklist
---

# Release Preparation Checklist

Use this workflow before tagging a new release to ensure all documentation and configuration files are consistent.

## 1. Version Bump & Configuration

- [ ] **`pyproject.toml`**: Update `version = "x.y.z"`
- [ ] **`src/boring/__init__.py`**: Update version string (if applicable)

## 2. Documentation Updates

Check the following files for version numbers and new features:

- [ ] **`CHANGELOG.md`**: Add new section `## [x.y.z] - YYYY-MM-DD`
- [ ] **`README.md`**:
    - Update Badge: `[![Version](...-x.y.z-green.svg)]`
    - Check "New Features" section is up to date
- [ ] **`README_zh.md`**:
    - Update Badge: `[![Version](...-x.y.z-green.svg)]`
    - Check "New Features" section (translated)
- [ ] **`CONTRIBUTING.md`**: Check for any process changes
- [ ] **`GEMINI.md`**: Update context if architecture changed

## 3. Verification

- [ ] Run `boring verify --level FULL`
- [ ] Check `boring hooks status`

## 4. Git Operations

```bash
git add pyproject.toml CHANGELOG.md README.md README_zh.md
git commit -m "chore(release): Bump version to x.y.z"
git tag vx.y.z
git push origin main
git push origin vx.y.z
```
