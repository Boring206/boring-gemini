# Usage Analytics Dashboard (P4)

> **"Know your Agent."**

The **Usage Analytics Dashboard** (P4) provides deep insights into how your AI Agent is interacting with your project. It transforms the "Black Box" of AI operations into transparent, actionable metrics.

## Features

### 1. Personal Stats Panel
Available in both the CLI Monitor and Web Dashboard, this panel shows:
- **Top Tools**: Which tools does the Agent use most? (e.g., `read_file` vs `boring_rag_search`)
- **Activity Volume**: Total API calls over time.
- **Efficiency**: Identifying unused or redundant tool calls.

### 2. Self-Awareness (MCP Tool)
We introduced a specific tool, `boring_usage_stats`, that allows the Agent to **introspect** its own behavior.
- **Prompt**: "How much have I used the RAG tools today?"
- **Response**: The Agent queries `usage.json` and reports its own efficiency.

## Accessing the Dashboard

### CLI Monitor (TUI)
Fast, terminal-based monitoring.

```bash
boring-monitor
```

### Web Dashboard (Streamlit)
Rich, graphical visualization.

```bash
boring-monitor --web
```
*(Requires `boring-aicoding[gui]`)*

## Data Storage
Stats are persisted in `~/.boring/usage.json`. This JSON file acts as the "Long-Term Episodic Memory" for tool usage patterns.
