# 無伺服器協作指南 (Serverless Collaboration Guide)

> **核心哲學**: 零基礎設施，無限擴展。
> Boring-Gemini 使用 Git 作為代碼、狀態和知識的通用後端。

## 1. 插件生態系 ("App Store")

在 Boring 中，「應用商店」就是 GitHub。你不需要中央伺服器來發布或安裝擴充功能。

### 安裝插件 (Installing Plugins)
直接從 Git URL 安裝任何插件：
```bash
boring install https://github.com/boring/security-scanner
# 或者使用簡寫
boring install boring/security-scanner
```

### 建立與分享 Pack (Creating & Sharing Packs)
將你的工具、提示詞和工作流打包成單一的 `.boring-pack` 檔案：

1. **初始化**: `boring pack init --name my-awesome-pack`
2. **打包**: `cd my-awesome-pack && boring pack build`
3. **分享**: 上傳 `.boring-pack` 檔案到 GitHub Releases，或直接推送 Repo。

## 2. 知識共享 ("Brain")

你的代理 (Agent) 會隨著工作學習。你可以將這些學習成果轉移給隊友。

### 匯出知識 (Exporting Knowledge)
將你的向量資料庫 (ChromaDB) 匯出為可攜帶檔案：
```bash
boring brain export --output team-knowledge.boring-brain
```

### 匯入知識 (Importing Knowledge)
你的隊友可以匯入這些知識。它會與他們現有的大腦**合併 (merge)**，而不是覆蓋。
```bash
boring brain import team-knowledge.boring-brain
```

## 3. 團隊同步 (GitOps)

使用 `boring sync` 在同一專案上協作，無懼衝突。此命令處理透過 Git 同步 SQLite 狀態的複雜工作。

### 運作原理 (How it Works)
1. **匯出**: Boring 將內部 SQLite 狀態 (任務、里程碑) 導出為 `.boring/sync/state.json`。
2. **Git**: 提交此 JSON 檔案並拉取隊友的變更。
3. **合併**: 智能地將隊友的狀態合併到你的本地 SQLite。
4. **推送**: 推送你的更新。

### 使用方法 (Usage)
只需頻繁執行此命令：
```bash
boring sync
```

你也可以添加訊息：
```bash
boring sync -m "完成了認證模組"
```

## 總結

| 功能 | 命令 | 後端 |
|---------|---------|---------|
| **代碼** | `git push/pull` | Git |
| **狀態** | `boring sync` | Git + JSON |
| **插件** | `boring install` | Git / HTTP |
| **知識** | `boring brain` | Zip / File |

這種架構確保你擁有數據的所有權，並且依賴 $0 的外部基礎設施。
