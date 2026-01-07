# Knowledge System - Brain, RAG & Patterns

> Boring's intelligent memory system that learns and remembers across projects.

---

## 🧠 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 KNOWLEDGE SYSTEM                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ~/.boring_brain/          (Global - All Projects)     │
│  ├── patterns/             Learned error solutions     │
│  ├── rubrics/              Evaluation criteria         │
│  ├── shadow_config.json    Shadow Mode settings        │
│  └── quality_history.json  Score trends                │
│                                                         │
│  .boring_memory/           (Project-Specific)          │
│  ├── context.json          Session context             │
│  ├── decisions.json        Architecture decisions      │
│  └── learnings.json        Project learnings           │
│                                                         │
│  .boring_cache/            (Ephemeral - Temp)          │
│  ├── verification.json     Cached verification         │
│  └── rag_index/            Vector embeddings           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Reference

| Directory | Scope | Purpose | Migration |
|-----------|-------|---------|-----------|
| `~/.boring_brain/` | Global | Cross-project knowledge | Copy to new machine |
| `.boring_memory/` | Project | Project-specific context | Commit to repo |
| `.boring_cache/` | Temp | Ephemeral cache | Regenerated |

---

## 🧠 .boring_brain (Global Knowledge)

### Location
- **Linux/macOS**: `~/.boring_brain/`
- **Windows**: `C:\Users\<username>\.boring_brain\`

### Contents

#### patterns/ - Learned Patterns
```json
{
  "error_patterns": [
    {
      "error": "ModuleNotFoundError: No module named 'foo'",
      "solution": "pip install foo",
      "confidence": 0.95,
      "occurrences": 15
    }
  ]
}
```

AI learns from your error-solution pairs and applies them automatically.

#### rubrics/ - Evaluation Criteria
```markdown
# production-ready.md
- [ ] All tests passing (100%)
- [ ] No security vulnerabilities
- [ ] Documentation complete
- [ ] Performance benchmarked
```

Custom rubrics for `boring_evaluate`.

#### shadow_config.json - Security Settings
```json
{
  "level": "STRICT",
  "auto_approve_patterns": ["*.md", "docs/*"],
  "always_block_patterns": ["*.env", "secrets/*"]
}
```

Persistent across sessions.

### Migration

```bash
# Backup
cp -r ~/.boring_brain ~/boring_brain_backup

# Restore on new machine
cp -r ~/boring_brain_backup ~/.boring_brain
```

---

## 📂 .boring_memory (Project Knowledge)

### Location
- In your project root: `.boring_memory/`

### Contents

#### context.json - Session Context
```json
{
  "architecture": "microservices",
  "tech_stack": ["FastAPI", "PostgreSQL", "Redis"],
  "current_focus": "authentication module"
}
```

#### decisions.json - Architecture Decisions
```json
{
  "decisions": [
    {
      "date": "2024-01-15",
      "topic": "Database choice",
      "decision": "PostgreSQL over MySQL",
      "rationale": "Better JSON support, pg_vector for RAG"
    }
  ]
}
```

#### learnings.json - Project Learnings
```json
{
  "error_solutions": [
    {
      "error": "Connection timeout in production",
      "solution": "Increase pool_size in database config"
    }
  ]
}
```

### Best Practice

```bash
# Commit to repo for team sharing
git add .boring_memory/
git commit -m "docs: project context and decisions"
```

---

## 🔍 RAG System

### How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Your Code   │ ──▶ │   Indexer    │ ──▶ │ Vector DB    │
│  (src/*.py)  │     │ (embeddings) │     │ (ChromaDB)   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Results    │ ◀── │   Ranker     │ ◀── │ Hybrid Search│
│ (top_k=10)   │     │ (reranking)  │     │ Vector+BM25  │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Features

| Feature | Description |
|---------|-------------|
| **Hybrid Search** | Vector (semantic) + BM25 (keyword) |
| **Dependency Expansion** | Includes related files via import graph |
| **Incremental Index** | Only re-indexes changed files |
| **Auto-Update** | RAGWatcher detects file changes (V10.18.3+) |

### Commands

```python
# Build index
boring_rag_index(project_path=".", force=False)

# Search
boring_rag_search(
    query="authentication middleware",
    top_k=10,
    expand_deps=True
)

# Reload
boring_rag_reload(project_path=".")
```

### Storage

- **Index location**: `.boring_cache/rag_index/`
- **Size**: ~1MB per 1000 files
- **Regeneration**: Automatic if missing

---

## 📚 Patterns & AutoLearner

### How Patterns Are Learned

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ AI Response  │ ──▶ │ AutoLearner  │ ──▶ │ Pattern DB   │
│ "Fixed by X" │     │ (extraction) │     │ (.boring_brain)│
└──────────────┘     └──────────────┘     └──────────────┘
                             │
                             ▼
                    Next time: Auto-apply!
```

### Pattern Types

| Type | Example |
|------|---------|
| **Error Solutions** | `ImportError` → `pip install X` |
| **Code Patterns** | Auth middleware structure |
| **Refactoring** | Extract function pattern |

### Manual Learning

```python
# Trigger learning from session
boring_learn(
    project_path=".",
    topics=["error-handling", "testing", "patterns"]
)
```

---

## 🚚 Migration Guide

### To New Machine

```bash
# 1. Copy global knowledge
scp -r ~/.boring_brain user@newmachine:~/

# 2. Clone project (includes .boring_memory)
git clone your-repo

# 3. Rebuild cache (automatic on first use)
boring rag index
```

### To Team Members

```bash
# In .gitignore
.boring_cache/          # Don't commit cache

# Commit project knowledge
git add .boring_memory/
git add .boring.toml    # Project config
```

### Environment Variables

```bash
# Custom brain location
export BORING_BRAIN_PATH="/path/to/shared/brain"

# Custom cache location
export BORING_CACHE_PATH="/tmp/boring_cache"
```

---

## See Also

- [MCP Tools - RAG](./mcp-tools.md#6-rag-memory-boring_rag_search)
- [Pro Tips - Knowledge](./pro-tips.md#tip-11-cross-project-knowledge-sharing)
- [Cookbook - Recipe 9](./cookbook.md#recipe-9-rag-knowledge-base)
