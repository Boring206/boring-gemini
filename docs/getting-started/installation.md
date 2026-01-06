# Installation

## Recommended: Smithery (One-Click)

The easiest way to install Boring for use with Cursor or Claude Desktop:

```bash
npx @smithery/cli install boring
```

## Required Configuration

Boring requires companion MCP servers for full functionality. Add this to your IDE's MCP config:

```json
{
  "mcpServers": {
    "boring": {
      "command": "npx",
      "args": ["-y", "@smithery/cli", "run", "@boring/boring", "--config", "{}"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "criticalthink": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp@latest"]
    }
  }
}
```

## Alternative: pip install

For development or custom installations:

```bash
# Clone the repository
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini

# Install with all extras
pip install -e ".[all,dev]"

# Install extensions
boring setup-extensions
```

## Verify Installation

```bash
boring --help
boring-mcp --help
```
