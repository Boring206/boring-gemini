# Configuration Reference

> **Simple Guide for Beginners**: Boring has two ways to configure. Choose based on your needs.

---

## 🚦 Quick Start: Where do I edit?

### Scenario 1: I am a Solo Developer (Use Cursor/Claude)
**👉 You should edit `mcp.json` (or Cursor Settings)**
This is for preferences that affect **only you**, such as:
- Cost savings (Token Optimization)
- Performance tuning
- Profile Selection (Lite/Standard)

### Scenario 2: I am a Team Lead
**👉 You should create `.boring.toml` (in Project Root)**
This is for rules that **the whole team** must follow, such as:
- Code Quality Standards (Lint/Test)
- Security Scan Levels
- CI/CD Rules

---

## 🙋 Common Scenarios (Cookbook)

### 1. I want to Save Money (Token Optimization)
Edit your MCP JSON Config:
```json
"env": {
  "BORING_MCP_VERBOSITY": "minimal",  // Minimized output (Saves 90%)
  "BORING_MCP_PROFILE": "ultra_lite"  // Minimized tools
}
```

### 2. I want Max Performance (Parallelism)
Edit your MCP JSON Config:
```json
"env": {
  "BORING_WORKER_COUNT": "8"  // Run 8 threads parallel
}
```

### 3. I want Stricter Security (Shadow Mode)
Edit your `.boring.toml`:
```toml
[boring]
enable_shadow_mode = true

[boring.security]
secret_scan = true       # Scan for passwords
dependency_scan = true   # Scan for vulnerabilities
```

---

## 🔧 Detailed Reference

### 1. Project Config (`.boring.toml`)
Place this file in your project root.

#### `[boring]` Global Settings
```toml
[boring]
# Enable debug logs (default: false)
debug = false
# Enable RAG Memory (default: true)
enable_rag = true
```

#### `[boring.quality_gates]`
Define the "Definition of Done".
```toml
[boring.quality_gates]
min_coverage = 40        # Minimum Test Coverage %
max_complexity = 15      # Max allowed complexity
max_file_lines = 500     # Max lines per file
check_untyped_defs = true # Strict typing
```

#### `[boring.hooks]` (Git Hooks)
Control behavior on Commit/Push.
```toml
[boring.hooks]
pre_commit_level = "STANDARD" # Check on commit
pre_push_level = "FULL"       # Check on push
auto_fix = true               # Auto-fix simple errors
timeout_seconds = 300         # Timeout in seconds
```

### 2. Environment Variables & MCP JSON (`env`)
These are usually set in the `env` section of your Cursor/Claude MCP config.

| Variable Name | Default | Description |
| :--- | :--- | :--- |
| **Core Settings** | | |
| `BORING_MCP_PROFILE` | `lite` | Toolset Size (`minimal`, `lite`, `standard`, `full`, `ultra_lite`) |
| `BORING_MCP_VERBOSITY`| `standard` | Output Verbosity (`minimal`, `standard`, `verbose`) |
| `BORING_LAZY_MODE` | `0` | **Lazy Mode**: 0=Standard, 1=Lazy (Uses progressive disclosure to save 90% schema tokens) |
| `BORING_LOG_LEVEL` | `INFO` | Log Level |
| **Security Settings**| | |
| `SHADOW_MODE_LEVEL` | `ENABLED` | Sandbox Level (`DISABLED`, `ENABLED`, `STRICT`) |
| `BORING_ALLOW_DANGEROUS`| `false` | Allow dangerous ops (Not Recommended) |
| **Performance** | | |
| `BORING_WORKER_COUNT` | `4` | Number of parallel workers |
| `BORING_CACHE_DIR` | `.boring/cache`| Cache directory location |
| **System** | | |
| `BORING_PROJECT_ROOT` | `.` | Force project path |
| `BORING_RAG_ENABLED` | `1` | Enable RAG (0=Disable) |

---

## 📝 Complete Example: MCP JSON

This is what it looks like in your Cursor Settings:

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "BORING_MCP_MODE": "1",           // REQUIRED: Enable MCP Mode
        "BORING_MCP_PROFILE": "lite",     // RECOMMENDED: For daily dev
        "BORING_MCP_VERBOSITY": "minimal",// RECOMMENDED: Save tokens
        "PROJECT_ROOT_DEFAULT": "."       // Default to current dir
      }
    }
  }
}
```
