# Quick Start Tutorials

> Learn Boring by doing. 5-minute tutorials for common workflows.

---

## 📚 Tutorial Index

| Tutorial | Time | Skill Level |
|----------|------|-------------|
| [1. Your First Vibe Project](#1-your-first-vibe-project) | 5 min | Beginner |
| [2. Fix All Errors Instantly](#2-fix-all-errors-instantly) | 3 min | Beginner |
| [3. Add a New Feature](#3-add-a-new-feature) | 10 min | Intermediate |
| [4. Code Review with AI](#4-code-review-with-ai) | 5 min | Intermediate |
| [5. Set Up Quality Gates](#5-set-up-quality-gates) | 10 min | Advanced |
| [6. Multi-Agent Development](#6-multi-agent-development) | 15 min | Advanced |

---

## 1. Your First Vibe Project

**Goal**: Create a working app from a simple description.

### Step 1: Start the conversation

```
You: /vibe_start Build a simple REST API with FastAPI
```

### Step 2: Answer the clarifying questions

```
Boring: Great! Let me ask a few questions:
        1. What resources should the API manage?
        2. Need authentication?
        3. Database preference?

You: 1. Users and posts
     2. No auth for now
     3. SQLite
```

### Step 3: Review the generated plan

```
Boring: Here's my plan:
        1. Create project structure
        2. Set up FastAPI application
        3. Define User and Post models
        4. Create CRUD endpoints
        5. Add SQLite database
        
        Shall I proceed?

You: Yes, go ahead!
```

### Step 4: Get your working app

```bash
# Run your new API
uvicorn main:app --reload
```

**Done!** You now have a working FastAPI application.

---

## 2. Fix All Errors Instantly

**Goal**: Clear all linting and formatting errors in one command.

### Step 1: Run quick fix

```
You: /quick_fix
```

### Step 2: Watch the magic

```
Boring: Scanning for issues...
        ✅ Fixed 12 import sorting issues
        ✅ Fixed 8 formatting issues
        ✅ Fixed 3 unused variables
        
        All issues resolved!
```

**Done!** All code quality issues are fixed.

---

## 3. Add a New Feature

**Goal**: Add authentication to an existing project.

### Step 1: Describe the feature

```
You: Add JWT authentication to my FastAPI project
```

### Step 2: AI creates the plan

```
Boring: I'll add authentication with these steps:
        
        1. Install dependencies (pyjwt, passlib)
        2. Create auth/models.py - User model
        3. Create auth/utils.py - Password hashing
        4. Create auth/routes.py - Login/register
        5. Update main.py - Add auth router
        
        Shall I proceed?
```

### Step 3: Review the diff

```
Boring: Here's what I'll change:
        
        + auth/models.py (new)
        + auth/utils.py (new)
        + auth/routes.py (new)
        ~ main.py (modified)
        ~ requirements.txt (modified)
        
        Approve?

You: Yes, apply the changes
```

**Done!** Your app now has authentication.

---

## 4. Code Review with AI

**Goal**: Get expert-level code review feedback.

### Step 1: Request a review

```python
boring_evaluate(
    target="src/main.py",
    level="DIRECT",
    criteria=["correctness", "security", "performance"]
)
```

### Step 2: Review the feedback

```
Boring: Code Review for src/main.py
        
        Overall Score: 7.5/10
        
        ✅ Strengths:
        - Clean function signatures
        - Good error handling
        
        ⚠️ Issues:
        1. SQL injection risk on line 45
        2. N+1 query pattern in get_posts()
        3. Missing input validation
        
        📝 Suggestions:
        - Use parameterized queries
        - Add eager loading for posts
        - Add Pydantic validation
```

**Done!** You have actionable feedback.

---

## 5. Set Up Quality Gates

**Goal**: Add automated quality checks to your CI pipeline.

### Step 1: Install hooks locally

```bash
boring hooks install
```

### Step 2: Create GitHub Actions workflow

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
      - run: pip install "boring-aicoding[all]"
      - run: boring verify --level FULL
```

### Step 3: Test locally

```bash
# Run verification
boring verify --level FULL

# Expected output:
✅ Syntax Check: Passed
✅ Linting: Passed
✅ Security Scan: Passed
✅ Tests: 42 passed, 0 failed
```

**Done!** Your repo now has quality gates.

---

## 6. Multi-Agent Development

**Goal**: Use specialized agents for complex tasks.

### Step 1: Start the workflow

```python
boring_multi_agent(
    workflow="plan_and_implement",
    context={
        "feature": "Real-time notifications with WebSockets"
    }
)
```

### Step 2: Agents collaborate

```
🧠 Planner Agent:
   Creating implementation plan...
   - WebSocket server setup
   - Event system design
   - Client integration

📝 Coder Agent:
   Implementing changes...
   - src/websocket.py (new)
   - src/events.py (new)
   - src/main.py (modified)

🔍 Reviewer Agent:
   Reviewing changes...
   - ✅ No security issues
   - ⚠️ Consider rate limiting
   - ✅ Tests passing
```

### Step 3: Review final output

```
Boring: Multi-agent workflow complete!
        
        Created files:
        - src/websocket.py
        - src/events.py
        
        Modified files:
        - src/main.py
        - requirements.txt
        
        All tests passing. Ready for deployment.
```

**Done!** Complex feature implemented with AI collaboration.

---

## See Also

- [Pro Tips](./pro-tips.md) - Expert tips
- [Git Hooks](./git-hooks.md) - Local automation
- [MCP Tools](../features/mcp-tools.md) - Full tool reference
