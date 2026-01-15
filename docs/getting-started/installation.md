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
# Output: boring v13.0.0 (or newer)
```
