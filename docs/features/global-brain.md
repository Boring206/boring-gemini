# Global Brain - Cross-Project Knowledge Sharing

## 🌐 Overview

**Global Brain** is Boring's cross-project knowledge sharing system, allowing you to share best practices, error solutions, and code patterns across different projects.

### Core Concepts

- **Project Brain** (`.boring/brain/`): Each project's own knowledge base
- **Global Brain** (`~/.boring/brain/`): Global knowledge base across all projects
- **Knowledge Flow**: Project → Global → Other Projects

## 📂 Storage Location

Global Brain is stored in your **user home directory**:

- **Windows**: `C:\Users\{YourName}\.boring/brain\global_patterns.json`
- **Linux/Mac**: `/home/{username}/.boring/brain/global_patterns.json`

**Benefits**: 
- ✅ Independent from projects, won't be accidentally deleted
- ✅ Not managed by Git, protects privacy
- ✅ Automatically shared across all projects

---

## 🌐 Knowledge Swarm (Sync)

Starting from V11.0, Global Brain supports automated synchronization via Git, known as **Knowledge Swarm**.

-   **Tool**: `boring_brain_sync(remote_url=...)`
-   **Collaborative Power**: By pointing your global brain to a team repository, every developer's agent can pull successful patterns from others.
-   **Auto-Propagation**: Solutions for difficult architecture or configuration bugs propagate across the hive mind in minutes.

## 🧰 Available Tools

### 1. `boring_global_export`
**Export** high-quality patterns from current project to Global Brain

```python
boring_global_export(min_success_count=2)
```

**Parameters**:
- `min_success_count`: Minimum success count (default: 2)
  - Only export verified patterns
  - Higher = better quality

**Use Cases**:
- ✅ Project ending, want to preserve knowledge
- ✅ Solved important bug, want to share with other projects
- ✅ Accumulated sufficient experience, export best practices

---

### 2. `boring_global_import`
**Import** patterns from Global Brain to current project

```python
boring_global_import()  # Import all types
boring_global_import(pattern_types=["error_solution"])  # Only error solutions
```

**Parameters**:
- `pattern_types`: Filter by type (optional)
  - `["error_solution"]` - Only error solutions
  - `["code_style", "performance"]` - Multiple types

**Use Cases**:
- ✅ Starting new project, want quick experience boost
- ✅ Facing similar issues, import known solutions
- ✅ Sync best practices across multiple projects

---

### 3. `boring_global_list`
View all knowledge in Global Brain

```python
boring_global_list()
```

**Returns**:
- Total pattern count
- Type distribution (error_solution, code_style, etc.)
- Each pattern's source project and success count

**Use Cases**:
- ✅ Want to know what's in Global Brain
- ✅ Decide which project to export from
- ✅ Understand accumulated experience

## 🎯 Typical Workflows

### Scenario 1: Share Knowledge from Old to New Project

```bash
# In old project (Project A)
cd ~/project-a
boring_global_export(min_success_count=3)  # Export quality patterns

# Switch to new project (Project B)
cd ~/project-b
boring_global_import()  # Import all knowledge
```

### Scenario 2: Team Best Practices Sharing

```bash
# Team member A exports from their project
boring_global_export(min_success_count=5)  # Only best patterns

# Team member B imports to their project
boring_global_import(pattern_types=["code_style", "performance"])
```

### Scenario 3: Personal Knowledge Base

```bash
# Regular knowledge review
boring_global_list()

# Export from multiple projects
boring_global_export()  # Run in each project

# One-click import for new projects
boring_global_import()
```

## 📊 Pattern Types

Global Brain supports these pattern types:

| Type | Description | Example |
|------|-------------|---------|
| `error_solution` | Error solutions | "How to fix ModuleNotFoundError" |
| `code_style` | Code style preferences | "Use dataclass instead of dict" |
| `performance` | Performance optimizations | "Use LRU cache for queries" |
| `security` | Security best practices | "Never hardcode API keys" |
| `workflow_tip` | Workflow suggestions | "Write tests before code" |

## ⚙️ Advanced Usage

### Selective Import

Import only specific knowledge types:

```python
# Only error solutions
boring_global_import(pattern_types=["error_solution"])

# Style and performance
boring_global_import(pattern_types=["code_style", "performance"])
```

### Quality Control

Export only well-verified patterns:

```python
# Only patterns with 5+ successes
boring_global_export(min_success_count=5)
```

### View Details

```python
result = boring_global_list()
print(result["patterns"])  # Detailed info for each pattern
```

## 🔒 Privacy & Security

### Auto-Filtering

- ❌ **Not exported**: API Keys, passwords, sensitive paths
- ✅ **Only exported**: Abstract patterns and solutions

### Local Storage

- Data stored only on your computer
- No cloud upload
- No automatic sharing with others

### Manual Sharing

To share with team:

1. Copy `~/.boring/brain/global_patterns.json`
2. Share through secure channel
3. Colleagues place in their `~/.boring/brain/` directory

## 💡 Best Practices

### ✅ Do

- Regularly export knowledge from completed projects
- Import global knowledge when starting new projects
- Use `min_success_count` to ensure quality
- Regularly review Global Brain content

### ❌ Don't

- Export low-quality, unverified patterns
- Commit `.boring/brain/` to Git
- Import all patterns without reviewing

## 🐛 FAQ

### Q: Global Brain is empty?
**A**: Run `boring_global_export` from any project first

### Q: No changes after import?
**A**: Use `boring_brain_summary` to view project Brain

### Q: How to delete a pattern?
**A**: Manually edit `~/.boring/brain/global_patterns.json`

### Q: Can teams share?
**A**: Yes, but requires manual JSON file copying

## 🔗 Related Tools

- `boring_learn` - Learn patterns from current project
- `boring_brain_summary` - View project knowledge base
- `boring_brain_health` - Brain health report
- `boring_pattern_stats` - Pattern statistics

## 📚 References

- [Knowledge System Guide](../guides/knowledge-system.md)
- [Brain Manager API](../api/intelligence_zh.md)
