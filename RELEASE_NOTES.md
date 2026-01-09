# Release Notes: Boring v10.28.1

## � PyPI Hotfix & CI Stability
This release resolves a critical version conflict on PyPI and integrates major stability improvements for the CI/CD pipeline.

### 🏠 Key Improvements (since v10.28.0)
- **PyPI Hotfix**: Synchronized local and remote versions to `10.28.1` to ensure successful deployment.
- **CI Stability**: Resolved `AttributeError` in MCP instance tests and fixed `publish.yml` dependency order.
- **Test Coverage Boost**: Added comprehensive unit test suites for `AgentProtocol`, `WorkspaceManager`, and `Core MCP Tools`, increasing project coverage.
- **Linting & Formatting**: 100% compliance with `ruff` check and `ruff format` policies.

---

## 🚀 Version 10.28.0 Features (Included)
This version introduces the **"The Diet Update"**, focusing on modularity and speed.

### 🏠 Architecture & Performance
- **Startup Latency**: Optimized CLI startup to ~575ms via lazy loading.
- **Dependency Separation**: Split heavy dependencies (ChromaDB, Torch, Streamlit) into optional extras.
    - `pip install boring-aicoding[vector]`
    - `pip install boring-aicoding[gui]`
- **Structural Refactoring**: Reorganized internal modules into `core`, `services`, `cli`, and `tools`.

### 🛠️ Fixed Issues
- Corrected version reporting in CLI `version` command and synced across `smithery.yaml`.
- Resolved import sorting and whitespace violations project-wide.

---
*Proudly built with AI-Human Collaboration.*
