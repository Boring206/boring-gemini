# V11 更新日誌

> V11.x 系列的所有功能和改進。

---



## [11.2.11] - 2026-01-13
### 🚑 Hotfix
- **完整性修復**: 補齊了 v11.2.10 版本中漏掉的 One Dragon Engine 核心檔案 (`detector.py`, `evolution.py`, `vibe_interface.py`)。

## [11.2.10] - 2026-01-13
### 🚀 重大功能
- **一條龍引擎 (One Dragon Engine)**：發布 `boring_flow` MCP 工具，賦能 AI 代理 (Cursor/Gemini) 全程驅動專案生命週期。
- **無頭流引擎 (Headless FlowEngine)**：重構核心引擎以支援非交互式執行，實現與 MCP 的無縫整合。
- **自動對齊 (Auto-Alignment)**：增強 Vibe Session 以處理模糊指令（如「做得漂亮點」），透過 LLM 自動解析歧義。

## [11.2.2] - 2026-01-12
### 🚀 重大功能
- **視覺化智能**：儀表板中新增 **大腦地圖 (Brain Map)**。
- **大腦擴展性**：將 `BrainManager` 遷移至 **SQLite** 後端（符合 ACID 並提升 10 倍性能）。
- **輕量化體驗**：實現了 **全域快取與延遲初始化** (`BORING_LAZY_MODE`)。
- **深度與批判性思考**：增強了用於自主邏輯驗證的多層推理狀態 (`ReasoningState`)。

### 🛠️ 改進項目
- **架構標準化**：所有核心工具現在均返回 `BoringResult` (TypedDict)。
- **安全沙箱**：為合成工具提供基於 AST 的驗證。

---

## [11.2.1] - 2026-01-11
### 🔧 修復項目
- **Vibe 工具**：解決了 `KeyError: 'message'` 和 `NameError`。
- **單元隔離**：修復了 `vibe.py` 中不一致的引擎使用。
- **知識同步**：優化了 Git 同步的重試邏輯。
- **反射穩定性**：改進了 Brain Reflex 的提示詞注入機制。
- **代碼規範**：清理了核心庫和單元測試中的 `ruff` 錯誤。

---

## [11.1.0] - 跨語言解析器優化 🔧

**JavaScript 解析修復**
- 修正 `function_expression` → `function` 節點類型，適配 tree-sitter-languages JavaScript 語法
- 將測試案例從 JSX 更新為純 JavaScript 模式，確保一致的解析行為

**類型特異性排序系統**
- 新增智能類型優先級：`interface > type_alias > namespace > method > function > class`
- 修復 Go interface 被錯誤分類為 `class` 的問題
- 所有 4 種語言 (JS/TS/Go/C++) 現已完全驗證，名稱和類型均正確

**修復**
- 將 CLI 版本回退值從 10.32.1 更新至 11.1.0
- 測試斷言現使用 `boring.__version__` 動態版本檢查

---

## [11.0.0] - 彈性基礎更新 🛡️

### Windows 優化
- **事務性原子寫入**：引入 `TransactionalFileWriter`，配合指數退避策略處理 `os.replace`，解決 Windows 強制文件鎖定衝突
- **競態條件防護**：為 `Web Monitor` 和 `Shadow Mode` 實現跨線程與跨進程安全的狀態持久化
- **預執行鎖定**：在文件修改前添加強制鎖定檢測，確保乾淨的回滾

### 多語言 RAG 精確度
- **匹配定義提取**：重新設計 `TreeSitterParser` 使用 `query.matches()`，確保屬性（Go 接收器、TS 介面名稱）精確綁定到其定義
- **Go 支援**：新增 Go 方法接收器和指標類型的強健提取
- **TypeScript & C++**：增強 TS Interface/Type Alias 和 C++ Namespace/Template 定義的語義邊界檢測
- **Tree-sitter 版本固定**：專案統一使用 `tree-sitter==0.21.3` 確保 API 穩定性

### 開發者體驗
- **零配置嚮導**：將 `boring wizard` 和跨平台引導程式（`install.ps1`、`install.sh`）整合為核心功能
- **Vibe 分數進化**：將「一鍵修復提示」邏輯完全整合到健康檢查中

### 零配置引導程式
- **一鍵安裝器**：引入 `install.ps1`（Windows）和 `install.sh`（Linux/macOS）提供統一穩定的安裝體驗
- **隔離環境**：引導程式現自動創建專用的 `~/.boring/env` 以防止 Python 衝突
- **嚮導增強**：為 `boring wizard` 添加 `Custom` 配置文件支援，無需編輯 JSON 即可精細控制 RAG 和日誌

### 永續性與品質
- **覆蓋率成功**：專案測試覆蓋率提升至 **60%**（從約 20% 提升）
- **智能層**：核心 AI 模組達到高覆蓋率：`brain_manager.py` (88%)、`pattern_clustering.py` (93%)、`pattern_mining.py` (86%)
- **彈性服務**：為 `web_monitor.py` (78%) 和 `rag_watcher.py` 建立強健測試
