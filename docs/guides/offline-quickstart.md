# Offline-First Mode Quickstart Guide 🔌

> **Version**: V14.0.0+
> **Prerequisites**: Python 3.10+, 8GB+ RAM (16GB recommended)

Boring-Gemini V14.0 introduces a true **Offline-First** architecture. This guide helps you set up a fully autonomous local development environment with zero internet dependency.

---

## 1. Quick Setup

### Step 1: Install Dependencies

Offline mode requires `llama-cpp-python` for local inference.

```bash
# Install with local support extras
pip install boring-aicoding[local]

# Or manually
pip install llama-cpp-python
```

> **GPU Acceleration**: If you have an NVIDIA GPU, install with CUDA support:
> `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python`

### Step 2: Download a Model

Use the built-in CLI to download a recommended GGUF model.

```bash
# List recommended models
boring model list

# Download a balanced model (e.g., Llama-3-8B-Quantized)
boring model download --name "llama-3-8b-instruct-q4_k_m.gguf"
```

Models are stored in `~/.boring/models/`.

### Step 3: Enable Offline Mode

You can enable offline mode globally or per session.

**Option A: CLI Toggle (Persistent)**
```bash
boring offline enable
```

**Option B: Environment Variable (Temporary)**
```bash
export BORING_OFFLINE_MODE=true
boring start
```

---

## 2. Verification

Run the doctor command to verify your offline status.

```bash
boring doctor
```

Output should show:
```
5. Offline Mode
  - Status: ENABLED
  
6. Local LLM Models
  - Models: 1 available
    - llama-3-8b-instruct-q4_k_m.gguf
```

---

## 3. How it Works

When Offline Mode is active:

1.  **Network Cutoff**: All external API calls (Gemini, OpenAI, Anthropic) are blocked.
2.  **Local Inference**: The Agent automatically routes LLM requests to your local GGUF model.
3.  **Local Tools**: Only local tools are loaded (File Ops, Local RAG, Shell). Web search tools are disabled.
4.  **Local RAG**: Queries use `SentenceTransformers` (local embeddings) and `ChromaDB` (local vector store).

### Fallback Behavior

If no local model is loaded but Offline Mode is ON, the system will error out gracefully suggesting you to run `boring model download`.

---

## 4. Performance Tuning

Create a `.env` file in your project to tune performance:

```ini
# .env
BORING_LOCAL_MODEL_PATH=~/.boring/models/my-custom-model.gguf
BORING_LOCAL_CTX_WINDOW=8192
BORING_LOCAL_GPU_LAYERS=35  # Offload layers to GPU
```

---

*Last updated: V14.0.0*
