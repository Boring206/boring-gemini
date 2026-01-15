# AI Connection Guide

Boring-Gemini is an AI-powered development engine that requires a connection to a powerful LLM (Large Language Model) to function. This guide will help you set up different AI providers.

## Supported Providers

| Provider | Scenario | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | **Default/Recommended** | Best compatibility, Native Function Calling, Long Context Window | Requires Internet |
| **Ollama** | Local/Privacy | Fully offline, private, no API cost | Requires strong hardware, limited advanced Tool features |
| **Claude** | Alternative | Strong reasoning (via Adapter) | Requires extra setup |

---

## 1. Google Gemini (Recommended) 💎

Boring is optimized for the Gemini architecture, so using Gemini provides the complete experience (One Dragon, Vibe Check, etc.).

### Method A: API Key (Fastest) 🚀

This is the simplest and most stable method.

1.  **Get Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to create an API Key.
2.  **Set Environment Variable**:

    **Windows (PowerShell):**
    ```powershell
    $env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

    **Linux / macOS:**
    ```bash
    export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

    **Persistent (Optional):**
    Create a `.env` file in the project root:
    ```env
    GOOGLE_API_KEY=YOUR_API_KEY_HERE
    ```

### Method B: Gemini CLI (Keyless) 🛡️

If you prefer not to manage API Keys or want to use Google Cloud quotas.

1.  Run the Boring Setup Wizard:
    ```bash
    boring wizard
    ```
2.  Select **Yes** when asked to install Node.js and Gemini CLI.
3.  The system will guide you through Google Account login (OAuth).

---

## 2. Ollama (Local LLM) 🦙

Boring supports connecting to local models via Ollama (e.g., Llama 3, Mistral, Gemma 2).

### Prerequisites
1.  Install [Ollama](https://ollama.com/).
2.  Download a model (e.g., Llama 3):
    ```bash
    ollama pull llama3
    ```
3.  Ensure Ollama is running (Default Port 11434).

### Configuration

You only need to set environment variables to switch the Provider.

**Windows (PowerShell):**
```powershell
# 1. Switch Provider
$env:BORING_LLM_PROVIDER="ollama"

# 2. (Optional) Specify model, default is llama3
$env:BORING_LLM_MODEL="llama3"

# 3. (Optional) If Ollama runs on a different port
$env:OLLAMA_BASE_URL="http://localhost:11434"
```

**Linux / macOS:**
```bash
export BORING_LLM_PROVIDER="ollama"
export BORING_LLM_MODEL="llama3"
```

### Known Limitations (Ollama Mode)
*   **Function Calling**: Currently, Ollama mode relies mainly on Prompt Engineering for tool calls, which is less accurate than Gemini Native Function Calling.
*   **Context Window**: Limited by the local model's context size (usually 4k-8k), so it might not handle RAG retrieval for very large files.

---

## 3. Verify Connection

After setup, run the following to test:

```bash
# Simple test
boring "Hello, which model are you using?"

# Check health (Shows current Provider)
boring health
```

---

## FAQ

**Q: Can I set up both Gemini and Ollama?**
A: Yes. Boring prioritizes the `BORING_LLM_PROVIDER` variable. If unset, it defaults to Gemini. You can switch between them by toggling this variable.

**Q: Ollama response is slow?**
A: Please ensure your GPU is powerful enough. Some Boring features (like Rerank, Embedding) also consume resources, which might compete with Ollama for VRAM.

**Q: Support for OpenAI or Anthropic?**
A: Core support focuses on Gemini and Ollama. While there is experimental Adapter support for Claude, Gemini is recommended for a stable experience.
