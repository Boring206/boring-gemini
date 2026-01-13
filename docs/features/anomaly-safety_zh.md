# 異常偵測安全網 (Anomaly Detection Safety Net) - P5

> **"AI 代理的守護天使。"**

**異常偵測系統 (P5)** 是一個內建的安全機制，專門保護您的專案免受 "Agent Loops"（代理無限迴圈）和意外資源耗盡的影響。它位於 AI 代理與工具之間，即時監控每一個操作。

## 核心能力

### 1. 防止無限迴圈
如果 Agent 嘗試重複呼叫完全相同的工具和參數（例如：連續 50 次 `read_file("main.py")`），安全網將會介入。
- **閾值**：連續 50 次完全相同的呼叫。
- **動作**：阻擋第 51 次呼叫。
- **回饋**：向 Agent 返回 `⛔ ANOMALY DETECTED: Loop detected`，迫使其改變策略。

### 2. 智慧批次處理
系統足夠聰明，能夠區分 *迴圈 (Loop)* 和 *批次操作 (Batch Operation)*。
- **情境 A**：讀取 *同一個* 檔案 50 次 -> **阻擋 (BLOCKED)** 🛑
- **情境 B**：讀取 50 個 *不同* 的檔案 -> **允許 (ALLOWED)** ✅

## 設定

您可以透過環境變數調整安全網的靈敏度：

```bash
# 設定最大連續相同呼叫次數 (預設: 50)
export BORING_ANOMALY_THRESHOLD=100
```

## 監控

當異常被觸發時，它將被記錄在 **Usage Dashboard** (`boring-monitor`) 中。
