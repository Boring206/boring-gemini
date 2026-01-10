# Token Optimization Guide

> **Requirement**: Boring V10.28+

Boring MCP introduces a new Token Optimization mechanism designed to address the cost and latency issues of large context windows. Through intelligent `verbosity` control and Prompt Caching, we can save up to **90%** of token consumption.

---

## Core Concepts

### 1. Verbosity Levels
All major tools now support the `verbosity` parameter, providing three levels of output:

| Level | Keyword | Token Usage | Use Case | Content |
|-------|---------|-------------|----------|---------|
| **Minimal** | `minimal` | ~20-100 | Automated scans, initial checks | Only status, scores, summary stats |
| **Standard** (Default) | `standard` | ~500 | Daily development, interactive queries | Key summary, Top 5 issues, key code snippets |
| **Verbose** | `verbose` | ~1000+ | Deep debugging, full review | Full report, all issue lists, fix suggestions |

### 2. Prompt Caching
For static content (like tool discovery `boring_discover`), we added special cache markers:
`<!-- CACHEABLE_CONTENT_START -->` ... `<!-- CACHEABLE_CONTENT_END -->`

This allows Claude and Gemini's Prompt Caching mechanism to automatically identify and cache this constant content, drastically reducing billing tokens for repetitive requests.

---

## 🛠️ Configuration Guide

### Global Settings (Recommended)
You can set the default verbosity for all tools via environment variables.

**Unix/Mac**:
```bash
export BORING_MCP_VERBOSITY=minimal
```

**Windows (PowerShell)**:
```powershell
$env:BORING_MCP_VERBOSITY="minimal"
```

**MCP Config (`claude_desktop_config.json` or `smithery.yaml`)**:
```json
{
  "mcpServers": {
    "boring": {
      "command": "boring-mcp",
      "env": {
        "BORING_MCP_VERBOSITY": "minimal",
        "BORING_MCP_PROFILE": "ultra_lite"
      }
    }
  }
}
```

### Single Call Override
You can override global settings at any time when calling a specific tool.

```python
# Even if global is minimal, this returns a detailed report
boring_security_scan(project_path=".", verbosity="verbose")
```

---

## 📊 Tool Behavior Details

### 1. Security Scan (`boring_security_scan`)

- **Minimal**: `{"status": "failed", "summary": "Found 3 issues (Secrets: 1, ...)", "hint": "..."}`
- **Standard**: Includes `top_issues` (Top 5 issue summaries) and detailed breakdown statistics.
- **Verbose**: Fully includes all `issues` lists, with file paths, line numbers, fix suggestions, and full descriptions.

### 2. RAG Search (`boring_rag_search`)

- **Minimal**: Lists only filenames and matching scores (`path/to/file.py (0.95)`).
- **Standard**: Shows matching files and key **code snippets** (Function/Class definitions).
- **Verbose**: Shows full function/class implementation content.

### 3. Code Review (`boring_code_review`)

- **Minimal**: Shows only total issue count and severity distribution (`High: 2, Low: 5`).
- **Standard**: Shows summary of top 10 issues and AI-identified major patterns.
- **Verbose**: Lists all specific issues, modification suggestions (diff), and complete optimization strategies.

### 4. Performance Tips (`boring_perf_tips`)

- **Minimal**: Shows only the count of optimization opportunities.
- **Standard**: Top 3 most important performance optimization suggestions.
- **Verbose**: Full analysis report, including complexity analysis and refactoring suggestions.

---

## 💡 Best Practices

1. **Daily Development**: Use **Standard** (Default). It provides enough context for any LLM to understand while keeping reasonable token usage.
2. **Automation/CI**: Use **Minimal**. If you are scripting checks for CI status, Minimal mode is the fastest and cheapest.
3. **When Stuck**: Switch to **Verbose**. When AI cannot understand the problem from the summary, explicitly call `verbosity="verbose"` to provide full context.
4. **Extreme Savings**: Use with `BORING_MCP_PROFILE="ultra_lite"`. This hides most tool descriptions, combined with `verbosity="minimal"` for >95% token savings.

---

## FAQ

**Q: Does Prompt Caching need extra configuration?**
A: No. As long as your LLM client (Claude/Gemini) supports and enables Caching, markers output by Boring MCP will take effect automatically.

**Q: Why does Minimal mode not return specific code lines?**
A: For extreme compression. Minimal mode assumes you only care about "Are there problems" or "Which files". If you need specific locations, use Standard.
