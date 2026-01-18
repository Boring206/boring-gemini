<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Boring for Gemini Logo">
</p>

# Boring for Gemini (V15.0.0) 💎

<h1 align="center">Boring</h1>

<p align="center">
  <strong>The Cognitive Reasoning Engine for Autonomous Development</strong>
</p>

<p align="center">
  <a href="https://smithery.ai/server/boring/boring"><img src="https://smithery.ai/badge/boring/boring" alt="Smithery Badge"></a>
  <a href="https://pypi.org/project/boring-aicoding/"><img src="https://img.shields.io/pypi/v/boring-aicoding.svg" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/boring-aicoding"><img src="https://static.pepy.tech/badge/boring-aicoding" alt="Downloads"></a>
  <a href="https://pypi.org/project/boring-aicoding/"><img src="https://img.shields.io/pypi/pyversions/boring-aicoding.svg" alt="Python Versions"></a>
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">繁體中文</a> | <a href="https://boring206.github.io/boring-gemini/">Documentation</a>
</p>

---

## ⚡ Beyond Generative AI: Agentic Cognition

Boring-Gemini isn't just a collection of tools; it's the **thinking layer** for your AI development workflow. While standard AI models *suggest* code, Boring **reasons, verifies, and learns**.

### 🧞‍♂️ The Vibe Coder Philosophy
> **"Intent is the new Implementation."**
>
> In the era of Vibe Coding, your role shifts from writing syntax to defining **Intent**. Boring-Gemini acts as your agentic partner, handling the gap between a "Vibe" (Natural Language) and "Production" (Verified Code).

---

## 🚀 The Three Pillars of Autonomy

### 🧠 Pillar I: [Cognitive Reasoning (Agentic Loop)](docs/features/agents.md)
Boring implements a rigorous **Planning -> Execution -> Verification** loop. It doesn't just run commands; it uses `sequentialthinking` and `criticalthinking` to analyze its own steps, critiquing logic *before* hitting your disk.

### 🛡️ Pillar II: [Resilient Autonomy (Active Recall)](docs/features/global-brain.md)
The first agent with a **Global Brain**. When Boring encounters a failure, it consults its persistent knowledge base (`.boring/brain`) to recall how similar issues were solved across sessions. It learns from its mistakes so you don't have to.

