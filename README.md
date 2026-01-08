[![PyPI version](https://badge.fury.io/py/boring-aicoding.svg)](https://badge.fury.io/py/boring-aicoding)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Vibe Coder](https://img.shields.io/badge/Vibe_Coder-Pure_Natural_Language-ff69b4)](docs/features/vibe-coder.md)

# Boring for Gemini

**Autonomous AI Agent Loop with VibeCoder Experience**

[English](README.md) | [繁體中文](README_zh.md)

---

## ✨ The Vibe Coder Experience (V10.24)

**No Code Needed.** Just describe the vibe.

Boring-Gemini now features a **Universal Natural Language Router**. You don't need to remember 98+ complex tools. Just say what you want in English or Chinese:

> "Search for authentication logic"
>
> "Review my code for security issues"
>
> "幫我寫測試" (Help me write tests)
>
> "我想做登入功能" (I want to build login feature)

**Try it in your terminal:**
```bash
boring-route "review my code"
# 🎯 Routes to boring_code_review (100%)
```

[👉 Learn more about Vibe Coder Experience](docs/features/vibe-coder.md)

---

## ⚡ boring 的厲害 (Why Boring?)

Boring isn't just an MCP server; it's a **Intelligence Maximization System**:

1.  **🧠 Autonomous Loop**: Not just a chatbot. Boring runs in a loop (`boring start`), thinking, coding, testing, and fixing until the job is done.
2.  **🕵️ Hybrid RAG**: Advanced code search combining keywords, vectors, and dependency graphs (HyDE + Cross-Encoder). It finds code you didn't even know existed.
3.  **🛡️ Security Shadow Mode**: Safe execution sandbox. It catches dangerous operations *before* they happen.
4.  **⚡ 30% Faster**: Smart caching and optimized router reduce context usage by 80% (from 98 tools to 19).
5.  **🧩 Vibe Coder**: The most human-friendly AI coding interface. Zero friction between thought and code.

---

## 🚀 Quick Start
[![Downloads](https://img.shields.io/pypi/dm/boring-aicoding.svg)](https://pypi.org/project/boring-aicoding/)
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
| ✨ **Vibe Coder Pro** | **Doc Gen** | **Test Gen** | **Code Review** | **Perf Tips** | **Arch Check** | Multi-Lang Support (Py/JS/TS) |

---

## 📦 Quick Installation

### Option 1: Smithery (✅ Recommended)

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

> ⚠️ **Gemini Client Users**: If you encounter issues installing via Smithery, please use **Option 2 (Local pip)**. Direct Smithery integration on Gemini Client can be intermittent.

### Option 2: Local pip Installation

```bash
# Install with all features (Recommended for Vibe Coder)
pip install "boring-aicoding[all]"

# Or minimal install
pip install boring-aicoding
```

**🤔 Which one should I choose?**

| Feature | `[all]` (Full) | Basic |
| :--- | :--- | :--- |
| **RAG Memory** | ✅ Vector + Semantic | ⚠️ Keyword only (Weak) |
| **Self-Verify** | ✅ Can run tests (`boring verify`) | ❌ Cannot verify |
| **Dashboard** | ✅ GUI Available | ❌ None |
| **Use Case** | **Vibe Coding** | CLI Only |

### Option 3: Clone from GitHub (Fallback)

> **Best for: Developers or if pip install fails**

```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e .
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
        "PROJECT_ROOT_DEFAULT": ".",
        "BORING_MCP_PROFILE": "lite"
      }
    }
  }
}
```

### 🎛️ Tool Profiles (V10.24)

> **Problem**: 98 tools can overwhelm LLM context windows.
> **Solution**: Choose a profile to expose only the tools you need.

| Profile | Tools | Best For |
|---------|-------|----------|
| `minimal` | 8 | Simple workflows, minimal context |
| `lite` | 20 | **Recommended** - everyday development |
| `standard` | 50 | Full-featured projects |
| `full` | 98+ | Power users who need everything |

**Configure in `.boring.toml`:**
```toml
[boring.mcp]
profile = "lite"  # Options: minimal, lite, standard, full
```

**Or via environment variable:**
```bash
export BORING_MCP_PROFILE=lite
```

**🎯 Universal Router**: With `lite` profile, use `boring("search for auth code")` - the router automatically directs to the right tool!

---

## 🎯 Quick Start Prompts

| Prompt | Usage |
|--------|-------|
| `/vibe_start` | Start a new project with AI guidance |
| `/full_stack_dev` | Build a complete full-stack application |
| `/release-prep`| **Turbo**: Auto-bump version & git tag |
| `/quick_fix` | Auto-fix all linting and formatting errors |
| `/smart_commit` | Generate semantic commit messages |

---

## 📚 Documentation

| Category | Links |
|----------|-------|
| **Getting Started** | [Vibe Coder Guide](docs/guides/vibe-coder.md) · [**🗣️ Natural Language Prompts**](docs/guides/vibe-coder-prompts.md) · [Quick Tutorials](docs/guides/quick-tutorials.md) |
| **Features** | [MCP Tools (55+)](docs/features/mcp-tools.md) · [Shadow Mode](docs/features/shadow-mode.md) · [Quality Gates](docs/features/quality-gates.md) |
| **Guides** | [Cookbook](docs/guides/cookbook.md) · [Pro Tips](docs/guides/pro-tips.md) · [Git Hooks](docs/guides/git-hooks.md) · [Workflows](docs/guides/workflows.md) |
| **Advanced** | [Plugins](docs/guides/plugins.md) · [Knowledge Mgmt](docs/guides/knowledge-management.md) · [API Integration](docs/guides/api-integration.md) · [Human Alignment](docs/guides/human-alignment.md) |
| **Reference** | [Architecture](docs/reference/architecture.md) · [Security & Privacy](docs/reference/security-privacy.md) · [Agent Comparison](docs/reference/comparison.md) · [V10 Changelog](docs/changelog/v10.md) |

---

## ✨ Vibe Coder Pro Toolset
> **🎉 Interactive Tutorial on Startup!**
> First-time MCP connection triggers `mcp_intro` to guide new users.

### 🗣️ Natural Language Triggers (No Code Required!)
**Just say these to Boring:**

| Goal | Just Say |
|------|----------|
| Write Tests | `Help me write tests for auth.py` |
| Review Code | `Review my code` |
| Health Check | `Vibe Check my project` |
| Check Impact | `Check impact of utils.py` |
| Plan Feature | `I want to add login`, `Plan this feature` |

👉 **[Full Prompt Guide](docs/guides/vibe-coder-prompts.md)**

### 🧰 Core Tools
| Tool | Description | Example |
|------|-------------|---------|
| 🧪 `boring_vibe_check` | **Project Health Scan** - Coverage, Docs, Security (S-F Grade) | `boring_vibe_check(project_path=".")` |
| 📊 `boring_impact_check` | **Impact Analysis** - Trace reverse dependencies (L1/L2/L3) | `boring_impact_check(file_path="core.py")` |
| 🧪 `boring_test_gen` | **Smart Test Gen** - Auto-generate simple tests (Py/JS/TS) | `boring_test_gen(file_path="utils.py")` |
| 📝 `boring_review` | **Friendly Review** - Constructive feedback & suggestions | `boring_review(file_path="app.py")` |
| 🚀 `boring_perf` | **Perf Tips** - Identify bottlenecks | `boring_perf(file_path="main.py")` |
| 📐 `boring_arch` | **Arch Check** - Visualize module structure | `boring_arch(project_path=".")` |
| 📄 `boring_doc_gen` | **Doc Gen** - Auto-generate docstrings | `boring_doc_gen(file_path="api.py")` |

### 🔐 Security Scan Integration
Vibe Coder Pro includes built-in Token detection for:
- **Python**: PyPI, AWS, GCP, Azure, etc.
- **JS/Node.js**: NPM, Vercel, Supabase, Firebase, Stripe.
- **General**: GitHub, GitLab, Slack, SendGrid (20+ types).

```python
# Health check triggers security scan automatically
result = boring_vibe_check(project_path=".", max_files=100)
print(result["security_issues"])
```

## 🚀 Performance Optimization (v10.21.0)
- **Thread-local SQLite**: Zero-overhead database connections.
- **WAL Mode**: 50% faster concurrent reads.
- **Smart Caching**: 30s Query Cache & Pattern Caching for instant RAG responses.

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
