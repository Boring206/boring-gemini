# 🛠️ Boring MCP Tool Manual

This manual explains how to use Boring MCP tools in real development.

---

## 📋 Quick Reference

### Most Used Tools (Top 10)

| Tool | Purpose | Example |
|------|---------|---------|
| `boring` | 🎯 Universal router | `"review my code"` → auto routes |
| `boring_rag_search` | 🔍 Search code | `query="authentication"` |
| `boring_code_review` | 📝 Code review | `file_path="src/api.py"` |
| `boring_vibe_check` | ✅ Health check | `target_path="src/"` |
| `boring_verify` | 🧪 Run verification | `level="FULL"` |
| `boring_test_gen` | 🧪 Generate tests | `file_path="src/utils.py"` |
| `boring_commit` | 📦 Smart commit | Auto-generates commit message |
| `boring_security_scan` | 🔒 Security scan | `scan_type="full"` |
| `boring_impact_check` | 💥 Impact analysis | `target_path="src/core.py"` |
| `boring_suggest_next` | 💡 Next step suggestion | Based on project state |

---

## 🔍 Code Search (RAG)

### Basic Search

```
boring_rag_search query="user authentication logic"
boring_rag_search query="database connection"
boring_rag_search query="error handling"
```

### Advanced Search

```
# Limit search scope
boring_rag_search query="login" file_filter="auth"

# Adjust result count
boring_rag_search query="API endpoints" max_results=20

# Expand dependency graph
boring_rag_expand chunk_id="chunk_123" depth=3
```

### First Use - Build Index

```
boring_rag_index project_path="."
boring_rag_status  # Check index status
```

---

## 📝 Code Review

### Single File Review

```
boring_code_review file_path="src/api/auth.py"
boring_code_review file_path="src/components/Login.tsx"
```

### Specify Review Focus

```
# Focus options: all, naming, error_handling, performance, security
boring_code_review file_path="src/api.py" focus="security"
boring_code_review file_path="src/utils.py" focus="performance"
```

---

## ✅ Health Check (Vibe Check)

### Quick Check

```
# Check single file
boring_vibe_check target_path="src/main.py"

# Check entire directory
boring_vibe_check target_path="src/"

# Check entire project
boring_vibe_check target_path="."
```

### Output Includes
- 🎯 Vibe Score (0-100)
- 📋 Lint issues list
- 🔒 Security issues
- 📚 Documentation coverage
- 🔧 One-click fix prompt

---

## 🧪 Test Generation

### Auto-generate Unit Tests

```
# Python files
boring_test_gen file_path="src/utils.py"

# TypeScript files
boring_test_gen file_path="src/services/auth.ts"

# Specify output directory
boring_test_gen file_path="src/api.py" output_dir="tests/"
```

### Supported Languages
- ✅ Python (pytest)
- ✅ JavaScript/TypeScript (jest)

---

## 🔒 Security Scanning

### Full Scan

```
boring_security_scan scan_type="full"
```

### Specific Scan Types

```
# Secrets only
boring_security_scan scan_type="secrets"

# Vulnerabilities only
boring_security_scan scan_type="vulnerabilities"

# Dependencies only
boring_security_scan scan_type="dependencies"
```

---

## 📦 Git Operations

### Smart Commit

```
# Auto-analyze changes and generate semantic commit message
boring_commit
boring_commit commit_type="feat" scope="auth"
```

### Git Hooks

```
# Install hooks (auto-verify before commit)
boring_hooks_install

# Check hooks status
boring_hooks_status

# Remove hooks
boring_hooks_uninstall
```

---

## 💥 Impact Analysis

### Pre-modification Analysis

```
# See what modules would be affected by modifying this file
boring_impact_check target_path="src/core/database.py"
boring_impact_check target_path="src/utils/helpers.ts" max_depth=3
```

### Output Includes
- 📊 List of modules depending on this file
- ⚠️ Risk level
- 🧪 Tests that need verification

---

## 🛡️ Shadow Mode (Safety Mode)

### Check Status

```
boring_shadow_status
```

### Switch Modes

```
# Normal mode (low-risk auto-executes)
boring_shadow_mode mode="ENABLED"

# Strict mode (all writes need approval)
boring_shadow_mode mode="STRICT"

# Disabled (not recommended)
boring_shadow_mode mode="DISABLED"
```

### Review Operations

```
boring_shadow_approve operation_id="xxx"
boring_shadow_reject operation_id="xxx"
```

---

## 📐 Architecture Analysis

### Generate Dependency Graph

```
boring_arch_check target_path="src/"
boring_visualize scope="module"
```

### Output Formats

```
# Mermaid diagram
boring_arch_check output_format="mermaid"

# JSON
boring_arch_check output_format="json"
```

---

## 💡 Smart Suggestions

### Get Next Step Suggestions

```
boring_suggest_next
boring_suggest_next limit=5
```

### Output Includes
- 🎯 Recommended next actions
- 📊 Project state analysis
- ⚠️ Potential issues

---

## 🚀 Workflow Examples

### New Feature Development

```
1. boring_rag_search query="related feature"    # Search existing code
2. boring_impact_check target_path="..."        # Analyze modification impact
3. [Develop code]
4. boring_code_review file_path="..."           # Review code
5. boring_test_gen file_path="..."              # Generate tests
6. boring_vibe_check target_path="..."          # Health check
7. boring_verify level="FULL"                   # Run verification
8. boring_commit                                # Smart commit
```

### Bug Fix

```
1. boring_rag_search query="error message"      # Search related code
2. [Fix code]
3. boring_security_scan                         # Ensure no security issues
4. boring_vibe_check                            # Health check
5. boring_commit commit_type="fix"              # Commit fix
```

### Code Review

```
1. boring_code_review file_path="..." focus="all"
2. boring_security_scan scan_type="secrets"
3. boring_arch_check target_path="..."
```

---

## ⚙️ Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `BORING_MCP_MODE` | `1` | Enable MCP mode (required) |
| `BORING_MCP_PROFILE` | `lite`/`standard`/`full` | Tool level |
| `PROJECT_ROOT_DEFAULT` | `.` | Default project path |

---

## 📚 Further Reading

- [MCP Configuration Guide](./mcp-configuration_en.md)
- [Usage Modes](./usage-modes_en.md)
- [YOLO Mode Integration](./yolo-boring-integration_en.md)
