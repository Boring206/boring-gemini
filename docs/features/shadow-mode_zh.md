# 影子模式 - 安全沙箱

> 影子模式是 Boring 的安全核心，為所有潛在破壞性操作提供人機協作保護。

---

> **✨ Vibe Coder 相容**: Shadow Mode 會攔截 **所有** 工具呼叫，包括透過 Vibe Coder (`boring()`) 或 CLI (`boring-route`) 發出的請求。

## 🛡️ 什麼是影子模式？

影子模式作為 AI 和檔案系統之間的**強制攔截層**。啟用時，它會：

1. **攔截** 所有破壞性操作（檔案寫入、刪除、命令執行）
2. **評估** 每個操作的影響
3. **排隊** 高風險操作等待批准
4. **要求** 人工確認後才執行

```
┌─────────────────────────────────────────────────────────┐
│                     AI 代理                              │
│                        │                                │
│                        ▼                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │              🛡️ 影子模式                         │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  風險評估器                                 │  │  │
│  │  │  ├─ 低風險 → 自動批准                      │  │  │
│  │  │  ├─ 中風險 → 記錄並執行                    │  │  │
│  │  │  └─ 高風險 → 🚨 需要批准                  │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │                     │                            │  │
│  │        待處理佇列（僅高風險）                     │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                │
│                        ▼                                │
│                   檔案系統                              │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 三種保護級別

| 級別 | 符號 | 行為 | 最適合 |
|------|------|------|--------|
| `DISABLED` | ⚠️ | 無攔截 | 僅限隔離容器 |
| `ENABLED` | 🛡️ | 自動批准低風險，阻擋高風險 | **預設 - 平衡** |
| `STRICT` | 🔒 | 攔截所有寫入操作 | 生產環境 |

### 級別詳情

#### DISABLED（⚠️ 謹慎使用）
```python
boring_shadow_mode(action="set_level", level="DISABLED")
```
- 不攔截任何操作
- 所有寫入立即執行
- **僅在隔離容器或沙箱中使用**

#### ENABLED（🛡️ 建議預設值）
```python
boring_shadow_mode(action="set_level", level="ENABLED")
```
- **自動批准**：讀取操作、小型檔案編輯
- **記錄**：中風險變更（新檔案 < 1KB）
- **阻擋**：刪除、系統檔案、大型重寫

#### STRICT（🔒 最高安全性）
```python
boring_shadow_mode(action="set_level", level="STRICT")
```
- **所有**寫入操作都需要批准
- 適合生產代碼審查
- 無法透過代理補丁繞過

---

## 🔧 配置與持久化

### 跨會話持久化

影子模式設定持久保存在 `~/.boring_brain/shadow_config.json`：

```json
{
  "level": "STRICT",
  "auto_approve_patterns": ["*.md", "docs/*"],
  "always_block_patterns": ["*.env", "secrets/*"],
  "last_updated": "2024-01-01T12:00:00Z"
}
```

### MCP 配置

在 `smithery.yaml` 或 MCP 配置中：

```yaml
SHADOW_MODE_LEVEL: "STRICT"    # DISABLED|ENABLED|STRICT
BORING_ALLOW_DANGEROUS: false  # 生產環境絕不設為 true
```

---

## 💻 工具參考

### 檢查狀態
```python
boring_shadow_mode(action="status")
# 返回: {"level": "ENABLED", "pending_count": 2}
```

### 設定級別
```python
boring_shadow_mode(action="set_level", level="STRICT")
```

### 查看待處理操作
```python
boring_shadow_mode(action="list_pending")
# 返回等待批准的操作列表
```

### 批准/拒絕
```python
boring_shadow_mode(action="approve", operation_id="op_123")
boring_shadow_mode(action="reject", operation_id="op_123")
```

---

## 🎯 風險分類

### 低風險（ENABLED 模式自動批准）
- 讀取檔案
- 列出目錄
- 查看 git 狀態
- 執行唯讀命令

### 中風險（記錄並執行）
- 建立小型檔案（< 1KB）
- 附加到現有檔案
- 執行測試

### 高風險（需要批准）
- ❌ 刪除檔案
- ❌ 修改系統檔案（`.env`、`config/*`）
- ❌ 大型檔案重寫（> 50% 內容變更）
- ❌ 執行有副作用的 shell 命令
- ❌ Git 操作（push、強制操作）

---

## 🔐 受保護的檔案工具（V10.17.5+）

為確保影子模式保護，請使用 Boring 的檔案工具：

```python
# 這些工具總是遵守影子模式
boring_write_file(path="config.py", content="...")
boring_read_file(path="src/main.py")
```

> ⚠️ **警告**：原生 MCP 工具如 `write_file`（部分客戶端提供）可能不會被影子模式攔截。請始終使用 `boring_write_file` 進行安全操作。

---

## 🏢 企業使用案例

### 代碼審查工作流程
```python
# 審查者設定 STRICT 模式
boring_shadow_mode(action="set_level", level="STRICT")

# AI 提出變更，全部排隊等待審查
# 審查者檢查每個待處理操作
# 僅批准已驗證的變更
```

### CI/CD 整合
```yaml
# 在 CI 管道中
- name: 使用影子模式執行 Boring
  env:
    SHADOW_MODE_LEVEL: ENABLED
    BORING_ALLOW_DANGEROUS: false
```

---

## 另請參閱

- [MCP 工具](./mcp-tools_zh.md) - 工具參考
- [品質閘道](./quality-gates_zh.md) - CI/CD 整合
- [專業技巧](../guides/pro-tips_zh.md) - 安全最佳實踐
