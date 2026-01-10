# Global Brain - 跨專案知識共享

## 🌐 概述

**Global Brain** 是 Boring 的跨專案知識共享系統，讓您在不同專案間分享學到的最佳實踐、錯誤解決方案和程式碼模式。

### 核心概念

- **專案 Brain** (`.boring/brain/`): 每個專案各自的知識庫
- **Global Brain** (`~/.boring/brain/`): 跨所有專案的全局知識庫
- **知識流向**: 專案 → Global → 其他專案

## 📂 儲存位置

Global Brain 儲存在您的**使用者主目錄**：

- **Windows**: `C:\Users\{YourName}\.boring/brain\global_patterns.json`
- **Linux/Mac**: `/home/{username}/.boring/brain/global_patterns.json`

**優點**: 
- ✅ 與專案無關，不會被誤刪
- ✅ 不受 Git 管理，保護隱私
- ✅ 所有專案自動共享

## 🧰 可用工具

### 1. `boring_global_export`
從當前專案**導出**高品質模式到 Global Brain

```python
boring_global_export(min_success_count=2)
```

**參數**:
- `min_success_count`: 最小成功次數（預設 2）
  - 只導出經過驗證的模式
  - 越高 = 品質越好

**使用情境**:
- ✅ 專案即將結束，想保留知識
- ✅ 解決了重要 bug，想分享給其他專案
- ✅ 累積足夠經驗，導出最佳實踐

---

### 2. `boring_global_import`
從 Global Brain **導入**模式到當前專案

```python
boring_global_import()  # 導入所有類型
boring_global_import(pattern_types=["error_solution"])  # 只導入錯誤解法
```

**參數**:
- `pattern_types`: 過濾類型（可選）
  - `["error_solution"]` - 只要錯誤解法
  - `["code_style", "performance"]` - 多種類型

**使用情境**:
- ✅ 開始新專案，想快速獲得經驗
- ✅ 遇到類似問題，導入已知解法
- ✅ 同步多個專案的最佳實踐

---

### 3. `boring_global_list`
查看 Global Brain 中的所有知識

```python
boring_global_list()
```

**回傳資訊**:
- 總 Pattern 數量
- 類型分布（error_solution, code_style 等）
- 每個 Pattern 的來源專案和成功次數

**使用情境**:
- ✅ 想知道 Global Brain 裡有什麼
- ✅ 決定從哪個專案導出知識
- ✅ 了解自己累積了多少經驗

## 🎯 典型工作流程

### 情境 1：從舊專案分享知識給新專案

```bash
# 在舊專案中（Project A）
cd ~/project-a
boring_global_export(min_success_count=3)  # 導出高品質模式

# 切換到新專案（Project B）
cd ~/project-b
boring_global_import()  # 導入所有知識
```

### 情境 2：跨團隊共享最佳實踐

```bash
# 團隊成員 A 從自己專案導出
boring_global_export(min_success_count=5)  # 只導出最佳模式

# 團隊成員 B 導入到自己專案
boring_global_import(pattern_types=["code_style", "performance"])
```

### 情境 3：個人知識庫管理

```bash
# 定期查看累積的知識
boring_global_list()

# 從多個專案導出
boring_global_export()  # 在每個專案執行

# 新專案一鍵導入
boring_global_import()
```

## 📊 Pattern 類型

Global Brain 支援以下類型的 Pattern：

| 類型 | 說明 | 範例 |
|------|------|------|
| `error_solution` | 錯誤解決方案 | "ModuleNotFoundError 的修復方法" |
| `code_style` | 程式碼風格偏好 | "使用 dataclass 而非 dict" |
| `performance` | 效能優化技巧 | "使用 LRU cache 加速查詢" |
| `security` | 安全性最佳實踐 | "永不硬編碼 API key" |
| `workflow_tip` | 工作流程建議 | "先寫測試再寫程式碼" |

## ⚙️ 進階用法

### 選擇性導入

只導入特定類型的知識：

```python
# 只要錯誤解法
boring_global_import(pattern_types=["error_solution"])

# 要風格和效能相關
boring_global_import(pattern_types=["code_style", "performance"])
```

### 品質控制

只導出經過充分驗證的模式：

```python
# 只導出成功 5 次以上的模式
boring_global_export(min_success_count=5)
```

### 查看詳細資訊

```python
result = boring_global_list()
print(result["patterns"])  # 每個 pattern 的詳細資訊
```

## 🔒 隱私與安全

### 自動過濾

- ❌ **不會導出**: API Keys、密碼、敏感路徑
- ✅ **只導出**: 抽象的模式和解決方案

### 本地儲存

- 資料只儲存在您的電腦
- 不會上傳到雲端
- 不會與他人自動分享

### 手動分享

如果您想與團隊分享：

1. 複製 `~/.boring/brain/global_patterns.json`
2. 透過安全管道傳給同事
3. 同事放到他們的 `~/.boring/brain/` 目錄

## 💡 最佳實踐

### ✅ 做

- 定期從完成的專案導出知識
- 新專案開始時先導入全局知識
- 使用 `min_success_count` 確保品質
- 定期查看 Global Brain 內容

### ❌ 不要

- 匯出低品質、未驗證的模式
- 在 Git 中 commit `.boring/brain/` 目錄
- 導入所有模式而不先查看內容

## 🐛 常見問題

### Q: Global Brain 是空的？
**A**: 先從任一專案執行 `boring_global_export`

### Q: 導入後沒看到變化？
**A**: 使用 `boring_brain_summary` 查看專案 Brain

### Q: 如何刪除某個 Pattern？
**A**: 手動編輯 `~/.boring/brain/global_patterns.json`

### Q: 可以在團隊間共享嗎？
**A**: 可以，但需要手動複製 JSON 檔案

## 🔗 相關工具

- `boring_learn` - 從當前專案學習模式
- `boring_brain_summary` - 查看專案知識庫
- `boring_brain_health` - 大腦健康報告
- `boring_pattern_stats` - Pattern 統計

## 📚 參考

- [Knowledge System Guide](knowledge.md)
- [Brain Manager API](../api/brain_manager.md)
