# Boring Usage Modes Guide

This document explains the three main usage modes of Boring and their respective configurations.

## Mode Comparison

| Feature | MCP Tool Mode | Gemini CLI YOLO Mode | Boring Autonomous Loop |
|---------|---------------|---------------------|------------------------|
| **Execution** | One question, one answer | `gemini --yolo` | `boring start` |
| **Requires API Key** | ❌ | ❌ (Uses Google account) | ✅ `GEMINI_API_KEY` |
| **Requires PROMPT.md** | ❌ | ❌ | ✅ |
| **Auto-stop** | N/A | ❌ Manual Ctrl+C | ✅ Auto-detects completion |
| **Safety Protection** | ✅ | ⚠️ No confirmation | ✅ Shadow Mode |
| **Stability** | ✅ Stable | ✅ Official support | ⚠️ Experimental |

---

## Mode 1: MCP Tool Mode (Recommended for Daily Use)

This is the most stable usage pattern, suitable for daily development.

### How It Works

```
You → Gemini CLI → MCP Tools (boring_rag_search, etc.) → Results
```

### Setup

1. Install via Smithery:
   ```bash
   npx -y @smithery/cli@latest install @anthropic/boring-mcp --client claude
   ```

2. Or manually configure `~/.gemini/settings.json`

### Available Tools

- `boring_rag_search` - Semantic code search
- `boring_code_review` - AI code review
- `boring_vibe_check` - Project health score
- `boring_impact_check` - Impact analysis
- 50+ more tools...

---

## Mode 2: Gemini CLI YOLO Mode (Recommended for Autonomous Dev)

> ✅ **Recommended**: This is currently the most stable autonomous development approach, officially supported by Google.

YOLO (You Only Live Once) mode allows Gemini CLI to automatically execute tools and commands **without confirmation**.

### How It Works

```
gemini --yolo "Complete all tasks in TODO list" → AI auto-executes → Until done or you press Ctrl+C
```

### Activation

```bash
# Method 1: Command line flag
gemini --yolo

# Method 2: Hotkey during interaction
# Press Ctrl+Y after entering gemini to enable YOLO mode
```

### Using with Boring MCP Tools

YOLO mode can call Boring's MCP tools!

1. Set up MCP first (see Mode 1)
2. Enable YOLO mode
3. AI will automatically call `boring_rag_search`, `boring_code_review`, etc.

### Advantages

- ✅ No API Key required (uses Google account login)
- ✅ Official support, stable and reliable
- ✅ Built-in ReAct Loop (reasoning + action)
- ✅ Compatible with all MCP tools

### Caution

> ⚠️ **Warning**: YOLO mode skips all confirmations! AI can directly modify files and execute commands.
> Recommended to use in **trusted environments** or **Docker containers**.

---

## Mode 3: Boring Autonomous Loop (Experimental)

> ⚠️ **Note**: This feature is still under development and lacks sufficient testing. For autonomous development, we recommend using Gemini CLI YOLO mode first.

This mode lets AI develop completely autonomously. The AI reads `PROMPT.md`, executes tasks automatically, and continues until all work is complete.

### How It Works

```
boring start → Read PROMPT.md → Call AI → Parse response → Repeat until done
```

### Requirements

1. **API Key**: Set environment variable
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

2. **Project Structure**:
   ```
   your-project/
   ├── PROMPT.md      # AI work instructions
   ├── @fix_plan.md   # Task checklist
   └── specs/         # Project specifications
   ```

### Usage

```bash
# Create new project
boring-setup my-project
cd my-project

# Edit PROMPT.md and @fix_plan.md

# Start autonomous loop
boring start --calls 50 --timeout 30
```

### Status Reporting

AI must include status block at response end:

```
---BORING_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
EXIT_SIGNAL: false | true
RECOMMENDATION: Next step suggestion
---END_BORING_STATUS---
```

---

## Template Files

The `src/boring/templates/` directory contains:

| File | Purpose | When Used |
|------|---------|-----------|
| `PROMPT.md` | AI work instructions | Autonomous loop mode |
| `workflows/*.md` | Workflow templates | Both modes |
| `specs/` | Specification placeholder | User fills in |

### When Do You Need These Templates?

| Mode | PROMPT.md | workflows/ | specs/ |
|------|-----------|------------|--------|
| MCP Tools | ❌ | ✅ (Optional) | ❌ |
| Autonomous | ✅ Required | ✅ | ✅ |

---

## FAQ

### Q: Do I need an API Key for Gemini CLI?

No. Gemini CLI uses your Google account login, no API Key needed.

### Q: Will the autonomous loop run for a long time?

Yes. Set `--calls 50` to limit API calls and avoid overspending.

### Q: Why does autonomous mode need PROMPT.md?

Because `boring start` needs to know what the AI should do. It reads `PROMPT.md` and sends it to the AI.

### Q: What are the limitations of MCP mode?

- Can only do one thing at a time (you need to issue the next command)
- Cannot auto-retry failed operations
- Requires your ongoing supervision

---

## Recommendations

| Scenario | Recommended Mode |
|----------|-----------------|
| Daily dev, code search, review | MCP Tool Mode |
| Rapid prototyping, auto-fix, overnight tasks | Autonomous Loop |
| Stability first | MCP Tool Mode |
| Want to try new features | Autonomous Loop |
