[![Smithery Badge](https://smithery.ai/badge/boring-mcp)](https://smithery.ai/server/boring-mcp)
[![PyPI version](https://badge.fury.io/py/boring-aicoding.svg)](https://badge.fury.io/py/boring-aicoding)
[![Downloads](https://static.pepy.tech/badge/boring-aicoding)](https://pepy.tech/project/boring-aicoding)
[![Python Versions](https://img.shields.io/pypi/pyversions/boring-aicoding.svg)](https://pypi.org/project/boring-aicoding/)
[![Build Status](https://github.com/ralphgeminicode/boring-gemini/actions/workflows/ci.yml/badge.svg)](https://github.com/ralphgeminicode/boring-gemini/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Vibe Coder](https://img.shields.io/badge/Vibe_Coder-Pure_Natural_Language-ff69b4)](docs/features/vibe-coder.md)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green)](tests/)

# Boring for Gemini

**Autonomous AI Agent Loop with VibeCoder Experience**

[English](README.md) | [繁體中文](README_zh.md)

> 🤖 **Proudly Built with AI-Human Collaboration**
>
> _"This project explores the limits of autonomous AI coding. While we strive for quality, some logic is AI-generated and subject to continuous improvement. Pull Requests are welcome!"_

---

## ✨ The Vibe Coder Experience (V10.27)

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

## 🧪 NotebookLM Optimizations (V10.27)

Boring-Gemini V10.27 introduces several critical optimizations inspired by NotebookLM research to maximize LLM comprehension and minimize token overhead:

- **Theme-Tips Hierarchical Output**: Restructures complex tool outputs into a "Theme → Tips" format. This hierarchical structure has been shown to improve LLM comprehension accuracy by **+1.13%** by reducing cognitive load.
- **PREPAIR Reasoning Cache**: Implements the *PREPAIR* technique for code evaluation. By caching pointwise reasoning results before pairwise comparison, we eliminate evaluation bias and reduce LLM "laziness" during code selection.
- **Dynamic Prompts with Contextual Embedding**: Modular prompt system that only loads what is necessary (logs, diffs, or code chunks) on-demand, saving up to 60% in token costs for routine tasks.

---
> **Boring is now primarily an MCP tool (used via Cursor / Claude Desktop / IDE)**
> 
> - ❌ **Not recommended to run `boring start` directly in CMD/terminal**: Gemini CLI no longer supports free authorization (unless using API, which is not well-tested)
> - ✅ **Recommended usage**: Use Boring tools through Smithery or MCP config in your IDE or Client
> - ✅ **Monitoring tools still work**: `boring-monitor`, `boring-dashboard` can be run locally
> 
> Most features are optimized for the MCP environment. CLI mode is no longer the primary supported method.

---

## 🚀 Quick Start

## 📦 Installation

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

| Feature | `[all]` (Full / Local) | `Lite` (Basic / Smithery Default) |
| :--- | :--- | :--- |
| **RAG Memory** | ✅ Vector + Semantic | ⚠️ Keyword only (No vector DB) |
| **Self-Verify** | ✅ Can run tests (`boring verify`) | ❌ Cannot verify (Missing pytest) |
| **Dashboard** | ✅ GUI Available | ❌ None |
| **Vibe Coding**| ✅ **Full Experience** (Think + Fix) | ⚠️ **Lite** (Write code only) |

### ⚙️ MCP Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `BORING_MCP_MODE` | `1` (required) | Enable MCP mode |
| `BORING_MCP_PROFILE` | `ultra_lite` / `minimal` / `lite` / `standard` / `full` | Tool exposure level |
| `PROJECT_ROOT_DEFAULT` | `.` or path | Default project root |

**Profile Comparison:**

| Profile | Tools | Token Savings | Best For |
|---------|-------|---------------|----------|
| `ultra_lite` | 3 | **97%** | Token-constrained LLMs |
| `minimal` | 8 | 92% | Quick tasks |
| `lite` | 20 | 80% | Daily dev (Default) |
| `standard` | 50 | 50% | Professional dev |
| `full` | ~98 | 0% | Power Users |

> 📖 **[Full MCP Configuration Guide](docs/guides/mcp-configuration_en.md)**

### Option 3: Clone from GitHub (Fallback)

> **Best for: Developers or if pip install fails**

```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e .
```

---

---

## 🚀 Usage

### 1️⃣ MCP Mode (Recommended)
Add Boring to your **Cursor** or **VS Code** config. The Agent will become an autonomous engineer in your IDE.

- **Prompts**: Click the ✨ button or use `Cmd+I` to select a prompt.
- **Workflows**: Type `/` in Chat to trigger a workflow.

#### 💎 Top 5 Most Used Functions

**[👉 View Complete Reference Manual (All 30+ Functions)](docs/reference/prompts.md)**

| Command | Type | Description |
| :--- | :--- | :--- |
| **`vibe_start`** | Prompt | **One-click project kick-off**. From idea to architecture plan. |
| **`quick_fix`** | Prompt | **Auto-fix everything**. Repairs lint errors and bugs. |
| **`/speckit-plan`** | Workflow | **Technical Planning**. Creates a detailed implementation plan. |
| **`smart_commit`** | Prompt | **Auto Commit**. Generates commit message from progress. |
| **`review_code`** | Prompt | **Architect Review**. Deep code analysis for issues. |


### 2️⃣ Maintenance Commands
Run these commands in your terminal:

```bash
# Install Git Hooks (Auto-verify commits)
python -m boring hooks install

# Open Dashboard (Web UI)
python -m boring dashboard

# Check Health
python -m boring status
```

### 3️⃣ LSP Server (Optional - For VS Code / Neovim Only)

> [!NOTE]
> **Cursor users: You DON'T need LSP!** Cursor has built-in AI features. Just use MCP config above.
>
> LSP is for: VS Code (without AI), Neovim, and other terminal editors.

**What's the difference?**
| | MCP | LSP |
|---|-----|-----|
| **Purpose** | AI Agent tools (chat commands) | Editor syntax services |
| **Interaction** | Chat: "Review my code" | Auto-complete, diagnostics |
| **Required?** | ✅ **Yes** | ⚠️ Optional |

<details>
<summary>🔧 <b>LSP Configuration (click to expand)</b></summary>

1. **Install**:
   ```bash
   pip install "boring-aicoding[all]"
   ```

2. **VS Code** (`settings.json`):
   ```json
   {
     "boring.lsp.enabled": true,
     "boring.lsp.command": "python",
     "boring.lsp.args": ["-m", "boring", "lsp", "start"]
   }
   ```

3. **Neovim** (`nvim-lspconfig` - for Linux/Mac terminal users):
   ```lua
   require('lspconfig').boring.setup {
     cmd = { "python", "-m", "boring", "lsp", "start" },
     filetypes = { "python", "javascript", "typescript" },
   }
   ```
</details>

> [!CAUTION]
> **DO NOT run `python -m boring lsp start` directly in terminal.**
> This command is for editor configuration only. The LSP server communicates via stdin/stdout.

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
| **Features** | [MCP Tools (55+)](docs/features/mcp-tools.md) · [Shadow Mode](docs/features/shadow-mode.md) · [Quality Gates](docs/features/quality-gates.md) · [Monitoring](docs/features/monitor.md) · **[📊 Evaluation Metrics](docs/guides/evaluation-metrics.md)** |
| **Guides** | [Cookbook](docs/guides/cookbook.md) · [Pro Tips](docs/guides/pro-tips.md) · [Git Hooks](docs/guides/git-hooks.md) · [Workflows](docs/guides/workflows.md) |
| **Learning** | [Tutorials](docs/tutorials/TUTORIAL.md) · [Skills Guide](docs/guides/skills_guide.md) · [Knowledge Mgmt](docs/guides/knowledge-management.md) |
| **Advanced** | [Plugins](docs/guides/plugins.md) · [API Integration](docs/guides/api-integration.md) · [Human Alignment](docs/guides/human-alignment.md) |
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
| 🔍 `boring_skills_browse` | **Skills Discovery** - Find and install MCP skills | `boring_skills_browse(query="web")` |

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


## 🧠 External Intelligence

Boring integrates the most powerful external MCP tools by default, turning the Agent into a super engineer.

| Tool | Function | How to Use |
|------|----------|------------|
| **Context7** | 📚 **Real-time Docs**<br>Query latest library usage, solving stale training data issues. | `context7_query_docs` |
| **Sequential Thinking** | 🤔 **Deep Thinking**<br>Force Agent into a full chain of thought from analysis to verification before coding. | `sequentialthinking` |
| **Critical Thinking** | 🧐 **Critical Thinking**<br>Self-reflection and blind spot detection for high-quality Code Review. | `boring-route "think deeper"` |
| **Boring Monitor** | 🖥️ **TUI Dashboard**<br>Real-time terminal view of status, logs (v10.23+). | `boring-monitor` / `python -m boring.monitor` |
| **Boring Dashboard**| 🎨 **GUI Dashboard**<br>Comprehensive web view with Brain Explorer. | `boring-dashboard` / `python -m boring dashboard` / `python -m boring.monitor --web` |

## 🚀 Performance (v10.21.0)
- **Thread-local SQLite**: Zero-overhead DB connections.
- **WAL Mode**: 50% faster concurrent reads.
- **Smart Caching**: 30s query cache & Pattern cache for instant RAG.

---

## 🛡️ Shadow Mode

Shadow mode protects you from destructive AI operations:

```
DISABLED  ⚠️  No protection (Container only)
ENABLED   🛡️  Auto-approve safe, Block risky (Default)
STRICT    🔒  Approve all writes (Production)
```

```python
boring_shadow_mode(action="set_level", level="STRICT")
```

---


## 🔧 Troubleshooting & Environment

### Common Issues

**1. "Command not found" or Wrong Python Version**
If running `boring` commands fails or uses the wrong Python environment (e.g., system Python instead of venv), use `python -m`:

```bash
# ✅ Recommended usage for reliability
python -m boring --help
python -m boring hooks install
```

**2. "tree-sitter-languages not installed" Warning**
This means the advanced code parser is missing. RAG features will be limited to keyword search only.

**Fix**:
```bash
pip install tree-sitter-languages
# Or update all dependencies
pip install "boring-aicoding[all]"
```

---

## 🎯 Future Vision

**Note: The following features require server support (not yet implemented)**

- **🌐 Boring Cloud**: Cloud collaboration and team sharing
- **🤝 Team Workflows**: Multi-person workflow synchronization
- **🔐 Enterprise SSO**: Enterprise-grade identity authentication


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
