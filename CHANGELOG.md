# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.1.0] - 2026-01-02

### Added
- **Smithery Deployment**: `smithery.yaml` configuration for one-click installation across all IDEs
- **Docker Support**: Multi-stage `Dockerfile` with python:3.9-slim, non-root user, and health checks
- **Granular MCP Tools**:
  - `boring_apply_patch`: Single-file search/replace operations
  - `boring_verify_file`: Single-file syntax and lint verification
  - `boring_extract_patches`: Extract and apply patches from AI output
  - `boring_done`: Clean exit mechanism for agent completion signaling
- **Universal IDE Compatibility**: Works with Cursor, Claude Desktop, VS Code, and any MCP-compatible client
- **Verified Platforms**: Gemini CLI, Antigravity, Cursor officially tested and verified
- **Text-to-Tool Extraction**: CLI mode now parses `# File:` and `SEARCH_REPLACE` blocks automatically

### Changed
- **README.md**: Complete refactor for clarity; mandatory config block with context7/notebooklm
- **MCP Mode Backend**: Disabled nested CLI spawning to prevent hangs (use SDK or Delegation)
- **SpecKit Workflows**: Added autonomous mode instruction injection for CLI execution
- **Version bump**: 4.1.0 → 5.1.0

### Fixed
- **Critical**: `run_boring` hanging in Gemini CLI due to nested process spawning
- **Critical**: `speckit_*` tools refusing execution in non-interactive CLI mode
- `boring_health_check` failing when API key not set but CLI available

### Documentation
- Smithery installation guide with complete JSON config example
- Docker build and run commands
- Docker Compose example configuration

## [4.1.0] - 2025-12-31

### Added
- **State Pattern Architecture**: Complete `AgentLoop` refactoring into state machine
  - `ThinkingState`: Handles Gemini API generation with function calling
  - `PatchingState`: Processes `write_file` and `search_replace` function calls
  - `VerifyingState`: Runs syntax, lint, and test verification
  - `RecoveryState`: Contextual error recovery with retry logic
- **New CLI Flag**: `--experimental / -x` to opt-in to State Pattern architecture
- **Integration Test Suite**: Full simulation tests with only Gemini API mocked
- **Windows Path Compatibility**: Fixed path validation for Windows temp directories

### Changed
- **Response Analyzer**: Prioritizes function call results over text-based heuristics
- **Import Structure**: Direct imports from modules instead of `core.py` re-exports
- **BackupManager**: Now accepts configurable `project_root` parameter

### Deprecated
- `core.py` re-exports: Use direct imports from `.circuit`, `.logger`, `.limiter`
- `extract_file_blocks()`: Use `process_structured_calls()` instead

### Fixed
- `test_response_analyzer.py` ImportError for removed constants
- Windows path case-sensitivity in security validation
- Path containment checks for temp directories

## [4.0.0] - 2025-12-31

### Added
- **Function Calling**: Native Gemini function calling with `write_file`, `search_replace`, `report_status` tools
- **Diff Patching**: `diff_patcher.py` module for targeted SEARCH_REPLACE edits (5x token reduction)
- **Vector Memory**: `vector_memory.py` with ChromaDB for semantic experience retrieval (optional)
- **Interactions API**: `interactions_client.py` for stateful conversations and MCP support (experimental)
- **Security Module**: `security.py` with file path whitelist, sensitive data masking, input sanitization
- **Abstract Interfaces**: `interfaces.py` with `LLMClient`, `MemoryProvider`, `CodeVerifierBase` for DI
- **Test Coverage**: 90+ tests including `test_verification.py`, `test_security.py`, `test_diff_patcher.py`
- **V4.0 Feature Flags**: `USE_FUNCTION_CALLING`, `USE_VECTOR_MEMORY`, `USE_INTERACTIONS_API`, `USE_DIFF_PATCHING`
- **New Models Support**: gemini-3-flash-preview, gemini-3-pro-preview, gemini-2.5-*

### Changed
- Updated `SYSTEM_INSTRUCTION` to teach AI function calling and diff patching
- Integrated security whitelist validation into `file_patcher.py`
- Updated `config.py` with `SUPPORTED_MODELS` list and feature flags
- Version bumped to 4.0.0

### Security
- Path traversal prevention with whitelist validation
- Blocked directories (.git, node_modules, __pycache__)
- Blocked sensitive filenames (.env, secrets.json)
- Sensitive data masking in logs (API keys, passwords, tokens)

## [3.0.5] - 2025-12-30

### Added
- Pytest testing framework with comprehensive test coverage for `core.py` and `response_analyzer.py`
- Tenacity retry decorator on `_execute_gemini_cli` with exponential backoff (3 retries)
- Ruff linter configuration in `pyproject.toml`
- Mypy type checker configuration in `pyproject.toml`
- `_find_gemini_cli()` function for automatic CLI discovery (local node_modules first, then global PATH)
- CHANGELOG.md file for tracking changes

### Changed
- Migrated from BATS to pytest testing framework
- Changed CLI argument passing to use stdin piping (prevents E2BIG errors on large prompts)
- Rewrote `GEMINI.md` to accurately describe Python architecture

### Removed
- `CLAUDE.md` (legacy Claude Code documentation)
- BATS test files (`tests/unit/*.bats`, `tests/integration/*.bats`, `tests/helpers/*.bash`)
- Unused `tempfile` import from `main.py`

### Fixed
- Fixed potential E2BIG error when passing large prompts as CLI arguments
- Fixed hardcoded Gemini CLI path (now discovers local and global installations)

## [0.1.0] - 2025-12-30

### Added
- Initial Python implementation of Boring autonomous AI development loop
- Typer CLI with Rich console output
- Rate limiting with configurable calls per hour
- Circuit breaker pattern to prevent infinite loops
- Intelligent exit detection based on completion signals
- Live monitoring dashboard (`boring-monitor`)
- Project setup commands (`boring-setup`, `boring-import`)
- Response analyzer for parsing Gemini output
