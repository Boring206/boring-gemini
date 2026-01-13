<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Boring for Gemini Logo">
</p>

<h1 align="center">Boring</h1>

<p align="center">
  <strong>The Cognitive Reasoning Engine for Autonomous Development</strong>
</p>

<p align="center">
  <a href="https://smithery.ai/server/boring/boring"><img src="https://smithery.ai/badge/boring/boring" alt="Smithery Badge"></a>
  <a href="https://pypi.org/project/boring-aicoding/"><img src="https://img.shields.io/pypi/v/boring-aicoding.svg?v=11.5.0" alt="PyPI version"></a>
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

### 🧬 Pillar V: [Full-Power Boring (V11.4.2)](docs/features/cognitive.md)
Not just execution, but evolution. V11.3.0 achieves **Full-Power** status by activating all high-value cognitive tools.
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

---

## 🛠️ Key Capabilities

| | Feature | Description |
| :--- | :--- | :--- |
| 🧠 | **[Unified Gateway (Cognitive Router)](docs/features/mcp-tools.md)** | The `boring` tool is now your single entry point. Use `boring "check security"`, `boring help`, or `boring discover "rag"` to access all capabilities. |
| 🕵️ | **[Hybrid RAG](docs/features/rag.md)** | Combined Vector + Dependency Graph search. Understands not just *what* code says, but *how* it's used globally. |
| 🧪 | **[Vibe Check](docs/features/quality-gates.md)** | Gamified health scanning. Calculates a **Vibe Score** and generates a "One-Click Fix Prompt" for the agent. |
| 🛡️ | **[Active Recall](docs/features/global-brain.md)** | Automatically learns from error patterns. Recalls past solutions to avoid repeating mistakes across sessions. |
| 📚 | **[Full Tool Reference](docs/reference/APPENDIX_A_TOOL_REFERENCE.md)** | Complete catalog of 98+ tools with parameters and usage ([中文](docs/reference/APPENDIX_A_TOOL_REFERENCE_zh.md)). |
| 🧬 | **[Skill Compilation](docs/features/cognitive.md)** | Distills repeated successful patterns into high-level **Strategic Skills**. |
| 🪢 | **[Node.js Autonomy](docs/features/nodejs.md)** | Zeroconf Node.js & gemini-cli setup. No manual installation required. |

---

## 🎛️ Intelligent Tool Profiles (V10.26+)
Boring adapts to your environment to save tokens and context:
- **LITE (Default)**: Essential tools for daily coding using ~5% of context window.
- **FULL**: All 98+ tools active.
- **ADAPTIVE (Recommended)**: Automatically builds a custom profile based on your top 20 most frequently used tools + Prompt Injection.
  - Enable: `export BORING_MCP_PROFILE=adaptive`

---

## 📦 Getting Started

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
```

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

---

## 🧠 External Intelligence
Boring comes bundled with elite tools to boost AI performance:
- **Context7**: Real-time documentation querying for the latest libraries.
- **Thinking Mode**: Forces the agent into deep analytical reasoning (Sequential Thinking).
- **Security Shadow Mode**: A safety sandbox that intercepts dangerous AI operations.

---


## 📄 License & Links
- **License**: [MIT](LICENSE)
- **Repository**: [GitHub](https://github.com/Boring206/boring-gemini)
- **Smithery**: [Boring Server](https://smithery.ai/server/boring/boring)

<p align="center">
  <sub>Built by <strong>Boring206</strong> with 🤖 AI-Human Collaboration</sub>
</p>
