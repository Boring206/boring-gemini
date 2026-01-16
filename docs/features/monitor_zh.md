# 🖥️ Boring 監控工具

> 即時監控 Agent 的大腦與身體狀態。

Boring 提供三種監控自主迴圈的方式，您可以根據環境與需求選擇最合適的工具。

---

## 🛠️ 監控工具分組表

Boring 的介面主要分為 **TUI (基於終端)** 與 **Dashboard (基於網頁)** 兩大類。

| 介面類型 | 工具名稱 | 觸發指令 | 自動/手動 | 核心功能 |
| :--- | :--- | :--- | :--- | :--- |
| **TUI** | **Boring Flow** | `boring flow` | **自動** (隨 `boring start` 啟動) | 顯示狀態機運作、Architect/Builder/Healer 進度。 |
| **TUI** | **Boring Watch** | `boring watch` | **手動** | 實時監控檔案變更，並自動觸發 **Ruff/Lint** 檢查與 AI 修復建議。 |
| **TUI** | **Boring Monitor** | `boring-monitor` | **手動** | 終端機內的即時 Token 成本、成功率、ASCII 依賴圖。 |
| **組件** | **RAG Watcher** | *(背景運作)* | **自動** | **隱形功能**：自動偵測檔案變更並更新 RAG 向量索引，無需手動干預。 |
| **Web** | **Boring Dashboard** | `boring-dashboard` | **手動** | 網頁版圖表：Token 趨勢、長期品質分數回顧、日誌視覺化。 |

---

## 🚀 介面詳細說明

### 1. 📊 Boring Monitor (TUI)
最快且最硬核的監控方式，直接顯示在終端機內。不需要開啟瀏覽器。

**觸發指令：**
```bash
boring-monitor
```

### 4. 👁️ Boring Watch (TUI)
一個專門的監控模式，它會監聽您的代碼變動：
- **自動檢查**：每當儲存檔案時，會自動執行 `ruff`、`mypy` 或測試。
- **AI 修復**：檢測到錯誤時，會在終端即時顯示 AI 的修復建議。

```bash
boring watch
```

### 🧠 RAG 自動索引 (隱形背景功能)
其實還有一個您看不見的「自動觸發」。Boring V13+ 內建了 **RAG Watcher**，只要您處於 `boring start` 循環中，系統會**自動偵測**您的檔案變更並更新本地向量資料庫（RAG），確保 AI 永遠擁有最新的代碼上下文，無需您手動執行索引更新。

### 2. 🐉 Boring Flow (TUI)
當您執行 `boring start` 或任何「一條龍」流程時，系統會**自動開啟**此介面，無需手動啟動。

**觸發指令：**
```bash
boring flow
# 或執行 start 時自動開啟
boring start 
```

### 3. 🤖 Boring Dashboard (Web/Streamlit)
如果您需要精美的圖表分析或查看 RAG 大腦索引，這是您的首選。

**觸發指令：**
```bash
boring-dashboard
```
*注意：若指令無效，請嘗試 `python -m boring dashboard`。*

---

## ✨ 核心功能 (Dashboard)

### 📊 即時狀態 (Live Status)
- **Loop Count**: 當前自主迴圈的執行次數。
- **Status**: Agent 是在 `THINKING` (思考)、`CODING` (編碼) 還是 `SLEEPING` (休眠)。
- **API Calls**: 監控 Token 使用量與 API 呼叫頻率。

### 🛑 斷路器 (Circuit Breaker)
- 查看斷路器狀態 (`CLOSED`/`OPEN`)。
- 如果 Agent 卡住或連續出錯，斷路器會跳開以保護您的 API 配額。

### 🧠 Brain Explorer (大腦瀏覽器)
查看您 Agent 的 **RAG 記憶** 與 **學習模式**。
- **Learned Patterns**: 看看 Agent 學會了哪些「錯誤->修復」模式。
- **Project Context**: 查看 RAG 索引了哪些檔案與專案結構。

### 📝 即時日誌 (Live Logs)
- 即時查看 Agent 的思考過程與除錯日誌。

---

## 🛠️ 常見問題與排查 (Troubleshooting)

### 1. 明明安裝了卻顯示 "not installed"？
這通常是因為 **Python 環境衝突**。如果你電腦裝了多個 Python 版本（例如 3.12 和 3.13），`pip` 安裝的地方可能跟 `boring` 指令執行的環境不同。

**解決方法：使用 Python 模組方式執行**
使用 `python -m` 可以強制指定當前環境的 Python 來執行：
- 啟動 Dashboard: `python -m boring dashboard` / `python -m boring.monitor --web`
- 啟動 Monitor: `python -m boring.monitor`

### 2. 出現 "Streamlit is required" 錯誤
如果執行 `boring-dashboard` 時提示缺少 `streamlit`，請確認您安裝的是完整版：
```bash
pip install "boring-aicoding[gui]"
# 或者
pip install "boring-aicoding[all]"
```
如果您使用虛擬環境，請確保已將其開啟（Activate）。

### 3. 出現 "tree-sitter-languages not installed" 警告
這是進階程式碼解析所需的套件。排查方法同上，如果安裝後仍顯示找不到，請改用 `python -m boring`。

### 4. 為什麼修改了程式碼（如翻譯、工具設定）卻沒生效？
這通常是因為 **MCP 伺服器 (Server) 尚未重新讀取**。
- **解決方法**：在 IDE (如 Cursor) 的 MCP 設定頁面點擊 **"Refresh" (重新整理)**。修改任何 Python 工具程式碼後，必須重啟伺服器，AI 才會學到新技能或看到更新後的邏輯。

> **Pro Tip**: 您可以邊寫 Code 邊開著監控視窗，就像是駭客電影裡的畫面一樣帥！😎
