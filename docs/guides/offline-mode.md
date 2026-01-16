# 🔌 Offline-First Mode

Boring V13.2 introduces powerful offline-first capabilities, allowing you to enjoy AI-assisted development even without an internet connection or in environments with high privacy requirements.

## 🌟 Key Features

- **Zero Network Dependency**: After initial setup, all LLM inferences run locally on your machine.
- **Privacy Guaranteed**: Your code, data, and conversations never leave your local environment.
- **Intelligent Switching**: Automatically switches between local models and APIs to optimize performance and accuracy.
- **Multi-Model Support**: Supports state-of-the-art lightweight local models like Phi-3, Qwen2.5, and Llama 3.2.

## 🛠️ Installation & Setup

### 1. Install Local Dependencies
Install the extra packages required for local model support:

```bash
pip install "boring-aicoding[local]"
```

### 2. Download Local Models
Boring provides built-in tools to help download recommended GGUF models:

```bash
# Download the default recommended model (Qwen2.5-1.5B)
boring local download
```

## ⚙️ Configuration

Configure your local model path in `.boring.toml`:

```toml
[boring]
offline_mode = true
local_llm_model = "~/.boring/models/phi-3-mini-4k-instruct.gguf"
local_llm_context_size = 4096
```

### Quick Mode Toggle
You can also switch modes quickly via environment variables:

- `BORING_OFFLINE_MODE=1`: Force offline mode.
- `BORING_PREFER_LOCAL=1`: Prefer local models for simple tasks.

## 🎯 Intelligent Routing Rules

Boring's `ModelRouter` automatically selects the backend based on task complexity:

| Task Type | Complexity | Preferred Backend |
|-----------|------------|-------------------|
| Docstring Generation | Simple | Local Model |
| Code Refactoring | Medium | Local Model or API |
| Architecture Design | Complex | API (Local if offline) |

## ⚠️ Important Notes

1. **Memory Usage**: Running local models requires RAM (at least 8GB recommended).
2. **GPU Acceleration**: If your environment supports CUDA or Metal, `llama-cpp-python` will automatically attempt to enable GPU acceleration.
3. **Model Performance**: Local models may not match the reasoning depth of large API models (like Gemini Pro) for complex logic; they are best suited for routine coding assistance.

---
*Boring V13.2 - Respect your machine, respect your privacy.*
