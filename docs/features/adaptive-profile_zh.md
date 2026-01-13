# 智慧適應性設定檔 (Intelligent Adaptive Profile) - P6

> **"懂你工作習慣的 AI 助手。"**

**適應性設定檔 (`adaptive`)** 是 Boring V11.5 引入的革命性功能。它不再強迫你在 "Lite"（快速但受限）和 "Full"（強大但昂貴）之間做選擇，而是根據你的行為**動態調整**系統配置。

## 運作原理

1.  **使用量追蹤**：系統會默默觀察你最常使用的工具（透過 `UsageTracker`）。
2.  **智慧上下文**：自動識別並鎖定你的 "Top 20" 核心工具。
3.  **情境注入 (Contextual Injection)**：
    - 當你開始測試時，自動注入 `Testing Guide`（測試指南）。
    - 當你進行除錯時，自動載入 `Error Analysis`（錯誤分析）工具。
4.  **提示詞注入 (Prompt Injection)**：根據目前活躍的工具類別，自動將相關的 Prompt 加入系統上下文。

## 主要優勢

- **⚡ 高效**：初始狀態與 `lite` 設定檔一樣輕量（節省 97% Token）。
- **🧠 智能**：當你需要時，瞬間變身為 `full` 設定檔的完整火力。
- **🛡️ 安全**：隱藏與當前任務無關的工具（例如在純寫 Code 時隱藏 Git 工具），防止上下文污染。

## 如何啟用

你可以透過 **Boring Wizard** 啟用：

```bash
boring wizard
# 在選單中選擇 "adaptive"
```

或手動修改 `.boring.toml`：

```toml
[mcp]
profile = "adaptive"
```

或設定環境變數：

```bash
export BORING_MCP_PROFILE=adaptive
```

## 隱私說明

所有使用數據僅儲存在本地的 `~/.boring/usage.json`。**絕不會** 上傳至雲端。你可以透過 `boring-monitor` 儀表板查看自己的數據。
