# Intelligent Adaptive Profile (P6)

> **"A tool that learns how you work."**

The **Adaptive Profile** (`adaptive`) is a revolutionary new operating mode in Boring V11.5. Instead of forcing you to manually choose between "Lite" (fast but limited) and "Full" (powerful but expensive), the Adaptive Profile **dynamically adjusts itself** based on your behavior.

## How It Works

1.  **Usage Tracking**: The system quietly observes which tools you use most frequently (via `UsageTracker`).
2.  **Smart Context**: It identifies your "Top 20" essential tools and keeps them available.
3.  **Contextual Injection**: 
    - If you start testing, it auto-injects the `Testing Guide`.
    - If you are debugging, it brings in `Error Analysis` tools.
4.  **Prompt Injection**: Relevant guidelines (Prompts) are automatically added to the system prompt based on active tool categories.

## Benefits

- **⚡ Efficiency**: Starts as light as `lite` profile (~97% token savings).
- **🧠 Intelligence**: Becomes as powerful as `full` profile exactly when needed.
- **🛡️ Safety**: Prevents "Context Window Bloat" by hiding irrelevant tools (e.g., hiding Git tools during pure coding sessions).

## Activation

You can enable the Adaptive Profile using the **Boring Wizard**:

```bash
boring wizard
# Choose "adaptive" from the menu
```

Or manually in `.boring.toml`:

```toml
[mcp]
profile = "adaptive"
```

Or via environment variable:

```bash
export BORING_MCP_PROFILE=adaptive
```

## Privacy

Usage data is stored locally in `~/.boring/usage.json`. It is **never** sent to the cloud. You can view your own stats using the `boring-monitor` dashboard.
