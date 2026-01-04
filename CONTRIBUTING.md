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

## Project Structure (V10.5 - Pure CLI Mode)

> **Important**: V10.5 introduced "Pure CLI Mode" - MCP tools like `run_boring`, `speckit_*`, and `boring_multi_agent` 
> now return workflow templates with CLI commands instead of executing AI internally.

```
boring-gemini/
├── src/boring/
│   ├── mcp/                  # MCP Server Package
│   │   ├── server.py         # FastMCP entry point
│   │   ├── tools/            # Modular tool packages
│   │   │   ├── core.py       # run_boring, health_check (Pure CLI Mode)
│   │   │   ├── speckit.py    # SpecKit tools (Returns templates)
│   │   │   ├── agents.py     # Multi-agent tools (Returns templates)
│   │   │   └── ...
│   │   └── v9_tools.py       # V9 features (auto_fix, workspace)
│   ├── plugins/              # Plugin system
│   ├── rag/                  # RAG System (Vector + Graph)
│   │   ├── parser.py         # Tree-sitter AST Parser (V10.10)
│   │   ├── code_indexer.py   # Code chunking logic
│   │   └── ...
│   ├── verification.py       # CodeVerifier (Generic Dispatcher)
│   ├── judge.py              # LLM-as-a-Judge (Confidence & Bias Mitigation)
│   └── ...
├── .agent/workflows/         # SpecKit workflows (evolvable)
│   └── _base/                # Base templates for rollback
├── .boring_brain/            # Knowledge base
└── tests/                    # Test suite (pytest)
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

