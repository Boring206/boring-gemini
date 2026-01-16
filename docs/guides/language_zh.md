# 語言與環境配置指南

Boring-Gemini V14.0.0 支援多國語言以及靈活的環境變數配置。

## 🌍 語言設定 (Language Settings)

您可以調整 Boring CLI 的輸出語言（例如：標題、診斷報告、說明文字）。

### 方法 1：環境變數 (推薦)
在終端機中設定 `BORING_LANG`。這會立即生效並覆蓋其他設定。

*   **PowerShell**: `$env:BORING_LANG = "zh"` (繁體中文) 或 `"en"` (英文)
*   **Linux/macOS**: `export BORING_LANG=zh`

### 方法 2：設定檔案 (`.boring.toml`)
在專案目錄或全域目錄 (`~/.boring.toml`) 中加入語言設定。

```toml
[settings]
language = "zh"  # 可選 "zh" 或 "en"
```

## 🔑 API 金鑰標準化

從 V14.0.0 開始，系統統一優先使用 **`GOOGLE_API_KEY`**。

- **必要項目**: `GOOGLE_API_KEY` (用於 Gemini API 調用、診斷與線上預測器)。
- **相容性**: `GEMINI_API_KEY` 仍支援部分直接 SDK 調用，但 `boring doctor` 會驗證 `GOOGLE_API_KEY` 以確保環境一致。

### 如何設定：
*   **Windows (PowerShell)**: `[System.Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', '您的金鑰', 'User')`
*   **macOS/Linux**: 在您的 `.bashrc` 或 `.zshrc` 加入 `export GOOGLE_API_KEY=您的金鑰`。

## 🩺 診斷輸出

執行 `boring health` 或 `boring diagnostic` 時，系統會根據您的語系設定顯示對應的翻譯文字。如果您看到混合語言，請確認您的 `BORING_LANG` 是否正確。
