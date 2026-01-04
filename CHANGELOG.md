# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [10.5.0] - 2026-01-04

### Changed - Pure CLI Mode Architecture
- **`run_boring`**: Now returns CLI command template instead of executing `StatefulAgentLoop` internally (which fails in MCP mode)
- **`boring_multi_agent`**: Returns multi-step CLI workflow template instead of internal `asyncio.run()` calls
- **`boring_agent_plan/review`**: Returns CLI command templates for external execution
- **`speckit_*` tools**: Return `WORKFLOW_TEMPLATE` status with suggested prompts and CLI commands
- **`boring_auto_fix`**: Executes real verification but returns CLI commands for fixes (removed broken mock function)

### Fixed
- **Critical**: "event loop already running" error in `boring_multi_agent` and agent tools - removed all internal `asyncio` calls
- **Critical**: `boring_auto_fix` stalling issue - was using mock function that never actually fixed anything
- **API Connection Failures**: Tools no longer attempt internal API calls that fail in MCP environment
- **`boring_suggest_next`**: Improved context detection - now checks multiple code locations (src/, lib/, root), detects spec/plan files, git activity, and provides accurate code/test counts
- **Windows RAG Search**: Fixed "index is empty" issue on Windows - normalized all file paths to use forward slashes for cross-platform consistency
- **`boring_evaluate` 0/5 Score**: Added diagnostic error reporting when evaluation fails, explaining possible causes and suggesting interactive mode

### Added
- Clear documentation about MCP mode limitations in all affected tools
- `WORKFLOW_TEMPLATE` status type for tools that return execution templates
- `cli_command` and `suggested_prompt` fields in tool responses for easy external execution
- Enhanced pattern matching in `PatternMiner` with support for planning, debugging, and code review states
- **NEW: `boring_rag_status`**: Health check tool for RAG index diagnostics
- **NEW: Multi-dimensional evaluation**: `boring_evaluate` now returns scores for Cleanliness, Security, Performance, and Maintainability

### Documentation
- Updated README with Pure CLI Mode architecture explanation
- Added "⚠️ V10.5 重大變更" section explaining the new behavior
- Updated tool descriptions to reflect actual MCP mode behavior

## [10.1.0] - 2026-01-04

### Added
- **Modular LLM Architecture**: Refactored monolithic `gemini_client.py` into modular `src/boring/llm/` package (SDK, Tools, Executor).
- **Async RAG Retrieval**: Added `retrieve_async()` to `RAGRetriever` for non-blocking high-performance queries.
- **Integration Test Suite**: Added comprehensive integration tests (`tests/integration/test_mcp_startup.py`).

### Changed
- **CoderAgent Upgrade**: 
  - Full support for `<<<<<<< SEARCH ... >>>>>>> REPLACE` blocks.
  - Patch-type file application logic for targeted edits.
  - Integrated ShadowMode directly into write operations.
- **Security Hardening**: `AgentOrchestrator` and `CoderAgent` now enforce ShadowGuard checks before critical write operations.
- **Quality Standards**: Increased test coverage threshold from 28% to 60%.

### Removed
- **Legacy Components**: Cleaned up deprecated code in `gemini_client.py` (now a lightweight re-export facade).

## [10.0.0] - 2026-01-04

### Added

#### RAG Memory System (Vector + Graph)
- **Vector-based Code Search**: Semantic search across entire codebase via ChromaDB
- **AST-based Code Indexer**: Parses Python files into semantic chunks (functions, classes) with dependency tracking
- **Graph RAG**: Bidirectional dependency graph with `get_impact_zone()` for smart context expansion
- **New MCP Tools**: `boring_rag_index`, `boring_rag_search`, `boring_rag_context`, `boring_rag_expand`

#### Multi-Agent Orchestration
- **Specialized Agents**:
  - `ArchitectAgent`: Planning & design specialist (no code writing)
  - `CoderAgent`: Implementation specialist following the plan
  - `ReviewerAgent`: "Devil's Advocate" security & bug reviewer
- **Orchestrator**: Automated "Plan → Code → Review" loop with human approval checkpoints
- **New MCP Tools**: `boring_multi_agent`, `boring_agent_plan`, `boring_agent_review`

#### Shadow Mode (Human-in-the-Loop)
- **Protection Levels**: `DISABLED`, `ENABLED` (default), `STRICT`
- **Smart Filtering**: Auto-approves read ops; blocks HIGH/CRITICAL ops (deletion, secrets, config changes)
- **Async Approval**: Pending operations queue for non-blocking review
- **New MCP Tools**: `boring_shadow_status`, `boring_shadow_approve`, `boring_shadow_reject`, `boring_shadow_mode`

## [9.1.0] - 2026-01-04

### Added
- **Modular MCP Package**: Complete refactor of `mcp_server.py` into `src/boring/mcp/` package
  - `tools/core.py`: Core agent tools (run_boring, health_check, quickstart, status, done)
  - `tools/verification.py`: Code verification tools
  - `tools/speckit.py`: SpecKit workflow tools
  - `tools/git.py`: Git hooks management
  - `tools/patching.py`: Code patching tools
  - `tools/workflow.py`: Workflow evolution tools
  - `tools/knowledge.py`: Brain/memory tools
  - `tools/integration.py`: Extension setup
  - `tools/evaluation.py`: LLM Judge evaluation
- **Unit Tests for MCP**: Test suite in `tests/unit/mcp/` covering core MCP functionality
- **Plugin System Documentation**: Added comprehensive plugin guide to README

### Changed
- Modular architecture improves maintainability and testability
- Updated `.gitignore` with additional temporary file patterns

