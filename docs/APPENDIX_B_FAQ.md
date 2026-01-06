# Appendix B: Frequently Asked Questions (FAQ)

---

## Installation & Setup

### Q: How do I install Boring for Gemini?

```bash
pip install boring-gemini
```

Or install from source:
```bash
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e ".[mcp]"
```

---

### Q: How do I configure Boring with Cursor/VSCode?

Add to your MCP config (`.cursor/mcp.json` or `mcp_config.json`):

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "GOOGLE_API_KEY": "your-key-here"
      }
    }
  }
}
```

---

### Q: Do I need a Google API Key?

**Core Tools (No Key Required)**:
- `boring_verify`, `boring_security_scan`, `boring_commit`, `boring_hooks_install`
- These work 100% locally without any API key.

**LLM-Enhanced Features (Key Required)**:
- `boring_evaluate` (LLM-as-Judge)
- `boring_rag_search` (Semantic search with embeddings)
- `boring_multi_agent` (Multi-agent orchestration)

**Smithery Deployment**: No API key is required in the config schema. The platform may have its own authentication, but Boring itself does not mandate a key.

---

## Troubleshooting

### Q: MCP server won't start - "EOF" error

**Cause**: Wrong entry point.
**Fix**: Use `boring.mcp.server`, not `boring.mcp.instance`.

```json
"args": ["-m", "boring.mcp.server"]  ✅
"args": ["-m", "boring.mcp.instance"] ❌
```

---

### Q: "Functions with **kwargs are not supported"

**Cause**: FastMCP doesn't support `**kwargs` in tool functions.
**Fix**: Use `args: dict = Field(...)` instead.

```python
# Wrong
def my_tool(**kwargs): ...

# Correct
def my_tool(args: dict = Field(default={}, description="...")): ...
```

---

### Q: Tests fail with "BackgroundTaskRunner.__new__() got unexpected argument"

**Cause**: Singleton pattern conflict in tests.
**Fix**: Reset singleton before each test:

```python
@pytest.fixture
def runner():
    BackgroundTaskRunner._instance = None
    instance = object.__new__(BackgroundTaskRunner)
    instance._initialized = False
    BackgroundTaskRunner._instance = instance
    instance.__init__(max_workers=2)
    yield instance
    instance.shutdown(wait=False)
    BackgroundTaskRunner._instance = None
```

---

### Q: Smithery shows "Documentation Quality Score < 100"

**Cause**: Missing parameter descriptions.
**Fix**: Always use `Field(description=...)`:

```python
# Wrong
def my_tool(target: str = "src/"): ...

# Correct
def my_tool(target: str = Field(default="src/", description="Target path")): ...
```

---

## Features

### Q: What's the difference between `boring_verify` levels?

| Level | Checks |
|-------|--------|
| `BASIC` | Syntax, imports |
| `STANDARD` | + Linting (ruff), type hints |
| `FULL` | + Tests, coverage, security |
| `SEMANTIC` | + LLM-based code review |
| `DOCS` | Documentation completeness |

---

### Q: How does Shadow Mode work?

1. Enable: `boring_shadow_mode(mode="STRICT")`
2. High-risk operations are captured, not executed
3. Human reviews pending operations
4. Approve or reject each operation

Use for: file deletions, DB migrations, production deploys.

---

### Q: What's the difference between `boring_multi_agent` and `boring_delegate`?

| Tool | Purpose |
|------|---------|
| `boring_multi_agent` | Full Architect→Coder→Reviewer workflow |
| `boring_delegate` | Single task to specialized sub-agent |

Use `multi_agent` for features, `delegate` for atomic tasks.

---

### Q: How do I make RAG search work?

1. First, index your codebase:
   ```python
   boring_rag_index(force=True)
   ```

2. Then search:
   ```python
   boring_rag_search(query="authentication middleware")
   ```

Index is stored in `.boring_brain/` and persists between sessions.

---

## Performance

### Q: Why are some tools slow?

Long-running operations run in background threads:
- `boring_verify(level='FULL')` → ~10-60s
- `boring_security_scan` → ~5-30s
- `boring_rag_index` → ~10-120s (first run)

Use `boring_background_task()` for non-blocking execution.

---

### Q: How do I reduce context window usage?

1. Use Dynamic Discovery:
   - Query `boring://capabilities` first
   - Only load tools you need

2. Use concise prompts:
   - `vibe_start` is optimized for minimal context

---

## Security

### Q: Is my code sent to external servers?

**Local mode**: No, everything runs locally.
**Smithery mode**: Code context may be sent to Gemini API.
**RAG indexing**: Embeddings stored locally in SQLite.

---

### Q: How do I scan for secrets?

```python
boring_security_scan(scan_type="secrets")
```

Detects: AWS keys, Google API keys, private keys, tokens, passwords.

---

## Contributing

### Q: How do I add a new tool?

1. Create `src/boring/mcp/tools/my_tool.py`
2. Use `@mcp.tool()` decorator
3. Add `Field(description=...)` to all parameters
4. Import in `src/boring/mcp/server.py`
5. Add to `CAPABILITIES` in `discovery.py`

See `CONTRIBUTING.md` for full guide.

---

### Q: How do I run tests?

```bash
pytest tests/ -v --cov=src/boring
```

Coverage requirement: 39%

---

*Have a question not listed? Open an issue on GitHub!*
