<p align="center">
  <img src="docs/assets/logo.png" width="180" alt="Boring for Gemini Logo">
</p>

<h1 align="center">Boring</h1>

<p align="center">
  <strong>The Cognitive Reasoning Engine for Autonomous Development</strong>
</p>

<p align="center">
  <a href="https://smithery.ai/server/boring/boring"><img src="https://smithery.ai/badge/boring/boring" alt="Smithery Badge"></a>
  <a href="https://badge.fury.io/py/boring-aicoding"><img src="https://badge.fury.io/py/boring-aicoding" alt="PyPI version"></a>
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

### 🧠 Pillar I: Cognitive Reasoning (Agentic Loop)
Boring implements a rigorous **Planning -> Execution -> Verification** loop. It doesn't just run commands; it uses `sequentialthinking` and `criticalthinking` to analyze its own steps, critiquing logic *before* hitting your disk.

### 🛡️ Pillar II: Resilient Autonomy (Active Recall)
The first agent with a **Global Brain**. When Boring encounters a failure, it consults its persistent knowledge base (`.boring/brain`) to recall how similar issues were solved across sessions. It learns from its mistakes so you don't have to.

### ⚡ Pillar III: Ultra-Fast Ecosystem (UV Native)
Designed for the modern Python stack. Boring natively supports **[uv](https://github.com/astral-sh/uv)** for near-instant package management, lockfile synchronization, and isolated environment execution.

### ⚓ Pillar IV: Production-Grade Safety (Safety Net)
Trust is built on safety. Boring automatically creates **Git Checkpoints** before any risky operation. Combined with **Shadow Mode**, you have a "undo" button for AI agentic actions, ensuring your repository remains stable even during complex refactors.

---

## 🛠️ Key Capabilities

| | Feature | Description |
| :--- | :--- | :--- |
> **Universal Natural Language Router**: You don't need to learn 98 tool names. Just say:
> *"Review my code for security issues"* or *"Add a Google login feature"* — Boring handles the routing.

---

## 📦 Getting Started

### Quick Install (Smithery)

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

### Power User Install (pip)

```bash
pip install "boring-aicoding[all]"
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

### 💎 Top Interaction Triggers
Just say these phrases to the AI in your IDE (Cursor/Claude):

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
