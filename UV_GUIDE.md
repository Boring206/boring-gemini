# 🚀 UV 快速使用指南

## 安裝 uv

```powershell
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 常用命令

### 專案設置
```bash
# 同步安裝所有依賴
uv sync

# 安裝專案 (可編輯模式)
uv pip install -e .

# 安裝所有依賴 (包含開發和 GUI)
uv pip install -e ".[dev,gui]"
```

### 開發工作流程
```bash
# 運行測試
uv run pytest

# 運行測試並顯示覆蓋率
uv run pytest --cov=src/boring --cov-report=html

# Linting 和格式化
uv run ruff check .
uv run ruff format .

# 運行 MkDocs 文檔伺服器
uv run mkdocs serve

# 部署文檔到 GitHub Pages
uv run mkdocs gh-deploy
```

### 運行 Boring 命令
```bash
# 顯示幫助
uv run boring --help

# 運行 dashboard
uv run boring dashboard

# 健康檢查
uv run boring health

# 自動修復
uv run boring auto-fix
```

### 依賴管理
```bash
# 添加新依賴
uv add <package-name>

# 添加開發依賴
uv add --dev <package-name>

# 移除依賴
uv remove <package-name>

# 更新所有依賴
uv pip install --upgrade -e ".[dev,gui]"

# 列出已安裝的包
uv pip list

# 檢查過時的包
uv pip list --outdated
```

### 虛擬環境管理
```bash
# 創建虛擬環境
uv venv

# 激活虛擬環境 (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 激活虛擬環境 (Windows CMD)
.venv\Scripts\activate.bat

# 停用虛擬環境
deactivate
```

## 為什麼使用 uv？

✅ **速度快** - 比 pip 快 10-100 倍  
✅ **兼容性好** - 完全兼容 pip 和 PyPI  
✅ **內存效率** - 使用 Rust 編寫，內存佔用小  
✅ **依賴解析** - 更智能的依賴解析算法  
✅ **跨平台** - Windows、macOS、Linux 完美支持  

## 實用技巧

### 快速開發環境設置
```bash
# 一鍵設置開發環境
uv venv && .venv\Scripts\Activate.ps1 && uv pip install -e ".[dev,gui]"
```

### CI/CD 使用
```bash
# 在 CI 中使用 uv 加速安裝
uv pip install --no-cache -e ".[dev]"
```

### 鎖定依賴版本
```bash
# 生成鎖定文件
uv pip freeze > requirements-lock.txt

# 從鎖定文件安裝
uv pip install -r requirements-lock.txt
```

## 遷移到 uv

如果您之前使用 pip，可以無縫切換：

```bash
# pip install -r requirements.txt
uv pip install -r requirements.txt

# pip install package
uv pip install package

# pip list
uv pip list
```

所有 pip 命令只需將 `pip` 替換為 `uv pip` 即可！

## 疑難排解

### 如果 uv 找不到
```powershell
# 重新載入 PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### 清除快取
```bash
uv cache clean
```

## 更多資源

- 官方文檔: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
