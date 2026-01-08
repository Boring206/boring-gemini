# 🖥️ Boring 監控工具

> 即時監控 Agent 的大腦與身體狀態。

Boring 提供三種監控自主迴圈的方式，您可以根據環境與需求選擇最合適的工具。

---

## 🛠️ 監控工具版本

### 1. 📊 Boring Monitor (TUI)
基於終端的即時儀表板。適合在不離開終端機的情況下快速監控。

**指令：**
```bash
boring-monitor
```
> [!IMPORTANT]
> 請注意連字號！`boring-monitor` 是一個獨立指令，而不是 `boring` 的子指令。

### 2. 🌐 Boring Monitor (Web/FastAPI)
基於 FastAPI 的輕量級網頁儀表板。適合資源受限的環境。

**指令：**
```bash
boring-monitor --web
```
*需要安裝：`pip install fastapi uvicorn`。*

### 3. 🤖 Boring Dashboard (GUI/Streamlit)
功能最完整的視覺化儀表板。包含 **Brain Explorer**（大腦瀏覽器）與日誌視覺化功能。

**指令：**
```bash
boring-dashboard
```
*需要安裝：`pip install "boring-aicoding[gui]"`。*

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
