# Plugin Development Guide

> Extend Boring's capabilities with custom Python tools.

---

## 🛠️ Overview

Boring features a dynamic plugin system that allows you to register custom Python functions as AI-accessible tools. Plugins can be project-specific or global.

### Plugin Locations
1.  **Project-Local**: `{project_root}/.boring_plugins/`
2.  **User-Global**: `~/.boring/plugins/`

---

## 📝 Creating a Plugin

To create a plugin, define a Python function and decorate it with `@plugin`.

### Example: `my_tool_plugin.py`

```python
from boring.plugins.loader import plugin

@plugin(
    name="my_custom_linter",
    description="Custom linting rules for specific business logic",
    version="1.0.0",
    author="Vibe Coder",
    tags=["lint", "custom"]
)
def my_custom_linter(file_path: str) -> dict:
    """
    Analyzes a file for custom patterns.
    """
    # Your logic here
    if "todo" in open(file_path).read().lower():
        return {"passed": False, "issues": ["Found lingering TODOs"]}
    
    return {"passed": True, "issues": []}
```

---

## 🚀 Loading and Hot-Reload

- **Discovery**: Any `.py` file or files ending in `_plugin.py` in the search paths are automatically discovered.
- **Hot-Reload**: Boring monitors plugin files. If you edit a plugin while the loop is running, it will automatically reload the new logic for the next iteration.

---

## 🔍 Using Plugins

Once loaded, your plugin becomes available to the AI agent just like built-in tools. The agent will discover it via semantic search or tool listing.

To list currently loaded plugins:
```bash
boring list-plugins
```

---

## 💡 Best Practices

1.  **Type Hints**: Always use type hints for arguments to help the LLM understand the input.
2.  **Docstrings**: Provide clear, descriptive docstrings as they are used by the AI to decide when to call the tool.
3.  **Return Format**: Return structured data (dict) rather than just strings for better agent processing.
