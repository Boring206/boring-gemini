# ✨ Vibe Coder Experience (V10.24)

> **Philosophy**: "Don't write code. Just describe the vibe."

The **Vibe Coder** feature set in Boring-Gemini V10.24 is designed for the modern AI-assisted developer who prefers natural language over manual configuration. It transforms the 98+ complex MCP tools into a seamless, conversational interface.

## 🎯 The Universal Router

Instead of remembering dozens of tool names like `boring_rag_search`, `boring_security_scan`, or `boring_test_gen`, you now have a single entry point: **`boring()`**.

### How it Works

The router uses semantic analysis to understand your intent and route your request to the best tool.

```python
# Old Way (Classic MCP)
# You had to know the tool name and specific parameters
client.call_tool("boring_rag_search", query="authentication logic", threshold=0.5)

# ✨ Vibe Coder Way
# Just say what you want
boring("search for authentication logic")
```

### Supported Categories

The router understands intents across 17 categories:

| Category | Keywords (English/Chinese) | Target Tools |
|----------|----------------------------|--------------|
| **Coding** | `code`, `search`, `找程式碼` | `rag_search` |
| **Testing** | `test`, `verify`, `幫我寫測試` | `test_gen`, `verify` |
| **Review** | `review`, `audit`, `審查`, `健檢` | `code_review`, `security_scan` |
| **Planning** | `plan`, `architect`, `我想做...` | `prompt_plan` |
| **Git** | `commit`, `push`, `提交` | `commit` |

## 💻 CLI Usage: `boring-route`

We've added a CLI tool so you can use Vibe Coder capabilities directly from your terminal, without needing an elaborate IDE setup.

```bash
# Ask for tests
boring-route "帮我写测试"
# 🎯 Matched: boring_test_gen (100%)

# Check security
boring-route "review my code for security"
# 🎯 Matched: boring_security_scan (85%)
```

## 🎛️ Tool Profiles

To further optimize your experience and save LLM token usage, we introduced **Tool Profiles**.

| Profile | Tools Loaded | Best For |
|---------|--------------|----------|
| **Minimal** | 8 | Pure conversation, minimal overhead |
| **Lite** (Default) | 19 | Everyday Vibe Coding (Router + Essentials) |
| **Standard** | 50 | Heavy development tasks |
| **Full** | 98+ | Power user, full control |

### Configuration

In `.boring.toml`:
```toml
[boring.mcp]
profile = "lite"
enable_router = true
```

## 🚀 Why This Matters

1.  **Context Efficiency**: Reduces context window usage by ~80% (19 tools vs 98 tools).
2.  **Accuracy**: The router logic helps the LLM avoid "hallucinating" tool names.
3.  **Speed**: Faster tool selection means faster turnaround time.
4.  **Simplicity**: You only need to know **one** function: `boring()`.
