# 安裝指南 (Installation)

> **🇨🇳 懶人包**: 推薦使用 **Option 1 (Smithery)** 自動安裝，或 **Option 2 (pip)** 手動安裝。
> 安裝完後，請參閱 [快速入門](./quickstart.md)。

---

## 🚀 Quick Install

### Option 1: Smithery for Claude/Gemini (Recommended)

The easiest way to install without touching the terminal.

```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```

### Option 2: pip (Manual)

If you prefer control or use `pip`:

```bash
# Recommended for Vibe Coder (Includes RAG & Verified tools)
pip install "boring-aicoding[all]"
```

---

## ⚙️ MCP Configuration (Critical!)

After installation, add this to your MCP Config (Cursor/Claude):

### for Cursor / Claude Desktop

```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp",
      "args": [],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "lite",  
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

> **Profiles**:
> - `lite` (Default): 20 essential tools. Fast & Cheap.
> - `standard`: 50 tools. Good for power users.
> - `full`: 98+ tools. Expensive on tokens.

---

## ✅ Verify

Run this in your terminal:

```bash
boring --version
# Output: boring v10.31.0  (or newer)
```
