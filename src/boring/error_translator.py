import re
from dataclasses import dataclass
from re import Pattern
from typing import Optional


@dataclass
class ErrorExplanation:
    original_error: str
    friendly_message: str
    technical_summary: str
    fix_command: Optional[str] = None
    complexity: str = "Low"


class ErrorTranslator:
    def __init__(self):
        # Patterns: (Regex, Friendly Message Template, Technical Summary, Fix Command Template)
        self.patterns: list[tuple[Pattern, str, str, Optional[str]]] = [
            (
                re.compile(r"ModuleNotFoundError: No module named '(.*?)'"),
                "看起來你的程式碼用到了一個還沒安裝的工具箱 ({0})。",
                "Missing Python library",
                "boring_run_plugin('install_package', package='{0}')",
            ),
            (
                re.compile(r"SyntaxError:"),
                "程式碼有語法錯誤。通常是忘了括號、冒號，或是拼字錯誤。請檢查紅線標示的地方。",
                "Syntax Error",
                None,
            ),
            (
                re.compile(r"IndentationError:"),
                "程式碼縮排有問題。Python 很講究對齊，請確認每一行的縮排是否一致（建議都用 4 個空白鍵）。",
                "Indentation Error",
                "gemini --prompt 'Fix indentation in {filename}'",
            ),
            # === JavaScript / TypeScript Errors ===
            (
                re.compile(r"ReferenceError: (.*?) is not defined"),
                "找不到變數 '{0}'。可能是忘了宣告 (const/let)，或是拼錯字了。",
                "JS Reference Error",
                None,
            ),
            (
                re.compile(r"TypeError: (.*?) is not a function"),
                "你試圖呼叫的 '{0}' 不是一個函式。請檢查它是否被正確賦值，或者是不是還沒定義。",
                "JS Type Error (Not a function)",
                None,
            ),
            (
                re.compile(r"TypeError: Cannot read properties of (null|undefined)"),
                "試圖讀取空值 (null/undefined) 的屬性。請檢查變數是否已初始化，或使用 Optional Chaining (?.)。",
                "JS Null Pointer Access",
                None,
            ),
            (
                re.compile(r"SyntaxError: Unexpected token"),
                "JS/TS 語法錯誤。通常是多了或少了符號 (例如括號、分號)，或是在不該出現的地方寫了程式碼。",
                "JS Syntax Error",
                None,
            ),
        ]

    def translate(self, error_message: str) -> ErrorExplanation:
        for pattern, friendly_tmpl, tech_summary, fix_tmpl in self.patterns:
            match = pattern.search(error_message)
            if match:
                # Extract groups for formatting
                groups = match.groups()
                friendly_msg = friendly_tmpl.format(*groups)
                fix_cmd = fix_tmpl.format(*groups) if fix_tmpl else None

                return ErrorExplanation(
                    original_error=error_message,
                    friendly_message=friendly_msg,
                    technical_summary=tech_summary,
                    fix_command=fix_cmd,
                )

        return ErrorExplanation(
            original_error=error_message,
            friendly_message="發生了一個錯誤，但我目前無法精確翻譯。請參考下方的原始錯誤訊息。",
            technical_summary="Unknown error",
        )
