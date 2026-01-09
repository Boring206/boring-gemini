# Boring for Gemini

[![PyPI version](https://badge.fury.io/py/boring-aicoding.svg)](https://badge.fury.io/py/boring-aicoding)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Autonomous AI Agent Loop with VibeCoder Experience**

---

## ✨ The Vibe Coder Experience

**No Code Needed.** Just describe the vibe.

Boring-Gemini features a **Universal Natural Language Router**. You don't need to remember 98+ complex tools. Just say what you want:

> "Search for authentication logic"  
> "Review my code for security issues"  
> "幫我寫測試" (Help me write tests)

---

## ⚡ Why Boring?

| Feature | Description |
|---------|-------------|
| 🧠 **Autonomous Loop** | Runs continuously, thinking, coding, testing, and fixing until done |
| 🕵️ **Hybrid RAG** | Advanced code search with HyDE + Cross-Encoder |
| 🛡️ **Shadow Mode** | Safe execution sandbox catches dangerous ops before they happen |
| ⚡ **30% Faster** | Smart caching reduces context usage by 80% |
| 🧩 **Vibe Coder** | Most human-friendly AI coding interface |

---

## 🚀 Quick Installation

### Smithery (Recommended)

```bash
npx -y @smithery/cli@latest install boring/boring --client cursor
```

### Local pip

```bash
pip install boring-aicoding[mcp]
```

---

## 📦 Usage

### As MCP Server (Recommended)

Add to your IDE's MCP configuration:

```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp"
    }
  }
}
```

### CLI Tools

```bash
boring-monitor      # TUI Dashboard
boring-dashboard    # Web Dashboard  
boring-route "query"  # Natural Language Router
```

---

## 🔧 Key Features

- **55+ MCP Tools**: RAG, Testing, Review, Security, Git, and more
- **Multi-Language**: Python, JavaScript, TypeScript support
- **Quality Gates**: CI/CD integration with multi-tier verification
- **Memory System**: Persistent learning and pattern recognition
- **LLM-as-a-Judge**: Advanced evaluation with bias monitoring

---

## 📚 Documentation

- [GitHub Repository](https://github.com/Boring206/boring-gemini)
- [Vibe Coder Guide](https://github.com/Boring206/boring-gemini/blob/main/docs/guides/vibe-coder.md)
- [MCP Tools Reference](https://github.com/Boring206/boring-gemini/blob/main/docs/features/mcp-tools.md)

---

## 📄 License

Apache 2.0 - See [LICENSE](https://github.com/Boring206/boring-gemini/blob/main/LICENSE)
