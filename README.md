[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-10.18.1-green.svg)](https://github.com/Boring206/boring-gemini)
[![Evaluation](https://img.shields.io/badge/Smithery-58%2F58-brightgreen.svg)](https://smithery.ai/server/boring/boring)
[![smithery badge](https://smithery.ai/badge/boring/boring)](https://smithery.ai/server/boring/boring)

# Boring: Your Autonomous Coding Partner for Vibe Development

> **Enterprise-grade Autonomous AI Development Agent**  
> A full-language automated coding and verification engine built for Cursor / Claude Desktop / VS Code / Gemini CLI.

**[中文版 README](README_zh.md)**

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

> **Best for: Multi-project workflows, frequent project switching, cloud-based development**

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

✅ **Advantages**: Automatic updates, consistent environment, no path issues  
⚠️ **Note**: Requires npx/Node.js installed

### Option 2: Local pip Installation

> **Best for: Single-project development, CI/CD pipelines, offline environments**

```bash
# Basic installation (core features)
pip install boring-aicoding

# Full installation with all features (RAG, MCP, GUI, Vector Search)
pip install "boring-aicoding[all]"

# Or install specific extras:
pip install "boring-aicoding[mcp]"     # MCP server support (includes RAG)
pip install "boring-aicoding[vector]"  # Pure RAG/Vector search (chromadb, sentence-transformers)
pip install "boring-aicoding[gui]"     # Streamlit dashboard
pip install "boring-aicoding[dev]"     # Development tools
```

> ⚠️ **Path Issue Warning**: Local installation may encounter path issues when switching between different project directories. For multi-project workflows, we recommend **Smithery deployment**.

### MCP Configuration

#### For Smithery (Recommended)

In `mcp_config.json` or IDE settings:

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

#### For Local pip Installation

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

## 🎮 Two Usage Modes

### Mode 1: MCP/Smithery (Recommended for most users)

Use Boring tools directly inside **Gemini CLI**, **Cursor**, or **Claude Desktop**:

```
You (in Gemini CLI): "Help me build a FastAPI auth service"
                     or
                     "/vibe_start Build an auth service"

Gemini + Boring: "Sure! Let me ask a few questions first..."
```

✅ No `PROMPT.md` required  
✅ Interactive conversation  
✅ Works with any MCP-compatible client

### Mode 2: Autonomous Loop (`boring start`)

For **long-running, fully automated development** via CLI:

```bash
# Requires PROMPT.md in project root (created via boring-setup)
boring-setup my-project              # 1. Initialize project (Required!)
cd my-project                        # 2. Enter project directory
boring start                         # 3. Start autonomous loop
boring start --provider claude-code  # Use Claude Code CLI
boring start --provider gemini-cli   # Use Gemini CLI
boring run "Fix all lint errors"     # One-shot command
```

**Required files for `boring start`:**
```
your-project/
├── PROMPT.md      # ✅ Required - Instructions for AI
├── @fix_plan.md   # Optional - Task checklist
└── GEMINI.md      # Optional - Project context
```

---

## 📚 Complete Documentation

### Tutorials & Guides
| Document | Description | Audience |
|----------|-------------|----------|
| [**Getting Started**](docs/getting-started/installation.md) | Installation, first steps, MCP setup | New users |
| [**🔥 Practical Demo**](docs/PRACTICAL_DEMO_en.md) | 10-min hands-on showcase, 6 real-world examples | 🆕 Vibe Coders |
| [**Complete Tutorial**](docs/TUTORIAL_en.md) | Quick start, core workflows, practical examples | All developers |
| [**Advanced Developer Guide**](docs/ADVANCED_TUTORIAL.md) | Architecture deep dive, tool development, internals | Senior developers |
| [**Professional Playbook**](docs/PROFESSIONAL_PLAYBOOK_en.md) | 18 expert workflows with `/slash` commands | Senior developers |

### Reference & Appendices
| Document | Description | Audience |
|----------|-------------|----------|
| [**Tool Reference (Appendix A)**](docs/APPENDIX_A_TOOL_REFERENCE.md) | Complete 55+ MCP tools reference | Quick lookup |
| [**FAQ (Appendix B)**](docs/APPENDIX_B_FAQ.md) | Installation, troubleshooting, API key questions | When encountering issues |
| [**Prompt Philosophy (Appendix C)**](docs/APPENDIX_C_PROMPT_PHILOSOPHY.md) | Architect persona design principles | Prompt engineers |
| [**Architect Mode**](docs/architect_mode.md) | Hostile Architect evaluation mode | Production code review |

---


## ⚡ Performance & Architecture

### 1. Incremental Verification
- **Smart Caching**: `.boring_cache/verification.json` stores file hashes.
- **Speed**: Re-verifying 100+ unchanged files takes <2 seconds.
- **Force Mode**: Use `boring verify --force` to bypass cache.

### 2. Incremental RAG Indexing
- **State Tracking**: Only re-indexes changed files.
- **CLI**: `boring rag index` (incremental by default).

### 3. Private AI & Tool Switching
- **Supported Modes**: Gemini CLI (recommended), Claude Code CLI (recommended), Ollama (local), SDK (API Key).
- **Auto-detection**: System automatically detects local command tools at startup.
- **Configuration**:
  ```bash
  # Run with custom timeout
  boring start --timeout 60
  
  # One-Shot Command (New!)
  boring run "Review this code and fix bugs"
  boring start --provider claude-code
  boring verify --provider gemini-cli
  ```

### 4. Quality Trend Tracking
- **History Recording**: Audit scores stored in `.boring_brain/quality_history.json`.
- **Visualization**: Use `boring_quality_trend` tool to draw ASCII trend charts.

### 5. Parallel Verification (V10.13)
- **Concurrent Processing**: Uses `ThreadPoolExecutor` to maximize CPU utilization for large projects.
- **Speed Boost**: 3x-5x faster verification on clean builds.
- **Real-time Progress**: Rich CLI progress bar independent of CI logs.

### 6. Contrastive Evaluation
- **A/B Testing**: Use `evaluate --level PAIRWISE` to compare two implementations side-by-side.
- **LLM Judge**: AI selects winner based on correctness, logic, and efficiency.
- **Bias Mitigation**: Automatic position bias handling via A/B/A order verification.

### 7. Developer Experience
- **Config File**: `.boring.toml` for project-specific rules.
- **Custom Prompts**: Override Judge Prompts in `[boring.prompts]`.
- **Linter Override**: Customize tool parameters in `[boring.linter_configs]`.

---

## 🛠️ MCP Toolset (Consolidated & Dynamic)

Boring V10.16 adopts **Dynamic Discovery Architecture** to solve context overflow caused by too many tools.

### 🔎 Dynamic Discovery (AI Only)
- **`boring://capabilities`**: Read this resource to discover all available capabilities.
- **`boring://tools/{category}`**: Read detailed tool usage for a specific category.

### 🧰 Core Tools (Consolidated)

To reduce context consumption, we consolidated 50+ tools into 14 high-level entry points:

| Category | Main Tool | Description |
|----------|-----------|-------------|
| **Security** | `boring_security_scan` | SAST, secret detection, dependency scanning (Bandit/Safety) |
| **Transactions** | `boring_transaction` | Atomic Git operations (Start/Commit/Rollback) |
| **Background** | `boring_task` | Async background tasks (Verify/Test/Lint) |
| **Context** | `boring_context` | Cross-session memory save/load |
| **Profile** | `boring_profile` | User preferences and cross-project learning |
| **Verification** | `boring_verify` | Multi-level code verification (Basic/Standard/Full) |
| **RAG Memory** | `boring_rag_search` | Semantic search and dependency context retrieval. Use `boring_rag_reload` to hot-reload dependencies after installation. |
| **Agents** | `boring_multi_agent` | **[PROMPT GENERATOR / EXECUTOR]** Returns prompts or executes workflow in background (`execute=True`). Helper tools: `boring_prompt_plan`, `boring_prompt_fix` |
| **Shadow** | `boring_shadow_mode` | Safe sandbox for high-risk operations |
| **Git** | `boring_commit` | Semantic commit message generation from task.md (used by `smart_commit` prompt) |
| **Workspace** | `boring_workspace_switch` | Multi-project workspace switching |
| **Knowledge** | `boring_learn` | Project knowledge extraction and storage |
| **Plugins** | `boring_run_plugin` | External plugin execution |
| **Evaluation** | `boring_evaluate` | LLM-as-Judge code scoring |

### 🧠 MCP Intelligence (V10.18+)

| Feature | Description |
|---------|-------------|
| **Auto Pattern Detection** | `AutoLearner` automatically extracts error→solution patterns from AI responses |
| **RAG Auto-Update** | `RAGWatcher` detects file changes and triggers incremental re-indexing |
| **Cross-Project Knowledge** | `GlobalKnowledgeStore` shares learned patterns via `~/.boring_brain/` |
| **Smart Suggestions** | `boring_suggest_next` now includes git changes, task progress, and learned patterns |

### 🚀 Quick Start Prompts

One-click workflows designed for Claude Desktop / Gemini CLI users:

| Prompt | Purpose | Usage |
|--------|---------|-------|
| `vibe_start` | Launch complete development workflow | `/vibe_start Build a FastAPI auth service` |
| `quick_fix` | Auto-fix all code issues | `/quick_fix` |
| `full_stack_dev` | Full-stack app development | `/full_stack_dev my-app "Next.js + FastAPI"` |

> 💡 **Vibe Coding Mode**: Describe your idea, let AI handle the rest!

### 🚀 Quick Start
Use **Slash Commands** to jumpstart your development:

1. **Start Boring**:
   ```bash
   boring start
   ```

2. **Enter Command**:
   ```text
   /vibe_start Build a FastAPI auth service
   ```

   Or for specific tech stacks:
   ```text
   /full_stack_dev my-app "Next.js + Tailwind + Supabase"
   ```

> **Note**: All templates and shortcuts are now consolidated into Slash Commands (Prompts) for a unified experience.

# List available templates
boring templates list
```

**Built-in Templates:**
| Template ID | Description |
|-------------|-------------|
| `fastapi-auth` | FastAPI + JWT authentication service |
| `nextjs-dashboard` | Next.js admin dashboard |
| `cli-tool` | Python CLI tool (Typer) |
| `vue-spa` | Vue 3 single-page application |

---

## 📊 Live Monitoring

Two monitoring options for terminal lovers and visual dashboards:

- **Terminal Dashboard (TUI)**: Run `boring-monitor`. Displays status, API call counts, and recent logs in terminal.
- **Web Dashboard**: Run `boring-dashboard`. Streamlit-powered visual interface with project trends and knowledge base inspection.

---

## 🌐 Supported Languages

| Language | Syntax Check | Linter | Test Runner |
|----------|--------------|--------|-------------|
| Python | ✅ compile() | ✅ ruff | ✅ pytest |
| JS/TS | ✅ node --check | ✅ eslint | ✅ npm test |
| Go | ✅ go fmt | ✅ golangci-lint | ✅ go test |
| Rust | ✅ rustc | ✅ cargo clippy | ✅ cargo test |
| Java | ✅ javac | - | ✅ mvn/gradle |
| C/C++ | ✅ gcc/g++ | ✅ clang-tidy | - |

---

## 💡 Pro Tips

### Tip 1: SpecKit Workflow (5 Steps)

Before writing code, Boring guides you through:

1. `speckit_constitution` → Establish Principles (Constitution)
2. `speckit_clarify` → Clarify Requirements
3. `speckit_plan` → Create Implementation Plan
4. `speckit_checklist` → Build Acceptance Criteria
5. `speckit_analyze` → Verify Consistency (Spec vs Plan)

> **"Measure Twice, Cut Once"** - AI implementation!

### Tip 2: Use Hybrid Mode

| Task Type | Recommended Tool |
|-----------|------------------|
| Small changes | `boring_apply_patch` |
| Large features | `run_boring` + SpecKit |
| Quality check | `boring_evaluate` |

### Tip 3: Accumulate Experience

```
Develop → AI fixes errors → Record to .boring_memory
Project ends → boring_learn → Extract patterns to .boring_brain
Next project → AI auto-references!
```

### Tip 4: Custom Lint Rules

Create `ruff.toml`:

```toml
line-length = 120
[lint]
ignore = ["T201", "F401"]  # Allow print() and unused imports
```

---

## 📚 Quick Tutorials

### 1. New Project Development

```
You: Help me create a TypeScript API project
AI: (runs speckit_plan) Generating implementation_plan.md...
You: Approve this plan
AI: (runs boring_multi_agent) Starting Plan→Code→Review loop...
```

### 2. Code Verification

```
You: Verify the code quality of this project
AI: (runs boring_verify --level FULL) 
    ✅ Syntax check passed
    ⚠️ Found 3 lint issues
    ✅ Tests passed (12/12)
```

### 3. RAG Search

```
You: I want to find code that handles user authentication
AI: (runs boring_rag_search "user authentication")
    Found 3 related functions:
    1. auth.py:verify_token (L23-45)
    2. middleware.py:require_auth (L67-89)
    ...
```

---

## 🔌 Git Hooks

Automatically verify code before commit/push:

```bash
boring hooks install    # Install
boring hooks status     # Status
boring hooks uninstall  # Remove
```

| Hook | Trigger | Verification Level |
|------|---------|-------------------|
| pre-commit | Every commit | STANDARD |
| pre-push | Every push | FULL |
| quick-check | Every commit | QUICK (multi-language) |

---

## 🆕 V10.17.5 New Features - Protected File Tools 🛡️

### Secure File Operations
We introduced `boring_write_file` and `boring_read_file` to provide robust security guarantees within Shadow Mode.

> [!IMPORTANT]
> **Security Warning**: Standard MCP tools like `write_file` (provided by some clients) are **NOT** intercepted by Shadow Mode. For secure, audited file operations, always use `boring_write_file`.

- **`boring_write_file`**: Writes content with strict path validation and Shadow Mode approval (in STRICT mode).
- **`boring_read_file`**: Reads content safely within project boundaries.

## 🆕 V10.16.3 New Features (Security & Stability)

### 1. Enhanced Shadow Mode 🛡️
**What is Shadow Mode?**
Shadow Mode is the security core of Boring, acting as a **mandatory interception layer** between the AI and your file system.
- **Function**: It intercepts all destructive operations (e.g., file writes, deletions, command execution).
- **Workflow**: AI requests operation -> Shadow Mode evaluates impact -> Puts in pending queue -> Requires YOUR approval (`boring_shadow_approve`) to execute.
- **Strict Enforcement**: In v10.16.3, we patched all bypasses. Even background agent patches or minor edits require approval if you are in `STRICT` mode.

**Three Modes:**
- **DISABLED** (⚠️ Risky): No interception. For isolated containers only.
- **ENABLED** (🛡️ Default): Auto-approves low-risk ops (reads), blocks high-risk ops.
- **STRICT** (🔒 Secure): Intercepts **ALL** write operations. Highest security level.

### 2. Robust Transactions 💾
**Non-Interactive Git**: `boring_transaction` now automatically bypasses GPG/credential prompts, preventing CI hangs.

### 3. Smart RAG Environment 🧠
**Auto-Discovery**: RAG tools now automatically find user-installed Python packages (`chromadb`), solving "module not found" issues in isolated environments.

## 🆕 V10.16.0 New Features

### 1. Quality Gates (CI/CD)

Project includes `.github/workflows/quality-gates.yml`:

```yaml
# Auto-runs on push to GitHub
Tier 1: Lint & Format     # ruff check, ruff format
Tier 2: Security Scan     # bandit, safety
Tier 3: Unit Tests        # pytest --cov-fail-under=39
Tier 4: Integration Tests # main branch only
```

### 2. Project Configuration (.boring.toml)

Create `.boring.toml` in project root for custom quality policies:

```toml
[boring.quality_gates]
min_coverage = 40           # Minimum coverage
max_complexity = 15         # Maximum complexity
max_file_lines = 500        # Maximum file lines
```

### 3. Evaluation Rubric (LLM Judge)

Use standardized rubrics for code quality evaluation:

```bash
boring_evaluate --target src/main.py --level DIRECT
```

### 4. Quick Multi-language Check

```bash
# Install Quick Check Hook
boring hooks install
```

---

## 🆕 V10.15 New Features

### 1. Incremental Verification (Git-based)

```bash
# Verify only Git-changed files
boring verify --incremental

# MCP call
boring_verify(incremental=true)
```

### 2. Multi-project RAG Search

```python
boring_rag_search(
    query="authentication middleware",
    additional_roots=["/path/to/other-project"]
)
```

### 3. Dependency Graph Visualization

```bash
boring_visualize --scope full --output mermaid
```

### 4. Parallel Review (Multi-Reviewer)

```bash
boring_agent_review --parallel
```

### 5. VS Code Integration (JSON-RPC Server)

Enables native development experience in editors:

1. **Real-time Error Hints**: Red squiggles in code on save
2. **Quality Score CodeLens**: Display `Quality: 4.5/5` above functions
3. **Sidebar Semantic Search**: Natural language code search
4. **One-click Quick Fix**: Auto-fix via lightbulb icon

```json
// .vscode/settings.json
{
  "boring.enableServer": true,
  "boring.port": 8765
}
```

### 6. Other IDE Support (LSP & CLI)

- **Cursor / VS Code derivatives**: Full support via MCP Server
- **IntelliJ / PyCharm / Vim**: Run `boring lsp start --port 9876` for JSON-RPC server
- **CLI Mode**: All automation available via `boring` command

### 7. Error Diagnostics

Auto-analyze errors and suggest fixes:

```bash
boring_diagnose --error "ModuleNotFoundError: No module named 'foo'"
```

---

## 🎯 Future Vision

> **Note**: The following features require server support (not yet implemented)

- 🌐 **Boring Cloud**: Cloud collaboration and team sharing
- 🤝 **Team Workflows**: Multi-person workflow synchronization
- 🔐 **Enterprise SSO**: Enterprise-grade identity authentication

---

## 🙏 Acknowledgments

Thanks to the following projects and communities:

- [Google Gemini](https://deepmind.google/technologies/gemini/) - Powerful AI model
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standardized AI tool protocol
- [Tree-sitter](https://tree-sitter.github.io/) - Efficient multi-language parser
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Ruff](https://docs.astral.sh/ruff/) - Ultra-fast Python Linter
- [FastMCP](https://github.com/jlooper/fastmcp) - MCP Server framework
- All Contributors and users!

---

## 📄 License

[Apache License 2.0](LICENSE)

---

## 🔗 Links

- [GitHub Repository](https://github.com/Boring206/boring-gemini)
- [Smithery](https://smithery.ai/server/boring/boring)
- [Bug Reports](https://github.com/Boring206/boring-gemini/issues)
- [CHANGELOG](CHANGELOG.md)
- [Contributing Guide](CONTRIBUTING.md)
