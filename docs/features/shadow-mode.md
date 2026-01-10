# Shadow Mode - Security Sandbox

> Shadow Mode is Boring's security core, providing human-in-the-loop protection for all potentially destructive operations.

---

> **✨ Vibe Coder Compatible**: Shadow Mode intercepts **ALL** tools, including those called via Vibe Coder (`boring()`) or CLI (`boring-route`).

## 🛡️ What is Shadow Mode?

Shadow Mode acts as a **mandatory interception layer** between AI and your file system. When enabled, it:

1. **Intercepts** all destructive operations (file writes, deletions, command execution)
2. **Evaluates** the impact of each operation
3. **Queues** high-risk operations for approval
4. **Requires** human confirmation before execution

```
┌─────────────────────────────────────────────────────────┐
│                     AI Agent                            │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │              🛡️ SHADOW MODE                      │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Risk Evaluator                            │  │  │
│  │  │  ├─ Low Risk → Auto-approve               │  │  │
│  │  │  ├─ Medium Risk → Log & Execute           │  │  │
│  │  │  └─ High Risk → 🚨 REQUIRE APPROVAL      │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │                     │                            │  │
│  │        Pending Queue (High Risk Only)           │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                │
│                        ▼                                │
│                 File System                             │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Three Protection Levels

| Level | Symbol | Behavior | Best For |
|-------|--------|----------|----------|
| `DISABLED` | ⚠️ | No interception | Isolated containers only |
| `ENABLED` | 🛡️ | Auto-approve low-risk, block high-risk | **Default - Balanced** |
| `STRICT` | 🔒 | Intercept ALL write operations | Production environments |

### Level Details

#### DISABLED (⚠️ Use with Caution)
```python
boring_shadow_mode(action="set_level", level="DISABLED")
```
- No operations are intercepted
- All writes execute immediately
- **Only use in isolated containers or sandboxes**

#### ENABLED (🛡️ Recommended Default)
```python
boring_shadow_mode(action="set_level", level="ENABLED")
```
- **Auto-approved**: Read operations, small file edits
- **Logged**: Medium-risk changes (new files < 1KB)
- **Blocked**: Deletions, system files, large rewrites

#### STRICT (🔒 Maximum Security)
```python
boring_shadow_mode(action="set_level", level="STRICT")
```
- **ALL** write operations require approval
- Perfect for production code review
- Cannot be bypassed via agent patches

---

## 🔧 Configuration & Persistence

### Cross-Session Persistence

Shadow Mode settings persist across sessions in `~/.boring/brain/shadow_config.json`:

```json
{
  "level": "STRICT",
  "auto_approve_patterns": ["*.md", "docs/*"],
  "always_block_patterns": ["*.env", "secrets/*"],
  "last_updated": "2024-01-01T12:00:00Z"
}
```

### MCP Configuration

In `smithery.yaml` or MCP config:

```yaml
SHADOW_MODE_LEVEL: "STRICT"    # DISABLED|ENABLED|STRICT
BORING_ALLOW_DANGEROUS: false  # Never set to true in production
```

---

## 💻 Tool Reference

### Check Status
```python
boring_shadow_mode(action="status")
# Returns: {"level": "ENABLED", "pending_count": 2}
```

### Set Level
```python
boring_shadow_mode(action="set_level", level="STRICT")
```

### View Pending Operations
```python
boring_shadow_mode(action="list_pending")
# Returns list of operations awaiting approval
```

### Approve/Reject
```python
boring_shadow_mode(action="approve", operation_id="op_123")
boring_shadow_mode(action="reject", operation_id="op_123")
```

---

## 🎯 Risk Classification

### Low Risk (Auto-approved in ENABLED mode)
- Reading files
- Listing directories
- Viewing git status
- Running read-only commands

### Medium Risk (Logged, executed)
- Creating small files (< 1KB)
- Appending to existing files
- Running tests

### High Risk (Requires approval)
- ❌ Deleting files
- ❌ Modifying system files (`.env`, `config/*`)
- ❌ Large file rewrites (> 50% content change)
- ❌ Executing shell commands with side effects
- ❌ Git operations (push, force operations)

---

## 🔐 Protected File Tools (V10.17.5+)

For guaranteed Shadow Mode protection, use Boring's file tools:

```python
# These ALWAYS respect Shadow Mode
boring_write_file(path="config.py", content="...")
boring_read_file(path="src/main.py")
```

> ⚠️ **Warning**: Native MCP tools like `write_file` (from some clients) may NOT be intercepted by Shadow Mode. Always use `boring_write_file` for secure operations.

---

## 🛡️ Safety Net (Git Checkpoints) (V10.31)

While Shadow Mode intercepts individual operations, **Safety Net** protects your entire codebase during complex refactoring.

### How it Works
It creates a lightweight Git tag (checkpoint) before you start. If the AI messes up, you can instantly revert to that checkpoint.

### Usage

```python
# 1. Create a checkpoint
boring_checkpoint(action="save", message="Before refactoring auth")
# Returns: "Checkpoint 'checkpoint_20240101_120000' created"

# 2. Do risky stuff...
# ...

# 3. If it fails, restore!
boring_checkpoint(action="restore", checkpoint_id="checkpoint_20240101_120000")
```

> **Note**: This feature requires a clean working directory (committed changes).

---

## 🏢 Enterprise Use Cases

### Code Review Workflow
```python
# Reviewer sets STRICT mode
boring_shadow_mode(action="set_level", level="STRICT")

# AI proposes changes, all queued for review
# Reviewer inspects each pending operation
# Approve only verified changes
```

### CI/CD Integration
```yaml
# In CI pipeline
- name: Run Boring with Shadow Mode
  env:
    SHADOW_MODE_LEVEL: ENABLED
    BORING_ALLOW_DANGEROUS: false
```

---

## See Also

- [MCP Tools](./mcp-tools.md) - Tool reference
- [Quality Gates](./quality-gates.md) - CI/CD integration
- [Pro Tips](../guides/pro-tips.md) - Security best practices
