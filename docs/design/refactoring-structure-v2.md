# Boring-Gemini 專案結構重構計劃 V2

> **建立日期**: 2026-01-09  
> **目標**: 將 `src/boring/` 頂層 45+ 個檔案精簡至 ~15 個

---

## 📊 重構概覽

```
重構前                              重構後
src/boring/                         src/boring/
├── 45+ 個 .py 檔案 😵             ├── ~15 個核心 .py 檔案 ✅
├── 11 個子目錄                    ├── 16 個子目錄
└── 混合粒度                       └── 清晰分層
```

---

## 🎯 階段式重構計劃

### 階段 1：移入現有目錄（低風險）⭐ 推薦先做

**目標：減少 12 個頂層檔案，無需創建新目錄**

| 檔案 | 目標目錄 | 理由 |
|------|----------|------|
| `rubrics.py` | `judge/` | 評分標準屬於判斷系統 |
| `brain_manager.py` | `intelligence/` | 大腦管理屬於智能模組 |
| `feedback_learner.py` | `intelligence/` | 學習功能 |
| `auto_learner.py` | `intelligence/` | 自動學習 |
| `pattern_mining.py` | `intelligence/` | 模式挖掘 |
| `memory.py` | `intelligence/` | 記憶管理 |
| `vector_memory.py` | `intelligence/` | 向量記憶 |
| `shadow_mode.py` | `loop/` | 影子模式屬於工作流 |
| `workflow_manager.py` | `loop/` | 工作流管理 |
| `workflow_evolver.py` | `loop/` | 工作流演進 |
| `background_agent.py` | `loop/` | 後台代理 |
| `transactions.py` | `loop/` | 事務管理 |

**執行命令**:
```powershell
# 在 src/boring/ 目錄下執行
# 移動到 intelligence/
Move-Item brain_manager.py intelligence/
Move-Item feedback_learner.py intelligence/
Move-Item auto_learner.py intelligence/
Move-Item pattern_mining.py intelligence/
Move-Item memory.py intelligence/
Move-Item vector_memory.py intelligence/

# 移動到 loop/
Move-Item shadow_mode.py loop/
Move-Item workflow_manager.py loop/
Move-Item workflow_evolver.py loop/
Move-Item background_agent.py loop/
Move-Item transactions.py loop/

# 移動到 judge/
Move-Item rubrics.py judge/
```

---

### 階段 2：創建 `infra/` 目錄

**目標：減少 7 個頂層檔案**

| 檔案 | 說明 |
|------|------|
| `storage.py` | 存儲管理 |
| `cache.py` | 緩存系統 |
| `backup.py` | 備份功能 |
| `logger.py` | 日誌系統 |
| `limiter.py` | 限流器 |
| `streaming.py` | 流式處理 |
| `circuit.py` | 熔斷器 |

**執行命令**:
```powershell
# 創建目錄
New-Item -ItemType Directory -Path infra

# 創建 __init__.py
@"
"""基礎設施模組"""
from .storage import *
from .cache import *
from .logger import *
from .limiter import *
"@ | Out-File -FilePath infra/__init__.py -Encoding utf8

# 移動檔案
Move-Item storage.py infra/
Move-Item cache.py infra/
Move-Item backup.py infra/
Move-Item logger.py infra/
Move-Item limiter.py infra/
Move-Item streaming.py infra/
Move-Item circuit.py infra/
```

---

### 階段 3：創建 `monitoring/` 目錄

**目標：減少 6 個頂層檔案**

| 檔案 | 說明 |
|------|------|
| `monitor.py` | 主監控器 |
| `health.py` | 健康檢查 |
| `dashboard.py` | 儀表板 |
| `web_monitor.py` | Web 監控 |
| `audit.py` | 審計日誌 |
| `quality_tracker.py` | 品質追蹤 |

**執行命令**:
```powershell
New-Item -ItemType Directory -Path monitoring

@"
"""監控與審計模組"""
from .monitor import *
from .health import *
from .audit import *
"@ | Out-File -FilePath monitoring/__init__.py -Encoding utf8

Move-Item monitor.py monitoring/
Move-Item health.py monitoring/
Move-Item dashboard.py monitoring/
Move-Item web_monitor.py monitoring/
Move-Item audit.py monitoring/
Move-Item quality_tracker.py monitoring/
```

