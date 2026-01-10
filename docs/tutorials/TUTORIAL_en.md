# Boring for Gemini: Complete Tutorial

> **From Zero to Hero: 5 Minutes to Vibe Coding with Architect Backend**

---

## Part 1: Quick Start (5 Minutes)

### 1.1 What is Boring?

**Boring** is not just an AI code generator—it is your **Senior Architect Mentor**.

| Traditional AI Assistant | Boring Architect |
|--------------------------|------------------|
| Generates Code | Asks requirements first, then designs architecture |
| Fixes Errors | Explains why errors happened |
| Passive Response | Proactively warns about potential risks |

**Core Advantages**:
- 🏛️ **Architect Persona**: Every interaction includes architecture advice
- 🔄 **Auto-Repair Loop**: One-click fix for Lint/Test/Format
- 🛡️ **Shadow Mode**: Security audit for high-risk operations
- 🔍 **RAG Semantic Search**: Find code using natural language

---

### 1.2 Installation Guide

#### Method 1: pip install (Recommended)
```bash
pip install boring-aicoding
```

#### Method 2: Install from Source
```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e ".[mcp]"
```

---

### 1.3 IDE Integration

#### Cursor / Windsurf
Create `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key"
      }
    }
  }
}
```

#### Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"]
    }
  }
}
```

---

### 1.4 First Project

```bash
# Create New Project (Must do this before boring start!)
boring-setup my-app
cd my-app

# Check Status
boring status

# Install Git hooks
boring_hooks_install
```

**Project Structure**:
```
my-app/
├── src/
├── tests/
├── PROMPT.md          # AI Instructions
├── @fix_plan.md       # Task Checklist
└── .boring/brain/     # Knowledge Base
```

---

## Part 2: Core Workflows

### 2.1 Vibe Start Complete Flow

Use `vibe_start` prompt to launch fully automated dev flow:

```
You: "Build a REST API for user management"

Boring:
1️⃣ **Foundation** (Constitution & Clarify) → Establish principles & clarify needs
2️⃣ **Spec & Plan** (Plan, Checklist) → Generate implementation plan & criteria
3️⃣ **Pre-Analysis** (SpecKit Analyze) → Ensure plan consistency
4️⃣ **Implementation** (Multi-Agent) → Collaborative development
5️⃣ **Verification** (Verify & Fix) → Quality verification & fixing
```

**Conversation Example**:

> **You**: "Build a REST API for user management"
>
> **Boring**: (Thinking...) I will start the Vibe Coder workflow.
> *Calling tool: `boring_multi_agent` or `vibe_start`*


---

### 2.2 Quick Fix Auto-Repair

One-click fix for all code issues:

**Conversation Example**:

> **You**: "Fix all the linting errors"
> **Boring**: I'll run the quick fix loop.
> *Calling tool: `boring_auto_fix`*

**Or via CLI**:
```bash
boring-route "Fix the lint errors"
```

**Execution Flow**:
1. `boring_verify(level='FULL')` — Find all issues
2. `boring_auto_fix(max_iterations=3)` — Auto repair
3. Verify again to confirm success

---

### 2.3 Multi-Agent Collaboration

| Agent | Role | Responsibility |
|-------|------|----------------|
| 🏛️ Architect | Planner | Design architecture, create plan |
| 💻 Coder | Executor | Write code, implement features |
| 🔍 Reviewer | Auditor | Code review, quality gate |

**Conversation Example**:

> **You**: "Implement user authentication with JWT"
>
> **Boring**: I'll assign this to the Coder agent.
> *Calling tool: `boring_multi_agent`*


---

## Part 3: Advanced Features

### 3.1 RAG Semantic Search

Search code using natural language:

```python
# Create Index (First run only, needs chromadb)
boring_rag_index()

# Search
boring_rag_search(query="Function validating JWT token")
# Returns: Related files, function definitions, call graph

# Get Context for Specific Function
boring_rag_context(file_path="src/auth/jwt.py", function_name="validate")
```

---

### 3.2 Shadow Mode Safe Execution

Enable human review for high-risk operations:

```python
# Enable Strict Mode
boring_shadow_mode(mode="STRICT")

# Execute High-Risk Op (Captured, will not run directly)
boring_multi_agent(task="Delete all test files")
# Returns: pending_approval

# View Pending Ops
boring_shadow_status()

# Approve or Reject
boring_shadow_approve(operation_id="op-xyz")
boring_shadow_reject(operation_id="op-xyz", note="Too dangerous")
```

---

### 3.3 Transaction & Rollback

Git-based atomic operations, rollback anytime:

```python
# Start Transaction (Create Savepoint)
boring_transaction_start(message="Refactoring auth")

# Make Changes...
boring_multi_agent(task="Refactor authentication module")

# Verify
result = boring_verify(level="FULL")

if result["passed"]:
    boring_transaction_commit()  # Confirm changes
else:
    boring_rollback()  # Rollback to savepoint
```

---

### 3.4 Background Tasks

Run long-running tasks in background:

```python
# Submit Background Task
result = boring_background_task(task_type="verify", task_args={"level": "FULL"})
task_id = result["task_id"]

# Check Progress (Non-blocking)
status = boring_task_status(task_id=task_id)
# {"status": "running", "progress": 60}

