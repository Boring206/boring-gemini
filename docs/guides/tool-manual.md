# 🛠️ Boring MCP 工具使用手冊

本手冊說明如何在實際開發中使用 Boring MCP 工具。

---

## 📋 快速參考

### 最常用工具 (Top 10)

| 工具 | 用途 | 範例 |
|------|------|------|
| `boring` | 🎯 萬用路由器 | `"幫我審代碼"` → 自動路由 |
| `boring_rag_search` | 🔍 搜尋程式碼 | `query="authentication"` |
| `boring_code_review` | 📝 程式碼審查 | `file_path="src/api.py"` |
| `boring_vibe_check` | ✅ 健康檢查 | `target_path="src/"` |
| `boring_verify` | 🧪 執行驗證 | `level="FULL"` |
| `boring_test_gen` | 🧪 生成測試 | `file_path="src/utils.py"` |
| `boring_commit` | 📦 智能提交 | 自動生成 commit message |
| `boring_security_scan` | 🔒 安全掃描 | `scan_type="full"` |
| `boring_impact_check` | 💥 影響分析 | `target_path="src/core.py"` |
| `boring_suggest_next` | 💡 下一步建議 | 根據專案狀態推薦 |

---

## 🔍 搜尋程式碼 (RAG)

### 基本搜尋

```
boring_rag_search query="用戶認證邏輯"
boring_rag_search query="database connection"
boring_rag_search query="error handling"
```

### 進階搜尋

```
# 限制搜尋範圍
boring_rag_search query="login" file_filter="auth"

# 調整結果數量
boring_rag_search query="API endpoints" max_results=20

# 展開依賴圖
boring_rag_expand chunk_id="chunk_123" depth=3
```

### 首次使用需要建立索引

```
boring_rag_index project_path="."
boring_rag_status  # 查看索引狀態
```

---

## 📝 程式碼審查

### 單檔案審查

```
boring_code_review file_path="src/api/auth.py"
boring_code_review file_path="src/components/Login.tsx"
```

### 指定審查焦點

```
# 焦點選項: all, naming, error_handling, performance, security
boring_code_review file_path="src/api.py" focus="security"
boring_code_review file_path="src/utils.py" focus="performance"
```

---

## ✅ 健康檢查 (Vibe Check)

### 快速檢查

```
# 檢查單檔案
boring_vibe_check target_path="src/main.py"

# 檢查整個目錄
boring_vibe_check target_path="src/"

# 檢查整個專案
boring_vibe_check target_path="."
```

### 輸出包含
- 🎯 Vibe Score (0-100)
- 📋 Lint 問題列表
- 🔒 安全問題
- 📚 文檔覆蓋率
- 🔧 一鍵修復 Prompt

---

## 🧪 測試生成

### 自動生成單元測試

```
# Python 檔案
boring_test_gen file_path="src/utils.py"

# TypeScript 檔案
boring_test_gen file_path="src/services/auth.ts"

# 指定輸出目錄
boring_test_gen file_path="src/api.py" output_dir="tests/"
```

### 支援語言
- ✅ Python (pytest)
- ✅ JavaScript/TypeScript (jest)

---

## 🔒 安全掃描

### 完整掃描

```
boring_security_scan scan_type="full"
```

### 指定掃描類型

```
# 只掃描密鑰洩漏
boring_security_scan scan_type="secrets"

# 只掃描漏洞
boring_security_scan scan_type="vulnerabilities"

# 只掃描依賴
boring_security_scan scan_type="dependencies"
```

---

## 📦 Git 操作

### 智能提交

```
# 自動分析變更並生成語義化 commit message
boring_commit
boring_commit commit_type="feat" scope="auth"
```

### Git Hooks

```
# 安裝 hooks (提交前自動驗證)
boring_hooks_install

# 查看 hooks 狀態
boring_hooks_status

# 移除 hooks
boring_hooks_uninstall
```

---

## 💥 影響分析

### 修改前分析

```
# 查看修改此檔案會影響哪些模組
boring_impact_check target_path="src/core/database.py"
boring_impact_check target_path="src/utils/helpers.ts" max_depth=3
```

### 輸出包含
- 📊 依賴此檔案的模組列表
- ⚠️ 風險等級
- 🧪 需要驗證的測試

---

## 🛡️ Shadow Mode (安全模式)

### 查看狀態

```
boring_shadow_status
```

### 切換模式

```
# 正常模式 (低風險操作自動執行)
boring_shadow_mode mode="ENABLED"

# 嚴格模式 (所有寫入需確認)
boring_shadow_mode mode="STRICT"

# 關閉 (不推薦)
boring_shadow_mode mode="DISABLED"
```

### 審核操作

```
boring_shadow_approve operation_id="xxx"
boring_shadow_reject operation_id="xxx"
```

---

## 📐 架構分析

### 生成依賴圖

```
boring_arch_check target_path="src/"
boring_visualize scope="module"
```

### 輸出格式

```
# Mermaid 圖表
boring_arch_check output_format="mermaid"

# JSON
boring_arch_check output_format="json"
```

---

## 💡 智能建議

### 獲取下一步建議

```
boring_suggest_next
boring_suggest_next limit=5
```

### 輸出包含
- 🎯 推薦的下一步行動
- 📊 專案狀態分析
- ⚠️ 潛在問題

---

## 🚀 工作流範例

### 新功能開發

```
1. boring_rag_search query="相關功能"     # 搜尋現有程式碼
2. boring_impact_check target_path="..."  # 分析修改影響
3. [開發程式碼]
4. boring_code_review file_path="..."     # 審查程式碼
5. boring_test_gen file_path="..."        # 生成測試
6. boring_vibe_check target_path="..."    # 健康檢查
7. boring_verify level="FULL"             # 執行驗證
8. boring_commit                          # 智能提交
```

### 修復 Bug

```
1. boring_rag_search query="錯誤訊息"     # 搜尋相關程式碼
2. [修復程式碼]
3. boring_security_scan                   # 確保無安全問題
4. boring_vibe_check                      # 健康檢查
5. boring_commit commit_type="fix"        # 提交修復
```

### 程式碼審查

```
1. boring_code_review file_path="..." focus="all"
2. boring_security_scan scan_type="secrets"
3. boring_arch_check target_path="..."
```

---

## ⚙️ 環境變數

| 變數 | 值 | 說明 |
|------|---|------|
| `BORING_MCP_MODE` | `1` | 啟用 MCP 模式 (必須) |
| `BORING_MCP_PROFILE` | `lite`/`standard`/`full` | 工具層級 |
| `PROJECT_ROOT_DEFAULT` | `.` | 預設專案路徑 |

---

## 📚 延伸閱讀

- [MCP 設定指南](./mcp-configuration.md)
- [使用模式說明](./usage-modes.md)
- [YOLO 模式整合](./yolo-boring-integration.md)
