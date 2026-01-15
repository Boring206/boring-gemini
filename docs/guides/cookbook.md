# Cookbook - Complete Feature Recipes

> Ready-to-use recipes for every Boring feature. Copy, paste, and customize.

---

## 📚 Recipe Index

### 🚀 Getting Started
- [Recipe 1: First Project Setup](#recipe-1-first-project-setup)
- [Recipe 2: MCP Server Configuration](#recipe-2-mcp-server-configuration)

### 🔧 Daily Workflows
- [Recipe 3: Quick Bug Fix](#recipe-3-quick-bug-fix)
- [Recipe 4: Feature Development](#recipe-4-feature-development)
- [Recipe 5: The "One Dragon" Run](#recipe-5-the-one-dragon-run-autonomous-dev-)
- [Recipe 6: Code Review](#recipe-6-code-review)

### 🔒 Security & Quality
- [Recipe 7: Vibe Check](#recipe-7-vibe-check-quality-police)
- [Recipe 8: Security Audit](#recipe-8-security-audit)
- [Recipe 9: Shadow Mode Setup](#recipe-9-shadow-mode-setup)

### 🧠 Advanced
- [Recipe 10: Multi-Agent Workflow](#recipe-10-multi-agent-workflow)
- [Recipe 11: RAG Knowledge Base](#recipe-11-rag-knowledge-base)
- [Recipe 12: CI/CD Integration](#recipe-12-cicd-integration)

---

## Recipe 1: First Project Setup

### Ingredients
- Empty directory or existing project
- Python 3.9+
- pip

### Steps

```bash
# 1. Install Boring
pip install boring-aicoding

# 2. Initialize project (if new)
boring-setup my-project
cd my-project

### Quick Start

Before starting development, we recommend running the health check:

# Or use Vibe Coder CLI directly
boring-route "Initialize a new project called my-project"
```

### Expected Output
```
🚀 Boring v10.18.3 started
📁 Project: my-project
🔍 Monitoring for changes...
```

---

## Recipe 2: MCP Server Configuration

### For Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "PROJECT_ROOT_DEFAULT": "/path/to/your/project",
        "SHADOW_MODE_LEVEL": "ENABLED"
      }
    }
  }
}
```

### For Cursor

In Settings → MCP Servers:
```json
{
  "boring": {
    "command": "boring-mcp",
    "args": [],
    "env": {
      "PROJECT_ROOT_DEFAULT": "."
    }
  }
}
```

### For Smithery (Cloud)
```
npx -y @anthropic-ai/mcp install @boring/boring
```

---

## Recipe 3: Quick Bug Fix

### Problem
You have a bug and want AI to fix it.

### Steps

```python
# Option 1: Vibe Coder (Recommended)
# You: "Fix the login function - it crashes when password is empty"

# Option 2: CLI
# $ boring-route "Fix the login bug"

# Option 3: Python Tool
boring_apply_patch(
    project_path=".",
    description="Fix the login function - it crashes when password is empty"
)
```

### Verification
```python
boring_verify(level="FULL")
```

---

## Recipe 4: Feature Development

### Using SpecKit Workflow

### Vibe Coder Prompt
> **You**: "Deeply analyze the user authentication requirements, then create a detailed checklist and implement it."

### Python Workflow (SpecKit)
### Vibe Coder Prompt
> **You**: "Deeply analyze the user authentication requirements, then create a detailed checklist and implement it."

### Python Workflow (SpecKit)
```python
# Step 1: Establish principles
speckit_constitution(project_path=".")
# ... (rest of manual steps)
```

---

## Recipe 5: The "One Dragon" Run (Autonomous Dev) 🐉

**Goal**: Build a complete feature while you are AFK (Away From Keyboard).

**Ingredients**:
*   `boring start` (CLI)
*   A `task.md` file
*   Coffee ☕

**Steps**:

1.  **Define the Mission**: Create a `task.md` in your project root.
    ```markdown
    # Task: Build Login Page
    - [ ] Create login.html with Bootstrap
    - [ ] Create styles.css (Dark Mode)
    - [ ] Write logic.js for validation
    - [ ] Verify functionality
    ```

2.  **Launch the Dragon**:
    Open your terminal and run:
    ```bash
    boring start
    ```

3.  **Monitor (Optional)**:
    Open another terminal to watch the brain at work:
    ```bash
    boring-monitor
    ```

4.  **Result**:
    Boring will loop through Plan -> Code -> Test -> Fix until all checkboxes in `task.md` are marked `[x]`.

---

## Recipe 6: Code Review

### Direct Evaluation
```python
boring_evaluate(
    target="src/main.py",
    level="DIRECT",
    criteria=["correctness", "security", "performance", "maintainability"]
)
```

### Pairwise Comparison
```python
boring_evaluate(
    level="PAIRWISE",
    target_a="src/auth_v1.py",
    target_b="src/auth_v2.py"
)
```

### Rubric-Based Scoring
```python
boring_evaluate(
    target="src/",
    level="RUBRIC",
    rubric_path=".boring/rubrics/production-ready.md"
)
```

---

## Recipe 7: Vibe Check (Quality Police)

### Project Health Check
```python
boring_vibe_check(
    target_path="src/",
    verbosity="standard"
)
# Returns a Vibe Score (0-100)
```

---

## Recipe 8: Security Audit

### Full Security Scan
```python
boring_security_scan(
    project_path=".",
    scan_type="all"  # sast + secrets + dependencies
)
```

### Secrets Only
```python
boring_security_scan(
    project_path=".",
    scan_type="secrets"
)
```

### With Auto-Fix
```python
boring_security_scan(
    project_path=".",
    scan_type="all",
    fix_mode=True
)
```

---

## Recipe 9: Shadow Mode Setup

### Enable for Production
```python
# Set STRICT mode
boring_shadow_mode(action="set_level", level="STRICT")

# Verify status
boring_shadow_mode(action="status")
```

### Configure Patterns
Edit `~/.boring/brain/shadow_config.json`:
```json
{
  "level": "STRICT",
  "auto_approve_patterns": ["*.md", "docs/*"],
  "always_block_patterns": ["*.env", "secrets/*", ".git/*"]
}
```

---

## Recipe 10: Multi-Agent Workflow

### Plan and Implement
```python
boring_multi_agent(
    workflow="plan_and_implement",
    context={
        "feature": "Real-time notifications",
        "tech_stack": ["WebSockets", "Redis", "FastAPI"]
    },
    execute=True  # Actually run, not just generate prompt
)
```

### Review and Fix
```python
boring_multi_agent(
    workflow="review_and_fix",
    context={
        "target": "src/",
        "focus": ["security", "performance"]
    }
)
```

---

## Recipe 11: RAG Knowledge Base {: #recipe-11-rag-knowledge-base }

### Build Index
```python
boring_rag_index(
    project_path=".",
    force=False  # Incremental
)
```

### Search Code
```python
boring_rag_search(
    query="authentication middleware",
    project_path=".",
    top_k=10,
    expand_graph=True
)
```

### Multi-Project Search
```python
boring_rag_search(
    query="error handling patterns",
    additional_roots=[
        "/path/to/shared-libs",
        "/path/to/reference-project"
    ]
)
```

---

## Recipe 12: CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install boring-aicoding
      - run: boring verify --level FULL
      
  security:
    runs-on: ubuntu-latest
    needs: verify
    steps:
      - uses: actions/checkout@v4
      - run: pip install boring-aicoding
      - run: |
          python -c "
          from boring.mcp.tools import boring_security_scan
          result = boring_security_scan('.', 'all')
          if result.get('critical_count', 0) > 0:
              exit(1)
          "
```

---

## See Also

- [Vibe Coder Guide](./vibe-coder.md) - For visual/description-based developers
- [Quick Tutorials](./quick-tutorials.md) - Step-by-step guides
- [MCP Tools](../features/mcp-tools.md) - Complete tool reference
