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

### Option 2.5: uv (⚡ Ultra-Fast)

> **New!** Install 10-100x faster with [uv](https://github.com/astral-sh/uv)

```bash
# Install uv first (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install boring-aicoding with uv
uv pip install "boring-aicoding[all]"

# Or use uv to manage the entire project
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows
uv pip install "boring-aicoding[all]"
```

**Why uv?**
- ⚡ 10-100x faster than pip
- 🎯 Better dependency resolution
- 🔒 Deterministic builds
- 📦 Smaller cache

---

## ⚙️ MCP Configuration (Critical!)

After installation, add this to your MCP Config (Cursor/Claude):

### For Cursor / Claude Desktop (Standard pip)

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

### For uv Installation (⚡ Recommended for Performance)

**Method 1: uvx (No local installation required)**

```json
{
  "mcpServers": {
    "boring": {
      "command": "uvx",
      "args": ["--from", "boring-aicoding[all]", "python", "-m", "boring.mcp.server"],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "lite",
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

**Method 2: uv run (Using venv)**

```json
{
  "mcpServers": {
    "boring": {
      "command": "uv",
      "args": ["run", "python", "-m", "boring.mcp.server"],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "lite",
        "PROJECT_ROOT_DEFAULT": ".",
        "VIRTUAL_ENV": "/path/to/your/.venv"
      }
    }
  }
}
```

**Benefits of uv for MCP:**
- ⚡ Server startup ~30% faster
- 🔒 Isolated dependencies per project
- 📦 Automatic environment management
- 🎯 No global package pollution

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
