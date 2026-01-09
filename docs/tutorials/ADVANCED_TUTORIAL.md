# Boring for Gemini: Advanced Developer Guide

> **Audience**: Senior/Staff Engineers who want to understand the internals, extend the platform, or integrate it into enterprise workflows.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Client (Claude/Gemini)                │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol (stdio/HTTP)
┌─────────────────────────▼───────────────────────────────────┐
│                    FastMCP Server Layer                     │
│  ┌─────────────┬────────────────┬─────────────────────────┐ │
│  │ V9 Tools    │ V10 Tools      │ Advanced Tools          │ │
│  │ (Plugins,   │ (RAG, Agents,  │ (Security, Transactions,│ │
│  │  Workspace) │  Shadow Mode)  │  Background, Context)   │ │
│  └─────────────┴────────────────┴─────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Dynamic Discovery Resources                │ │
│  │  boring://capabilities  |  boring://tools/{category}   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Discovery-First**: ~55 tools consolidated into 14 categories. AI queries `boring://capabilities` first.
2. **Transactional Safety**: Git-based rollback for risky operations.
3. **Async by Default**: Long tasks (test, verify, security scan) run in background threads.
4. **Memory Persistence**: Cross-session context via SQLite + vector embeddings.

---

## 1.5. Universal Router & Tool Profiles (V10.24)

The **Universal Router** is the single gateway to all Boring tools. It uses keyword matching and category selection to route natural language intent to the right tools.

### Architecture
```
                  User: "Help me write tests" 
                              ↓
┌────────────────────────────────────┐
│  ToolRouter.route("write tests")  │
│        ↓                          │
│   KeywordMatch: testing (95%)     │
│        ↓                          │
│   → boring_test_gen              │
└────────────────────────────────────┘
```

### Tool Profiles
To reduce LLM context, use profiles:

| Profile | Tools | Use Case |
|---------|-------|---------|
| `minimal` | 8 | Simple single-tool workflows |
| `lite` | 20 | **Default** - daily dev work |
| `standard` | 50 | Full-featured projects |
| `full` | 98+ | Power users, everything exposed |

**Config** (`.boring.toml`):
```toml
[boring.mcp]
profile = "lite"
```

**CLI**:
```bash
boring-route "幫我寫測試"  # 自動路由到 boring_test_gen
boring-route "search for auth logic"  # 自動路由到 boring_rag_search
```

---

## 2. MCP Tool Registration Deep Dive

### Entry Point: `src/boring/mcp/server.py`

```python
def get_server_instance():
    """Configure and return the FastMCP server."""
    # V9: Plugins, Workspace, Auto-Fix
    register_v9_tools(mcp, audited, helpers)
    
    # V10: RAG, Multi-Agent, Shadow Mode
    register_v10_tools(mcp, audited, helpers)
    
    # V10.16: Security, Transactions, Background, Context
    register_advanced_tools(mcp)
    
    # Dynamic Discovery Resources
    register_discovery_resources(mcp)
```

### Creating a New Tool

```python
# src/boring/mcp/tools/my_tool.py
from pydantic import Field
from boring.mcp.instance import mcp

@mcp.tool()
def boring_my_tool(
    target: str = Field(description="Target path to process"),
    mode: str = Field(default="standard", description="Processing mode"),
) -> str:
    """One-line description shown in MCP."""
    # Implementation
    return {"status": "success", "result": ...}
```

> **Important**: All parameters MUST use `Field(description=...)` for Smithery schema generation.

---

## 3. Dynamic Discovery System

### How It Works

```python
# src/boring/mcp/tools/discovery.py
CAPABILITIES = {
    "security": {
        "description": "Security scanning, secret detection",
        "tools": ["boring_security_scan"],
        "docs": "Use boring_security_scan to check for vulnerabilities.",
    },
    # ... 13 more categories
}

@mcp.resource("boring://capabilities")
def get_capabilities() -> str:
    """AI calls this first to understand available tools."""
    return json.dumps(CAPABILITIES)
```

### AI Workflow
1. AI calls `boring://capabilities` → gets category list
2. AI calls `boring://tools/security` → gets detailed usage
3. AI invokes `boring_security_scan()`

