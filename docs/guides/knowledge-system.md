# Knowledge System - Brain, RAG & Patterns

> Boring's intelligent memory system that learns and remembers across projects.

---

## 🧠 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 KNOWLEDGE SYSTEM                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ~/.boring/brain/          (Global - All Projects)     │
│  ├── patterns/             Learned error solutions     │
│  ├── rubrics/              Evaluation criteria         │
│  ├── shadow_config.json    Shadow Mode settings        │
│  └── quality_history.json  Score trends                │
│                                                         │
│  .boring/memory/           (Project-Specific)          │
│  ├── sessions/             Session history             │
│  ├── db.sqlite             Structured memory           │
│  └── rag_index/            Web/Doc embeddings          │
│                                                         │
│  .boring/cache/            (Ephemeral - Temp)          │
│  └── rag_cache/            Code embeddings             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Reference

| Directory | Scope | Purpose | Migration |
|-----------|-------|---------|-----------|
| `~/.boring/brain/` | Global | Cross-project knowledge | Copy to new machine |
| `.boring/memory/` | Project | Project-specific context | Commit to repo |
| `.boring/cache/` | Temp | Ephemeral cache | Regenerated |

---

## 🧠 .boring/brain (Global Knowledge)

### Location
- **Linux/macOS**: `~/.boring/brain/`
- **Windows**: `C:\Users\<username>\.boring\brain\`

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
cp -r ~/.boring/brain ~/boring_brain_backup

# Restore on new machine
cp -r ~/boring_brain_backup ~/.boring/brain
```

---

## 📂 .boring/memory (Project Knowledge)

### Location
- In your project root: `.boring/memory/`

### Contents

#### db.sqlite - Structured Data
Contains session logs, tool outputs, and project context.

#### sessions/ - Conversation History
JSON files storing raw conversation logs for context restoration.

### Best Practice

```bash
# Commit to repo for team sharing
git add .boring/memory/
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
    expand_graph=True
)

# Reload
boring_rag_reload(project_path=".")
```

### Storage

- **Index location**: `.boring/memory/rag_index/`
- **Size**: ~1MB per 1000 files
- **Regeneration**: Automatic if missing

---

## 📚 Patterns, FeedbackLearner & Active Recall

### Cognitive Reflexes (Active Recall)

Starting in **V10.31**, the Agent possesses **Active Recall**. When it encounters an error (e.g., `pytest` failure), it doesn't just "try again." It queries the global Brain for similar past errors and retrieves proven solutions.

**Flow:**
1.  **Error Occurs**: Agent captures `ModuleNotFoundError`.
2.  **Reflex Query**: Agent calls `boring_suggest_next(error_message="...")`.
3.  **Brain Retrieval**: Brain scans `patterns.json` for semantic matches.
4.  **Solution Injection**: If a high-confidence match (e.g., 95%) is found, the solution is injected directly into the Agent's context.

### How Patterns Are Learned

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ AI Response  │ ──▶ │FeedbackLearner│ ──▶ │ Pattern DB   │
│ "Fixed by X" │     │ (extraction) │     │ (.boring/brain)│
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
scp -r ~/.boring/brain user@newmachine:~/

# 2. Clone project (includes .boring/memory)
git clone your-repo

# 3. Rebuild cache (automatic on first use)
boring rag index
```

### To Team Members

```bash
# In .gitignore
.boring/cache/          # Don't commit cache

# Commit project knowledge
git add .boring/memory/
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

- [MCP Tools - RAG](../features/mcp-tools.md#boring_rag_search)
- [Pro Tips - Knowledge](pro-tips.md#tip-11)
- [Cookbook - RAG Recipe](cookbook.md#recipe-9-rag-knowledge-base)
