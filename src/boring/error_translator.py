import re
from dataclasses import dataclass
from re import Pattern


@dataclass
class ErrorExplanation:
    original_error: str
    friendly_message: str
    technical_summary: str
    fix_command: str | None = None
    complexity: str = "Low"


class ErrorTranslator:
    def __init__(self):
        # Patterns: (Regex, Friendly Message Template, Technical Summary, Fix Command Template)
        self.patterns: list[tuple[Pattern, str, str, str | None]] = [
            (
                re.compile(r"requests\.exceptions\.(ConnectionError|ConnectTimeout|ReadTimeout)"),
                "網路連線失敗。如果你開啟了離線模式 (Offline Mode)，請確認你沒有嘗試呼叫外部 API。若需連網，請檢查網路狀態或代理設定。",
                "Network Error",
                "boring doctor",
            ),
            (
                re.compile(r"google\.api_core\.exceptions\.(Unauthenticated|PermissionDenied)"),
                "Google Gemini API 認證失敗。請檢查你的 GEMINI_API_KEY 是否正確，或是否過期。",
                "Auth Error",
                "boring wizard",
            ),
            (
                re.compile(r"(ResourceExhausted|429 Too Many Requests)"),
                "API 請求次數過多 (Rate Limit)。請稍候再試，或切換到付費方案。",
                "Rate Limit Exceeded",
                None,
            ),
            # === V14.0 Features ===
            (
                re.compile(r"Model '(.*?)' not found"),
                "找不到本地 LLM 模型 '{0}'。請先下載模型才能在離線模式使用。",
                "Local Model Missing",
                "boring model download {0}",
            ),
            (
                re.compile(r"FastMCP error:"),
                "MCP 伺服器內部錯誤。可能是工具註冊失敗或參數型別不符。",
                "MCP Server Error",
                "boring doctor",
            ),
            # === Config & Environment ===
            (
                re.compile(r"pydantic_settings\.exceptions\.SettingsError"),
                "設定檔載入失敗。請檢查 .env 檔案格式是否正確。",
                "Configuration Error",
                "boring doctor",
            ),
            (
                re.compile(r"tomllib\.TOMLDecodeError"),
                "解析 pyproject.toml 失敗。文件格式可能有錯，請檢查語法。",
                "TOML Parse Error",
                None,
            ),
            # === Python Specific ===
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
            # === Git Errors (V14.6) ===
            (
                re.compile(r"git\.exc\.InvalidGitRepositoryError"),
                "這不是一個 Git 倉庫。請先執行 `git init` 初始化，或者確認你是否在正確的專案目錄下。",
                "Not a Git Repository",
                "git init",
            ),
            (
                re.compile(r"git\.exc\.GitCommandError:.*pathspec.*did not match any file"),
                "Git 找不到指定的檔案。請確認檔案是否已經被 commit，或者拼字是否正確。",
                "Git File Not Found",
                None,
            ),
            # === System & Permissions ===
            (
                re.compile(r"PermissionError: \[Errno 13\] Permission denied: '(.*?)'"),
                "權限不足，無法存取 '{0}'。請嘗試以管理員身分執行，或檢查檔案權限設定。",
                "Permission Denied",
                None,
            ),
            (
                re.compile(r"OSError: \[Errno 28\] No space left on device"),
                "磁碟空間不足！請清理一些舊檔案或暫存檔。",
                "Disk Full",
                "boring clean --all",
            ),
            # === V15.0 Resilience ===
            (
                re.compile(r"UnicodeDecodeError:"),
                "檔案編碼錯誤。試圖讀取非 UTF-8 格式的檔案。這通常發生在讀取中文舊專案 (Big5/CP950) 時。",
                "Encoding Error",
                None,
            ),
            (
                re.compile(r"json\.decoder\.JSONDecodeError"),
                "JSON 解析失敗。設定檔或回應格式有誤，可能是多了逗號或引號未閉合。",
                "JSON Error",
                "boring doctor",
            ),
            (
                re.compile(r"RecursionError: maximum recursion depth exceeded"),
                "遞迴過深 (Stack Overflow)。可能是程式寫了無窮迴圈的函式呼叫。",
                "Recursion Error",
                None,
            ),
            (
                re.compile(r"(WinError 32|Check your file permissions)"),
                "檔案被鎖定 (WinError 32)。另一個程式正在使用這個檔案。請暫時關閉 VS Code 或防毒軟體後重試。",
                "File Locked",
                None,
            ),
            (
                re.compile(r"KeyboardInterrupt"),
                "使用者手動中斷。任務已取消。",
                "User Interrupted",
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
