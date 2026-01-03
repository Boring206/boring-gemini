[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-5.2.0-green.svg)](https://github.com/Boring206/boring-gemini)

# Boring for Gemini (V5.2)

> **企業級自主 AI 開發代理 (Autonomous Developer)**  
> 專為 Cursor / Claude Desktop / VS Code 打造，利用 Google Gemini 模型驅動的自動化編碼與驗證引擎。
>
> ✅ **Verified Platforms**: Gemini CLI • Antigravity • Cursor

---

## 🚀 核心優勢 (Why Boring?)

- **🤖 Autonomous & Architect Mode**: 既能自動寫全套程式 (Standalone)，也能作為架構師 (Architect) 指揮您的 IDE AI 協同工作。
- **🔌 Full MCP Support**: 完美整合 Protocol，支援 `context7` (查文件)、`notebooklm` (查知識庫) 與 `criticalthink` (深度思考)。
- **🛡️ 企業級防護**: 內建斷路器 (Circuit Breaker)、自動修復 (Self-Healing) 與 100% 測試覆蓋率。
- **🧩 Spec-Driven Development**: 整合 SpecKit，從 PRD 到 Code 實現 100% 規格一致性。

---

## 📦 安裝指南 (Installation)

請選擇適合您的方式：

### 推薦方式：Smithery (一鍵部署，免 Python 環境)(目前失敗註冊smithery不知道爲什麼所以這是未來期許.....)

最適合 **Cursor** 或 **Claude Desktop** 使用者。

1.  **安裝本體**:
    ```bash
    npx @smithery/cli install boring-gemini
    ```

2.  **配置配套服務 (⚠️ 重要 / Required)**:
    Boring 的部分核心功能依賴外部 MCP Server。請務必在您的 IDE 設定檔 (`claude_desktop_config.json` 或 Cursor 設定) 中加入以下**完整配置**：

    ```json
    {
      "mcpServers": {
        "boring": {
          "command": "npx",
          "args": ["-y", "@smithery/cli", "run", "boring-gemini", "--config", "{}"]
        },
        "context7": {
          "command": "npx",
          "args": ["-y", "@upstash/context7-mcp"]
        },
        "criticalthink": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
        },
        "notebooklm": {
          "command": "npx",
          "args": ["-y", "notebooklm-mcp@latest"]
        }
      }
    }
    ```
    > **注意**: `notebooklm` 需要登入，初次使用請執行 `npx -y notebooklm-mcp@latest setup_auth` 完成 Google 認證。

### 開發者方式：Python Source (適合貢獻代碼)

```bash
# Clone & Install
git clone https://github.com/Boring206/boring-gemini.git
cd boring-gemini
pip install -e ".[all,dev]"

# 安裝擴展
boring setup-extensions
```

---

## 🛠️ 功能與指令 (Features & Usage)

安裝完成後，您可以在 Chat 中直接與 AI 互動，或使用以下工具：

### 1. 核心工具 (Agent Tools)

| 工具名稱 | 用途 |
| :--- | :--- |
| **`run_boring`** | **主要入口**。給它一個任務描述，它會自動規劃並執行。 |
| **`boring_quickstart`** | 🆕 **新手引導**。取得推薦步驟和可用工具清單。 |
| **`boring_verify`** | 執行全專案檢查 (Lint, Test, Import)。 |
| **`boring_health_check`** | 檢查系統健康狀態。 |
| **`boring_done`** | 🔔 完成通知。Agent 完成任務時呼叫，會發送 **Windows 桌面通知**。 |
| **`boring_learn`** | 🆕 從 `.boring_memory` 提取學習模式到 `.boring_brain`。 |
| **`boring_create_rubrics`** | 🆕 創建評估標準 (LLM-as-Judge)。 |
| **`boring_brain_summary`** | 🆕 查看知識庫摘要。 |

### 2. SpecKit 工作流 (Spec-Driven)

| 工具名稱 | 用途 |
| :--- | :--- |
| **`speckit_plan`** | 根據 PRD 生成 `IMPLEMENTATION_PLAN.md`。 |
| **`speckit_tasks`** | 將計畫拆解為 `task.md`。 |
| **`speckit_analyze`** | 比對 Code 與 Spec 的一致性 (Consistency Check)。 |
| **`speckit_constitution`** | 建立專案核心原則與開發準則。 |
| **`speckit_clarify`** | AI 反問模式，釐清模糊需求。 |
| **`speckit_checklist`** | 生成品質驗證檢查清單。 |

### 2.1 動態工作流程演化 (Workflow Evolution) 🆕

AI 可根據專案需求**動態修改** SpecKit 工作流程：

| 工具名稱 | 用途 |
| :--- | :--- |
| **`speckit_evolve_workflow`** | 修改工作流程內容以適應專案。 |
| **`speckit_reset_workflow`** | 回滾到原始模板。 |
| **`speckit_backup_workflows`** | 備份所有工作流程到 `_base/`。 |
| **`speckit_workflow_status`** | 查看工作流程演化狀態。 |

### 3. 微操作 (Granular Tools)

| 工具名稱 | 用途 |
| :--- | :--- |
| **`boring_apply_patch`** | 精確修改檔案 (Search/Replace)，不破壞其他部分。 |
| **`boring_verify_file`** | 單檔快速驗證。 |
| **`boring_extract_patches`** | 從 AI 輸出中萃取並套用程式碼修改 (支援多種格式)。 |

---

## 💡 使用範例

### 快速開始
```
你: 請幫我建立一個 TypeScript API 專案的規劃
AI: (呼叫 speckit_plan) 生成 implementation_plan.md...
```

### 動態演化工作流程
```
你: 這個專案需要特別強調安全測試，請調整 speckit-checklist 工作流程
AI: (呼叫 speckit_evolve_workflow) 已修改 speckit-checklist.md，
    添加了 OWASP Top 10 安全檢查項目...
```

### 使用記憶系統
```
你: 上次解決類似問題的方式是什麼？
AI: (查詢 .boring_memory) 找到 3 個相關經驗，建議使用...
```

---

## 🌍 Gemini CLI 整合

如果您偏好在終端機使用 Gemini CLI，可以將 Smithery 版 Boring 註冊進去：

```bash
gemini mcp add boring npx -- -y @smithery/cli run boring-gemini
```
註冊後即可在終端機對話：「請用 boring 幫我重構這個資料夾...」。

---

## 常見問題 (Troubleshooting)

1.  **`context7` 相關錯誤**:
    請確認您已正確複製上方的完整 JSON 配置，`context7` 是必備組件。

2.  **Interactive Mode (卡住/沒反應)**:
    當在 IDE 中使用時，Boring 預設為 **Architect Mode**。它會生成計畫與指令，然後**停下來**等您 (或 IDE 的 AI) 去執行寫入操作。這是正常且安全的設計。

3.  **NotebookLM 無法連接**:
    請務必執行 `setup_auth` 進行瀏覽器登入。

---

## 📁 專案結構

```text
my-project/
├── .boring_memory/      # 錯誤學習資料庫 (SQLite)
├── .boring_brain/       # 🆕 知識庫 (演化記錄、學習模式)
│   ├── workflow_adaptations/
│   ├── learned_patterns/
│   └── rubrics/
├── .agent/workflows/    # SpecKit 工作流程
│   ├── _base/          # 基礎模板備份
│   └── *.md            # 可演化的活動版本
├── PROMPT.md           # 專案核心指令
├── @fix_plan.md        # 任務進度表
├── src/                # 您的源碼
└── logs/               # JSON 結構化日誌
```

---

**Boring V5.2 - Making AI Development Boringly Reliable.**
