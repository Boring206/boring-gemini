# Boring for Gemini

[![PyPI version](https://badge.fury.io/py/boring-aicoding.svg)](https://badge.fury.io/py/boring-aicoding)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Autonomous AI Agent Loop with VibeCoder Experience**

---

## ✨ The Vibe Coder Experience

**No Code Needed.** Just describe the vibe.

Boring-Gemini features a **Universal Natural Language Router**. You don't need to remember 60+ complex tools. Just say what you want:

> "Search for authentication logic"  
> "Review my code for security issues"  
> "幫我寫測試" (Help me write tests)

---

## 🚀 Quick Start (One-Click)

### 🪄 Zero-Config Wizard 
Boring features a smart setup wizard that automatically bridges your IDE (Cursor, VS Code, Claude Desktop) with the Gemini agent.

```bash
pip install "boring-aicoding[all]"
boring wizard
```

### 💎 Smithery Integration
One-click install for Cursor/Claude Desktop.

```bash
npx -y @smithery/cli@latest install boring/boring --client cursor
```

---

## 🧐 Async Evolution (V13.0.0)

V13.0.0 marks the **Async Evolution** era, focusing on multi-agent collaboration and extreme performance:

- **⚡ Async Agent Runner**: Simultaneous execution of Architect, Coder, and Reviewer for 3x development speed.
- **📂 Semantic Storage Fallback**: Full FAISS integration for local vector search when ChromaDB is unavailable.
- **🚀 Prompt Caching**: Smart context reuse reduces token costs by ~15-30% for iterative loops.
- **🐉 One Dragon Flow**: Integrated State-Machine (Architect -> Builder -> Healer -> Polish -> Evolver).
- **🏆 Skill Compilation**: High-frequency successful patterns distilled into Strategic Skills.
- **🌐 Global Swarm Sync**: Real-time knowledge synchronization via Git.

---

## ⚡ Core Capabilities

| Feature | Description |
|---------|-------------|
| 🧠 **Autonomous Loop** | Runs continuously: thinking → coding → testing → fixing. |
| 🕵️ **Context Optimization** | 80% token savings via smart chunking and specificity ranking. |
| 🛡️ **Shadow Mode** | Safe execution sandbox catches destructive operations before they happen. |
| 🧩 **Natural Language** | Universal Router: "幫我寫測試" or "Fix auth bugs" triggered instantly. |
| 🧪 **Vibe Score** | Gamified health check: Lint, Security, and Docs tracked over time. |

---

## 📦 Usage Modes

### As MCP Server (Recommended for IDEs)
```json
{
  "mcpServers": {
    "boring": { "command": "boring-mcp" }
  }
}
```

### Managed CLI Utilities
- `boring-monitor`: Fullscreen TUI dashboard for live agent monitoring.
- `boring-dashboard`: Modern web UI for project health and history.
- `boring-setup`: Scaffold new Boring-ready projects in seconds.

**About `boring-route`**: This command only **shows** which MCP tool would be selected for your query. To actually execute the tool, use it in your MCP client (Cursor/Claude Desktop).

---

## 🔧 Key Features

- **67+ MCP Tools**: RAG, Testing, Review, Security, Git, and more
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
