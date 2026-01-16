# 🖥️ Boring Monitoring Tools

> Real-time monitoring of your Agent's brain and body state.

Boring provides three ways to monitor your autonomous loop, depending on your environment and needs.

---

## 🛠️ Interface Comparison

Boring interfaces are categorized into **TUI (Terminal-based)** and **Dashboard (Web-based)**.

| Type | Name | Trigger Command | Trigger Type | Core Features |
| :--- | :--- | :--- | :--- | :--- |
| **TUI** | **Boring Flow** | `boring flow` | **Automatic** (via `boring start`) | Shows state-machine activity, Architect/Builder/Healer progress. |
| **TUI** | **Boring Watch** | `boring watch` | **Manual** | Real-time file monitoring with **Automatic Ruff/Lint** checks and AI fix suggestions. |
| **TUI** | **Boring Monitor** | `boring-monitor` | **Manual** | Real-time Token cost, success rates, ASCII dependency graphs. |
| **Component** | **RAG Watcher** | *(Background)* | **Automatic** | **Invisible Feature**: Auto-detects file changes and updates RAG vector index silently. |
| **Web** | **Boring Dashboard** | `boring-dashboard` | **Manual** | Web Analytics: Token trends, Quality Score history, Log Explorer. |

---

## 🚀 Interface Detailed Guide

### 1. 📊 Boring Monitor (TUI)
The fastest, most direct way to monitor. No browser needed.

**Trigger:**
```bash
boring-monitor
```

### 4. 👁️ Boring Watch (TUI)
A dedicated monitoring mode that listens for code changes:
- **Auto-check**: Automatically runs `ruff`, `mypy`, or tests whenever you save a file.
- **AI Fix**: Displays immediate AI fix suggestions in the terminal when errors are detected.

```bash
boring watch
```

### 🧠 Automatic RAG Indexing (Hidden Feature)
There is also an "invisible trigger". Boring V13+ includes a **RAG Watcher**. While you are in a `boring start` loop, the system **automatically detects** your file changes and updates the local vector database (RAG). This ensures the AI always has the latest code context without requiring manual re-indexing.

### 2. 🐉 Boring Flow (TUI)
Automatically enabled when running `boring start` or the "One Dragon" workflow. No manual trigger required during active loops.

**Trigger:**
```bash
boring flow
# OR automatically via start
boring start
```

### 3. 🤖 Boring Dashboard (Web/Streamlit)
Best for beautiful analytics and deep RAG Brain inspection.

**Trigger:**
```bash
boring-dashboard
```
*Note: If the command isn't found, try `python -m boring dashboard`.*

---

## ✨ Core Features (Dashboard)

### 📊 Live Status
- **Loop Count**: Current autonomous loop iteration.
- **Status**: Is the Agent `THINKING`, `CODING`, or `SLEEPING`.
- **API Calls**: Monitor token usage and API call frequency.
- **Personal Stats**: See your top tools and usage patterns. [Learn more](./usage-dashboard.md).

### 🔍 Usage Analytics (New in V11.5)
The Monitor now includes a dedicated **Usage Stats** tab for introspection.
- See which tools you use most.
- Identify efficiency bottlenecks.
- View data powered by `boring_usage_stats`.

### 🛑 Circuit Breaker
- View breaker status (`CLOSED`/`OPEN`).
- If the Agent gets stuck or fails repeatedly, the breaker trips to protect your API Quota.
- **Anomaly Detection**: View loop anomalies blocked by the P5 Safety Net. [Learn more](./anomaly-safety.md).

### 🧠 Brain Explorer
See your Agent's **RAG Memory** and **Learning Patterns**.
- **Learned Patterns**: See what "Error->Fix" patterns the Agent has learned.
- **Project Context**: View which files and structures are indexed by RAG.

### 📝 Live Logs
- Watch the Agent's thought process and debugging logs in real-time.

---

## 🛠️ Troubleshooting & FAQ

### 1. Packages "not installed" despite pip success?
This usually happens when you have **multiple Python versions** (e.g., 3.12 and 3.13) installed on Windows. Your `pip` might be installing to a different version than the global `boring` command uses.

**Solution: Run as a Python module**
Use `python -m` to force the use of the Python environment where you installed the packages:
- Launch Dashboard: `python -m boring dashboard` / `python -m boring.monitor --web`
- Launch Monitor: `python -m boring.monitor`

### 2. "Streamlit is required" Error
If running `boring-dashboard` prompts that `streamlit` is missing, ensure you installed the GUI extras:
```bash
pip install "boring-aicoding[gui]"
# Or the full version
pip install "boring-aicoding[all]"
```
If you are using a virtual environment, ensure it is activated.

### 3. "No such command 'monitor'"
Remember that `monitor` is not a subcommand. Use `boring-monitor` (with a hyphen) instead.

### 4. Missing "tree-sitter-languages"
This is used for advanced code parsing. If it's not detected after installation, use the `python -m boring` method described above.

### 5. Why don't my changes take effect?
This usually happens because the **MCP Server** hasn't reloaded your code.
- **Solution**: In your IDE (e.g., Cursor) MCP Settings, click the **"Refresh"** button next to your connection. After modifying any Python tool code, you must restart the server for the AI to learn new skills or see logic updates.

> **Pro Tip**: Keep the monitor open while coding, just like a monitoring screen in a hacker movie! 😎
