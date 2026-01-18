# 貢獻指南 (Contributing to Boring-Gemini)

感謝您有興趣為 Boring-Gemini 做出貢獻！ 🎉

## ❤️ 如何貢獻 (How to Contribute)

我們歡迎各種形式的貢獻：

- 🐛 **回報錯誤 (Bug Reports)**：使用 GitHub Issues 並標記為 `bug`。
- 💡 **功能請求 (Feature Requests)**：使用 GitHub Issues 並標記為 `enhancement`。
- 📖 **文獻改進 (Documentation)**：改進文件、README 或增加範例。
- 🔌 **插件開發 (Plugins)**：建立並分享自訂插件 (詳見 [Plugin Guide](docs/guides/plugins_zh.md))。

> **完整指南**：請參閱 [Docs: Contributing Guide](docs/reference/contributing.md) 獲取詳細流程。

## 開發環境設置 (Development Setup)

```bash
# 複製專案
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini

# 安裝開發依賴（包含所有質量工具）
pip install -e ".[dev]"

# 設置 pre-commit hooks（重要！）
pre-commit install
pre-commit install --hook-type commit-msg

# 首次運行所有 hooks
pre-commit run --all-files

# 運行完整質量檢查
./scripts/quality-check.sh    # Linux/macOS
# 或
.\scripts\quality-check.ps1   # Windows
```

## 程式碼規範 (Code Standards)

### 必須遵守的質量標準

我們維持 **100 分可維護性標準**。所有貢獻必須滿足：

#### 代碼質量
- ✅ **型別提示 (Type Hints)**：所有公開函數必須包含完整型別提示
- ✅ **文件字串 (Docstrings)**：使用 Google 風格，包含參數、返回值、範例
- ✅ **代碼風格**：通過 Ruff linting 和 formatting
- ✅ **類型檢查**：通過 Mypy 嚴格模式檢查
- ✅ **代碼複雜度**：Cyclomatic Complexity < 10

#### 測試要求
- ✅ **測試覆蓋率**：≥ 80%（新代碼應該 100%）
- ✅ **單元測試**：所有新功能必須有對應測試
- ✅ **集成測試**：複雜功能需要集成測試
- ✅ **所有測試通過**：本地和 CI 都要通過

#### 文檔要求
- ✅ **文檔覆蓋率**：≥ 80%
- ✅ **API 文檔**：公開 API 必須有完整文檔
- ✅ **代碼註釋**：複雜邏輯需要解釋性註釋
- ✅ **更新 CHANGELOG**：記錄所有變更

#### 安全要求
- ✅ **無硬編碼密鑰**：使用環境變量或配置文件
- ✅ **Bandit 掃描**：通過安全掃描（無高/中危漏洞）
- ✅ **依賴安全**：通過 pip-audit 檢查
- ✅ **輸入驗證**：所有外部輸入都要驗證

### 快速檢查指令

```bash
# 代碼風格和 linting
ruff check src/ tests/ --fix
ruff format src/ tests/

# 類型檢查
mypy src/boring/

# 測試覆蓋率
pytest tests/unit/ --cov=src/boring --cov-report=html

# 文檔覆蓋率
interrogate -vv src/boring/

# 代碼複雜度
radon cc src/boring/ -a

# 安全掃描
bandit -r src/
pip-audit

# 或一次性運行所有檢查
./scripts/quality-check.sh
```

## Pull Request 流程

### 1. 準備工作

```bash
# Fork 並克隆倉庫
git clone https://github.com/YOUR_USERNAME/boring-gemini.git
cd boring-gemini

# 添加上游倉庫
git remote add upstream https://github.com/Boring206/boring-gemini.git

# 安裝依賴和 hooks
pip install -e ".[dev]"
pre-commit install
```

### 2. 創建功能分支

```bash
# 與 main 同步
git checkout main
git pull upstream main

# 創建描述性分支名
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/issue-123
# 或
git checkout -b docs/improve-readme
```

### 3. 開發和測試

```bash
# 進行修改
# ...編寫代碼...

# 添加測試
# ...編寫測試...

# 添加文檔
# ...更新 docstrings 和文檔...

# 本地驗證
./scripts/quality-check.sh

# 運行測試
pytest -v
```

### 4. 提交代碼

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```bash
# 提交格式：<type>(<scope>): <subject>
git add .
git commit -m "feat(mcp): add new tool for code analysis"

# 類型 (type):
# - feat: 新功能
# - fix: 錯誤修復
# - docs: 文檔更新
# - style: 代碼格式（不影響功能）
# - refactor: 代碼重構
# - test: 測試相關
# - chore: 構建/工具變更
# - perf: 性能改進
```

### 5. 推送並創建 PR

```bash
# 推送到你的 fork
git push origin feature/your-feature-name

# 在 GitHub 上創建 Pull Request
# 使用提供的 PR 模板填寫所有信息
```

### 6. PR 審查流程

- ✅ **自動 CI 檢查**：所有檢查必須通過
- ✅ **代碼審查**：CODEOWNERS 會自動分配審查者
- ✅ **回應反饋**：及時回應審查意見
- ✅ **保持更新**：與 main 分支保持同步

```bash
# 與 main 同步
git fetch upstream
git rebase upstream/main

# 如果有衝突，解決後：
git rebase --continue
git push -f origin feature/your-feature-name
```