---

## 4. Transaction & Rollback Pattern

### Usage
```python
# Start transaction (creates git stash)
boring_transaction_start(message="Refactoring auth module")

# Make risky changes...
boring_multi_agent(task="Refactor authentication")

# Verify
result = boring_verify(level="FULL")

if result["passed"]:
    boring_transaction_commit()  # Finalize
else:
    boring_rollback()  # Restore previous state
```

### Internals (`src/boring/transactions.py`)
- Uses `git stash` for atomic savepoints
- Tracks transaction stack for nested operations
- Auto-rollback on unhandled exceptions

---

## 5. Background Task System

### Architecture
```
┌──────────────────┐     ┌─────────────────────┐
│  MCP Tool Call   │────▶│ BackgroundTaskRunner│
│  (non-blocking)  │     │  (ThreadPoolExecutor)│
└──────────────────┘     └──────────┬──────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
  ┌─────────┐                 ┌─────────┐                  ┌─────────┐
  │ verify  │                 │  test   │                  │ security│
  │  task   │                 │  task   │                  │  scan   │
  └─────────┘                 └─────────┘                  └─────────┘
```

### Usage
```python
# Submit task
result = boring_background_task(task_type="verify", task_args={"level": "FULL"})
task_id = result["task_id"]  # "task-a1b2c3d4"

# Check status (non-blocking)
status = boring_task_status(task_id=task_id)
# {"status": "running", "progress": 45, ...}

# List all active tasks
tasks = boring_list_tasks()
```

---

## 6. Shadow Mode (Human-in-the-Loop)

### When to Use
- File deletions
- Database migrations
- Production deployments
- Any operation marked "high-risk"

### Workflow
```python
# Enable Shadow Mode
boring_shadow_mode(mode="STRICT")

# High-risk operation is CAPTURED, not executed
boring_multi_agent(task="Delete all test files")
# Returns: {"status": "pending_approval", "operation_id": "op-xyz"}

# Human reviews
boring_shadow_status()  # See pending operations

# Approve or Reject
boring_shadow_approve(operation_id="op-xyz", note="Reviewed, safe to proceed")
# or
boring_shadow_reject(operation_id="op-xyz", note="Too risky")
```

---

## 7. Plugin Development

### Structure
```
.boring_plugins/
├── my_plugin/
│   ├── plugin.yaml      # Metadata
│   ├── __init__.py      # Entry point
│   └── handlers.py      # Logic
```

### plugin.yaml
```yaml
name: my_plugin
version: 1.0.0
description: Custom code analyzer
hooks:
  - pre_verify
  - post_commit
```

### __init__.py
```python
def pre_verify(context):
    """Called before every verification."""
    print(f"Verifying: {context.project_path}")
    return {"skip": False}  # Return {"skip": True} to bypass

def post_commit(context):
    """Called after every commit."""
    # Send Slack notification, update dashboard, etc.
```

### Registration
```bash
boring_run_plugin(name="my_plugin", args={"target": "src/"})
```

---

## 8. RAG & Semantic Search

### Indexing
```python
# Index the codebase (runs on first call)
boring_rag_index(force=True)  # Rebuild index
```

### Search
```python
# Natural language query
results = boring_rag_search(
    query="authentication middleware that validates JWT",
    max_results=5,
    expand_graph=True,  # Include callers/callees
)
```

### Dependency Graph
```python
# Get context for a specific function
context = boring_rag_context(
    file_path="src/auth/jwt.py",
    function_name="validate_token",
)
# Returns: callers, callees, related files
```

---

## 9. Multi-Agent Orchestration

### Agent Roles
| Agent | Role | Tools Used |
|-------|------|------------|
| **Architect** | Design, planning | `boring_agent_plan` |
| **Coder** | Implementation | File edits, `boring_delegate` |
| **Reviewer** | Quality assurance | `boring_agent_review`, `boring_verify` |

### Custom Delegation
```python
# Delegate to specialized sub-agent
boring_delegate(
    task="Query the database for user schema",
    tool_type="database",  # database, web_search, file_system, api, reasoning
)
```

---

## 10. SpecKit Workflows

