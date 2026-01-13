# V12 更新日誌 (Changelog)

## [12.0.0] - 2026-01-14 - The True One Dragon Update 🐉🧠

### 🚀 Major Features
- **One Dragon Flow (V12.0.0)**: A comprehensive, state-machine driven autonomous development loop. Includes `Architect`, `Builder`, `Healer`, `Polish`, and `Evolver` stages.
- **Cognitive Reflex**: Integrated semantic search (RAG) directly into the Brain for high-speed fuzzy error correction.
- **Global Swarm Sync**: Real-time knowledge synchronization via Git across multiple project instances.

### 🔧 Fixes
- **CLI Compatibility**: Fixed "Requested entity was not found" error for Keyless OAuth users (Gemini CLI).
- **Import Precision**: Fixed `boring_checkpoint` imports in HealerNode.
- **Node Stability**: Fixed `NameError` for `boring_speckit_tasks` in `engine.py` by ensuring proper fallback initialization for all optional SpecKit tools.

### 🛡️ Quality & Stability
- **Tool Count Alignment**: Synchronized all documentation and router metadata to reflect verified tool counts (67+ standard, 43 lite).
- **Timeout Protection**: Implemented a **1-hour global timeout** for `AgentLoop` within the `FlowEngine` to prevent perpetual hangs.
- **Integrity Audit**: Purged "ghost feature" references to `VectorMemory` and `AutoLearner` from all documentation and guides.
- **Standardized Results**: 100% of tools now return the `BoringResult` TypedDict for better LLM reasoning.
