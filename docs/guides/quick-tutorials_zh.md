# 快速入門教學

> 透過實作學習 Boring。5 分鐘常見工作流程教學。

---

## 📚 教學索引

| 教學 | 時間 | 技能水平 |
|------|------|----------|
| [1. 你的第一個 Vibe 專案](#1-你的第一個-vibe-專案) | 5 分鐘 | 初學者 |
| [2. 一鍵修復所有錯誤](#2-一鍵修復所有錯誤) | 3 分鐘 | 初學者 |
| [3. 新增功能](#3-新增功能) | 10 分鐘 | 中級 |
| [4. AI 代碼審查](#4-ai-代碼審查) | 5 分鐘 | 中級 |
| [5. 設定品質閘道](#5-設定品質閘道) | 10 分鐘 | 進階 |
| [6. 多代理開發](#6-多代理開發) | 15 分鐘 | 進階 |

---

## 1. 你的第一個 Vibe 專案

**目標**：從簡單描述建立可運行的應用。

### 步驟 1：開始對話

```
你：/vibe_start 建立一個簡單的 FastAPI REST API
```

### 步驟 2：回答澄清問題

```
Boring：很好！讓我問幾個問題：
        1. API 應該管理什麼資源？
        2. 需要認證嗎？
        3. 資料庫偏好？

你：1. 使用者和文章
    2. 暫時不需要認證
    3. SQLite
```

### 步驟 3：審查生成的計畫

```
Boring：這是我的計畫：
        1. 建立專案結構
        2. 設定 FastAPI 應用
        3. 定義 User 和 Post 模型
        4. 建立 CRUD 端點
        5. 新增 SQLite 資料庫
        
        要繼續嗎？

你：是的，請開始！
```

### 步驟 4：取得可運行的應用

```bash
# 執行你的新 API
uvicorn main:app --reload
```

**完成！** 你現在有一個可運行的 FastAPI 應用。

---

## 2. 一鍵修復所有錯誤

**目標**：一個命令清除所有 linting 和格式錯誤。

### 步驟 1：執行快速修復

```
你：/quick_fix
```

### 步驟 2：見證魔法

```
Boring：掃描問題中...
        ✅ 修復了 12 個 import 排序問題
        ✅ 修復了 8 個格式問題
        ✅ 修復了 3 個未使用的變數
        
        所有問題已解決！
```

**完成！** 所有代碼品質問題都已修復。

---

## 3. 新增功能

**目標**：為現有專案新增認證功能。

### 步驟 1：描述功能

```
你：為我的 FastAPI 專案新增 JWT 認證
```

### 步驟 2：AI 建立計畫

```
Boring：我將透過以下步驟新增認證：
        
        1. 安裝依賴（pyjwt, passlib）
        2. 建立 auth/models.py - User 模型
        3. 建立 auth/utils.py - 密碼雜湊
        4. 建立 auth/routes.py - 登入/註冊
        5. 更新 main.py - 新增 auth 路由
        
        要繼續嗎？
```

### 步驟 3：審查差異

```
Boring：這是我將變更的內容：
        
        + auth/models.py（新增）
        + auth/utils.py（新增）
        + auth/routes.py（新增）
        ~ main.py（修改）
        ~ requirements.txt（修改）
        
        批准嗎？

你：是的，套用變更
```

**完成！** 你的應用現在有認證功能了。

---

## 4. AI 代碼審查

**目標**：取得專家級代碼審查回饋。

### 步驟 1：請求審查

```python
boring_evaluate(
    target="src/main.py",
    level="DIRECT",
    criteria=["correctness", "security", "performance"]
)
```

### 步驟 2：審查回饋

```
Boring：src/main.py 代碼審查
        
        總體評分：7.5/10
        
        ✅ 優點：
        - 乾淨的函數簽名
        - 良好的錯誤處理
        
        ⚠️ 問題：
        1. 第 45 行有 SQL 注入風險
        2. get_posts() 中有 N+1 查詢模式
        3. 缺少輸入驗證
        
        📝 建議：
        - 使用參數化查詢
        - 為 posts 新增 eager loading
        - 新增 Pydantic 驗證
```

**完成！** 你有可執行的回饋了。

---

## 5. 設定品質閘道

**目標**：為 CI 管道新增自動化品質檢查。

### 步驟 1：本地安裝 hooks

```bash
boring hooks install
```

### 步驟 2：建立 GitHub Actions 工作流程

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install boring-aicoding
      - run: boring verify --level FULL
```

### 步驟 3：本地測試

```bash
# 執行驗證
boring verify --level FULL

# 預期輸出：
✅ 語法檢查：通過
✅ Linting：通過
✅ 安全掃描：通過
✅ 測試：42 通過，0 失敗
```

**完成！** 你的 repo 現在有品質閘道了。

---

## 6. 多代理開發

**目標**：使用專門代理處理複雜任務。

### 步驟 1：啟動工作流程

```python
boring_multi_agent(
    workflow="plan_and_implement",
    context={
        "feature": "使用 WebSockets 的即時通知"
    }
)
```

### 步驟 2：代理協作

```
🧠 規劃代理：
   建立實作計畫...
   - WebSocket 伺服器設定
   - 事件系統設計
   - 客戶端整合

📝 編碼代理：
   實作變更...
   - src/websocket.py（新增）
   - src/events.py（新增）
   - src/main.py（修改）

🔍 審查代理：
   審查變更...
   - ✅ 無安全問題
   - ⚠️ 考慮速率限制
   - ✅ 測試通過
```

### 步驟 3：審查最終輸出

```
Boring：多代理工作流程完成！
        
        建立的檔案：
        - src/websocket.py
        - src/events.py
        
        修改的檔案：
        - src/main.py
        - requirements.txt
        
        所有測試通過。準備部署。
```

**完成！** 複雜功能透過 AI 協作實作完成。

---

## 另請參閱

- [專業技巧](./pro-tips_zh.md) - 專家技巧
- [Git Hooks](./git-hooks_zh.md) - 本地自動化
- [MCP 工具](../features/mcp-tools_zh.md) - 完整工具參考
