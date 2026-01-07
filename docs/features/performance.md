# Performance & Architecture

> Boring is designed for maximum efficiency in large-scale projects. This document explains the performance-focused architecture and optimization strategies.

---

## 🚀 Incremental Verification

### Smart Caching System

Boring maintains a verification cache at `.boring_cache/verification.json` that stores file hashes. This enables:

- **100+ unchanged files** → Re-verification in **< 2 seconds**
- **Only changed files** are re-analyzed
- **Cache invalidation** is automatic on file modification

```bash
# Normal verification (uses cache)
boring verify

# Force full verification (bypass cache)
boring verify --force
```

### Performance Metrics

| Operation | Cold Start | Cached |
|-----------|-----------|--------|
| Syntax Check (100 files) | ~5s | < 1s |
| Lint (100 files) | ~15s | < 2s |
| Full Verification | ~60s | ~5s |

---

## 🧠 Incremental RAG Indexing

### State Tracking

RAG indexing uses content hashing to track changes:

```bash
# Incremental index (default - only changed files)
boring rag index

# Full re-index
boring rag index --force
```

### Auto-Update with RAGWatcher (V10.18+)

Starting from V10.18.3, `RAGWatcher` automatically detects file changes and triggers incremental re-indexing:

```python
# Automatic - no manual commands needed
# RAGWatcher runs in background during boring start
```

---

## ⚡ Parallel Verification (V10.13+)

### Thread Pool Architecture

Boring uses `ThreadPoolExecutor` for concurrent checks:

```
┌─────────────────────────────────────────┐
│           Verification Engine           │
├─────────────────────────────────────────┤
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐    │
│  │ T1  │  │ T2  │  │ T3  │  │ T4  │    │
│  │Lint │  │Test │  │Type │  │Sec  │    │
│  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘    │
│     └────────┴────────┴────────┘       │
│              Aggregator                 │
└─────────────────────────────────────────┘
```

### Performance Gains

| Project Size | Sequential | Parallel (4 threads) | Speedup |
|--------------|-----------|----------------------|---------|
| Small (50 files) | 15s | 8s | 1.9x |
| Medium (200 files) | 45s | 15s | 3x |
| Large (500+ files) | 120s | 30s | 4x |

---

## 🔄 Provider Switching

### Polyglot Architecture

Boring supports multiple AI providers with automatic detection:

| Provider | API Key Required | Best For |
|----------|-----------------|----------|
| Gemini CLI | ❌ | General development |
| Claude Code CLI | ❌ | Complex reasoning |
| Ollama (Local) | ❌ | Privacy-sensitive |
| SDK Mode | ✅ | Custom integration |

```bash
# Auto-detection at startup
boring start

# Explicit provider
boring start --provider gemini-cli
boring start --provider claude-code
boring start --provider ollama
```

---

## 📊 Quality Trend Tracking

### History Recording

Audit scores are stored in `.boring_brain/quality_history.json`:

```json
{
  "2024-01-01": {"score": 4.2, "issues": 15},
  "2024-01-02": {"score": 4.5, "issues": 10},
  "2024-01-03": {"score": 4.8, "issues": 5}
}
```

### Visualization

```bash
# ASCII trend chart
boring_quality_trend --days 30
```

```
Quality Score Trend (Last 30 Days)
5.0 |                    ████████
4.5 |          ████████████
4.0 |  ██████████
3.5 |██
    └───────────────────────────────
       Jan 1       Jan 15       Jan 30
```

---

## 🛠️ Configuration

### Project-Level Settings (.boring.toml)

```toml
[boring.performance]
parallel_workers = 4          # Thread count
verification_cache = true     # Enable caching
incremental_rag = true        # Auto RAG updates

[boring.timeouts]
api_call = 60                 # Seconds
verification = 300            # Seconds
```

---

## 💡 Best Practices

### For Large Projects

1. **Enable caching** - Keep `.boring_cache/` in `.gitignore`
2. **Use incremental mode** - `boring verify --incremental`
3. **Parallelize** - Ensure CPU cores are utilized

### For CI/CD

1. **Warm the cache** - Run verification once before parallel jobs
2. **Use tiered gates** - `BASIC` → `STANDARD` → `FULL`
3. **Monitor trends** - Fail on quality regression

---

## See Also

- [Quality Gates](./quality-gates.md) - CI/CD configuration
- [MCP Tools](./mcp-tools.md) - Tool reference
- [Pro Tips](../guides/pro-tips.md) - Optimization strategies
