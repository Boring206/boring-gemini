# Enterprise Security & Privacy Whitepaper

> A technical overview of data handling, LLM interaction, and security safeguards in Boring.

---

## 🔐 Data Architecture

Boring follows a **"Local-First, LLM-Assisted"** architecture.

### 🏠 Local Storage (No Cloud sync)
- **Codebase Index**: All vector embeddings (RAG) are stored locally in the project directory.
- **Learnings & Patterns**: Experience gained is stored in local JSON files.
- **Logs**: Execution logs and traces never leave your machine unless manually exported.

### 🌐 Outbound Traffic (LLM API)
Only the following data is sent to the LLM (Google Gemini or Anthropic Claude):
1.  **Prompt**: The task instructions.
2.  **Code Chunks**: Relevant snippets retrieved via RAG (filtered for relevance).
3.  **File Metadata**: Filenames and directory structures needed for context.

> [!IMPORTANT]
> Boring does **not** upload your entire repository to the cloud. It only sends snippets strictly necessary for the current task.

---

## 🛡️ Execution Safety

### Shadow Mode
High-risk operations (file deletion, system command execution, network requests) are intercepted by the **Shadow Interceptor**.
- **Rule-based**: You can whitelist paths or tools.
- **Human-in-the-Loop**: Dangerous operations pause and wait for your explicit approval in the UI.

### Quality Gates
Before any code is considered "final", Boring runs it through multiple local verification layers:
- Static analysis (Linter)
- Security scans (Secret detection, SAST)
- Dynamic tests (Unit Tests)

---

## ⚖️ Privacy Compliance

- **No Training**: We do not use your code to train foundation models.
- **Compliance**: Boring respects `.gitignore` and `.dockerignore` to avoid indexing sensitive or temporary files.
- **Transparency**: Every outgoing request and every tool execution is logged for audit purposes.

---

## 🛡️ Recommended Security Configuration

For enterprise environments, we recommend the following `.boring.toml` settings:
```toml
[security]
shadow_mode = "STRICT"      # Require approval for all write operations
scan_for_secrets = true     # Block commits containing API keys
allowed_domains = ["*"]     # Restrict outgoing network calls if necessary
```
