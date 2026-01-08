# 插件開發指南

> 使用自定義 Python 工具擴充 Boring 的功能。

---

## 🛠️ 概述

Boring 具備動態插件系統，允許您將自定義 Python 函數註冊為 AI 可呼叫的工具。插件可以是專案專用或全域通用的。

### 插件存放位置
1.  **專案本地**：`{project_root}/.boring_plugins/`
2.  **使用者全域**：`~/.boring/plugins/`

---

## 📝 建立插件

要建立插件，請定義一個 Python 函數並使用 `@plugin` 裝飾器。

### 範例：`my_tool_plugin.py`

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

## 🚀 載入與熱重載 (Hot-Reload)

- **自動發現**：位於搜尋路徑中的任何 `.py` 或以 `_plugin.py` 結尾的檔案都會被自動發現。
- **熱重載**：Boring 會監控插件檔案。如果您在循環執行期間修改插件，系統會在下一次迭代時自動載入新邏輯。

---

## 🔍 使用插件

載入後，您的插件會像內建工具一樣提供給 AI 代理使用。代理會透過語義搜尋或工具列表發現它。

列出目前已載入的插件：
```bash
boring list-plugins
```

---

## 💡 最佳實踐

1.  **型別提示 (Type Hints)**：務必為參數提供型別提示，這能幫助 LLM 理解輸入要求。
2.  **文檔字串 (Docstrings)**：提供清晰、具描述性的文檔字串，因為 AI 依靠這些資訊決定何時呼叫該工具。
3.  **回傳格式**：回傳結構化數據（dict）而非純字串，以便代理進行後續處理。