### ⚡ Pillar III: [Ultra-Fast Ecosystem (UV Native)](https://docs.astral.sh/uv/)
Designed for the modern Python stack. Boring natively supports **[uv](https://github.com/astral-sh/uv)** for near-instant package management, lockfile synchronization, and isolated environment execution.

### ⚓ Pillar IV: [Production-Grade Safety (Safety Net)](docs/features/shadow-mode.md)
Trust is built on safety. Boring automatically creates **Git Checkpoints** before any risky operation. Combined with **Shadow Mode**, you have a "undo" button for AI agentic actions, ensuring your repository remains stable even during complex refactors.

### 🧬 Pillar V: [The Diet & Skills Update (V11.4.2)](docs/features/cognitive.md)
Boring achieved **Full-Power** status by activating all high-value cognitive tools.
- **SpecKit Activation**: Enabled full Specification-Driven Development tools (`plan`, `tasks`, `analyze`) for methodical planning.
- **Global Brain Tools**: Unlocked cross-project knowledge sharing (`boring_global_export`) to recycle success patterns.
- **Skills Autonomy**: New `boring_skills_install` allows the Agent to autonomously install missing Python packages.
- **Node.js Autonomy**: Automatic Node.js download/install to ensure `gemini-cli` works even on fresh systems.
- **Lightweight Mode (BORING_LAZY_MODE)**: Perfect for "Quick Fixes" without polluting directories with `.boring` folders.

### 🧠 Pillar VI: [Intelligent Adaptability (V11.5.0)](docs/features/adaptive-intelligence.md)
Introduction of **Self-Awareness** and **Adaptive Safety**.
- **Usage Dashboard (P4)**: The Agent now tracks its own tool usage, visualizing stats in a CLI/Web dashboard.
- **Anomaly Safety Net (P5)**: Automatically halts "stuck" loops (same tool + same args > 50 times) to save tokens and prevent crashes.
- **Contextual Prompts (P6)**: Adaptive Profile now injects specific guides (e.g., *Testing Guide*) only when you need them.

### 🛡️ Pillar VII: [The True One Dragon (V12.0.0)](docs/features/flow.md)
The legacy production standard. Introduction of a **State-Machine Workflow** and **Deep Shadow Mode**.
- **Unified Flow Graph**: Dynamic orchestration (Architect -> Builder -> Healer -> Polish -> Evolver).
- **Deep Shadow Mode**: `HealerNode` activates **STRICT** safety enforcement during auto-repairs.
- **Cognitive Reflex**: Semantic Search integrated into the Brain for fuzzy error correction.

### 🧐 Pillar VIII: [Async Evolution (V13.0.0)](docs/changelog/v13.md)
The current high-performance standard. Focused on **Parallel Orchestration** and **Hybrid Storage**.
- **Async Agent Runner**: Parallel execution of sub-tasks for faster completion.
- **Semantic Storage Fallback**: FAISS integration for robust vector search when ChromaDB is unavailable.
- **One Dragon 2.0**: Enhanced state management for complex "One Dragon" workflows.

### 🔮 Pillar IX: [Intelligence & Offline (V13.1 - V13.5)](docs/features/predictive_zh.md)
The cutting edge. Shifting from reactive to **Predictive** and **Local-First**.
- **[Offline-First Mode](docs/guides/offline-mode_zh.md)**: Local LLM support (llama-cpp-python) for 100% privacy and zero-network operation.
- **Predictive Error Detection**: AI-powered anti-pattern detection and proactive warnings *before* errors occur.
- **AI Git Bisect**: Semantic analysis of commit history to instantly identify bug sources.
- **Lazy Loading System**: Optimized MCP startup (<500ms) for high-performance developer environments.

### 🏆 Pillar X: [Sovereign Autonomy & Perfection (V14.0.0)](docs/changelog/v14.md)
The **Sovereign Edition**. Achieving "100-Point Perfection" through enterprise-grade governance and knowledge continuity.
- **Project Biography (`boring bio`)**: Persistent team-wide knowledge continuity.
- **Policy-as-Code (`boring policy`)**: Secure, auditable tool permission guardrails.
- **Sovereign Audit (`boring perfection`)**: Automated 7-stage validation for production readiness.
- **Self-Healing Doctor (`boring doctor --fix`)**: Autonomous environment repair and dependency resolution.
- **System Optimizer (`boring doctor --optimize`)**: Deep storage cleanup (VACUUM), brain pattern maintenance (Decay/Pruning), and reconciler checkpointing.
- **Migration Engine (`boring migrate`)**: Forward-compatible project state transition.

### 💖 Pillar XI: [Anti-Rage UX (V15.0.0)](docs/changelog/v15.md)
The **Delight Update**. Transforming the user experience from "Frustrating" to "Fluid".
- **Visual Feedback**: Rich Spinners, Step Tracking (`Step 5/50`), and Task Progress bars.
- **Cost Awareness**: Proactive API cost warnings to prevent bill shock.
- **Resilience**: Robust file locking handling (WinError 32) and friendly error translations.
- **State Serialization**: Ability to `pause` and `resume` long-running flows.

### 🌍 Pillar XII: [The Zero-Cost Ecosystem (V15.0)](docs/guides/registry-format.md)
The **Democratization Update**. A fully decentralized, zero-cost plugin economy.
- **Pack & Install**: `boring pack` and `boring install` turn any repo into a plugin.
- **Knowledge Share**: `boring brain export` lets you share your AI's learned wisdom.
- **GitOps Sync**: `boring sync` enables serverless team collaboration via Git.
- **Registry Spec**: Open standard (`registry.json`) for a decentralized internet of agents.


---

## 🛠️ Key Capabilities

| | Feature | Description |
| :--- | :--- | :--- |
| 🧠 | **[Unified Gateway (Cognitive Router)](docs/features/mcp-tools.md)** | The `boring` tool is now your single entry point. Use `boring "check security"`, `boring help`, or `boring discover "rag"` to access all capabilities. |
| 🕵️ | **[Hybrid RAG](docs/features/rag.md)** | Combined Vector + Dependency Graph search. Understands not just *what* code says, but *how* it's used globally. Now with **HyDE** expansion. |
| 🧪 | **[Vibe Check](docs/features/quality-gates.md)** | Gamified health scanning. Calculates a **Vibe Score** and generates a "One-Click Fix Prompt" for the agent. |
| 🛡️ | **[Active Recall](docs/features/global-brain.md)** | Automatically learns from error patterns. Recalls past solutions to avoid repeating mistakes across sessions. |
| 📚 | **[Full Tool Reference](docs/reference/APPENDIX_A_TOOL_REFERENCE.md)** | Complete catalog of **67+ tools** with parameters and usage ([中文](docs/reference/APPENDIX_A_TOOL_REFERENCE_zh.md)). |
| 🧬 | **[Skill Compilation](docs/features/cognitive.md)** | Distills repeated successful patterns into high-level **Strategic Skills**. |
| 🪢 | **[Node.js Autonomy](docs/features/nodejs.md)** | Zeroconf Node.js & gemini-cli setup. No manual installation required. |
| 🔌 | **[Offline-First](docs/guides/offline-mode_zh.md)** | Zero-network operation with local LLMs (Phi-3, Qwen) for maximum privacy. |
| 🌍 | **[Language Setup](docs/guides/language.md)** | Configure English or Traditional Chinese output via environment variables. |
| 🔮 | **[Predictive AI](docs/features/predictive_zh.md)** | Prevents issues before they happen with pattern-based error prediction. |
| 🕵️ | **[AI Git Bisect](docs/features/predictive_zh.md)** | Semantic diagnostics for commit history. Finds the root cause of bugs instantly. |
| 🏆 | **[Sovereign Audit](docs/changelog/v14.md)** | `boring perfection` certifies a project as 100/100 Production Ready. |
| 📜 | **[Project Bio](docs/features/agents.md)** | `boring bio` maintains tribal knowledge and project context over time. |
| 🛡️ | **[Policy-as-Code](docs/features/shadow-mode.md)** | `boring policy` enforces granular security and tool permissions. |
| 🔄 | **[Migrate](docs/changelog/v14.md)** | `boring migrate` ensures project state is always forward-compatible. |
| 📦 | **[Ecosystem](docs/guides/pack-format.md)** | `boring pack/install` decentralized plugin system. Build, Share, Run. |

---

## 🎛️ Intelligent Tool Profiles (V10.26+)
Boring adapts to your environment to save tokens and context:
- **LITE (Default)**: Essential tools for daily coding (43 tools) using ~15% of context window.
- **FULL**: All 67+ tools active.
- **ADAPTIVE (Recommended)**: Automatically builds a custom profile based on your top 20 most frequently used tools + Prompt Injection.
  - Enable: `export BORING_MCP_PROFILE=adaptive`

---

## 🔔 Enterprise Notifications (V14.0+)
Boring supports multi-channel task notifications to keep you informed:
- **Desktop**: Windows Toast, macOS, Linux notifications.
- **Webhooks**: Slack, Discord.
- **Messaging**: LINE Notify, Facebook Messenger.
- **Email**: Gmail (via SMTP).

Configure these in `.boring.toml`:
```toml
[boring]
slack_webhook = "..."
discord_webhook = "..."
line_notify_token = "..."
gmail_user = "..."
gmail_password = "..."
email_notify = "..."
```

---

## 📦 Getting Started

### 🎭 Dual-Mode Architecture (Hybrid Engine)

Boring is a **Hybrid Agent** that adapts to your workflow. It works in two distinct modes:

### 1. Cyborg Mode (MCP Server) 🧠
*   **Where**: Inside Cursor, Claude Desktop, or VSCode.
*   **Role**: Your "second brain". It sits alongside you as an MCP server.
*   **Usage**: You chat with it via the `@boring` command. It remembers context, provides tools, and offers "Active Recall" suggestions.
*   **Best For**: Daily coding, debugging, and interactive problem solving.

### 2. Autonomous Mode (CLI Agent) 🤖
*   **Where**: Standard Terminal / Command Prompt.
*   **Role**: Your "unattended worker". It runs as a standalone process.
*   **Usage**: Run `boring start` (NOT `boring run`). It reads `task.md`, executes the plan loop (Plan -> Code -> Test -> Fix), and stops when done.
*   **Best For**: Bulk refactoring, massive migrations, or long-running tasks while you sleep.

### 3. VS Code Extension (GUI Helper) 🖥️
*   **Where**: `extensions/vscode-boring/`
*   **Role**: A graphical interface for the CLI Agent inside VS Code.
*   **Features**: One-click Start/Stop, Live Dashboard, and Status Bar integration.
*   **How to use**: Open the directory in VS Code, press `F5` to debug, or compile with `npm run compile`.

---

## 🔒 Data Privacy & The "Global Brain"

Your data stays YOURS. Boring uses a two-tier memory system:

1.  **Project Memory** (`.boring/memory/`):
    *   Lives in your project folder.
    *   Contains project-specific graphs and indexes.
    *   **Safe to commit**: Share with your team via Git.

2.  **Global Brain** (`~/.boring/brain/`):
    *   Lives in your user home directory (Local Manager).
    *   Stores **learned patterns** and **skills** across all your projects.
    *   **NEVER uploaded**: This data never leaves your machine unless you explicitly configure a sync.

---

### Quick Install (One-Click)
Designed for Vibe Coders. Setup in < 30 seconds.

**Windows (PowerShell):**
```powershell
powershell -c "irm https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.ps1 | iex"
```

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.sh | bash
```

### Manual Install (pip)

```bash
pip install boring-aicoding
boring wizard

# Optional: Install RAG intelligence for full semantic search
pip install sentence-transformers chromadb
```

> [!NOTE]
> Once installed, please refer to the **[AI Connection Guide (Gemini / Ollama)](docs/guides/connection.md)** to set up your models.

<details>
<summary><b>🔧 Advanced Installation (uv, modular)</b></summary>

**Using [uv](https://github.com/astral-sh/uv) (Recommended for Speed):**
```bash
uv pip install "boring-aicoding[all]"
```

**Modular Components:**
```bash
pip install "boring-aicoding[vector]" # RAG Support
pip install "boring-aicoding[gui]"    # Dashboard
pip install "boring-aicoding[mcp]"    # MCP Server
```
</details>

---

## 🛠️ Usage & Workflows

> [!TIP]
> **New to Boring?** Check out the [Visual Cheatsheet](docs/CHEATSHEET.md) for a one-page summary of the 5 core commands.

### 💎 Top Interaction Triggers
Just say these phrases to the AI in your IDE (Cursor/Claude):

- **`boring_flow`**: 🐉 **One Dragon Engine**. The ultimate autonomous workflow. Handles Setup -> Plan -> Build -> Polish automatically via code.
- **`start session`**: 🚀 **Vibe Session**. Activates Deep Thinking to autonomously manage the entire lifecycle of a complex task.
- **`/vibe_start`**: Kick off a new project from scratch.
- **`quick_fix`**: Automatically repair all linting and formatting errors.
- **`review_code`**: Request a technical audit of your current file.
- **`smart_commit`**: Generate a semantic commit message from your progress.
- **`boring_vibe_check`**: Run a comprehensive health scan of the project.
- **`boring doctor --optimize`**: Perform deep system optimization (Storage, Brain, and Checkpoints).

---

## 🧠 External Intelligence
Boring comes bundled with elite tools to boost AI performance:
- **Context7**: Real-time documentation querying for the latest libraries.
- **Thinking Mode**: Forces the agent into deep analytical reasoning (Sequential Thinking).
- **Security Shadow Mode**: A safety sandbox that intercepts dangerous AI operations.

---


## 📄 License & Links
- **License**: [Apache 2.0](LICENSE)
- **Repository**: [GitHub](https://github.com/Boring206/boring-gemini)
- **Smithery**: [Boring Server](https://smithery.ai/server/boring/boring)

<p align="center">
  <sub>Built by <strong>Boring206</strong> with 🤖 AI-Human Collaboration</sub>
</p>
