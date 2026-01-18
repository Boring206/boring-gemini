
# Changelog

All notable changes to the "Boring-Gemini" project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [15.1.0] - 2026-01-18

### ✨ Smart Wizard & Ecosystem (V15.1.0)
- **Smart Scan**: Setup wizard now only lists installed editors, preventing UX clutter.
- **Ecosystem Sync**: New "Scan MCP Ecosystem" feature detects and syncs existing `@context7`, `@criticalthink`, and `@sequential-thinking` servers.
- **Modern IDE Support**: Verified path mappings for Windsurf, Trae, Void, Cursor, and Zed on Windows.
- **OpenCode Integration**: Native support for OpenCode configuration and CLI registration.
- **Fix**: Resolved `AttributeError` for `LOCAL_LLM_MODEL` in offline mode configuration.

## [15.0.1] - 2026-01-18

### 🛡️ Quick Fixes (V15.0.1)
- **Fix**: Resolved `AttributeError` for `LOCAL_LLM_MODEL` in setup wizard when enabling Offline Mode.
- **Improved**: Added missing `LOCAL_LLM_CONTEXT_SIZE` and `MODEL_DIR` to global settings.

## [15.0.0] - 2026-01-18

### 🌍 Ecosystem (Zero-Cost Platform) [NEW]
Goal: Decentralized, Serverless, Free.

- **Decentralized Plugins**: New `boring install <git-url>` allows installing extensions directly from GitHub or local `.boring-pack` files.
- **Cognitive Packs**: Defined `.boring-pack` format to bundle Tools, Workflows, Prompts, and Knowledge into a single portable zip.
- **Knowledge Sharing**: Added `boring brain export` & `import` to transfer Agent learning (ChromaDB) between teammates.
- **Serverless Collaboration**: New `boring sync` command orchestrates GitOps flows to synchronize SQLite project state without a server.
- **Release Automation**: `boring publish` simplifies the versioning and tagging process for pack creators.

### 🚀 UX Hardening & Resilience (The "Anti-Rage" Update)
Goal: Elevate UX from "Frustrating" to "Delightful" (Anti-Keyboard-Smash Index: 5/5).

#### ✨ Quick Wins (UX)
- **Visual Progress**: Added a rich spinner to `flow run` with step counting (e.g., `Step 5/50: Architect`).
- **Cost Awareness**: Added API cost warnings when execution exceeds threshold (25 steps / ~$5).
- **Explicit Feedback**: Architect & Builder now output absolute paths for generated files (`implementation_plan.md`, `task.md`) to avoid "Where is it?" confusion.
- **Task Tracking**: Builder displays granular task progress (e.g., `任務進度: 3/10`).

#### 🧠 Intelligence
- **Goal Validator**: New `GoalValidator` prevents "hallucinated plans" by verifying request feasibility against project structure (e.g., warning if asking for Vue.js in a pure Python project).
- **Smart Stop**: Added `MAX_CONSECUTIVE_FAILURES` check to prevent infinite failure loops.

#### 🛡️ Resilience
- **Interruption Checkpoints**: Added interactive checkpoints every 10 steps to allow users to pause or stop long-running flows safely.
- **Robust File Locking**: Enhanced `TransactionalFileWriter` with adaptive retries (increased delay) to handle Windows file locking (AV/Editor conflicts).
- **Friendly Errors**: Expanded `ErrorTranslator` to cover `WinError 32`, `UnicodeDecodeError`, `JSONDecodeError`, and `RecursionError` with actionable advice.

#### 🔧 Technical
- **Auto Mode Support**: Propagated `auto_mode` flag to `FlowContext` to enable headless testing and automation.

#### 🌊 Advanced (Phase 4)
- **Streaming Support**: Implemented `GeminiProvider.generate_stream` and `ArchitectNode` UI feedback ("Thinking...") to reduce user anxiety during long generation tasks.
- **State Serialization**: Added `StateSerializer` to save flow state (`.boring/checkpoints/latest.pkl`). Triggered automatically on interruption, enabling future `resume` capabilities.

## [14.9.0] - 2026-01-18

### 🚀 Release Notes (Quality & Resilience)
#### 🔧 Technical Fixes
- **Configuration Hardening**: Added missing `Settings` attributes (`PROMPTS`, `CLI_PATH`, `BORING_EVENT_*`, `VERIFICATION_EXCLUDES`, `LINTER_CONFIGS`) to resolve runtime `AttributeError`s and ensure stability.
- **Test Suite Stability**: Fixed flaky tests in `ledger_integrity` (SQLite migration migration logic) and `integrity_chaos` (mocking path security checks for isolation).
- **Verifying Loop**: Fixed `task.md` path resolution bug in `VerifyingState` to correctly support relative paths in testing contexts.

#### 🛡️ Quality Gates
- **Linting & Formatting**: Enforced strict `ruff` compliance across all modules.
- **Security Check**: Verified with `bandit`.
- **Type Safety**: Resolved `mypy` configuration ambiguities.

## [14.8.0] - 2026-01-17

### 🚀 Major Improvements (World Class Edition)

#### 🛡️ Resilience & Data Integrity
- **Robust Event Store**: Replaced JSONL with **SQLite (WAL Mode)** for atomic durability (`.boring/events.db`).
- **Data Safety**: Implemented **Dead Letter Queue (DLQ)** (`dead_letters.jsonl`) to capture events if DB writes fail after retries.
- **Failover**: Added `Self-Healing` for EventWriter thread - automatically detects thread death and restarts without data loss.
- **Circuit Breaker**: Added `AdaptiveCircuitBreaker` with exponential backoff for external API resilience.
- **State Recovery**: Optimized `StateManager` to hydration from ledger + lazy snapshots.

#### 🧠 Intelligence Engine
- **Process Isolation**: Embedding computation now runs in a `ProcessPoolExecutor`, unblocking the main thread (GIL reduced).
- **Graceful Degradation**: `VectorSearchEngine` now handles ChromaDB unavailability by falling back to keyword search or returning empty results safely.
- **Cache Protection**: Implemented `Singleflight` pattern to prevent cache stampedes on pattern lookup.

#### ⚡ Performance
- **Startup Time**: Optimized to **< 200ms** (Cold Start) via lazy loading of heavy modules (Pydantic, Chroma).
- **Concurrency**: Verified to support **20+ concurrent sessions** with 100% data integrity (P95 < 800ms).

### 🐛 Bug Fixes
- **CRIT-001**: Fixed `AsyncEventStore` returning invalid sequence numbers (`-1`). Now waits for writer ack when strict consistency is required.
- **CRIT-002**: Fixed silent event loss on DB lock. Added Retry Policy.
- **RISK-008**: Fixed `UnitOfWork` rollback semantics to strictly truncate the ledger on failure.

### 📚 Documentation
- Added `ARCHITECTURE.md`: High-level system design.
- Added `TROUBLESHOOTING.md`: Guide for common issues (Locking, DLQ).
- Added `docs/performance_baseline.md`: Load test results.

## [14.0.0] - 2026-01-15
- Initial "Boring" Release.
