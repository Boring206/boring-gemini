# Git Hooks 整合

> 自動化每次提交和推送的品質檢查。再也不會推送壞掉的代碼。

---

## 🚀 快速設定

### 一鍵安裝

```bash
boring hooks install
```

這會安裝：
- **pre-commit** - 執行 STANDARD 驗證
- **pre-push** - 執行 FULL 驗證

---

## 📋 Hook 級別

| Hook | 觸發時機 | 驗證級別 | 繞過方式 |
|------|----------|----------|----------|
| pre-commit | `git commit` | STANDARD | `--no-verify` |
| pre-push | `git push` | FULL | `--no-verify` |

### 每個級別檢查的內容

**STANDARD（pre-commit）**：
- ✅ 語法錯誤
- ✅ Linting（ruff）
- ✅ 格式化
- ✅ Import 排序

**FULL（pre-push）**：
- STANDARD 的所有內容，加上：
- ✅ 單元測試
- ✅ 安全掃描
- ✅ 依賴審計

---

## ⚙️ 配置

### 自訂 Hook 配置（.boring.toml）

```toml
[boring.hooks]
pre_commit_level = "STANDARD"    # BASIC|STANDARD|FULL
pre_push_level = "FULL"          # STANDARD|FULL
auto_fix = true                  # 自動修復 linting 問題
timeout_seconds = 300            # 最大 hook 執行時間

[boring.hooks.bypass_patterns]
# 跳過這些檔案模式的驗證
skip_files = ["*.md", "docs/*", "*.txt"]
```

### 手動 Hook 腳本

如果你偏好手動控制，建立 `.git/hooks/pre-commit`：

```bash
#!/bin/bash
boring verify --level STANDARD
exit $?
```

和 `.git/hooks/pre-push`：

```bash
#!/bin/bash
boring verify --level FULL
exit $?
```

設為可執行：
```bash
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

---

## 🛠️ 命令

### 安裝 Hooks
```bash
boring hooks install
```

### 檢查狀態
```bash
boring hooks status

# 輸出：
# pre-commit: ✅ 已安裝（STANDARD）
# pre-push: ✅ 已安裝（FULL）
```

### 解除安裝 Hooks
```bash
boring hooks uninstall
```

### 升級 Hooks
```bash
boring hooks install --force
```

---

## 🔄 工作流程範例

```bash
# 做變更
vim src/main.py

# 暫存變更
git add src/main.py

# 提交觸發 pre-commit hook
git commit -m "feat: 新增使用者認證"
# ✅ 語法檢查：通過
# ✅ Linting：通過（3 個自動修復）
# ✅ 格式化：通過
# [main abc1234] feat: 新增使用者認證

# 推送觸發 pre-push hook
git push origin main
# ✅ 語法檢查：通過
# ✅ Linting：通過
# ✅ 測試：42 通過
# ✅ 安全：無問題
# 推送到 origin...
```

---

## ⚡ 效能技巧

### 使用增量模式

Hooks 自動使用增量驗證：
- 只檢查**已暫存的檔案**（pre-commit）
- 只檢查**要推送的提交**（pre-push）

### 跳過重型檢查

開發期間的快速提交：

```toml
# .boring.toml
[boring.hooks]
pre_commit_level = "BASIC"  # 僅快速語法檢查
pre_push_level = "STANDARD" # 將 FULL 留給 CI
```

### 必要時繞過

```bash
# 跳過 hooks（謹慎使用！）
git commit --no-verify -m "WIP: 進行中的工作"
git push --no-verify
```

---

## 🏢 團隊配置

### 共享 Hook 配置

提交 `.boring.toml` 與團隊分享：

```bash
git add .boring.toml
git commit -m "新增團隊品質標準"
```

### 建議的團隊設定

```toml
# .boring.toml
[boring.hooks]
pre_commit_level = "STANDARD"
pre_push_level = "FULL"
auto_fix = true

[boring.quality_gates]
min_coverage = 40
max_complexity = 15
```

---

## 🔧 疑難排解

### Hook 沒有執行

```bash
# 檢查 hooks 是否已安裝
ls -la .git/hooks/

# 重新安裝
boring hooks install --force
```

### Hook 太慢

```toml
# .boring.toml
[boring.hooks]
pre_commit_level = "BASIC"  # 更快
timeout_seconds = 60        # 新增超時
```

### 測試在 Hook 中失敗

```bash
# 手動執行驗證查看詳情
boring verify --level FULL --verbose
```

---

## 另請參閱

- [品質閘道](../features/quality-gates_zh.md) - CI/CD 整合
- [效能](../features/performance_zh.md) - 優化
- [專業技巧](./pro-tips_zh.md) - 最佳實踐
