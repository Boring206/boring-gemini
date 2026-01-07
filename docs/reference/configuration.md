# Configuration Reference

> The complete guide to configuring Boring via `.boring.toml` and Environment Variables.

---

## 📄 Project Configuration (`.boring.toml`)

Place this file in your project root to control Boring's behavior.

### `[boring]` Global Settings

```toml
[boring]
# Enable debug logging (default: false)
debug = false

# Enable/Disable specific features
enable_shadow_mode = true
enable_rag = true
```

### `[boring.performance]`

Performance tuning settings.

```toml
[boring.performance]
# Number of parallel workers for verification (default: 4)
# Recommendations: 
# - Small projects (<500 files): 2-4
# - Large projects (>1000 files): 8-16
parallel_workers = 4

# Enable caching of verification results (default: true)
# Disabling this forces a full re-check every time.
verification_cache = true

# Incrementally update RAG index (default: true)
incremental_rag = true
```

### `[boring.quality_gates]`

Thresholds for verification failure.

```toml
[boring.quality_gates]
# Minimum unit test coverage percentage (0-100)
min_coverage = 40

# Maximum Allowed Cyclomatic Complexity (McCabe)
max_complexity = 15

# Max lines per file allowed
max_file_lines = 500

# Max lines per function allowed
max_function_lines = 50

# Strict Type Checking (mypy)
check_untyped_defs = true
disallow_any_generics = false
```

### `[boring.hooks]`

Git Hook behavior.

```toml
[boring.hooks]
# Verification level for 'git commit'
# Options: BASIC, STANDARD, FULL
pre_commit_level = "STANDARD"

# Verification level for 'git push'
pre_push_level = "FULL"

# Automatically fix linting errors (default: true)
auto_fix = true

# Timeout in seconds for hooks
timeout_seconds = 300

[boring.hooks.bypass_patterns]
# Files to ignore during hook verification
skip_files = ["*.md", "docs/*", "tests/fixtures/*"]
```

### `[boring.security]`

Security scan configuration.

```toml
[boring.security]
# Minimum severity to report (low, medium, high)
bandit_severity = "medium"

# Scan project dependencies for vulnerabilities
dependency_scan = true

# Scan for secrets/credentials
secret_scan = true
```

---

## 🌐 Environment Variables

Global overrides, best set in `.env` or CI/CD pipelines.

### Core
| Variable | Default | Description |
|----------|---------|-------------|
| `BORING_LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `BORING_PROJECT_ROOT` | `.` | Override project root path |
| `BORING_CI_MODE` | `0` | Set to `1` to disable interactive prompts |

### Shadow Mode
| Variable | Default | Description |
|----------|---------|-------------|
| `SHADOW_MODE_LEVEL` | `ENABLED` | Security level (`DISABLED`, `ENABLED`, `STRICT`) |
| `BORING_ALLOW_DANGEROUS` | `false` | Set `true` to bypass some safety checks (NOT RECOMMENDED) |

### Performance
| Variable | Default | Description |
|----------|---------|-------------|
| `BORING_WORKER_COUNT` | `4` | Override parallel worker count |
| `BORING_CACHE_DIR` | `.boring_cache` | Custom cache directory |

### Brain & Memory
| Variable | Default | Description |
|----------|---------|-------------|
| `BORING_BRAIN_PATH` | `~/.boring_brain` | Global knowledge storage path |
| `BORING_RAG_ENABLED` | `1` | Set `0` to disable RAG entirely |

---

## 🛠️ MCP Configuration (`smithery.yaml`/`mcp_config.json`)

When running as an MCP Server:

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "SHADOW_MODE_LEVEL": "STRICT",
        "BORING_MCP_MODE": "1"
      }
    }
  }
}
```

### MCP-Specific Variables

| Variable | Description |
|----------|-------------|
| `BORING_MCP_MODE` | Must be `1` for MCP server operation |
| `PROJECT_ROOT_DEFAULT` | Default path if client doesn't provide one |

---

## 💡 Example: Full Production Config

**.boring.toml**
```toml
[boring]
debug = false

[boring.performance]
parallel_workers = 8
verification_cache = true

[boring.quality_gates]
min_coverage = 80
max_complexity = 10
check_untyped_defs = true

[boring.hooks]
pre_commit_level = "STANDARD"
pre_push_level = "FULL"
auto_fix = false 

[boring.security]
bandit_severity = "high"
```

**.env**
```bash
SHADOW_MODE_LEVEL=STRICT
BORING_CI_MODE=1
```
