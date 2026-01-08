# 品質閘道 - CI/CD 整合

> 內建多層驗證閘道，適用於 CI/CD 管道。快速失敗，安全失敗。

---

## 🚦 閘道架構

```
┌─────────────────────────────────────────────────────────┐
│                   品質閘道                               │
├─────────────────────────────────────────────────────────┤
│  第一層：Lint 與格式    ━━━━▶ 快速回饋（~10秒）         │
│  第二層：安全掃描       ━━━━▶ 漏洞檢查                  │
│  第三層：單元測試       ━━━━▶ 覆蓋率驗證                │
│  第四層：整合測試       ━━━━▶ 完整系統測試              │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    ✅ 部署 或 ❌ 阻擋
```

---

## 📋 層級細分

### 第一層：Lint 與格式（約 10 秒）

```yaml
- name: Lint & Format
  run: |
    ruff check --output-format=github .
    ruff format --check .
```

**工具**：Ruff（Python）、ESLint（JS/TS）、golangci-lint（Go）

### 第二層：安全掃描（約 30 秒）

```yaml
- name: Security Scan
  run: |
    bandit -r src/ --severity-level medium
    pip-audit --strict
```

**工具**：Bandit（SAST）、pip-audit（依賴）、Safety

### 第三層：單元測試（約 2-5 分鐘）

```yaml
- name: Unit Tests
  run: |
    pytest --cov=src --cov-fail-under=40
```

**閾值**：預設最低 40% 覆蓋率

### 第四層：整合測試（僅 main 分支）

```yaml
- name: Integration Tests
  if: github.ref == 'refs/heads/main'
  run: |
    pytest tests/integration/ -v
```

---

## ⚙️ 配置

### 專案設定（.boring.toml）

```toml
[boring.quality_gates]
min_coverage = 40           # 最低測試覆蓋率 %
max_complexity = 15         # 最大圈複雜度
max_file_lines = 500        # 每個檔案最大行數
max_function_lines = 50     # 每個函數最大行數

[boring.linter_configs]
ruff_line_length = 100
eslint_max_warnings = 0

[boring.security]
bandit_severity = "medium"  # low|medium|high
dependency_scan = true
secret_scan = true
```

### GitHub Actions（.github/workflows/quality-gates.yml）

```yaml
name: Quality Gates

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff
      - run: ruff check --output-format=github .
      - run: ruff format --check .

  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit pip-audit
      - run: bandit -r src/ -ll
      - run: pip-audit

  test:
    runs-on: ubuntu-latest
    needs: security
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src --cov-fail-under=40

  integration:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -v
```

---

## 🛠️ MCP 工具整合

### 驗證命令

```python
# 快速語法檢查
boring_verify(level="BASIC")

# 標準含 Lint
boring_verify(level="STANDARD", incremental=True)

# 完整含測試
boring_verify(level="FULL")

# AI 語意審查
boring_verify(level="SEMANTIC")
```

#### ✨ Vibe Coder CLI
```bash
# 自然語言驗證
boring-route "幫我驗證程式碼"
# 🎯 boring_verify (STANDARD)

boring-route "做一次完整檢查"
# 🎯 boring_verify (FULL)
```

### 背景任務

```python
# 在背景執行驗證
task_id = boring_task(
    action="start",
    task_type="verify",
    level="FULL"
)

# 檢查狀態
boring_task(action="status", task_id=task_id)
```

---

## 🔄 Git Hooks

### 安裝

```bash
# 安裝所有 hooks
boring hooks install

# 檢查狀態
boring hooks status

# 解除安裝
boring hooks uninstall
```

### Hook 級別

| Hook | 觸發時機 | 級別 |
|------|----------|------|
| pre-commit | 每次提交 | STANDARD |
| pre-push | 每次推送 | FULL |
| quick-check | 儲存時（可選） | BASIC |

---

## 📊 品質趨勢

### 查看歷史

```bash
boring_quality_trend --days 30
```

### 回歸時失敗

```python
# 在 CI 中
if current_score < historical_average - 0.5:
    fail("偵測到品質回歸")
```

---

## 🏢 企業模式

### 分支保護規則

```yaml
# GitHub 分支保護
required_status_checks:
  strict: true
  checks:
    - lint
    - security
    - test
```

### 多環境閘道

```yaml
# 每個環境不同的閘道
staging:
  min_coverage: 60
  security_level: high

production:
  min_coverage: 80
  security_level: critical
  require_integration: true
```

---

## 另請參閱

- [效能](./performance_zh.md) - 優化
- [Git Hooks](../guides/git-hooks_zh.md) - 本地 hooks
- [專業技巧](../guides/pro-tips_zh.md) - 最佳實踐