---

### 階段 4：創建 `clients/` 目錄

**目標：減少 5 個頂層檔案**

| 檔案 | 說明 |
|------|------|
| `gemini_client.py` | Gemini API 客戶端 |
| `cli_client.py` | CLI 客戶端 |
| `interactions_client.py` | 互動客戶端 |
| `interactive.py` | 互動模式 |
| `vscode_server.py` | VS Code 服務器 |

**執行命令**:
```powershell
New-Item -ItemType Directory -Path clients

@"
"""客戶端連接模組"""
from .gemini_client import *
"@ | Out-File -FilePath clients/__init__.py -Encoding utf8

Move-Item gemini_client.py clients/
Move-Item cli_client.py clients/
Move-Item interactions_client.py clients/
Move-Item interactive.py clients/
Move-Item vscode_server.py clients/
```

---

### 階段 5：創建 `patching/` 目錄

**目標：減少 6 個頂層檔案**

| 檔案 | 說明 |
|------|------|
| `diff_patcher.py` | Diff 修補 |
| `file_patcher.py` | 檔案修補 |
| `auto_fix.py` | 自動修復 |
| `error_diagnostics.py` | 錯誤診斷 |
| `error_translator.py` | 錯誤翻譯 |
| `debugger.py` | 調試器 |

**執行命令**:
```powershell
New-Item -ItemType Directory -Path patching

@"
"""代碼修補與錯誤處理模組"""
from .diff_patcher import *
from .file_patcher import *
from .auto_fix import *
"@ | Out-File -FilePath patching/__init__.py -Encoding utf8

Move-Item diff_patcher.py patching/
Move-Item file_patcher.py patching/
Move-Item auto_fix.py patching/
Move-Item error_diagnostics.py patching/
Move-Item error_translator.py patching/
Move-Item debugger.py patching/
```

---

### 階段 6：其他整理

```powershell
# 移動到 intelligence/
Move-Item context_selector.py intelligence/
Move-Item context_sync.py intelligence/
Move-Item response_analyzer.py intelligence/

# 移動到 verification/
Move-Item security.py verification/
Move-Item trust_rules.py verification/
```

---

## 📁 最終目錄結構

```
src/boring/
├── __init__.py          # 版本 + 向後兼容導出
├── __main__.py          # 入口點
├── main.py              # 主程式
├── config.py            # 配置
├── constants.py         # 常量
├── exceptions.py        # 異常
├── models.py            # 資料模型
├── interfaces.py        # 介面定義
├── utils.py             # 工具函數
├── core.py              # 核心引擎
├── setup.py             # 設置
├── quickstart.py        # 快速開始
├── extensions.py        # 擴展
├── hooks.py             # 鉤子
├── workspace.py         # 工作區
├── skills_catalog.py    # 技能目錄
├── tutorial.py          # 教程
│
├── agents/              # 代理系統 (已存在)
├── intelligence/        # 智能分析 (擴充)
│   ├── adaptive_cache.py
│   ├── brain_manager.py      # 新增
│   ├── memory.py             # 新增
│   ├── vector_memory.py      # 新增
│   └── ...
├── loop/                # 工作流循環 (擴充)
│   ├── agent.py
│   ├── shadow_mode.py        # 新增
│   ├── workflow_manager.py   # 新增
│   └── ...
├── rag/                 # RAG 系統 (已存在)
├── mcp/                 # MCP 服務 (已存在)
├── judge/               # 評判系統 (擴充)
│   ├── rubrics.py            # 新增
│   └── ...
├── verification/        # 驗證系統 (擴充)
│   ├── security.py           # 新增
│   ├── trust_rules.py        # 新增
│   └── ...
├── vibe/                # Vibe 功能 (已存在)
├── llm/                 # LLM 相關 (已存在)
├── plugins/             # 插件 (已存在)
├── templates/           # 模板 (已存在)
│
├── infra/               # 基礎設施 (新建)
│   ├── __init__.py
│   ├── storage.py
│   ├── cache.py
│   ├── backup.py
│   ├── logger.py
│   ├── limiter.py
│   ├── streaming.py
│   └── circuit.py
│
├── monitoring/          # 監控審計 (新建)
│   ├── __init__.py
│   ├── monitor.py
│   ├── health.py
│   ├── dashboard.py
│   ├── web_monitor.py
│   ├── audit.py
│   └── quality_tracker.py
│
├── clients/             # 客戶端 (新建)
│   ├── __init__.py
│   ├── gemini_client.py
│   ├── cli_client.py
│   ├── interactions_client.py
│   ├── interactive.py
│   └── vscode_server.py
│
└── patching/            # 修補系統 (新建)
    ├── __init__.py
    ├── diff_patcher.py
    ├── file_patcher.py
    ├── auto_fix.py
    ├── error_diagnostics.py
    ├── error_translator.py
    └── debugger.py
```

