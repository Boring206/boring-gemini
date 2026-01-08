# Boring Error Translator (Phase 3)

## Goal
Transform cryptic technical error messages into clear, actionable, natural language explanations for Vibe Coders.

## Architecture Guidelines (100分架構)
1.  **Single Responsibility**: `ErrorTranslator` class solely responsible for translation logic.
2.  **Extensibility**: Use a plugin/strategy pattern for language support (ZH, EN) and error types.
3.  **No Hardcoding**: Load error patterns and solutions from a structured knowledge base (JSON/YAML) or use `llm_client` for dynamic translation.
4.  **Graceful Degradation**: If translation fails, return original error with a generic helpful tip.
5.  **Integration**: Simple hook into `MainLoop` and `boring_verify`.

## High-Level Design

### Class: `ErrorTranslator`
- **Input**: Raw error string (e.g., "ModuleNotFoundError: No module named 'pandas'")
- **Output**: `ErrorExplanation` dataclass
    - `technical_summary`: "Missing Python library"
    - `friendly_message`: "看起來你的程式碼用到了一個還沒安裝的工具箱 (pandas)。"
    - `fix_command`: "boring_run_plugin('install_package', package='pandas')" (or similar)
    - `complexity`: "Low"

### Strategy
1.  **Pattern Matching (Regex)**: Fast path for common errors (`ModuleNotFoundError`, `SyntaxError`, `IndentationError`).
2.  **LLM Fallback**: For complex errors, use a lightweight LLM call (via `gemini` CLI or internal API) to interpret.

## Implementation Plan
1.  Create `src/boring/error_translator.py`
2.  Define `ErrorExplanation` dataclass
3.  Implement `ErrorTranslator` with Regex patterns first.
4.  Integrate into `boring` CLI output (e.g., in `main.py` exception handling).

## Core Error Patterns to Cover
- `ModuleNotFoundError` -> "缺套件"
- `SyntaxError` -> "語法錯誤 (可能是忘了括號或冒號)"
- `IndentationError` -> "縮排錯誤 (對齊問題)"
- `NameError` -> "變數未定義 (打錯字?)"
- `TypeError` -> "型別錯誤 (把文字當數字算?)"
