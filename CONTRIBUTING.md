# Contributing to Boring-Gemini

Thank you for your interest in contributing to Boring-Gemini! 🎉

## ❤️ How to Contribute

We welcome contributions of all kinds:
- 🐛 **Bug Reports**: Use GitHub Issues with the `bug` label
- 💡 **Feature Requests**: Use GitHub Issues with the `enhancement` label
- 📖 **Documentation**: Improve docs, README, or add examples
- 🔌 **Plugins**: Create and share custom plugins (see below)

## Development Setup

```bash
# Clone the repository
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini

# Install with development dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest

# Run linter
ruff check src/
```

## Code Standards

- **Type Hints**: All public functions must have type hints
- **Docstrings**: Use Google-style docstrings
- **Testing**: Maintain 80%+ coverage
- **Linting**: Code must pass ruff without errors

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run `pytest` and `ruff check`
5. Commit with conventional commits (`feat:`, `fix:`, `docs:`)
6. Push and create a Pull Request

## Project Structure (V9.0)

```
boring-gemini/
├── src/boring/
│   ├── mcp_server.py        # MCP entry point (30+ tools)
│   ├── mcp/                  # 🆕 Modular tool packages
│   │   ├── core_tools.py     # Essential tools
│   │   ├── speckit_tools.py  # SpecKit workflows
│   │   ├── brain_tools.py    # Learning tools
│   │   ├── v9_tools.py       # 🆕 V9 features
│   │   └── async_utils.py    # Async execution
│   ├── plugins/              # 🆕 Plugin system
│   │   ├── __init__.py
│   │   └── loader.py         # PluginLoader + @plugin
│   ├── streaming.py          # 🆕 Progress reporting
│   ├── workspace.py          # 🆕 Multi-project manager
│   ├── auto_fix.py           # 🆕 Auto-fix pipeline
│   ├── pattern_mining.py     # 🆕 Suggestion engine
│   ├── audit.py              # 🆕 JSONL audit logging
│   ├── gemini_client.py      # Gemini SDK wrapper
│   ├── workflow_evolver.py   # Workflow evolution
│   └── loop/                 # State machine
├── .agent/workflows/         # SpecKit workflows (evolvable)
│   └── _base/                # Base templates for rollback
├── .boring_brain/            # Knowledge base
├── tests/                    # Test suite (pytest)
│   ├── unit/
│   └── integration/
└── docs/                     # Documentation
```

## 🔌 Creating Plugins

Plugins extend Boring without modifying core code. Create a file in `~/.boring/plugins/` or `.boring_plugins/`:

```python
# my_plugin.py
from boring.plugins import plugin

@plugin(
    name="my_custom_tool",
    description="Does something awesome",
    author="Your Name"
)
def my_custom_tool(arg1: str) -> dict:
    return {"status": "SUCCESS", "result": arg1.upper()}
```

Reload with `boring_reload_plugins` and use with `boring_run_plugin`.

## Questions?

Open an issue or start a discussion!

