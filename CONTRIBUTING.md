# Contributing to Boring-Gemini

Thank you for your interest in contributing to Boring-Gemini! 🎉

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

## Project Structure

```
boring-gemini/
├── src/boring/          # Main package
│   ├── gemini_client.py # Gemini SDK wrapper
│   ├── loop/            # State machine
│   └── ...
├── tests/               # Test suite
│   ├── unit/
│   └── integration/
└── docs/                # Documentation
```

## Questions?

Open an issue or start a discussion!
