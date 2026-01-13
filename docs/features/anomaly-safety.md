# Anomaly Detection Safety Net (P5)

> **"A guardian angel for your AI."**

The **Anomaly Detection** system (P5) is a built-in safety mechanism that protects your project from "Agent Loops" and accidental resource exhaustion. It sits between the AI Agent and your tools, monitoring every action in real-time.

## Capabilities

### 1. Infinite Loop Prevention
If an Agent tries to call the exact same tool with the exact same arguments repeatedly (e.g., `read_file("main.py")` 50 times in a row), the Safety Net intervenes.
- **Threshold**: 50 consecutive identical calls.
- **Action**: Blocks the 51st call.
- **Feedback**: Returns `⛔ ANOMALY DETECTED: Loop detected` to the Agent, forcing it to change strategy.

### 2. Smart Batching
The system is intelligent enough to distinguish between a *Loop* and a *Batch Operation*.
- **Scenario A**: Reading the *same* file 50 times -> **BLOCKED** 🛑
- **Scenario B**: Reading 50 *different* files -> **ALLOWED** ✅

## Configuration

You can adjust the sensitivity of the Safety Net via environment variables:

```bash
# Set max consecutive identical calls (Default: 50)
export BORING_ANOMALY_THRESHOLD=100
```

## Monitoring

When an anomaly is triggered, it is recorded in the **Usage Dashboard** (`boring-monitor`) under the "Anomalies" tab (coming soon).
