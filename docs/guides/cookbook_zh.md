# Cookbook - 完整功能食譜

> 每個 Boring 功能的即用食譜。複製、貼上、自訂。

---

## 📚 食譜索引

### 🚀 入門
- [食譜 1：首次專案設定](#食譜-1首次專案設定)
- [食譜 2：MCP 伺服器配置](#食譜-2mcp-伺服器配置)

### 🔧 日常工作流程
- [食譜 3：快速修復錯誤](#食譜-3快速修復錯誤)
- [食譜 4：功能開發](#食譜-4功能開發)
- [食譜 5：代碼審查](#食譜-5代碼審查)

### 🔒 安全
- [食譜 6：安全審計](#食譜-6安全審計)
- [食譜 7：影子模式設定](#食譜-7影子模式設定)

### 🧠 進階
- [食譜 8：多代理工作流程](#食譜-8多代理工作流程)
- [食譜 9：RAG 知識庫](#食譜-9rag-知識庫)
- [食譜 10：CI/CD 整合](#食譜-10cicd-整合)

---

## 食譜 1：首次專案設定

### 材料
- 空目錄或現有專案
- Python 3.9+
- pip

### 步驟

```bash
# 1. 安裝 Boring
pip install boring-aicoding

# 2. 初始化專案（如果是新專案）
boring-setup my-project
cd my-project

# 3. 開始開發
boring start
```

### 預期輸出
```
🚀 Boring v10.18.3 已啟動
📁 專案：my-project
🔍 監控變更中...
```

---

## 食譜 2：MCP 伺服器配置

### Claude Desktop

編輯 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "PROJECT_ROOT_DEFAULT": "/path/to/your/project",
        "SHADOW_MODE_LEVEL": "ENABLED"
      }
    }
  }
}
```

### Cursor

在 Settings → MCP Servers：
```json
{
  "boring": {
    "command": "boring-mcp",
    "args": [],
    "env": {
      "PROJECT_ROOT_DEFAULT": "."
    }
  }
}
```

### Smithery（雲端）
```
npx -y @anthropic-ai/mcp install @boring/boring
```

---

## 食譜 3：快速修復錯誤

### 問題
你有一個錯誤，想讓 AI 修復它。

### 步驟

```python
# 選項 1：描述錯誤
boring_apply_patch(
    project_path=".",
    description="修復登入函數 - 密碼為空時會崩潰"
)

# 選項 2：使用 quick_fix 提示
# 只需說：/quick_fix
```

### 驗證
```python
boring_verify(level="FULL")
```

---

## 食譜 4：功能開發

### 使用 SpecKit 工作流程

```python
# 步驟 1：建立原則
speckit_constitution(project_path=".")

# 步驟 2：澄清需求
speckit_clarify(
    feature="使用 OAuth 的使用者認證",
    questions=["providers", "storage", "session"]
)

# 步驟 3：建立實作計畫
speckit_plan(feature="user-auth")

# 步驟 4：生成檢查清單
speckit_checklist(plan_path=".boring/plans/user-auth.md")

# 步驟 5：實作
boring_multi_agent(
    workflow="plan_and_implement",
    context={"feature": "user-auth"}
)
```

---

## 食譜 5：代碼審查

### 直接評估
```python
boring_evaluate(
    target="src/main.py",
    level="DIRECT",
    criteria=["correctness", "security", "performance", "maintainability"]
)
```

### 配對比較
```python
boring_evaluate(
    level="PAIRWISE",
    target_a="src/auth_v1.py",
    target_b="src/auth_v2.py"
)
```

### 基於評分標準的評分
```python
boring_evaluate(
    target="src/",
    level="RUBRIC",
    rubric_path=".boring/rubrics/production-ready.md"
)
```

---

## 食譜 6：安全審計

### 完整安全掃描
```python
boring_security_scan(
    project_path=".",
    scan_type="all"  # sast + secrets + dependencies
)
```

### 僅密鑰
```python
boring_security_scan(
    project_path=".",
    scan_type="secrets"
)
```

### 帶自動修復
```python
boring_security_scan(
    project_path=".",
    scan_type="all",
    fix_mode=True
)
```

---

## 食譜 7：影子模式設定

### 為生產環境啟用
```python
# 設定 STRICT 模式
boring_shadow_mode(action="set_level", level="STRICT")

# 驗證狀態
boring_shadow_mode(action="status")
```

### 配置模式
編輯 `~/.boring_brain/shadow_config.json`：
```json
{
  "level": "STRICT",
  "auto_approve_patterns": ["*.md", "docs/*"],
  "always_block_patterns": ["*.env", "secrets/*", ".git/*"]
}
```

---

## 食譜 8：多代理工作流程

### 計畫並實作
```python
boring_multi_agent(
    workflow="plan_and_implement",
    context={
        "feature": "即時通知",
        "tech_stack": ["WebSockets", "Redis", "FastAPI"]
    },
    execute=True  # 實際執行，而非只生成提示
)
```

### 審查並修復
```python
boring_multi_agent(
    workflow="review_and_fix",
    context={
        "target": "src/",
        "focus": ["security", "performance"]
    }
)
```

---

## 食譜 9：RAG 知識庫

### 建立索引
```python
boring_rag_index(
    project_path=".",
    force=False  # 增量
)
```

### 搜尋代碼
```python
boring_rag_search(
    query="認證中介軟體",
    project_path=".",
    top_k=10,
    expand_deps=True
)
```

### 多專案搜尋
```python
boring_rag_search(
    query="錯誤處理模式",
    additional_roots=[
        "/path/to/shared-libs",
        "/path/to/reference-project"
    ]
)
```

---

## 食譜 10：CI/CD 整合

### GitHub Actions

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
        with:
          python-version: '3.11'
      - run: pip install boring-aicoding
      - run: boring verify --level FULL
      
  security:
    runs-on: ubuntu-latest
    needs: verify
    steps:
      - uses: actions/checkout@v4
      - run: pip install boring-aicoding
      - run: |
          python -c "
          from boring.mcp.tools import boring_security_scan
          result = boring_security_scan('.', 'all')
          if result.get('critical_count', 0) > 0:
              exit(1)
          "
```

---

## 另請參閱

- [Vibe Coder 指南](./vibe-coder_zh.md) - 適合視覺化/描述式開發者
- [快速教學](./quick-tutorials_zh.md) - 逐步指南
- [MCP 工具](../features/mcp-tools_zh.md) - 完整工具參考
