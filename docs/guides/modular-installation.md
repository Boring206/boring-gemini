# 📦 Modular Installation Guide (Boring Diet)

## Why Modular Installation? (Deep Thinking Analysis)

Boring-Gemini v10.28.0 introduces the **"Boring Diet"** optimization. While the core package is still `boring-aicoding`, the installation is now split into multiple optional "Extras".

### 1. Size & Start-up Speed
- **Core Package (< 50MB)**: Light, fast, and starts in milliseconds.
- **Full Package (> 1.5GB)**: Includes heavy-weights like **Torch**, **ChromaDB**, and **Sentence-Transformers**.
- **The Logic**: By splitting these, we ensure users who only need the CLI for basic Git automation don't pay the performance tax of loading heavy ML libraries.

### 2. Environment Compatibility
- **Dependency Conflicts**: Large libraries like `torch` have complex dependency trees that might clash with other tools in your environment.
- **Isolated Environments**: In CI/CD or lightweight containers, you usually only need the core logic. Modular installation allows you to keep your containers small and stable.

### 3. Token Economy & LLM Attention
- **MCP Context**: When using Boring as an MCP server, a cleaner environment helps the LLM reasoning process. It reduces the chance of the model being confused by unrelated library metadata.

---

## 🛠️ Installation Commands

| Command | Features | Recommended Profile | Recommended For |
| :--- | :--- | :--- | :--- |
| `pip install boring-aicoding` | Base CLI + Core logic | `lite` | Daily Git tasks, simple automation. |
| `pip install "boring-aicoding[vector]"` | + RAG (ChromaDB + Torch) | `standard` | Projects requiring deep semantic search. |
| `pip install "boring-aicoding[gui]"` | + Dashboard (Streamlit) | - | Visualizing project health metrics. |
| `pip install "boring-aicoding[mcp]"` | + FastMCP | `standard` / `full` | Professional IDE integration. |
| `pip install "boring-aicoding[all]"` | **Complete Experience** | `full` | **Vibe Coders** (Power Users). |

---

## ⚡ Quick Reference: Installation vs. Profile

If you use **Modular Installation**, match your `BORING_MCP_PROFILE` to your installation level:

- **Core**: Use `minimal` or `lite`.
- **Vector**: Use `standard`.
- **Full**: Use `full` (God Mode).
