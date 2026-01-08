# Architect Mode Guide (V10.16)

## Overview
Architect Mode is a specialized evaluation mode initiated by the `PRODUCTION_RUBRIC`. It switches the AI persona from a "Helpful Code Reviewer" to a "Hostile Principal Architect".

## How to Use
Run `boring evaluate` with the `--level production` flag:

```bash
boring evaluate src/core/database.py --level production
```

## What to Expect
The Hostile Architect will **NOT** care about:
- Variable naming
- PEP 8 formatting
- Missing docstrings (unless critical)

It **WILL** aggressively attack your design on:
1.  **Concurrency**: "This lock implementation will cause a deadlock under high load."
2.  **Scalability**: "This N+1 query pattern will kill your DB at 10k RPS."
3.  **Resilience**: "Where is the circuit breaker for this external API call?"
4.  **Tech Stack**: "Why are you using `requests` (blocking) instead of `httpx` (async)?"

## Configuration
You can customize the prompt in `src/boring/judge.py` if you find the architect too mean (or not mean enough).
