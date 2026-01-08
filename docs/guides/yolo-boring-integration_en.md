# Gemini YOLO + Boring Maximum Utilization Guide

This guide explains how to combine Gemini CLI's YOLO mode with Boring MCP tools for maximum autonomous development efficiency(AUTO LOOP).

## Core Concept

```
Gemini YOLO = Engine (Execution Power)
Boring MCP  = Toolbox (Professional Skills)
```

When combined, AI can automatically use Boring's 50+ tools to complete complex tasks.

---

## Prerequisites

### 1. Install Boring MCP

Ensure `~/.gemini/settings.json` contains:

```json
{
  "mcpServers": {
    "boring": {
      "command": "uvx",
      "args": ["boring-aicoding"]
    }
  }
}
```

### 2. Verify Setup

```bash
gemini "List all available boring tools"
```

---

## Common YOLO Commands

### 🔍 Code Search + Modification

```bash
gemini --yolo "Use boring_rag_search to find auth-related code, then fix the login bug"
```

### 🧪 Auto Test + Fix

```bash
gemini --yolo "Run boring_verify, if it fails fix the issues, repeat until passing"
```

### 📝 Code Review + Refactor

```bash
gemini --yolo "Run boring_code_review on all Python files in src/, then fix all suggestions"
```

### 🚀 Release Workflow

```bash
gemini --yolo "Execute /release-prep workflow, complete all steps"
```

---

## Advanced Combinations

### Full Auto Development Loop

```bash
gemini --yolo "
1. Use boring_rag_search to understand code structure
2. Read @fix_plan.md to find the next task
3. Implement that task
4. Use boring_verify to validate
5. If passing, mark [x] in @fix_plan.md
6. Repeat until all tasks complete
"
```

### Quality Gate Loop

```bash
gemini --yolo "
For each modified file:
1. boring_code_review audit
2. boring_perf_tips performance check  
3. boring_vibe_check health score
Fix all issues until vibe score > 80
"
```

---

## Boring Tools Quick Reference

| Tool | Purpose | YOLO Usage Example |
|------|---------|-------------------|
| `boring_rag_search` | Semantic code search | Understand project structure |
| `boring_code_review` | AI code review | Auto-fix suggestions |
| `boring_vibe_check` | Project health score | Quality gate |
| `boring_verify` | Run verification | CI/CD automation |
| `boring_impact_check` | Impact analysis | Safe refactoring |
| `boring_security_scan` | Security scan | Prevent leaks |
| `boring_test_gen` | Auto generate tests | Increase coverage |
| `boring_doc_gen` | Auto generate docs | Keep docs synced |

---

## Automation Scripts

### Windows PowerShell

```powershell
# yolo_loop.ps1 - Automated YOLO loop
$MAX_LOOPS = 5

for ($i = 1; $i -le $MAX_LOOPS; $i++) {
    Write-Host "=== Loop $i / $MAX_LOOPS ===" -ForegroundColor Cyan
    
    # Execute one round
    gemini --yolo "Complete the next [ ] task in @fix_plan.md, mark as [x] when done"
    
    # Verify
    boring verify
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Verification passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Needs fixing" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 5
}
```

### Linux/Mac Bash

```bash
#!/bin/bash
# yolo_loop.sh - Automated YOLO loop

MAX_LOOPS=5
for i in $(seq 1 $MAX_LOOPS); do
    echo "=== Loop $i / $MAX_LOOPS ==="
    
    # Execute one round (with timeout to prevent infinite runs)
    timeout 5m gemini --yolo "Complete the next task in @fix_plan.md"
    
    # Verify
    boring verify
    
    if [ $? -eq 0 ]; then
        echo "✅ Verification passed"
    else
        echo "❌ Needs fixing"
    fi
    
    sleep 5
done
```

---

## Common Scenario Commands

| Scenario | Recommended Command |
|----------|---------------------|
| Understand new project | `gemini --yolo "boring_rag_search analyze entire codebase"` |
| Fix bug | `gemini --yolo "Find and fix XXX issue"` |
| Refactor | `gemini --yolo "boring_impact_check + safe refactor"` |
| Release | `gemini --yolo "/release-prep"` |
| Write tests | `gemini --yolo "boring_test_gen generate tests for src/"` |
| Security check | `gemini --yolo "boring_security_scan and fix issues"` |

---

## Cautions

> ⚠️ **Warning**: YOLO mode skips all confirmations! AI can directly modify files and execute commands.

### Safety Recommendations

1. **Use Git**: Ensure all changes can be rolled back
2. **Set boundaries**: Clearly tell AI which files cannot be touched
3. **Execute in segments**: Break large tasks into smaller steps
4. **Regular reviews**: Manually review changes every few rounds

### Recommended Environments

- Docker containers
- Virtual machines
- Isolated test projects
- Projects with complete backups
