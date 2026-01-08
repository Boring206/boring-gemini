# 🖥️ Boring Monitor (儀表板)

> 即時監控 Agent 的大腦與身體狀態。

**Boring Monitor** 是一個基於 Streamlit 的圖形化儀表板，讓您對 Agent 的運作一目了然。

---

## ✨ 核心功能

### 1. 📊 即時狀態 (Live Status)
- **Loop Count**: 當前自主迴圈的執行次數。
- **Status**: Agent 是在 `THINKING`, `CODING` 還是 `SLEEPING`。
- **API Calls**: 監控 token 使用量與 API 呼叫頻率。

### 2. 🛑 斷路器監控 (Circuit Breaker)
- 查看斷路器狀態 (`CLOSED`/`OPEN`)。
- 如果 Agent 卡住或連續出錯，斷路器會跳開保護您的 API Quota。
- 您可以在這裡手動重置斷路器。

### 3. 🧠 Brain Explorer (大腦瀏覽器)
這或許是最有趣的部分！您可以看到 Agent 的 **RAG 記憶** 與 **學習模式**。
- **Learned Patterns**: 看看 Agent 學會了哪些「錯誤->修復」模式。
- **Project Context**: 查看 RAG 索引了哪些檔案與結構。

### 4. 📝 Live Logs
- 即時查看 Agent 的思考過程與除錯日誌。

---

## 🚀 如何啟動？

在您的專案根目錄執行：

```bash
boring-dashboard
```

或者（如果上面的指令無效）：
```bash
streamlit run src/boring/dashboard.py
```

瀏覽器會自動開啟，預設網址為 `http://localhost:8501`。

> **Pro Tip**: 您可以邊寫 Code 邊開著它，就像是駭客電影裡的監控螢幕一樣！😎
