# Language & Environment Configuration

Boring-Gemini V14.0.0 supports multiple languages and flexible environment configuration.

## 🌍 Language Settings

You can adjust the output language of the Boring CLI (e.g., headers, diagnostic reports, help text).

### Option 1: Environment Variable (Recommended)
Set `BORING_LANG` in your terminal session. This takes immediate effect.

*   **PowerShell**: `$env:BORING_LANG = "en"` (English) or `"zh"` (Traditional Chinese)
*   **Linux/macOS**: `export BORING_LANG=en`

### Option 2: Config File (`.boring.toml`)
Add the `language` setting to your project's `.boring.toml` or the global one in `~/.boring.toml`.

```toml
[settings]
language = "en"  # "en" or "zh"
```

## 🔑 API Key Standardization

Starting with V14.0.0, the system standardizes on **`GOOGLE_API_KEY`**.

- **Required**: `GOOGLE_API_KEY` (Used for Gemini API calls, diagnostics, and online predictors).
- **Legacy**: `GEMINI_API_KEY` is still supported by direct SDK calls but `boring doctor` verifies `GOOGLE_API_KEY` for consistency.

### How to set:
*   **Windows**: `[System.Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', 'your-key-here', 'User')`
*   **macOS/Linux**: Add `export GOOGLE_API_KEY=your-key-here` to your `.bashrc` or `.zshrc`.

## 🩺 Diagnostic Output

Running `boring health` or `boring diagnostic` will use your configured language. If you see mixed languages, ensure your `BORING_LANG` is set correctly.
