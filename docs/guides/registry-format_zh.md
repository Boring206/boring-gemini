# Boring Registry 格式規範

> **版本**: 1.0.0  
> **狀態**: 草稿  
> **日期**: 2026-01-18

這份文件定義了 `registry.json` 的結構，這是 Boring-Gemini 去中心化插件生態系的索引檔案。

## 核心哲學 (Core Philosophy)
- **僅索引 (Index Only)**: Registry 只做索引，不存代碼。
- **Git 原生 (Git-Native)**: 依賴 Git URL 作為唯一的「真相來源 (Source of Truth)」。
- **去中心化 (Decentralized)**: 任何人都可以 fork 這個 registry 並維護自己的清單。

## JSON 結構

```json
{
  "schema_version": "1.0",
  "last_updated": "YYYY-MM-DD",
  "maintainer": "Boring Team",
  "plugins": [
    {
      "id": "namespace/plugin-name",
      "type": "plugin",
      "name": "Display Name",
      "description": "Short description",
      "repo": "https://github.com/user/repo",
      "branch": "main",
      "path": "/",
      "min_core_version": "15.0.0",
      "tags": ["tag1", "tag2"],
      "verified": false
    }
  ]
}
```

## 欄位定義

### Root Object (根物件)
| 欄位 | 類型 | 描述 |
|-------|------|-------------|
| `schema_version` | string | Registry 格式版本 (e.g. "1.0") |
| `last_updated` | string | 最後更新日期 (ISO 8601) |
| `plugins` | array | 插件清單 |

### Plugin Object (插件物件)
| 欄位 | 類型 | 必填 | 描述 |
|-------|------|----------|-------------|
| `id` | string | Yes | 唯一識別符，格式 `namespace/name`。通常對應 `github_user/repo_name`。 |
| `type` | string | Yes | 資源類型: `plugin`, `workflow`, `brain`, `theme` |
| `name` | string | Yes | 人類可讀的顯示名稱 |
| `description` | string | Yes | 簡短說明 (建議 < 100 字) |
| `repo` | string | Yes | 完整的 Git Repository URL (HTTPS) |
| `branch` | string | No | 指定分支，預設為 `main` 或 `master` |
| `path` | string | No | Repository 內的子目錄路徑，預設為根目錄 `/` |
| `min_core_version` | string | No | 需要的 boring-gemini 最低版本 (SemVer) |
| `tags` | array | No | 搜尋用的關鍵字標籤 |
| `verified` | bool | No | (官方用) 是否經過官方安全審核 |

## 範例

```json
{
  "schema_version": "1.0",
  "last_updated": "2026-01-18",
  "plugins": [
    {
      "id": "boring/security-scanner",
      "type": "plugin",
      "name": "Security Scanner",
      "description": "Advanced static analysis for Python code security.",
      "repo": "https://github.com/boring-plugins/security-scanner",
      "min_core_version": "15.0.0",
      "tags": ["security", "audit", "linter"],
      "verified": true
    }
  ]
}
```
