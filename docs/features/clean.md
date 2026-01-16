# 🧹 Cleanup Tool (boring clean)

The `boring clean` command is your primary tool for maintaining a clean and unified development environment. It identifies and removes temporary artifacts, caches, and legacy files that are no longer needed.

## 🌟 Key Features

- **Unified Structure Enforcement**: Helps shift legacy standalone files (like `.boring_memory`) into the unified `.boring/` directory.
- **Artifact Removal**: Safely removes circuit breaker states, response analyses, and temporary prompt files.
- **Selective Cleanup**: Choose between a standard cleanup or a complete deep purge of all Boring-related metadata.

## 🛠️ Usage

### Standard Cleanup
Removes temporary files and logs that are safe to delete without losing project history.

```bash
boring clean
```

### Deep Purge (All)
Removes **all** Boring-related metadata, including backups, Brain records, and memory. Use this when you want to reset Boring for a specific project.

```bash
boring clean --all
```

### Skip Confirmations
Combine with `--force` to run non-interactively.

```bash
boring clean --force
boring clean --all --force
```

## 📂 What gets cleaned?

### Standard Mode
- `.circuit_breaker_state`, `.circuit_breaker_history`
- `.exit_signals`, `.last_loop_summary`
- `.call_count`, `.last_reset`
- `.response_analysis`
- `boring.log`
- Temporary prompt files (`.boring_run_prompt.md`)

### Deep Mode (`--all`)
- `.boring/` (Unified Data Directory)
- `.boring_memory`, `.boring_brain` (Knowledge Base)
- `.boring_cache`, `.boring_data`
- `.boring_backups`
- legacy `.agent/` directories

## ⚠️ Important Note
`boring clean --all` is a destructive operation. While Boring keeps backups in `.boring_backups` for some operations, `clean --all` will remove those backups as well. Use with caution.

---
*Boring Cleanup - Keep your workspace lean and focused.*
