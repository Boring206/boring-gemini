# 🖥️ Boring Monitoring Tools

> Real-time monitoring of your Agent's brain and body state.

Boring provides three ways to monitor your autonomous loop, depending on your environment and needs.

---

## 🛠️ Monitoring Variants

### 1. 📊 Boring Monitor (TUI)
A terminal-based real-time dashboard. Perfect for fast monitoring without leaving the console.

**Command:**
```bash
boring-monitor
```
> [!IMPORTANT]
> Note the hyphen! `boring-monitor` is a standalone command, not a subcommand of `boring`.

### 2. 🌐 Boring Monitor (Web/FastAPI)
A lightweight web dashboard powered by FastAPI. Good for low-resource environments.

**Command:**
```bash
boring-monitor --web
```
*Requires `pip install fastapi uvicorn`.*

### 3. 🤖 Boring Dashboard (GUI/Streamlit)
The most comprehensive visual dashboard. Includes the **Brain Explorer** and log visualizer.

**Command:**
```bash
boring-dashboard
```
*Requires `pip install "boring-aicoding[gui]"`.*

---

## ✨ Core Features (Dashboard)

### 📊 Live Status
- **Loop Count**: Current autonomous loop iteration.
- **Status**: Is the Agent `THINKING`, `CODING`, or `SLEEPING`.
- **API Calls**: Monitor token usage and API call frequency.

### 🛑 Circuit Breaker
- View breaker status (`CLOSED`/`OPEN`).
- If the Agent gets stuck or fails repeatedly, the breaker trips to protect your API Quota.

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
