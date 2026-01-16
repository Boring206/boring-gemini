# Offline Mode Guide (離線模式指南)

Boring supports full offline operation for privacy-conscious users and air-gapped environments.

## Quick Start

```bash
# Enable offline mode
export BORING_OFFLINE_MODE=true

# Or in .boring.toml
[boring]
offline_mode = true
```

## Offline Capabilities

### ✅ Fully Offline Features
| Feature | Description |
|---------|-------------|
| RAG Search | Local vector search (after initial embedding model download) |
| Code Review | Pattern-based analysis using Brain patterns |
| Vibe Check | Local linting with ruff, pyright |
| Git Hooks | Pre-commit verification |
| Checkpoint | Git-based save states |
| Predict/Bisect | Historical pattern analysis |

### ⚠️ Requires Initial Setup
| Component | First-time Action |
|-----------|-------------------|
| Embedding Model | `boring rag setup --offline` (downloads ~500MB) |
| Local LLM | `boring model download qwen2.5-coder-1.5b` |

### ❌ Cloud-Only Features
| Feature | Reason |
|---------|--------|
| Gemini API calls | Requires network |
| Context7 docs | External service |
| Skill installation | Network download |

## Local LLM Setup

1. **Install llama-cpp-python:**
   ```bash
   pip install llama-cpp-python
   ```

2. **Download a model:**
   ```bash
   # Recommended for coding tasks
   boring model download qwen2.5-coder-1.5b
   
   # Available models
   boring model list
   ```

3. **Configure:**
   ```toml
   # .boring.toml
   [boring]
   offline_mode = true
   local_llm_model = "~/.boring/models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BORING_OFFLINE_MODE` | Enable offline mode | `false` |
| `BORING_LOCAL_LLM_MODEL` | Path to GGUF model | Auto-detect |
| `BORING_MODEL_DIR` | Model storage directory | `~/.boring/models` |

## Fallback Behavior

When `BORING_OFFLINE_MODE=true`:

```
API Request
    ↓
Check Local LLM Available?
    ├─ Yes → Use Local LLM
    └─ No → Return graceful error with suggestion
```

## Pre-downloading for Air-gapped Environments

```bash
# On connected machine
boring rag setup --export ~/boring-offline-pack.tar.gz

# On air-gapped machine
boring rag setup --import ~/boring-offline-pack.tar.gz
```

## Troubleshooting

### "Local LLM not available"
```bash
# Check model status
boring model status

# Verify llama-cpp-python installation
python -c "import llama_cpp; print('OK')"
```

### "RAG index requires network"
```bash
# Pre-download embedding model
boring rag setup --offline
```
