# Boring Pack 格式規範 (.boring-pack)

> **版本**: 1.0.0  
> **狀態**: 草稿  
> **日期**: 2026-01-18

Boring Pack 是 Boring-Gemini 生態系的標準分發格式。它不僅僅是 Python 代碼，更是一個包含工具、流程、提示詞和知識的「認知容器 (Cognitive Container)」。

## 📦 什麼是 Boring Pack?

一個 Boring Pack 是一個標準化的目錄結構（通常壓縮為 ZIP），包含：
1. **Tools**: 擴充功能的 Python 實作
2. **Workflows**: 定義代理行為的標準作業程序 (.md)
3. **Prompts**: 專家級的提示詞模板
4. **Knowledge (Brain)**: 預先索引的領域知識

## 📂 目錄結構

```text
my-awesome-pack/
├── boring-pack.json       # Manifest (必填)
├── README.md              # 文檔
├── LICENSE                # 授權文件
├── requirements.txt       # Python 依賴
├── tools/                 # Python 插件代碼
│   ├── __init__.py
│   └── my_tool.py
├── workflows/             # Agent Workflows
│   └── deploy_flow.md
├── prompts/               # Prompt Templates
│   └── system_prompt.md
├── brain/                 # 知識庫 (可選)
│   └── knowledge.parquet
└── assets/                # 圖片/圖示
    └── icon.png
```

## 📄 Manifest 格式 (boring-pack.json)

```json
{
  "spec_version": "1.0",
  "id": "boring/full-stack-pack",
  "version": "1.0.0",
  "name": "Full Stack Developer Pack",
  "description": "A complete suite for Full Stack development.",
  "author": "Boring Team",
  "license": "Apache-2.0",
  "homepage": "https://github.com/boring/pack",
  
  "min_boring_version": "15.0.0",
  
  "components": {
    "tools": ["tools/"],
    "workflows": ["workflows/"],
    "prompts": ["prompts/"],
    "brain": ["brain/"]
  },
  
  "permissions": [
    "filesystem:read",
    "network:http"
  ]
}
```

## 🛠️ 組件詳情

### Tools (工具)
標準的 Boring Plugin 寫法，使用 `@plugin` 裝飾器。Pack Loader 會自動加載 `tools/` 目錄下的所有模組。

### Workflows (工作流)
Markdown 格式的工作流定義。安裝後，使用者可以通過 `boring flow run <workflow_name>` 執行。

### Prompts (提示詞)
文本或 Markdown 格式。安裝後，Agent 可以在對話中引用，例如 `@prompt:system_prompt`。

### Brain (大腦/知識)
預先計算好的向量數據。安裝時會詢問是否合併到使用者的 Global Brain。

## 🚀 打包與分發

### 打包 (Packing)
使用 `boring pack` 命令將目錄打包為 `.boring-pack` (ZIP 格式)。
```bash
boring pack . --output my-pack.boring-pack
```

### 安裝 (Installing)
使用 `boring install` 命令安裝：
```bash
# 從 GitHub (源碼)
boring install https://github.com/user/my-pack

# 從本地檔案 (Pack 包)
boring install ./my-pack.boring-pack
```

### 安全性 (Security)
安裝 Pack 時，系統會顯示請求的權限 (`permissions` 欄位) 並要求使用者確認。
嚴格模式下，未簽署的 Pack 可能會被拒絕加載危險權限。
