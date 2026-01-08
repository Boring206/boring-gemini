# Installation Guide

> Get Boring installed in under 2 minutes.

---

## 🚀 Quick Install

### Option 1: Smithery (Recommended)

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

> ⚠️ **Gemini Client Users**: If you encounter issues installing via Smithery, please use **Option 2 (pip)**. Direct Smithery integration on Gemini Client can be intermittent.

**Best for**: Multi-project workflows, cloud development, automatic updates.

### Option 2: pip

```bash
# Full Installation (Recommended for Vibe Coder)
pip install "boring-aicoding[all]"

# Minimal Installation
pip install boring-aicoding
```

**🤔 Which one should I choose?**

| Feature | `[all]` (Full) | Basic |
| :--- | :--- | :--- |
| **RAG Memory** | ✅ Vector + Semantic | ⚠️ Keyword only (Weak) |
| **Self-Verify** | ✅ Can run tests (`boring verify`) | ❌ Cannot verify |
| **Dashboard** | ✅ GUI Available | ❌ None |
| **Use Case** | **Vibe Coding** | CLI Only |

**Best for**: Single projects, CI/CD, offline environments. `[all]` includes everything needed for full Vibe Coder experience (RAG, self-healing, GUI).

### Option 3: Manual Clone (Fallback)

If `pip install` fails or you want the latest source:

```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e .
```

---

## ⚙️ MCP Configuration

### Claude Desktop / Cursor

Add to your MCP config:

{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp",
      "args": [],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "pro",
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

> **Note**: `boring-mcp` is installed automatically with pip. It enables a cleaner configuration than invoking python directly.

### 🖥️ Dashboard & GUI

If you installed with `[all]` or `[gui]`, you can launch the control dashboard:

```bash
boring-dashboard
```

This opens a browser interface to view logs, circuit breaker status, and memory patterns.

### Config File Locations

| Client | Location |
|--------|----------|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | Settings → MCP Servers |

---

## ✅ Verify Installation

```bash
boring --version
boring --version
# Expected: boring v10.18.3

boring-route --help
# Expected: Boring Route - Natural Language Tool Router

```

---

## Next Steps

- [Quick Start Guide](./quickstart.md)
- [Vibe Coder Guide](../guides/vibe-coder.md)
- [Full Documentation](../index.md)
