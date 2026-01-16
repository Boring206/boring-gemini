# 🧹 清理工具 (boring clean)

`boring clean` 指令是維護專案開發環境整潔的核心工具。它能智能識別並移除不再需要的臨時文件、快取以及舊版的殘留檔案。

## 🌟 核心特色

- **統一結構強制執行**：協助將分散的舊版文件（如 `.boring_memory`）整合或清理，強制執行統一的 `.boring/` 目錄結構。
- **自動清理殘餘**：安全地移除斷路器狀態、響應分析以及臨時生成的 Prompt 文件。
- **分級清理**：支援標準清理與深層徹底清理（Deep Purge）。

## 🛠️ 使用說明

### 標準清理
移除臨時文件與日誌，這些文件可以安全刪除且不會丟失專案的長期記憶或歷史。

```bash
boring clean
```

### 深度清理 (All)
移除 **所有** 與 Boring 相關的元數據，包含備份 (Backups)、大腦記錄 (Brain) 與記憶。當您想為特定專案重置 Boring 狀態時使用。

```bash
boring clean --all
```

### 跳過確認
結合 `--force` 參數可跳過互動式確認，適用於自動化腳本。

```bash
boring clean --force
boring clean --all --force
```

## 📂 清理清單

### 標準模式
- `.circuit_breaker_state`, `.circuit_breaker_history` (斷路器狀態)
- `.exit_signals`, `.last_loop_summary` (結束信號與摘要)
- `.call_count`, `.last_reset` (API 調用統計)
- `.response_analysis` (AI 響應分析)
- `boring.log` (日誌文件)
- 臨時 Prompt 文件 (`.boring_run_prompt.md`)

### 深度模式 (`--all`)
- `.boring/` (統一數據目錄)
- `.boring_memory`, `.boring_brain` (知識庫與大腦)
- `.boring_cache`, `.boring_data` (快取與數據)
- `.boring_backups` (備份目錄)
- 舊版 `.agent/` 目錄

## ⚠️ 注意事項
`boring clean --all` 是一項破壞性操作。雖然 Boring 在某些操作中會自動建立備份，但 `clean --all` 會連同備份目錄一併刪除。執行前請務必確認。

---
*Boring Cleanup - 讓您的工作空間保持輕巧與專注。*