---

## 🔄 Import 更新指南

### 更新相對導入

每個移動的檔案內部的 import 需要更新：

```python
# 舊（在頂層時）
from .config import settings
from .logger import log_status

# 新（在子目錄時）
from ..config import settings
from ..infra.logger import log_status  # 如果 logger 在 infra/
# 或
from boring.config import settings     # 使用絕對導入
```

### 向後兼容層

在 `src/boring/__init__.py` 添加重新導出：

```python
__version__ = "10.26.0"

# 向後兼容 - 保持舊的導入路徑可用
# 這些將在 v12.0 中移除
from boring.infra.storage import StorageManager
from boring.infra.cache import CacheManager
from boring.infra.logger import log_status, get_logger
from boring.monitoring.monitor import SystemMonitor
from boring.clients.gemini_client import GeminiClient
# ... 其他需要向後兼容的導出

import warnings

def __getattr__(name):
    """支援舊路徑的動態導入"""
    deprecated_modules = {
        'storage': 'boring.infra.storage',
        'cache': 'boring.infra.cache',
        'logger': 'boring.infra.logger',
        # ...
    }
    if name in deprecated_modules:
        warnings.warn(
            f"Importing {name} from boring is deprecated. "
            f"Use {deprecated_modules[name]} instead.",
            DeprecationWarning,
            stacklevel=2
        )
        import importlib
        return importlib.import_module(deprecated_modules[name])
    raise AttributeError(f"module 'boring' has no attribute '{name}'")
```

---

## ✅ 驗證清單

每個階段完成後執行：

```powershell
# 1. 運行測試
cd d:\User\Desktop\ralphgeminicode\boring-gemini
pytest tests/ -v

# 2. 檢查導入
python -c "from boring import *; print('Import OK')"

# 3. 運行 linter
ruff check src/boring/

# 4. 測試 MCP 服務
python -m boring.mcp.server --help
```

---

## 📈 預期效果

| 指標 | 重構前 | 重構後 | 改善 |
|------|--------|--------|------|
| 頂層 .py 檔案 | 45+ | ~17 | -62% |
| 子目錄數量 | 11 | 16 | +45% |
| 平均目錄深度 | 1.5 | 2.0 | 更清晰 |
| 可維護性評分 | ★★★★ | ★★★★★ | +25% |

---

## ⏱️ 時間估算

| 階段 | 預計時間 | 風險等級 |
|------|----------|----------|
| 階段 1 | 2-3 小時 | 🟢 低 |
| 階段 2 | 1-2 小時 | 🟡 中 |
| 階段 3 | 1-2 小時 | 🟡 中 |
| 階段 4 | 1-2 小時 | 🟡 中 |
| 階段 5 | 1-2 小時 | 🟡 中 |
| 階段 6 | 1 小時 | 🟢 低 |
| 測試修復 | 2-4 小時 | 🟠 視情況 |
| 文檔更新 | 1 小時 | 🟢 低 |
| **總計** | **10-17 小時** | - |

---

## 🚀 建議執行順序

1. **先做階段 1** - 風險最低，效果明顯
2. **再做階段 2 (infra/)** - logger.py 被廣泛使用，統一管理
3. **階段 3-5 可並行規劃**
4. **每階段獨立 PR**，方便 Code Review

---

## 📝 注意事項

1. **備份**: 重構前確保 git 狀態乾淨，創建新分支
2. **測試**: 每移動一批檔案就運行測試
3. **CI/CD**: 確保 GitHub Actions 通過
4. **文檔**: 同步更新 ARCHITECTURE.md
5. **通知**: 如有其他開發者，提前告知結構變更
