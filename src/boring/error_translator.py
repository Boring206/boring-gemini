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
            (
                re.compile(r"FileNotFoundError: \[Errno 2\] No such file or directory: '(.*?)'"),
                "找不到檔案 '{0}'。請檢查路徑是否正確，或者是檔案不小心被移動、刪除了。",
                "File Not Found",
                None,
            ),
            (
                re.compile(r"(?:❌\s*)?找不到(檔案|目標)[\s：:]*(.*)"),
                "找不到你要處理的檔案或目錄 '{1}'。請確認檔案路徑是否正確（是相對路徑還是絕對路徑？）。",
                "File Not Found (Boring UI)",
                None,
            ),
            (
                re.compile(r"❌ 不支援的(檔案類型|格式): (.*)"),
                "目前還不支援 '{1}' 這種格式。目前我比較擅長處理 Python (.py)、JavaScript (.js, .jsx) 和 TypeScript (.ts, .tsx) 喔！",
                "Unsupported File Type",
                None,
            ),
            (
                re.compile(r"😅 沒有找到可測試的導出函式或類別"),
                "在這個檔案裡沒看到可以寫測試的東西（例如 function 或 class）。請確認你有沒有寫 export，或是檔案內容是否完整。",
                "No Testable Content",
                None,
            ),
            (
                re.compile(r"⚠️ 找不到可分析的程式碼檔案"),
                "在這個目錄下找不到我可以處理的程式碼 (Python, JS, TS)。請確認目標路徑是否正確。",
                "No Code Files Found",
                None,
            ),
            (
                re.compile(r"❌ (分析|審查)失敗: (.*)"),
                "哎呀，我在處理程式碼時卡住了。原始錯誤是：{1}。這通常是檔案太大或格式太亂導致的。",
                "Tool Execution Failure",
                None,
            ),
            (
                re.compile(r"Storage 未初始化"),
                "智能記憶系統 (Storage) 尚未啟動。這是進階功能，如果你想啟用歷史追蹤，請確認專案根目錄有 `.boring_memory` 資料夾。不過，這個功能是選配的，不影響主要工具運作。",
                "Storage Not Initialized",
                None,
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
