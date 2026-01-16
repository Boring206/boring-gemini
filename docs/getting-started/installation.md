# 安裝指南 (Installation)

> **🚀 推薦方式**: 使用 **One-Click Bootstrapper** (自動配置環境與 MCP)。
> **手動方式**: 使用 `pip` 安裝後執行 `boring wizard`。

---

## 🚀 方式 1: One-Click Bootstrapper (推薦)

這是一鍵完成安裝與配置的最快方式。它會自動：
1. 為 Boring 建立獨立的 Python 虛擬環境 (`~/.boring/env`)
2. 安裝最新版 `boring-aicoding`
3. 自動啟動配置精靈 (`boring wizard`) 來設定你的編輯器 (Cursor/Claude/VSCode)

### Windows (PowerShell)
```powershell
powershell -c "irm https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.ps1 | iex"
```

### Linux / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/Boring206/boring-gemini/main/scripts/install.sh | bash
```

---

## 🛠️ 方式 2: 手動安裝 (pip)

如果你希望手動管理 Python 環境：

### 1. 安裝套件
```bash
# 推薦 (包含 RAG 支持)
pip install "boring-aicoding[all]"

# 或者基礎版
pip install boring-aicoding
```

### 2. 配置編輯器 (MCP)
執行此指令來自動掃描並配置你的 IDE：
```bash
boring wizard
```
*(支援設定 Standard/Lite/Full/Custom 配置檔)*

---

## 🖥️ 支援的編輯器與客戶端 (Supported Clients)

Boring **Wizard** (V14+) 支援自動偵測與配置以下 **15+** 種 AI 客戶端：

### 🟢 IDEs & Editors
- **Cursor** (原生支援)
- **VS Code** (配合 Cline / Continue)
- **Windsurf** (Codeium)
- **Trae** (ByteDance)
- **Void** (Fork of Cursor)
- **OpenCode**

### 🔵 CLI Agents
- **Claude Code** (Anthropic)
- **Goose** (Block)
- **Aider** (Pair Programming)
- **Gemini CLI** (Google)
- **Qwen Code**

### 🟣 Autonomous Agents
- **OpenHands** (All-in-One)
- **Cline** (Autonomous)
- **Continue.dev** (Extension)

> 💡 **提示**: 只需執行 `boring wizard`，系統會自動掃描您已安裝的軟體並提供配置選項。

<details>
<summary><b>🛠️ 手動配置參考 (Manual Config Reference)</b></summary>

若您需要手動配置 MCP，以下是各客戶端的標準配置路徑：

| 客戶端 | 配置檔路徑 | 格式 |
|--------|------------|------|
| **Claude** | `~/.claude.json` | JSON |
| **Goose** | `~/.config/goose/config.yaml` | YAML |
| **Continue** | `~/.continue/mcpServers/boring.yaml` | YAML |
| **Windsurf** | `~/.../Windsurf/User/globalStorage/mcpServers.json` | JSON |
| **Trae** | `~/.../Trae/User/globalStorage/mcpServers.json` | JSON |
| **Aider** | `.aider.conf.yml` | YAML |
| **Cline** | VSCode Settings (`cline.mcpServers`) | JSON |

</details>

---

## ⚡ 方式 3: 進階用戶 (Smithery / uv)

<details>
<summary><b>Smithery (Gemini CLI)</b></summary>

適合不想污染本地環境的用戶：
```bash
npx -y @smithery/cli@latest install boring/boring --client gemini-cli
```
</details>

<details>
<summary><b>uv (極速安裝)</b></summary>

使用 `uv` 獲得 10-100x 安裝速度：
```bash
# 安裝
uv pip install "boring-aicoding[all]"

# 配置 MCP (推薦使用 wizard，或手動參考下方)
boring wizard
```
</details>

---

## ✅ 驗證安裝

在終端機輸入：
```bash
boring --version
# Output: boring v14.0.0 (or newer)
```

---

## 🔌 方式 4: 離線優先模式 (Offline-First)

如果您需要零網路依賴的開發環境：

### 1. 安裝包含本地支援的套件
```bash
pip install "boring-aicoding[local]"
```

### 2. 下載模型
```bash
boring model download
```

### 3. 啟用離線模式
```bash
boring offline enable
```

> 📖 **詳情請見**: [離線模式快速入門](../guides/offline-quickstart_zh.md)
