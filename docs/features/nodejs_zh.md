# Node.js 自主權 (Node.js Autonomy)

**Node.js 自主權** 功能確保即使你的系統沒有全域安裝 Node.js，Boring 依然能執行其進階的 AI 工具。

## 概述

Boring 依賴 `gemini-cli`（以及其他基於 npm 的 MCP server）來開啟許多進階功能。對於沒有安裝 Node.js 或受限系統的使用者，Boring 現在可以自動下載並管理一個 **免安裝 (portable)** 的 Node.js 環境。

## 核心特徵

- **系統優先策略**：Boring 始終優先使用你現有的系統 Node.js 和 npm 安裝。
- **免安裝備援**：如果缺少 Node.js 或版本不相容，Boring 會提議將免安裝的 v20 LTS 版本下載到 `~/.boring/node`。
- **零配置**：`boring wizard` 會自動處理偵測與安裝流程。
- **隔離性**：免安裝版本與系統資料夾分開，避免與其他專案產生版本衝突。
- **一鍵維護**：健康檢查 (`boring health`) 會在環境需要更新時提醒你，並提供快速修復指令。

## 運作原理

當你執行 `boring wizard` 或需要 Node.js 的指令時，`NodeManager` 服務會：
1. 在系統路徑 (PATH) 中檢查 `node` 和 `npm`。
2. 如果找不到，則檢查 `~/.boring/node`。
3. 如果依然缺失，會詢問是否進行下載 (約 100MB)。
4. 解壓縮二進制檔案並設定內部使用的環境變數。

## 相關指令

- `boring wizard`：執行設定精靈以觸發環境偵測。
- `boring health`：檢查 Boring 目前使用的是 **系統 (System)** 還是 **免安裝 (Portable)** 版 Node.js。
