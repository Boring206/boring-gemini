# Boring MCP Configuration Guide

This document explains all environment variables and configuration options for the Boring MCP Server.

---

## 📑 Table of Contents

- [Environment Variables](#environment-variables)
  - [BORING_MCP_MODE](#boring_mcp_mode)
  - [BORING_MCP_PROFILE](#boring_mcp_profile)
    - [Ultra Lite (3 tools)](#ultra-lite-3-tools---v1026-new)
    - [Minimal (8 tools)](#minimal-8-tools)
    - [Lite (20 tools)](#lite-20-tools)
    - [Standard (50 tools)](#standard-50-tools)
    - [Full (~98 tools)](#full-98-tools)
  - [PROJECT_ROOT_DEFAULT](#project_root_default)
  - [BORING_LLM_PROVIDER](#boring_llm_provider)
- [MCP Configuration Examples](#mcp-configuration-examples)
  - [Local Full Version (Recommended)](#local-full-version-recommended)
  - [Smithery Cloud Version](#smithery-cloud-version)
  - [Hybrid (Local + Cloud)](#hybrid-local--cloud)
- [Version Differences](#version-differences)
  - [Installation Options](#installation-options)
  - [Smithery vs Local](#smithery-vs-local)
- [FAQ](#faq)

---

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

| Profile | Tool Count | Token Savings | Description | Use Case |
|---------|------------|---------------|-------------|----------|
| `ultra_lite` | 3 | **97%** | Minimal | Token-constrained LLMs |
| `minimal` | 8 | 92% | Essential only | Quick tasks |
| `lite` | 20 | 80% | Daily development | **Default** |
| `standard` | 50 | 50% | Balanced | Professional dev |
| `full` | ~98 | 0% | All tools | Power User |

**Tools included in each profile:**

#### Ultra Lite (3 tools) - V10.26 NEW
- `boring` (universal router)
- `boring_help` (category discovery)
- `boring_discover` (on-demand tool schema)

> 💡 **Workflow**: Use `boring` to route natural language requests, `boring_discover` to fetch full schema for a specific tool, then call the target tool.

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

### `BORING_LLM_PROVIDER`

Select the underlying model provider.

| Provider | Value | Description |
|----------|-------|-------------|
| **Gemini** | `gemini-cli` | Default. Requires `gemini-cli`. |
| **Claude** | `claude-code` | Requires `claude` CLI. |
| **Ollama** | `ollama` | Local model (Experimental). |

> [!CAUTION]
> **Ollama Limitations**: The current Ollama implementation does **not** support Function Calling (Tool Use).
> If you use `ollama`, `boring` cannot execute tools (edit files, run tests). It will behave as a text-only chat bot.
> For Vibe Coder automation workflows, please use Gemini or Claude.

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

> 📋 **Smithery Deployment Info**
> - **Default Profile**: `lite` (~20 tools)
> - **Installation Type**: `[mcp-lite]` lightweight
> - **RAG Capability**: Degraded to keyword search (no vector DB)
> - **Adjustable**: Set `BORING_MCP_PROFILE: "dev"` or `"pro"` in config
> - **Full RAG**: Requires local install `pip install "boring-aicoding[all]"`

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
- `ultra_lite`, `minimal`, `lite`, `standard`, `full`

### Q: How do I see all available tools?

Call:
```
boring_help
```
Or set `BORING_MCP_PROFILE=full` to see everything.
