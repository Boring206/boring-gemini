# 插件開發指南

> 使用自定義 Python 工具擴充 Boring 的功能。
> 
> **解決風險**: 功能膨脹 - 鼓勵外部插件而非核心功能擴展

---

## 🛠️ 概述

Boring 具備動態插件系統，允許您將自定義 Python 函數註冊為 AI 可呼叫的工具。插件可以是專案專用或全域通用的。

### 為什麼使用插件？

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         插件 vs 核心功能                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────┐   ┌─────────────────────────────┐         │
│   │       🎯 核心功能            │   │       🔌 插件                │         │
│   ├─────────────────────────────┤   ├─────────────────────────────┤         │
│   │ • 所有用戶都需要             │   │ • 特定場景使用               │         │
│   │ • 穩定的 API                │   │ • 實驗性功能                 │         │
│   │ • 由核心團隊維護            │   │ • 社區或個人維護             │         │
│   │ • 嚴格的質量要求            │   │ • 快速迭代                   │         │
│   └─────────────────────────────┘   └─────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 插件存放位置
1.  **專案本地**：`{project_root}/.boring_plugins/`
2.  **使用者全域**：`~/.boring/plugins/`

---

## 📝 建立插件

要建立插件，請定義一個 Python 函數並使用 `@plugin` 裝飾器。

### 基本範例：`my_tool_plugin.py`

```python
from boring.plugins.loader import plugin

@plugin(
    name="my_custom_linter",
    description="針對特定業務邏輯的自定義 Lint 規則",
    version="1.0.0",
    author="Vibe Coder",
    tags=["lint", "custom"]
)
def my_custom_linter(file_path: str) -> dict:
    """
    分析檔案中是否存在自定義模式。
    """
    # 在這裡實作您的邏輯
    content = open(file_path).read().lower()
    if "todo" in content:
        return {"passed": False, "issues": ["發現尚未處理的 TODO"]}
    
    return {"passed": True, "issues": []}
```

---

## 🏗️ 進階插件架構

### 帶有配置的插件

```python
from pathlib import Path
from typing import Optional
from boring.plugins.loader import plugin

# 插件可以有自己的配置
PLUGIN_CONFIG = {
    "max_line_length": 120,
    "ignored_patterns": ["*.test.py", "*_mock.py"],
}

@plugin(
    name="configurable_linter",
    description="可配置的代碼風格檢查器",
    version="1.0.0",
    author="Your Name",
    tags=["lint", "configurable"]
)
def configurable_linter(
    file_path: str,
    max_line_length: Optional[int] = None,
) -> dict:
    """
    根據配置檢查代碼風格。
    
    Args:
        file_path: 要檢查的檔案路徑
        max_line_length: 覆蓋默認行長限制
        
    Returns:
        包含檢查結果的字典
    """
    line_limit = max_line_length or PLUGIN_CONFIG["max_line_length"]
    
    issues = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if len(line.rstrip()) > line_limit:
                issues.append(f"Line {i}: exceeds {line_limit} characters")
    
    return {
        "status": "PASS" if not issues else "FAIL",
        "file": file_path,
        "issues": issues,
        "config_used": {"max_line_length": line_limit},
    }
```

### 帶有外部依賴的插件

```python
from boring.plugins.loader import plugin

# 安全地導入可選依賴
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

@plugin(
    name="csv_analyzer",
    description="分析 CSV 檔案的統計資訊 (需要 pandas)",
    version="1.0.0",
    author="Data Team",
    tags=["data", "csv", "analysis"]
)
def csv_analyzer(file_path: str) -> dict:
    """
    分析 CSV 檔案並返回統計摘要。
    
    注意：此插件需要 pandas 庫。
    安裝：pip install pandas
    """
    if not PANDAS_AVAILABLE:
        return {
            "status": "ERROR",
            "error": "pandas not installed. Run: pip install pandas",
        }
    
    try:
        df = pd.read_csv(file_path)
        return {
            "status": "SUCCESS",
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
```

### 帶有 LLM 調用的插件

```python
from boring.plugins.loader import plugin
from boring.config import settings

@plugin(
    name="smart_summarizer",
    description="使用 LLM 智能摘要文件",
    version="1.0.0",
    author="AI Team",
    tags=["ai", "summarization"]
)
def smart_summarizer(file_path: str, max_words: int = 100) -> dict:
    """
    使用 AI 生成文件摘要。
    
    Args:
        file_path: 要摘要的檔案
        max_words: 摘要最大字數
    """
    from boring.llm import get_llm_provider
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        provider = get_llm_provider()
        if not provider.is_available:
            return {"status": "ERROR", "error": "No LLM provider available"}
        
        prompt = f"請用不超過 {max_words} 字摘要以下內容：\n\n{content[:5000]}"
        summary, success = provider.generate(prompt)
        
        if success:
            return {"status": "SUCCESS", "summary": summary}
        else:
            return {"status": "ERROR", "error": summary}
            
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
```

