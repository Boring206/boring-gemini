# 🖥️ Boring Monitor

> Real-time monitoring of your Agent's brain and body state.

**Boring Monitor** is a Streamlit-based graphical dashboard that gives you an at-a-glance view of your Agent's operation.

---

## ✨ Core Features

### 1. 📊 Live Status
- **Loop Count**: Current autonomous loop iteration.
- **Status**: Is the Agent `THINKING`, `CODING`, or `SLEEPING`.
- **API Calls**: Monitor token usage and API call frequency.

### 2. 🛑 Circuit Breaker
- View breaker status (`CLOSED`/`OPEN`).
- If the Agent gets stuck or fails repeatedly, the breaker trips to protect your API Quota.
- You can manually reset the breaker here.

### 3. 🧠 Brain Explorer
This might be the most interesting part! See your Agent's **RAG Memory** and **Learning Patterns**.
- **Learned Patterns**: See what "Error->Fix" patterns the Agent has learned.
- **Project Context**: View which files and structures are indexed by RAG.

### 4. 📝 Live Logs
- Watch the Agent's thought process and debugging logs in real-time.

---

## 🚀 How to Launch?

Run in your project root:

```bash
boring-dashboard
```

Or (if the above doesn't work):
```bash
streamlit run src/boring/dashboard.py
```

The browser will open automatically, usually at `http://localhost:8501`.

> **Pro Tip**: Keep it open while coding, just like a monitoring screen in a hacker movie! 😎