# List All Tasks
boring_list_tasks()
```

---

### 3.5 Auto-Learning (v10.18)

Boring observes your fixes and evolves automatically:

1. **Passive Learning**: When you reject AI changes and manually fix code, Boring analyzes diffs and learns.
2. **Active Learning**:
   ```python
   # Teach AI a new rule
   boring_learn_pattern(
       pattern_type="code_style",
       description="Always use UTC for datetimes",
       context="When handling time",
       solution="datetime.now(timezone.utc)"
   )
   ```
3. **View Knowledge**:
   ```python
   boring_brain_summary()
   ```

---

## Part 4: IDE Integration

### 4.1 Cursor/Windsurf MCP Config

Complete Config:
```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "GOOGLE_API_KEY": "your-key",
        "BORING_MCP_DEBUG": "1"
      }
    }
  }
}
```

---

### 4.2 Smithery Cloud Deployment

Visit [Smithery](https://smithery.ai/server/boring/boring):

1. Connect your GitHub account
2. Set `GOOGLE_API_KEY`
3. Use in any MCP client

---

### 4.3 Dynamic Discovery

AI automatically discovers available tools:

```python
# List all capability categories
boring://capabilities

# Get detailed usage for specific category
boring://tools/security
boring://tools/rag_search
```

---

## Part 5: Practical Cases

### 5.1 Demo: Build REST API

```python
# Step 1: Start Vibe Coding
vibe_start(idea="Build a FastAPI REST API for todo management")

# Boring will:
# 1. Ask you: Auth needed? Database choice?
# 2. Generate Plan: API endpoints, Data models
# 3. Execute Dev: Create files, Write tests
# 4. Verify: Run tests, Security scan
```

**Expected Output**:
```
src/
├── main.py          # FastAPI entry
├── models.py        # Pydantic models
├── routes/
│   └── todos.py     # CRUD routes
└── tests/
    └── test_todos.py # Tests
```

---

### 5.2 Demo: Refactor Legacy Code

```python
# Step 1: Architect Evaluation (Hostile Architect Mode)
evaluate_architecture(target="src/legacy/")

# Boring will point out:
# ⚠️ God class detected in UserManager
# ⚠️ N+1 query in get_users()
# ⚠️ Missing error handling
```

```python
# Step 2: Execute Refactor
boring_multi_agent(task="Refactor UserManager into smaller services")

# Step 3: Verify
boring_verify(level="FULL")
```

---

### 5.3 Demo: Debugging

```python
# Step 1: Debug Error
debug_error(error_message="TypeError: 'NoneType' object is not iterable")

# Boring Architect analyzes:
# 1. Root Cause: get_users() returns None when DB is empty
# 2. Likely Culprit: src/services/user.py:45
# 3. Suggested Fix: Return empty list instead of None
# 4. 🏛️ Architecture Lesson: Missing Null Object Pattern...
```

```python
# Step 2: Auto Fix
boring_auto_fix(max_iterations=3)

# Step 3: Verify
boring_verify(level="STANDARD")
```

---

## Part 6: Customization & Extension

### 6.1 Create Custom Plugin

**Directory Structure**:
```
.boring_plugins/
└── my_analyzer/
    ├── plugin.yaml
    └── __init__.py
```

**plugin.yaml**:
```yaml
name: my_analyzer
version: 1.0.0
description: Custom code analyzer
hooks:
  - pre_verify
```

**__init__.py**:
```python
def pre_verify(context):
    """Run before every verification"""
    print(f"Analyzing: {context.project_path}")
    # Your custom logic
    return {"skip": False}
```

**Usage**:
```python
boring_run_plugin(name="my_analyzer")
```

---

### 6.2 SpecKit Workflows

| Workflow | Usage |
|----------|-------|
| `/speckit-clarify` | Generate clarifying questions |
| `/speckit-plan` | Create implementation plan |
| `/speckit-tasks` | Break down into task list |
| `/speckit-analyze` | Cross-document consistency check |
| `/speckit-checklist` | Generate quality checklist |

**Example**:
```
You: /speckit-plan
Boring: Please provide requirement description...
You: I need a user auth system
Boring: [Generates detailed implementation plan]
```

---

### 6.3 Scoring Rubrics

Customize code quality rules:

**.boring/brain/rubrics/my_rules.yaml**:
```yaml
name: my_coding_standards
rules:
  - name: no_print_statements
    severity: warning
    pattern: "print\\("
    message: "Use logging instead of print"
    
  - name: require_docstrings
    severity: error
    check: functions_have_docstrings
```

**Usage**:
```python
boring_evaluate(target="src/", rubric="my_rules")
```

---

## Next Steps

- 📖 [Advanced Developer Guide](./ADVANCED_TUTORIAL.md) — Architecture & Internals
- 📚 [Full Tool Reference](../reference/APPENDIX_A_TOOL_REFERENCE.md) — All 55+ Tools
- ❓ [FAQ](../reference/APPENDIX_B_FAQ.md) — Troubleshooting
- 🏛️ [Prompt Philosophy](../reference/APPENDIX_C_PROMPT_PHILOSOPHY.md) — Architect Persona Design

---

*Built with ❤️ by the Boring for Gemini team*
