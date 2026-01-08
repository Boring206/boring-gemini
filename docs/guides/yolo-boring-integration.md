# Gemini YOLO + Boring 最大化利用指南

本指南說明如何結合 Gemini CLI 的 YOLO 模式與 Boring MCP 工具，達成最高效率的自主開發(自動化迴圈)。

## 核心概念

```
Gemini YOLO = 引擎（執行力）
Boring MCP  = 工具箱（專業技能）
```

當兩者結合，AI 可以自動使用 Boring 的 50+ 工具來完成複雜任務。

---

## 前置設定

### 1. 安裝 Boring MCP

確保 `~/.gemini/settings.json` 包含：

```json
{
  "mcpServers": {
    "boring": {
      "command": "uvx",
      "args": ["boring-aicoding"]
    }
  }
}
```

### 2. 驗證設定

```bash
gemini "列出所有可用的 boring 工具"
```

---

## 常用 YOLO 指令

### 🔍 程式碼搜尋 + 修改

```bash
gemini --yolo "使用 boring_rag_search 找到 auth 相關程式碼，然後修復登入 bug"
```

### 🧪 自動測試 + 修復

```bash
gemini --yolo "執行 boring_verify，如果失敗就修復問題，重複直到通過"
```

### 📝 程式碼審查 + 重構

```bash
gemini --yolo "對 src/ 下所有 Python 檔案執行 boring_code_review，然後修復所有建議"
```

### 🚀 發布流程

```bash
gemini --yolo "執行 /release-prep 工作流程，完成所有步驟"
```

---

## 進階組合技

### 全自動開發迴圈

```bash
gemini --yolo "
1. 使用 boring_rag_search 理解程式碼結構
2. 讀取 @fix_plan.md 找到下一個任務
3. 實作該任務
4. 使用 boring_verify 驗證
5. 如果通過，在 @fix_plan.md 標記 [x]
6. 重複直到所有任務完成
"
```

### 品質把關迴圈

```bash
gemini --yolo "
對每個修改的檔案：
1. boring_code_review 審查
2. boring_perf_tips 效能檢查  
3. boring_vibe_check 健康評分
修復所有問題直到 vibe score > 80
"
```

---

## Boring 工具速查表

| 工具 | 用途 | YOLO 搭配範例 |
|------|------|--------------|
| `boring_rag_search` | 語意搜尋程式碼 | 理解專案結構 |
| `boring_code_review` | AI 程式碼審查 | 自動修復建議 |
| `boring_vibe_check` | 專案健康評分 | 品質把關 |
| `boring_verify` | 執行驗證 | CI/CD 自動化 |
| `boring_impact_check` | 影響分析 | 安全重構 |
| `boring_security_scan` | 安全掃描 | 防止洩密 |
| `boring_test_gen` | 自動生成測試 | 提高覆蓋率 |
| `boring_doc_gen` | 自動生成文件 | 保持文件同步 |

---

## 自動化腳本

### Windows PowerShell

```powershell
# yolo_loop.ps1 - 自動化 YOLO 迴圈
$MAX_LOOPS = 5

for ($i = 1; $i -le $MAX_LOOPS; $i++) {
    Write-Host "=== Loop $i / $MAX_LOOPS ===" -ForegroundColor Cyan
    
    # 執行一輪
    gemini --yolo "完成 @fix_plan.md 中的下一個 [ ] 任務，完成後標記 [x]"
    
    # 驗證
    boring verify
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 驗證通過" -ForegroundColor Green
    } else {
        Write-Host "❌ 需要修復" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 5
}
```

### Linux/Mac Bash

```bash
#!/bin/bash
# yolo_loop.sh - 自動化 YOLO 迴圈

MAX_LOOPS=5
for i in $(seq 1 $MAX_LOOPS); do
    echo "=== Loop $i / $MAX_LOOPS ==="
    
    # 執行一輪（加上 timeout 避免無限跑）
    timeout 5m gemini --yolo "完成 @fix_plan.md 中的下一個任務"
    
    # 驗證
    boring verify
    
    if [ $? -eq 0 ]; then
        echo "✅ 驗證通過"
    else
        echo "❌ 需要修復"
    fi
    
    sleep 5
done
```

---

## 常見情境指令

| 情境 | 推薦指令 |
|------|---------|
| 理解新專案 | `gemini --yolo "boring_rag_search 分析整個程式碼庫"` |
| 修 Bug | `gemini --yolo "找到並修復 XXX 問題"` |
| 重構 | `gemini --yolo "boring_impact_check + 安全重構"` |
| 發布 | `gemini --yolo "/release-prep"` |
| 寫測試 | `gemini --yolo "boring_test_gen 為 src/ 生成測試"` |
| 安全檢查 | `gemini --yolo "boring_security_scan 掃描並修復"` |

---

## 注意事項

> ⚠️ **警告**：YOLO 模式會跳過所有確認！AI 可以直接修改檔案、執行指令。

### 安全建議

1. **使用 Git**：確保所有修改都可以回滾
2. **設定邊界**：明確告訴 AI 哪些檔案不能動
3. **分段執行**：大任務分成小步驟
4. **定期檢查**：每隔幾輪手動審查變更

### 推薦環境

- Docker 容器
- 虛擬機
- 獨立的測試專案
- 有完整備份的專案
