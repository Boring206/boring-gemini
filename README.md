[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-10.18.3-green.svg)](https://github.com/Boring206/boring-gemini)
[![Evaluation](https://img.shields.io/badge/Smithery-58%2F58-brightgreen.svg)](https://smithery.ai/server/boring/boring)
[![smithery badge](https://smithery.ai/badge/boring/boring)](https://smithery.ai/server/boring/boring)

# Boring: Your Autonomous Coding Partner

> **Enterprise-grade Autonomous AI Development Agent**  
> A full-language automated coding and verification engine built for Cursor / Claude Desktop / VS Code / Gemini CLI.

**[中文版 README](README_zh.md)** | **[Full Documentation](docs/index.md)**

---

## 🚀 Core Advantages

| Feature | Description |
|---------|-------------|
| 🌐 **Polyglot & CLI Native** | Seamless switching between Gemini CLI and Claude Code CLI, zero API key required |
| 🛡️ **Parallel Verification** | Multi-threaded parallel verification, 3-5x performance boost |
| 🧠 **RAG Memory** | Hybrid Search (Vector + Keyword) + dependency graph for real-time retrieval |
| 🛡️ **Shadow Mode** | High-risk operations require human approval, with persistent config |
| 📐 **Spec-Driven** | 100% specification consistency from PRD to Code |
| 🔒 **Quality Gates** | CI/CD multi-tier gates + multi-language linting + 20+ file type security scanning |

---

## 📦 Quick Installation

### Option 1: Smithery (✅ Recommended)

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

### Option 2: Local pip Installation

```bash
# Basic installation
pip install boring-aicoding

# Full installation with all features
pip install "boring-aicoding[all]"

# Specific extras
pip install "boring-aicoding[mcp]"     # MCP server + RAG
pip install "boring-aicoding[vector]"  # Pure RAG/Vector search
```

---

## ⚙️ MCP Configuration

### For Smithery

```json
{
  "mcpServers": {
    "boring": {
      "command": "npx",
      "args": ["-y", "@smithery/cli", "run", "@boring/boring", "--config", "{}"]
    }
  }
}
```

### For Local pip

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "BORING_MCP_MODE": "1",
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

---

## 🎯 Quick Start Prompts

| Prompt | Usage |
|--------|-------|
| `/vibe_start` | Start a new project with AI guidance |
| `/quick_fix` | Auto-fix all linting and formatting errors |
| `/smart_commit` | Generate semantic commit messages |
| `/full_stack_dev` | Build a complete full-stack application |

---

## 📚 Documentation

| Category | Links |
|----------|-------|
| **Getting Started** | [Vibe Coder Guide](docs/guides/vibe-coder.md) · [Quick Tutorials](docs/guides/quick-tutorials.md) |
| **Features** | [MCP Tools (55+)](docs/features/mcp-tools.md) · [Shadow Mode](docs/features/shadow-mode.md) · [Quality Gates](docs/features/quality-gates.md) |
| **Guides** | [Cookbook](docs/guides/cookbook.md) · [Pro Tips](docs/guides/pro-tips.md) · [Git Hooks](docs/guides/git-hooks.md) |
| **Reference** | [Tool Reference](docs/APPENDIX_A_TOOL_REFERENCE.md) · [FAQ](docs/APPENDIX_B_FAQ.md) · [V10 Changelog](docs/changelog/v10.md) |

---

## 🛡️ Shadow Mode

Shadow Mode protects you from destructive AI operations:

```
DISABLED  ⚠️  No protection (isolated containers only)
ENABLED   🛡️  Auto-approve safe, block dangerous (default)
STRICT    🔒  All writes require approval (production)
```

```python
boring_shadow_mode(action="set_level", level="STRICT")
```

---

## 🔭 Future Vision

| Phase | Focus |
|-------|-------|
| **Q1 2025** | NotebookLM Integration, MCP Compose |
| **Q2 2025** | Agent Orchestration 2.0, Cross-Repo Learning |
| **Q3 2025** | AI Code Generation Benchmarks, Self-Healing Pipelines |

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) - AI Engine
- [Anthropic Claude](https://anthropic.com/) - MCP Protocol
- [Smithery](https://smithery.ai/) - Deployment Platform

---

## 📄 License

[MIT License](LICENSE) - Open source and free to use

---

## 🔗 Links

[![GitHub](https://img.shields.io/badge/GitHub-Boring206%2Fboring--gemini-blue?logo=github)](https://github.com/Boring206/boring-gemini)
[![PyPI](https://img.shields.io/badge/PyPI-boring--aicoding-orange?logo=pypi)](https://pypi.org/project/boring-aicoding/)
[![Smithery](https://img.shields.io/badge/Smithery-boring%2Fboring-green)](https://smithery.ai/server/boring/boring)