### 7. 合併後清理

```bash
# PR 合併後，刪除本地分支
git checkout main
git pull upstream main
git branch -d feature/your-feature-name
```

---

## 🌟 成為核心貢獻者 (Become a Core Contributor)

我們正在積極招募各領域的維護者！

### 貢獻者階梯

```
Level 1: First-time Contributor (首次貢獻)
    ↓  1+ PR 被合併
Level 2: Regular Contributor (常規貢獻者)
    ↓  3+ PR 被合併，持續活躍
Level 3: Domain Expert (領域專家)
    ↓  5+ 特定領域 PR，負責該領域審查
Level 4: Core Maintainer (核心維護者)
    ↓  6+ 個月持續貢獻，展現架構理解
Level 5: Project Steward (項目管理者)
```

### 正在招募的領域專家

| 領域 | 需要技能 | 狀態 |
|------|----------|------|
| 🔍 RAG & Vector Memory | ChromaDB, Embedding, Semantic Search | 🟢 招募中 |
| 🔌 MCP Protocol | FastMCP, Tool Design | 🟢 招募中 |
| 🤖 LLM Integration | Gemini, Ollama, Claude | 🟢 招募中 |
| 🛡️ Security | Bandit, Vulnerability Assessment | 🟢 招募中 |
| 📚 Documentation | MkDocs, Bilingual Writing | 🟢 招募中 |
| 🧪 Testing & QA | Pytest, Performance Testing | 🟢 招募中 |

### 如何申請

1. 累積足夠的貢獻 (Level 2+)
2. 填寫 [維護者申請表](https://github.com/Boring206/boring-gemini/issues/new?template=maintainer_application.yml)
3. 等待現有維護者審核 (14 天內回覆)
4. 通過後進入 1 個月試用期

詳見 [MAINTAINERS.md](MAINTAINERS.md)

---

## 質量門檻說明

### CI/CD 流程

所有 PR 會經過 4 層質量檢查：

1. **Tier 1: 快速檢查** (< 2 分鐘)
   - Ruff linting
   - Code formatting
   - Mypy type checking

2. **Tier 2: 安全掃描**
   - Bandit 安全掃描
   - pip-audit 依賴檢查

3. **Tier 3: 測試和質量**
   - 單元測試（80% 覆蓋率）
   - 代碼複雜度檢查
   - 文檔覆蓋率檢查

4. **Tier 4: 集成測試**
   - 多組件集成測試

**所有層級必須通過才能合併。**

### 如何查看 CI 失敗

1. 點擊 PR 頁面的 "Details"
2. 查看失敗的作業日誌
3. 在本地重現問題
4. 修復後推送更新

## 完整可維護性指南

詳細的可維護性要求和最佳實踐，請參閱：

- 📖 [可維護性指南](docs/MAINTAINABILITY.md)
- 📋 [可維護性檢查清單](docs/MAINTAINABILITY_CHECKLIST.md)
- 🏗️ [架構決策記錄 (ADR)](docs/adr/README.md)
- 🌱 [可持續性策略](docs/reference/sustainability.md)
- 📊 [功能矩陣](docs/reference/feature-matrix.md)

## 專案結構 (V14.8.0 - Predictive & Offline Architecture)

```
boring-gemini/
├── src/boring/
│   ├── mcp/                  # MCP Server 套件
│   │   ├── server.py         # FastMCP Entry
│   │   ├── tool_router.py    # Universal Router (Core Logic)
│   │   ├── tools/            # Tools Implementation
│   │   │   ├── core.py       # Basic Tools
│   │   │   ├── reasoning.py  # Sequential Thinking Logic
│   │   │   └── ...
│   │   └── profiles/         # Context Optimization Profiles
│   ├── plugins/              # Plugin System
│   ├── rag/                  # RAG System
│   ├── llm/                  # LLM Provider Abstraction
│   │   ├── provider.py       # Abstract Interface
│   │   ├── gemini.py         # Google Gemini
│   │   ├── ollama.py         # Ollama (Local)
│   │   └── ...               # More providers
│   └── ...
├── docs/                     # Documentation (Reorganized)
│   ├── tutorials/            # Tutorials, Demos, Playbooks
│   ├── guides/               # Vibe Coder, Cookbook, Skills
│   └── reference/            # Configuration, API, FAQ
├── .agent/workflows/         # SpecKit Workflows
└── tests/                    # Test Suite
```

## 🔌 建立插件 (Creating Plugins)

插件可在不修改核心程式碼的情況下擴展 Boring 功能。

詳見 [插件開發指南](docs/guides/plugins_zh.md)

快速範例：

```python
# my_plugin.py
from boring.plugins import plugin

@plugin(
    name="my_custom_tool",
    description="Does something awesome",
    author="Your Name"
)
def my_custom_tool(arg1: str) -> dict:
    return {"status": "SUCCESS", "result": arg1.upper()}
```

使用 `boring_reload_plugins`重新載入，並透過 `boring_run_plugin` 執行。

## 🤖 添加新的 LLM Provider

想要支持新的語言模型？請參閱 [LLM 適配器開發指南](docs/reference/llm-adapters.md)

## 有問題嗎？

歡迎開啟 Issue 或發起 Discussion！

