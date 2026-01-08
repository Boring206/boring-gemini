---
description: Release Preparation Checklist (Turbo Mode)
---

// turbo-all
# Release Preparation Checklist

Use this workflow to let the AI Agent handle all release-related tasks automatically.

## 1. Version Bump & Configuration

- [ ] **Bump Version**: Detect current version in `pyproject.toml` and increment it (Patch by default).
- [ ] **Sync Config**: Update version strings in `src/boring/__init__.py`, `gemini-extension.json`, and `smithery.yaml`.
- [ ] **Asset Check**: Ensure `NOTICE` and `LICENSE` copyright years are current (if needed).

## 2. Documentation Updates

- [ ] **Changelog**: Analyze git logs since last tag and update `CHANGELOG.md`.
- [ ] **Bilingual Sync**: Cross-check all `docs/*.md` files with their `*_zh.md` counterparts to ensure feature parity.
- [ ] **English README**: Update Shields.io badges and "New Features" section in `README.md`.
- [ ] **Chinese README**: Synchronize translations and badges in `README_zh.md`.

## 3. Deep Verification (Strict CI)

- [ ] **Lint & Format**: Run `ruff check .` (Must pass with 0 errors).
- [ ] **Test Suite**: Run `pytest` (Must pass 100%).
- [ ] **Verify**: Run `boring verify --level FULL` (Ensure 100% pass).
- [ ] **Security**: Run `boring security-scan --scan-type all` to prevent secret leaks.
- [ ] **Docs**: Run `mkdocs build --strict` to ensure link integrity.
- [ ] **RAG**: Execute `boring rag-reindex --force` for a clean post-release index.

## 4. Automated Git Operations

- [ ] **Staging**: Add all modified version and documentation files.
- [ ] **Smart Commit**: Use `boring smart_commit` to generate a high-quality semantic commit message.
- [ ] **Tagging**: Create git tag `vx.y.z`.
- [ ] **Push**: Push branch and tags to origin.
