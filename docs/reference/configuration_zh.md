# 配置參考手冊 (Configuration)

> **給新手的簡單指南**：Boring 有兩種設定方式，請根據您的需求選擇。

---

## 🚦 快速開始：我該改哪裡？

### 情況 1：我是個人開發者 (使用 Cursor/Claude)
**👉 您應該修改 `mcp.json` (或 Cursor 設定)**
這是用來設定 **只有您自己** 會用到的偏好，例如：
- 省錢 (Token 優化)
- 效能調整
- Profile (Lite/Standard)

### 情況 2：我是團隊 Tech Lead
**👉 您應該建立 `.boring.toml` (放在專案根目錄)**
這是用來設定 **整個團隊** 都必須遵守的規則，例如：
- 程式碼品質標準 (Lint/Test)
- 安全掃描等級
- CI/CD 規則

---

## 🙋 常見設定情境 (Cookbook)

### 1. 我想要省錢 (Token 優化)
修改您的 MCP JSON 設定：
```json
"env": {
  "BORING_MCP_VERBOSITY": "minimal",  // 輸出極簡化 (省 90%)
  "BORING_MCP_PROFILE": "ultra_lite"  // 工具極簡化
}
```

### 2. 我想要效能全開 (平行處理)
修改您的 MCP JSON 設定：
```json
"env": {
  "BORING_WORKER_COUNT": "8"  // 開 8 個執行緒同時跑
}
```

### 3. 我想要更嚴格的安全檢查 (影子模式)
修改您的 `.boring.toml`：
```toml
[boring]
enable_shadow_mode = true

[boring.security]
secret_scan = true       # 掃描密碼
dependency_scan = true   # 掃描依賴漏洞
```

---

## 🔧 詳細配置參考

### 1. 專案配置 (`.boring.toml`)
將此檔案放在專案根目錄。

#### `[boring]` 全域設定
```toml
[boring]
# 啟用除錯日誌 (預設: false)
debug = false
# 啟用 RAG 記憶 (預設: true)
enable_rag = true
```

#### `[boring.quality_gates]` (品質閘道)
設定 "Done" 的標準。
```toml
[boring.quality_gates]
min_coverage = 40        # 最低測試覆蓋率 %
max_complexity = 15      # 允許的最大複雜度
max_file_lines = 500     # 單檔最大行數
check_untyped_defs = true # 強制型別檢查
```

#### `[boring.hooks]` (Git 鉤子)
控制 Commit/Push 時的行為。
```toml
[boring.hooks]
pre_commit_level = "STANDARD" # commit 時做標準檢查
pre_push_level = "FULL"       # push 時做完整檢查
auto_fix = true               # 自動修復簡單錯誤
timeout_seconds = 300         # 檢查超時秒數
```

### 2. 環境變數 & MCP JSON (`env`)
這些變數通常設定在您的 Cursor/Claude MCP 設定檔的 `env`區塊中。

| 變數名稱 | 預設值 | 說明 |
| :--- | :--- | :--- |
| **核心設定** | | |
| `BORING_MCP_PROFILE` | `lite` | 工具組大小 (`minimal`, `lite`, `standard`, `full`) |
| `BORING_MCP_VERBOSITY`| `standard` | 輸出詳細度 (`minimal`, `standard`, `verbose`) |
| `BORING_LOG_LEVEL` | `INFO` | 日誌等級 |
| **安全設定** | | |
| `SHADOW_MODE_LEVEL` | `ENABLED` | 安全沙箱等級 (`DISABLED`, `ENABLED`, `STRICT`) |
| `BORING_ALLOW_DANGEROUS`| `false` | 是否允許危險操作 (不建議) |
| **效能設定** | | |
| `BORING_WORKER_COUNT` | `4` | 平行處理的 Worker 數量 |
| `BORING_CACHE_DIR` | `.boring/cache`| 快取目錄位置 |
| **系統設定** | | |
| `BORING_PROJECT_ROOT` | `.` | 強制指定專案路徑 |
| `BORING_RAG_ENABLED` | `1` | 是否啟用 RAG (0=關閉) |

---

## 📝 完整 MCP JSON 範例

這是您在 Cursor Settings 中看起來的樣子：

```json
{
  "mcpServers": {
    "boring": {
      "command": "python",
      "args": ["-m", "boring.mcp.server"],
      "env": {
        "BORING_MCP_MODE": "1",           // 必填：啟動 MCP 模式
        "BORING_MCP_PROFILE": "lite",     // 推薦：日常開發用 Lite
        "BORING_MCP_VERBOSITY": "minimal",// 推薦：省錢模式
        "PROJECT_ROOT_DEFAULT": "."       // 預設當前目錄
      }
    }
  }
}
```
