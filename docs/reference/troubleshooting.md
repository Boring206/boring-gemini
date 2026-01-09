# Troubleshooting Guide

> Diagnose and fix common issues with Boring.

---

## 🔍 Diagnosis Tools

Before trying manual fixes, use built-in diagnosis tools:

```bash
# Check environment and system health
boring doctor

# Show current configuration (useful for debugging)
boring config show

# View logs
tail -f ~/.boring_logs/boring.log
```

---

## 🛑 Common Issues

### 1. "Agent is stuck in Thinking state"

**Symptoms**: The spinner keeps spinning for > 2 minutes with no output.

**Causes**:
- API rate limits (429)
- Complex prompt causing timeout
- Network connectivity issues

**Solutions**:
1. **Check logs**: `tail ~/.boring_logs/boring.log` for API errors.
2. **Restart**: `Ctrl+C` to stop, then `boring start` again. Boring resumes from memory.
3. **Reset context**: If stuck on a bad thought loop:
   ```bash
   rm .boring_memory/context.json
   boring start
   ```

### 2. "RAG search returns no results"

**Symptoms**: `boring_rag_search` returns empty list.

**Causes**:
- Index not built
- Embeddings missing
- `.gitignore` excluding source files

**Solutions**:
1. **Force re-index**:
   ```bash
   boring rag index --force
   ```
2. **Check `.gitignore`**: Ensure `src/` is not ignored.
3. **Verify installation**: Run `pip show chromadb`. If missing, install `boring-aicoding[mcp]`.

### 3. "Shadow Mode blocking everything"

**Symptoms**: Every operation asks for approval, even safe ones.

**Causes**:
- Level set to `STRICT` in global config.
- `auto_approve_patterns` are empty.

**Solutions**:
1. **Check level**:
   ```bash
   boring_shadow_mode status
   ```
2. **Lower level** (if safe):
   ```python
   boring_shadow_mode(action="set_level", level="ENABLED")
   ```
3. **Reset config**:
   Delete `~/.boring_brain/shadow_config.json` to restore defaults.

### 4. "Smithery installation fails on Gemini Client"

**Symptoms**: Error during `npx` installation or "Connection refused".

**Causes**:
- Gemini Client has specific network/environment constraints for Smithery.

**Solution**:
Use local pip installation as fallback:
1. `git clone https://github.com/Boring206/boring-gemini.git`
2. `pip install -e .`
3. Configure MCP manually (see [Configuration](./configuration.md)).

### 5. "Verification fails on clean code"

**Symptoms**: `boring verify` reports errors that exist only in cache.

**Causes**:
- Stale cache file.

**Solution**:
1. **Clear cache**:
   ```bash
   rm -rf .boring_cache/
   ```
2. **Run fresh verification**:
   ```bash
   boring verify --force
   ```

---

## 🐛 Debugging Modes

### Enable Debug Logs

In `.boring.toml`:
```toml
[boring]
debug = true
```

Or via ENV:
```bash
export BORING_LOG_LEVEL=DEBUG
boring start
```

### Trace API Calls

To see exactly what's sent to the LLM:
```bash
tail -f ~/.boring_logs/api_trace.log
```

---

## 🆘 Getting Help

If these steps don't fix it:

1. **Run `boring doctor`** and save the output.
2. **Collect logs**: Zip `~/.boring_logs/`.
4. **Open an Issue**: [GitHub Issues](https://github.com/Boring206/boring-gemini/issues) with the above info.

### 6. "Tools are missing / Command not found"

**Symptoms**: You try to use `boring_code_review` or `boring_test_gen` but the agent says "Tool not found".

**Causes**:
- You are likely in `minimal` or `ultra_lite` profile.

**Solution**:
1. Check current profile:
   ```bash
   boring config show
   ```
2. Switch to `lite` or `standard`:
   ```bash
   export BORING_MCP_PROFILE=lite
   # Restart your IDE/Server
   ```
   See [MCP Profiles Guide](../guides/mcp-profiles-comparison.md) for details.
