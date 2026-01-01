# Project Context

## Purpose
**Boring for Gemini** is an autonomous AI development loop system that uses the Google Gemini CLI to iteratively improve software projects.

## Tech Stack
- **Language:** Python 3.9+
- **CLI:** Typer + Rich
- **Testing:** Pytest
- **AI:** @google/gemini-cli

## Conventions
- Type hints mandatory
- Google-style docstrings
- Pydantic for data models
- PEP 8 formatting

## Architecture
- Circuit Breaker pattern (CLOSED/OPEN/HALF_OPEN)
- Exit signal detection
- Rate limiting (hourly)
- Response analysis

## Constraints
- Use `-p` flag for Gemini CLI non-interactive mode
- Windows: use `python -m pytest`
- State stored in hidden files (`.call_count`, `.exit_signals`, etc.)