### Available Workflows
| Command | Purpose |
|---------|---------|
| `/speckit-clarify` | Generate clarifying questions |
| `/speckit-plan` | Create implementation plan |
| `/speckit-tasks` | Break plan into actionable tasks |
| `/speckit-analyze` | Cross-artifact consistency check |
| `/speckit-checklist` | Generate quality checklist |

### Chaining Example
```
1. User: "Build a payment system"
2. AI: /speckit-clarify → "What payment providers? What currencies?"
3. User answers
4. AI: /speckit-plan → Detailed implementation plan
5. AI: /speckit-tasks → Checklist of 15 tasks
6. AI: boring_multi_agent() → Execute plan
```

---

## 13. Team Knowledge & Portability (Brain)
### The `.boring_brain/` Directory
The "Shared Brain" of your project. It contains portable knowledge that can be committed to Git and shared across your team.

| Subdirectory/File | Content | Portable? | Purpose |
|-------------------|---------|-----------|---------|
| `patterns.json` | Learned coding styles | ✅ YES | Teaches AI your team's specific coding patterns |
| `rubrics/*.yaml` | Evaluation standards | ✅ YES | Standardizes code review criteria across team |
| `quality_history.json` | Quality scores | ⚠️ NO | Project-specific history (don't copy to new repos) |

### Porting Knowledge
To transfer AI knowledge to a new project:
1. **Copy** `.boring_brain/patterns.json`
2. **Copy** `.boring_brain/rubrics/`
3. **Commit** to the new repo
4. **Result**: AI immediately adopts your team's coding style and review standards.

### Learning Patterns (`boring_learn`)
AI learns from *your* modifications.
1. You fix a bug or refactor code in your preferred style.
2. Run `/learn_patterns` (or `boring_learn`).
3. AI compares `HEAD` vs `HEAD~1`, extracts the "diff pattern", and saves it.
4. **Next time**: AI applies this pattern automatically.

---

## 11. Smithery Deployment

### smithery.yaml
```yaml
startCommand:
  type: stdio
  configSchema:
    type: object
    properties:
      GOOGLE_API_KEY:
        type: string
        description: API key for Gemini
    required:
      - GOOGLE_API_KEY
  commandFunction:
    command: python
    args: ["-m", "boring.mcp.server"]
```

### HTTP Mode (for debugging)
```bash
python -m boring.mcp.http --port 8000
# Access: http://localhost:8000/.well-known/mcp.json
```

---

## 12. Testing & Quality Gates

### Run Tests
```bash
pytest tests/ -v --cov=src/boring --cov-fail-under=39
```

### Pre-commit Hooks
```bash
boring_hooks_install  # Sets up pre-commit hooks
```

### CI/CD Integration
```yaml
# .github/workflows/quality.yml
jobs:
  lint:
    run: ruff check src/ tests/
  format:
    run: ruff format --check src/ tests/
  test:
    run: pytest tests/ --cov
  security:
    run: boring_security_scan
```

---

## Quick Reference Card

| Category | Key Tools |
|----------|-----------|
| **Knowledge** | `boring_learn`, `boring_create_rubrics` |
| **Verification** | `boring_verify`, `boring_auto_fix` |
| **Security** | `boring_security_scan` |
| **Transactions** | `boring_transaction_start`, `boring_rollback` |
| **Background** | `boring_background_task`, `boring_task_status` |
| **RAG** | `boring_rag_search`, `boring_rag_context` |
| **Agents** | `boring_multi_agent`, `boring_agent_plan` |
| **Shadow** | `boring_shadow_mode`, `boring_shadow_approve` |
| **Plugins** | `boring_run_plugin`, `boring_list_plugins` |
| **Workspace** | `boring_workspace_add`, `boring_workspace_switch` |

---

## Next Steps

1. **Explore**: Run `boring://capabilities` to see all available tools
2. **Experiment**: Try `boring_multi_agent(task="...", execute=True)` to run in background (Use with caution!)
3. **Extend**: Create a custom plugin in `.boring_plugins/`
4. **Contribute**: See `CONTRIBUTING.md` for development guidelines

---

*Built with ❤️ by the Boring for Gemini team*

---

*Last updated: V10.26.0*
