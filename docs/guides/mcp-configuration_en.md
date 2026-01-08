# Boring MCP Configuration Guide

This document explains all environment variables and configuration options for the Boring MCP Server.

## Environment Variables

### `BORING_MCP_MODE`

| Value | Description |
|-------|-------------|
| `1` | ✅ **Enable MCP mode** - Required |
| `0` or unset | ⚠️ Test/CLI mode, MCP tools may not work properly |

**Affected areas:**
- Shadow Mode interception
- Tool initialization
- Log output format

---

### `BORING_MCP_PROFILE`

Controls how many tools are exposed to the AI.

| Profile | Tool Count | Description | Use Case |
|---------|------------|-------------|----------|
| `minimal` | 8 | Essential only | Quick tasks |
| `lite` | 20 | Daily development | **Default** |
| `standard` | 50 | Balanced | Professional dev |
| `full` | ~98 | All tools | Power User |

**Tools included in each profile:**

#### Minimal (8 tools)
- `boring` (router)
- `boring_help`
- `boring_rag_search`
- `boring_commit`
- `boring_verify`
- `boring_vibe_check`
- `boring_shadow_status`
- `boring_suggest_next`

#### Lite (20 tools)
Includes all Minimal, plus:
- `boring_rag_index`, `boring_rag_context`
- `boring_code_review`, `boring_perf_tips`
- `boring_test_gen`, `boring_doc_gen`
- `boring_security_scan`
- `boring_prompt_plan`, `boring_prompt_fix`
- `boring_impact_check`, `boring_context`

#### Standard (50 tools)
Includes all Lite, plus:
- Full RAG suite (`boring_rag_expand`, `boring_rag_status`)
- Shadow Mode controls (`boring_shadow_mode`, `boring_shadow_approve`)
- Git Hooks (`boring_hooks_install`, `boring_hooks_status`)
- Intelligence (`boring_predict_impact`, `boring_brain_health`)
- Workspace management
- Multi-agent planning
- Core Speckit tools

#### Full (~98 tools)
All registered tools.

---

### `PROJECT_ROOT_DEFAULT`

| Value | Description |
|-------|-------------|
| `.` | Use current working directory |
| `/path/to/project` | Specify project path |

---

## MCP Configuration Examples

### Local Full Version (Recommended)

```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp",
      "args": [],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "standard",
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

### Smithery Cloud Version

```json
{
  "mcpServers": {
    "boring": {
      "url": "https://server.smithery.ai/@boring/boring-mcp/mcp"
    }
  }
}
```

### Hybrid (Local + Cloud)

```json
{
  "mcpServers": {
    "boring-cloud": {
      "url": "https://server.smithery.ai/@boring/boring-mcp/mcp"
    },
    "boring-local": {
      "command": "boring-mcp",
      "args": [],
      "env": {
        "BORING_MCP_MODE": "1",
        "BORING_MCP_PROFILE": "full",
        "PROJECT_ROOT_DEFAULT": "."
      }
    }
  }
}
```

---

## Version Differences

### Installation Options

| Installation | RAG Support | Docker Size |
|--------------|-------------|-------------|
| `pip install boring-aicoding[mcp-lite]` | ❌ Degraded | ~500MB |
| `pip install boring-aicoding[mcp]` | ✅ Full | ~4GB |

### Smithery vs Local

| Feature | Smithery (mcp-lite) | Local (mcp) |
|---------|---------------------|-------------|
| Basic tools | ✅ | ✅ |
| RAG semantic search | ⚠️ keyword fallback | ✅ Vector search |
| Local notifications | ❌ | ✅ |
| Offline use | ❌ | ✅ |

---

## FAQ

### Q: Smithery has fewer tools, what should I do?

Smithery defaults to `mcp-lite` + `lite` profile. For more features:
1. Install full version locally: `pip install "boring-aicoding[mcp]"`
2. Set `BORING_MCP_PROFILE=full`

### Q: What is the `pro` profile?

`pro` is not a valid value and falls back to `lite`. Valid values are:
- `minimal`, `lite`, `standard`, `full`

### Q: How do I see all available tools?

Call:
```
boring_help
```
Or set `BORING_MCP_PROFILE=full` to see everything.
