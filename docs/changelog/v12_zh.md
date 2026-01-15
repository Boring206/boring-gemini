# V12 更新日誌 (Changelog)

## [12.1.2] - 2026-01-14 - Honesty & Hardening 🛡️
### 🛡️ 質量與誠實 (Quality & Integrity)
- **文檔誠實度 (100%)**: 深度審核所有手冊，確保與實作 1:1 匹配。
- **代碼庫衛生**: 移除實驗性產物與「幽靈功能」。
- **驗證**: 驗證了 `boring verify --level FULL` 以及 `uv`/`smithery` 配置路徑。
### 🚀 功能加速 (Feature Acceleration)
- **白名單 Skill 安裝**: `boring_skills_install` 現在支援受信任的 URL (`GitHub`, `SkillsMP`)。
- **通用技能系統 (BUSS)**: 
    - 跨平台 Skill 載入器，支援 `.boring/`, `.gemini/`, `.claude/`, `.antigravity/` 目錄。
    - 新增 MCP 工具：`boring_skill_discover`, `boring_skill_activate`, `boring_skill_create`, `boring_skill_download`。
    - 支援自動同步到所有客戶端目錄。
- **工作區衛生 (Workspace Hygiene)**: 新增 `boring clean` 指令，可安全清除暫存檔案 (`.boring/`, `.boring_memory/`)，還原乾淨的專案狀態。

## [12.0.0] - 2026-01-14 - 一條龍更新 (The True One Dragon Update) 🐉🧠

### 🚀 主要功能 (Major Features)
- **一條龍流程 (One Dragon Flow V12.0.0)**: 一個完整的、由狀態機驅動的自主開發迴圈。包含 `Architect` (架構師), `Builder` (構建者), `Healer` (修復者), `Polish` (磨光師) 和 `Evolver` (進化者) 階段。
- **認知反射 (Cognitive Reflex)**: 將語義搜尋 (RAG) 直接整合進大腦 (Brain)，實現高速模糊錯誤修正。
- **全球群體同步 (Global Swarm Sync)**: 透過 Git 在多個專案實例之間實現即時知識同步。

### 🔧 修復 (Fixes)
- **CLI 相容性**: 修復了 Keyless OAuth 用戶 (Gemini CLI) 遇到的 "Requested entity was not found" 錯誤。
- **導入精確度**: 修復了 HealerNode 中 `boring_checkpoint` 的導入問題。
- **節點穩定性**: 修復了 `engine.py` 中 `boring_speckit_tasks` 的 `NameError`，確保所有選擇性的 SpecKit 工具都有正確的備用初始化。

### 🛡️ 質量與穩定性 (Quality & Stability)
- **工具數量對齊**: 同步了所有文檔與路由元數據，反映已驗證的工具數量（67+ 標準級別，43 輕量級別）。
- **超時保護**: 為 `FlowEngine` 內的 `AgentLoop` 實作了 **1 小時全體超時**，防止永久掛機。
- **完整性審核**: 清除了所有文檔和指南中對 `VectorMemory` 和 `AutoLearner` 的「幽靈功能」引用。
- **標準化結果**: 100% 的工具現在都返回 `BoringResult` TypedDict，以便 LLM 進行更好的推理。
