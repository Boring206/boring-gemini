# Offline Mode Guide

Offline mode lets Boring-Gemini run without cloud API calls by using local GGUF models.

## Quick Start (Recommended)

```bash
boring offline setup
```

This will:
- Download a recommended local model
- Save the model path to `.boring.toml` or `.env`
- Enable Offline Mode

## Manual Setup

1. **Download a model**
   - Recommended: `qwen2.5-coder-1.5b`
   - Use the CLI:
     ```bash
     boring model download qwen2.5-coder-1.5b
     ```

2. **Point Boring to the model**
   Add to `.env`:
   ```env
   BORING_LOCAL_LLM_MODEL=/absolute/path/to/model.gguf
   BORING_LOCAL_LLM_CONTEXT_SIZE=4096
   ```

3. **Enable Offline Mode**
   ```bash
   boring offline enable
   ```

## Recommended Models

| ID | Size (MB) | Context | Notes |
| --- | --- | --- | --- |
| `qwen2.5-coder-1.5b` | 1100 | 32768 | Code-optimized, recommended |
| `qwen2.5-1.5b` | 1000 | 32768 | Small and fast |
| `llama-3.2-1b` | 800 | 8192 | Smallest Llama |
| `phi-3-mini` | 2200 | 4096 | Good for general tasks |

## Useful Commands

```bash
boring model list
boring model download qwen2.5-coder-1.5b
boring offline status
boring offline disable
```

## Troubleshooting

- **Model download failed**
  - Verify internet access and disk space.
  - Try `--force` to re-download.

- **Model not detected**
  - Check `BORING_LOCAL_LLM_MODEL` path.
  - Ensure the file ends with `.gguf`.

- **Performance too slow**
  - Use a smaller model (e.g., `llama-3.2-1b`).
  - Reduce `BORING_LOCAL_LLM_CONTEXT_SIZE`.
