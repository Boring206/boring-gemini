# 🔮 預測性智慧與 AI 診斷 (Predictive & AI Diagnostics)

Boring V14.0 透過機器學習與腦部模式關聯，將開發體驗從「被動排錯」提升至「主動預警」。

## 🚀 主要功能

### 1. AI Git Bisect (智能斷點診斷)
與傳統的二分法查找不同，Boring 的 AI Git Bisect 會分析代碼變更的**語義**：
- **嫌疑度評分**：自動對最近的 Commit 進行評分（0.0 - 1.0）。
- **腦部模式對比**：對比歷史錯誤記錄，找出最相似的改動模式。
- **快速診斷**：無需運行所有測試，AI 即可從代碼邏輯中識別潛在的 Bug 引入源。

**使用指令：**
```bash
boring bisect --error "ValueError: name not defined" --file "src/main.py"
```

### 2. 預測性錯誤偵測 (Predictive Detection)
在您提交代碼或執行任務前，Boring 會自動掃描潛在風險：
- **反模式偵測**：偵測常見的 Python 陷阱（如可變默認參數、缺少 Null 檢查）。
- **歷史錯誤關聯**：如果您的改動與過去曾修復過的 Bug 模式相似，系統會立即發出警告。
- **安全掃描整合**：整合密鑰洩漏與 SQL 注入預警。

## 🧠 技術架構

Boring V14.0 的預測引擎由以下組件驅動：

1. **Predictor Engine**：實時分析代碼內容與 Diff。
2. **Brain Pattern Matcher**：從 `BrainManager` 中檢索相關的歷史成功/失敗模式。
3. **Risk Scoring**：根據修改廣度、複雜度與歷史風險計算整體風險指數。

## 🎨 使用場景

### 代碼提交前預檢
在 Commit 前執行預測掃描：
```bash
boring predict --diff
```

### 深度排錯
當遇到難以重現的 Bug 時：
```bash
boring diagnostic --last-known-good HEAD~10
```

## 📈 效益
- **減少 40% 的回歸錯誤**：在錯誤進入主分支前攔截。
- **加速 3x 的排錯時間**：精確定位嫌疑 Commit。
- **持續學習**：您的開發習慣會被 Brain 記錄，偵測精準度會隨時間提昇。

---
*Boring V14.0 - Coding at the edge of intelligence.*
