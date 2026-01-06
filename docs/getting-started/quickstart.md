# Quick Start

## Your First Boring Task

After installation, you can use Boring directly from your IDE chat:

### Using run_boring

```
@boring run_boring "Create a hello world Python script"
```

### Using SpecKit Workflows

```
@boring speckit_plan "Build a REST API with FastAPI"
@boring speckit_tasks
```

### Verifying Code

```
@boring boring_verify
```

## CLI Usage

If you're using the terminal:

```bash
# Start the Boring agent
boring start

# Check status
boring status

# Monitor in real-time
boring-monitor
```

## Project Setup

For new projects:

```bash
# 2. Setup a new project (Required for boring start!)
boring-setup my-project
cd my-project

# 3. Start the autonomous loop
boring start
```

## Available Tools

| Tool | Description |
|------|-------------|
| `run_boring` | Main entry point - autonomous task execution |
| `boring_verify` | Run lint, syntax, and test checks |
| `speckit_plan` | Generate implementation plan from requirements |
| `speckit_tasks` | Break plan into actionable tasks |
| `boring_apply_patch` | Apply precise file edits |

## Next Steps

- Browse the [API Reference](../api/gemini_client.md)
- Read about [Contributing](../contributing.md)
