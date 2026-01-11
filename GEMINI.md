# GEMINI.md - Boring for Gemini (V11.1.0)

## Project Overview

This repository contains **Boring for Gemini**, an autonomous AI development loop system. The project uses an AI coding assistant (the `@google/gemini-cli` CLI) to iteratively work on a software project until a defined goal is met.

The system is built entirely in **Python**, using modern CLI frameworks and rich console output.

**Core Features:**
- **Autonomous Development Loop:** Continuously runs the Gemini AI agent against a codebase based on instructions in a `PROMPT.md` file.
- **Intelligent Exit Detection:** The loop automatically terminates when it detects project completion through multiple signals (done signals, task list completion, test saturation).
- **Safeguards:** Implements rate limiting (to manage API costs), a circuit breaker (to prevent getting stuck in failing loops), and graceful handling of API usage limits.
- **Live Monitoring:** Provides real-time monitoring of the agent's status, logs, and API call usage via `boring-monitor`.
- **🆕 Zero-Config Wizard (V10.32):** One-click `boring wizard` to auto-configure MCP for Claude Desktop, Cursor, and VS Code.
- **🆕 Brain Reflex (V10.31):** Active Recall mechanism that automatically retrieves solutions for known errors from the Brain.
- **🆕 Cognitive Architecture (V11.0):** System 2 ReasoningState, Active Causal Memory, and Live Tool Synthesis (`boring_synth_tool`).
- **🆕 Safety Net (V10.31):** Autonomous Git Checkpoints (`boring_checkpoint`) allowing the Agent to save/restore state before risky ops.
- **🆕 Theme-Tips Output (V10.27):** Hierarchical tool output format for better LLM comprehension (+1.13% accuracy).
- **🆕 PRO-Files (V10.32):** Standard/Lite/Full/Custom profile selection for granular token and feature control.
- **🆕 PREPAIR Reasoning Cache (V10.27):** Caches pointwise analysis before pairwise comparisons, reducing evaluation bias.
- **🆕 Dynamic Prompts (V10.27):** MCP prompts with contextual embedding (logs, diffs, code) on-demand.
- **🆕 Token Economy (V10.26):** ULTRA_LITE profile with 97% token savings via progressive disclosure (`boring_discover` tool).
- **🆕 Hybrid RAG (V10.17):** Combined Vector + Keyword search with dependency graph expansion.
- **🆕 Security Guard (V10.17):** Cross-session persistent Shadow Mode and multi-file-type security scanning.
- **🆕 Knowledge Base (~/.boring/brain):** Persistent storage for workflow adaptations, learned patterns, and evaluation rubrics.

**Technology Stack:**
- **Language:** Python 3.9+
- **CLI Framework:** [Typer](https://typer.tiangolo.com/) with [Rich](https://rich.readthedocs.io/) for beautiful console output
- **Testing:** [Pytest](https://pytest.org/)
- **Key Dependencies:**
  - `@google/gemini-cli` (the AI agent, installed via npm)
  - `gitpython` (for Git operations)
  - `tenacity` (for retries)
  - `fastmcp` (for MCP server)

## Building and Running

### 1. Installation

**Recommended: One-Click Bootstrapper (Vibe Coder Way)**

Windows (PowerShell):
```powershell
./scripts/install.ps1
```

Linux/macOS:
```bash
./scripts/install.sh
```

**Alternative: Manual pip**

Install Boring as a Python package:

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/boring-gemini.git
cd boring-gemini

# Install in development mode
pip install -e .

# Configure Editor
boring wizard
```

This installs the following CLI commands:
- `boring` - Main autonomous loop
- `boring-monitor` - Live monitoring dashboard
- `boring-setup` - Create new Boring projects
- `boring-import` - Import PRD into a new project

### 2. Project Setup (Per-Project)

For each new project you want the agent to work on, initialize a Boring-compatible directory structure:

```bash
# Option A: Create a new, blank project
boring-setup <your-project-name>
cd <your-project-name>

# Option B: Import an existing Product Requirements Document (PRD)
boring-import <path-to-your-prd.md> <your-project-name>
cd <your-project-name>
```

### 3. Running the Agent

Once a project is set up, start the autonomous development loop:

```bash
# Navigate to the project directory
cd <your-project-name>

# Start the Boring loop
boring start

# With options
boring start --calls 50 --timeout 20 --verbose

# Check current status
boring status

# View circuit breaker status
boring circuit-status

# Reset circuit breaker after fixing issues
boring reset-circuit
```

### 4. Running Tests

The project uses **pytest** for testing:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_core.py
```

## Development Conventions

- **Testing:** All functionality is tested using **pytest**. Tests are located in the `tests/` directory.
- **Code Style:** Python code follows PEP 8 conventions.
  - Type hints are used throughout
  - Rich console output for user-facing messages
  - Logging via the `log_status` function
- **Modularity:** Core logic is organized in `src/boring/`:
  - `main.py` - CLI entry point and main loop
  - `intelligence/` - Brain Manager, Memory, Auto Learner, Pattern Mining
  - `loop/` - Background Agent, Shadow Mode, Workflow Manager, Transactions
  - `mcp/` - Model Context Protocol Server & Tools
  - `judge/` - Evaluation Rubrics and LLM Judge
  - `cli/` - Command-line interface subcommands
  - `services/` - Web Monitor and Health Checks
  - `setup.py` - Project scaffolding
- **AI-Facing Documentation:**
  - `PROMPT.md` - Primary instructions for the AI for a given project
  - `GEMINI.md` - Context about Boring's tools and environment
  - `@fix_plan.md` - Prioritized task checklist for the AI
- **State Management:** Loop state is managed through hidden files:
  - `.call_count` - API call counter
  - `.last_reset` - Rate limit reset timestamp
  - `.exit_signals` - Exit detection signals (JSON)
  - `.circuit_breaker_state` - Circuit breaker state (JSON)
- **Git Usage:** Projects are expected to be Git repositories. Boring uses Git to detect file changes between loops.

## CLI Commands Reference

| Command | Description |
|---------|-------------|
| `boring start` | Start the autonomous development loop |
| `boring wizard` | **(New)** Zero-Config Setup Wizard for MCP |
| `boring status` | Show current loop status |
| `boring circuit-status` | Show circuit breaker state |
| `boring reset-circuit` | Reset circuit breaker to CLOSED |
| `boring-setup <name>` | Create a new Boring project |
| `boring-import <prd> <name>` | Import a PRD into a new project |
| `boring-monitor` | Start the live monitoring dashboard |

## External Tools & MCP Integration

**Important Note:** The Model Context Protocol (MCP) integrations referenced here (such as `notebooklm-mcp`) are designed specifically for the `@google/gemini-cli`. If you are using other clients or environments, you will need to configure these MCP servers independently according to their respective documentation.

## Exit Conditions

The loop automatically exits when detecting:
- `MAX_CONSECUTIVE_TEST_LOOPS = 3` — Too many test-only iterations
- `MAX_CONSECUTIVE_DONE_SIGNALS = 2` — Multiple completion signals
- All items in `@fix_plan.md` marked as completed
- Strong completion indicators in AI responses

## Circuit Breaker

The circuit breaker prevents infinite loops when the AI gets stuck:
- **CLOSED** — Normal operation
- **OPEN** — Execution halted after consecutive failures
- **HALF_OPEN** — Testing recovery after timeout

Reset with: `boring reset-circuit`