### Fixed
- Project cleanup: removed stale files and directories

## [9.0.0] - 2026-01-03

### Added
- **Plugin System**: Extensible tool registration without modifying core code
  - `boring_list_plugins`: List all registered plugins
  - `boring_run_plugin`: Execute a plugin by name
  - `boring_reload_plugins`: Hot-reload changed plugins
  - Decorator-based API: `@plugin(name, description)`
  - Plugin directories: `~/.boring/plugins/` and `.boring_plugins/`
- **Multi-Project Workspace**: Manage multiple projects simultaneously
  - `boring_workspace_add`: Register a project
  - `boring_workspace_remove`: Unregister a project
  - `boring_workspace_list`: List all projects with tags
  - `boring_workspace_switch`: Switch active project context
- **Auto-Fix Pipeline**: Automated verify-and-fix loop
  - `boring_auto_fix`: Runs up to 3 iterations of verify → fix → verify
  - `AutoFixPipeline` class with progress tracking
- **Pattern Mining**: Context-aware suggestions based on project state
  - `boring_suggest_next`: AI-powered next-step recommendations
  - `PatternMiner` with 5 default patterns and custom pattern support
- **Streaming Progress**: Real-time progress reporting
  - `boring_get_progress`: Poll task progress
  - `ProgressReporter` with file output for IDE polling
  - `StreamingTaskManager` for concurrent task tracking

### New Files
- `src/boring/plugins/__init__.py`, `loader.py`
- `src/boring/streaming.py`
- `src/boring/workspace.py`
- `src/boring/auto_fix.py`
- `src/boring/pattern_mining.py`
- `src/boring/mcp/v9_tools.py`

## [8.0.0] - 2026-01-03

### Added
- **Audit Logging**: Structured JSONL logging for all MCP tool invocations
  - `AuditLogger` class with singleton pattern
  - `@audited` decorator for automatic logging
  - Sensitive data redaction (`[REDACTED]` for tokens/keys)
  - Output to `logs/audit.jsonl`
- **Modular MCP Architecture**: Split tools into focused modules
  - `src/boring/mcp/core_tools.py`: Essential tools
  - `src/boring/mcp/speckit_tools.py`: SpecKit workflows
  - `src/boring/mcp/brain_tools.py`: Learning and evaluation
  - `src/boring/mcp/async_utils.py`: Async execution utilities
- **Async Support**: Non-blocking execution framework
  - `ThreadPoolExecutor` with 4 workers
  - `@run_in_thread` decorator
  - `AsyncTaskRunner` with progress callbacks

### Changed
- `@audited` decorator applied to `run_boring` and `boring_verify`

## [7.0.0] - 2026-01-03

### Added
- **Serverless Registry (GitHub Gist)**: 真正的去中心化工作流倉庫
  - `boring workflow publish`: 一鍵發布工作流到 GitHub Gist，自動生成安裝連結。
  - 支援 Token 認證 (`--token` 或 `GITHUB_TOKEN`)。
  - 支援公開 (`--public`) 或私密 (`--private`) 發布。
  
### Optimized (Local-First)
- **Zero-Config Evaluation**: `boring evaluate` now defaults to local CLI usage (`gemini` command), removing the need for an API key.
- **Workflow Resilience**: Added auto-retry mechanism for network downloads and robust YAML parsing.

## [6.0.0] - 2026-01-03

### Added
- **Boring Hub (Workflow Ecosystem)**: 實現工作流的分享與再利用
  - `boring workflow export`: 將工作流打包為 `.bwf.json`
  - `boring workflow install`: 從檔案或 URL 安裝工作流
  - `boring workflow list`: 列出本地可用工作流
- **MCP Tools for Hub**:
  - `boring_install_workflow`: 讓 AI 協助安裝工作流
  - `boring_export_workflow`: 讓 AI 協助分享工作流
- **Workflow Manager**: 核心引擎 (`src/boring/workflow_manager.py`)
- **Logger Upgrade**: 重構 `log_status` 支援更靈活的 CLI 調用

### Breaking Changes
- `log_status` 函數簽名變更：`log_dir` 參數變為 Optional 且移至參數列表後方。

## [5.2.0] - 2026-01-03

### Added
- **Dynamic Workflow Evolution**: AI can now modify SpecKit workflows based on project needs
  - `speckit_evolve_workflow`: Modify workflow content dynamically
  - `speckit_reset_workflow`: Rollback to base template
  - `speckit_backup_workflows`: Backup all workflows to `_base/` directory
  - `speckit_workflow_status`: Check workflow evolution state
- **WorkflowEvolver Module**: Core engine for workflow evolution (`src/boring/workflow_evolver.py`)
- **Base Templates**: All 6 SpecKit workflows backed up to `.agent/workflows/_base/`
- **`.boring_brain` Directory Structure**:
  - `workflow_adaptations/`: Evolution history
  - `learned_patterns/`: Successful patterns
  - `rubrics/`: Evaluation criteria
- **Complete SpecKit Tool Coverage**: Added missing tools to README
  - `speckit_constitution`, `speckit_clarify`, `speckit_checklist`

### Changed
- **README.md**: Updated to V5.2.0 with workflow evolution documentation
- **Project Structure**: Enhanced with `.boring_brain` knowledge base

### Fixed
- Improved project structure documentation in README
- **Documentation**: Comprehensive "Pro Tips" section in README for advanced usage
- **Documentation**: Added copy-pasteable MCP Prompts for all 21 tools
- **Documentation**: Added IDE-specific rollback instructions (MCP Mode)
- **Documentation**: Added Agent Mode vs Micro Mode comparison guide

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