---

## 🚀 載入與熱重載 (Hot-Reload)

- **自動發現**：位於搜尋路徑中的任何 `.py` 或以 `_plugin.py` 結尾的檔案都會被自動發現。
- **熱重載**：Boring 會監控插件檔案。如果您在循環執行期間修改插件，系統會在下一次迭代時自動載入新邏輯。

---

## 🔍 使用插件

載入後，您的插件會像內建工具一樣提供給 AI 代理使用。代理會透過語義搜尋或工具列表發現它。

### CLI 命令

```bash
# 列出目前已載入的插件
boring list-plugins

# 重新載入所有插件
boring reload-plugins

# 執行特定插件
boring run-plugin my_custom_linter --file-path src/main.py
```

### MCP 工具

```
boring_list_plugins    # 列出插件
boring_reload_plugins  # 重新載入
boring_run_plugin      # 執行插件
```

---

## 🧪 測試插件

### 單元測試範例

```python
# tests/plugins/test_my_plugin.py
import pytest
from pathlib import Path

# 直接導入插件函數
from my_tool_plugin import my_custom_linter

class TestMyCustomLinter:
    def test_pass_no_todo(self, tmp_path):
        """測試沒有 TODO 時通過"""
        test_file = tmp_path / "clean.py"
        test_file.write_text("def hello(): pass")
        
        result = my_custom_linter(str(test_file))
        
        assert result["passed"] is True
        assert result["issues"] == []
    
    def test_fail_with_todo(self, tmp_path):
        """測試有 TODO 時失敗"""
        test_file = tmp_path / "dirty.py"
        test_file.write_text("# TODO: fix this")
        
        result = my_custom_linter(str(test_file))
        
        assert result["passed"] is False
        assert len(result["issues"]) > 0
```

---
 
## 🛡️ 安全與防護 (Security & Safety)

插件（特別是透過 `boring_synth_tool` 生成的工具）受到嚴格的安全約束：

1.  **AST 沙箱驗證**：所有即時合成的工具都會通過 `SynthesizedToolValidator` 進行語法樹掃描。
2.  **禁用操作**：為了防止破壞性行為，沙箱會封鎖：
    - **禁止導入**：`os`, `sys`, `subprocess`, `shutil`, `socket`
    - **禁止函數**：`exec()`, `eval()`, `open()`, `compile()`
3.  **影子模式綁定**：所有插件執行都受 **影子模式 (Shadow Mode)** 監控，為檔案操作提供第二層防線。

---

## 📦 發布插件

### 作為 Python 包發布

```python
# setup.py 或 pyproject.toml
[project]
name = "boring-plugin-mytools"
version = "1.0.0"
dependencies = ["boring-aicoding>=11.0.0"]

[project.entry-points."boring.plugins"]
my_tool = "boring_plugin_mytools:my_tool"
```

### 社區插件倉庫

我們歡迎社區貢獻插件！請：
1. 創建獨立的 Git 倉庫
2. 遵循命名約定：`boring-plugin-{name}`
3. 提交 Issue 將您的插件添加到官方列表

---

## 💡 最佳實踐

1.  **型別提示 (Type Hints)**：務必為參數提供型別提示，這能幫助 LLM 理解輸入要求。
2.  **文檔字串 (Docstrings)**：提供清晰、具描述性的文檔字串，因為 AI 依靠這些資訊決定何時呼叫該工具。
3.  **回傳格式**：回傳結構化數據（dict）而非純字串，以便代理進行後續處理。
4.  **錯誤處理**：總是返回 `{"status": "ERROR", "error": "..."}` 而不是拋出異常。
5.  **可選依賴**：使用 try/except 導入可選依賴，提供友好的錯誤訊息。
6.  **版本管理**：使用語義化版本號標記您的插件。

---

## 🔗 相關文檔

- [功能矩陣](../reference/feature-matrix.md) - 了解核心功能 vs 插件的定位
- [LLM 適配器指南](../reference/llm-adapters.md) - 如果您的插件需要 LLM
- [貢獻指南](../reference/contributing.md) - 如果您想將插件貢獻給核心
