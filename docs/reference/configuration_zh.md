# 配置參考手冊

> 透過 `.boring.toml` 和環境變數配置 Boring 的完整指南。

---

## 📄 專案配置 (`.boring.toml`)

將此檔案放在專案根目錄以控制 Boring 的行為。

### `[boring]` 全域設定

```toml
[boring]
# 啟用除錯日誌（預設：false）
debug = false

# 啟用/停用特定功能
enable_shadow_mode = true
enable_rag = true
```

### `[boring.performance]`

效能調優設定。

```toml
[boring.performance]
# 驗證的平行 worker 數量（預設：4）
# 建議：
# - 小型專案（<500 檔案）：2-4
# - 大型專案（>1000 檔案）：8-16
parallel_workers = 4

# 啟用驗證結果快取（預設：true）
# 停用將強制每次都進行完整重新檢查。
verification_cache = true

# 增量更新 RAG 索引（預設：true）
incremental_rag = true
```

### `[boring.quality_gates]`

驗證失敗的閾值。

```toml
[boring.quality_gates]
# 最低單元測試覆蓋率百分比（0-100）
min_coverage = 40

# 允許的最大圈複雜度 (McCabe)
max_complexity = 15

# 允許的每個檔案最大行數
max_file_lines = 500

# 允許的每個函數最大行數
max_function_lines = 50

# 嚴格類型檢查 (mypy)
check_untyped_defs = true
disallow_any_generics = false
```

### `[boring.hooks]`

Git Hook 行為。

```toml
[boring.hooks]
# 'git commit' 的驗證級別
# 選項：BASIC, STANDARD, FULL
pre_commit_level = "STANDARD"

# 'git push' 的驗證級別
pre_push_level = "FULL"

# 自動修復 linting 錯誤（預設：true）
auto_fix = true

# Hooks 超時秒數
timeout_seconds = 300

[boring.hooks.bypass_patterns]
# Hook 驗證期間忽略的檔案
skip_files = ["*.md", "docs/*", "tests/fixtures/*"]
```

### `[boring.security]`

安全掃描配置。

```toml
[boring.security]
# 報告的最低嚴重性（low, medium, high）
bandit_severity = "medium"

# 掃描專案依賴的漏洞
dependency_scan = true

# 掃描密鑰/憑證
secret_scan = true
```

---

## 🌐 環境變數

全域覆蓋，最好在 `.env` 或 CI/CD 管道中設定。

### 核心
| 變數 | 預設值 | 說明 |
|------|--------|------|
| `BORING_LOG_LEVEL` | `INFO` | 日誌詳細程度 (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `BORING_PROJECT_ROOT` | `.` | 覆蓋專案根目錄路徑 |
| `BORING_CI_MODE` | `0` | 設為 `1` 以停用互動式提示 |

### 影子模式
| 變數 | 預設值 | 說明 |
|------|--------|------|
| `SHADOW_MODE_LEVEL` | `ENABLED` | 安全級別 (`DISABLED`, `ENABLED`, `STRICT`) |
| `BORING_ALLOW_DANGEROUS` | `false` | 設為 `true` 以繞過某些安全檢查（不推薦） |

### 效能
| 變數 | 預設值 | 說明 |
|------|--------|------|
| `BORING_WORKER_COUNT` | `4` | 覆蓋平行 worker 數量 |
| `BORING_CACHE_DIR` | `.boring_cache` | 自訂快取目錄 |

### Brain 與記憶
| 變數 | 預設值 | 說明 |
|------|--------|------|
| `BORING_BRAIN_PATH` | `~/.boring_brain` | 全域知識儲存路徑 |
| `BORING_RAG_ENABLED` | `1` | 設為 `0` 以完全停用 RAG |

---

## 🛠️ MCP 配置 (`smithery.yaml`/`mcp_config.json`)

當作為 MCP 伺服器運行時：

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "SHADOW_MODE_LEVEL": "STRICT",
        "BORING_MCP_MODE": "1"
      }
    }
  }
}
```

### MCP 特定變數

| 變數 | 說明 |
|------|------|
| `BORING_MCP_MODE` | MCP 伺服器運作時必須為 `1` |
| `PROJECT_ROOT_DEFAULT` | 若客戶端未提供，則使用此預設路徑 |

---

## 💡 範例：完整生產配置

**.boring.toml**
```toml
[boring]
debug = false

[boring.performance]
parallel_workers = 8
verification_cache = true

[boring.quality_gates]
min_coverage = 80
max_complexity = 10
check_untyped_defs = true

[boring.hooks]
pre_commit_level = "STANDARD"
pre_push_level = "FULL"
auto_fix = false 

[boring.security]
bandit_severity = "high"
```

**.env**
```bash
SHADOW_MODE_LEVEL=STRICT
BORING_CI_MODE=1
```
