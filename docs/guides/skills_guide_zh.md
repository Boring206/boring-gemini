# Agent Skills 指南 (Universal System)

## 概覽

Boring V12.3 推出了 **通用技能系統 (Universal Skills System, BUSS)**。此系統統一了跨多個 AI 平台的技能管理，讓您可以在 **Gemini CLI**、**Claude Code**、**Antigravity** 和 **Boring Flow** 中使用相同的技能。

### 主要功能

1.  **一次編寫，處處運行**：使用標準 Markdown (`SKILL.md`) 編寫的技能可在所有支援的平台上運作。
2.  **本地「大腦」**：技能儲存在您的專案本地，賦予 Agent 持久且專屬於專案的專業知識。
3.  **自動同步**：透過 Boring 建立或下載的技能會自動同步到 `.gemini/skills` 和 `.claude/skills` 目錄。
4.  **Flow 整合**：Boring Flow Engine 在自主執行期間會自動發現並使用這些技能。

---

## 通用技能結構 (Universal Skill Structure)

通用技能只是一個包含帶有 YAML 前言 (frontmatter) 標頭的 `SKILL.md` 檔案的目錄。

**檔案路徑**：`.boring/skills/my-skill/SKILL.md`

```markdown
---
name: my-skill
description: 清楚描述此技能的功能。Agent 會使用此描述來決定何時激活它。
---

# 我的技能標題

## 指引 (Instructions)
1. 步驟一...
2. 步驟二...

## 規則 (Rules)
- 務必做 X...
- 絕不做 Y...
```

### 進階目錄結構 (OpenAI Codex / SkillsMP 相容)

對於更複雜的技能，您可以使用 Boring 自動偵測的標準目錄結構：

```text
my-skill/
├── SKILL.md        (必要：指引與元數據)
├── scripts/        (可選：可執行的 Python/Bash 腳本)
├── references/     (可選：PDF/文字文件)
└── assets/         (可選：範本、圖片、資源)
```

**Boring 會自動公開：**
- `scripts/` 中的腳本會列在激活提示詞 (prompt) 中。
- `references/` 中的文件會列為可用的上下文。


---

## 管理技能

### 1. 發現技能
Boring 會自動掃描以下目錄中的技能：
- `.boring/skills/` (主要樞紐 Hub)
- `.antigravity/skills/`
- `.gemini/skills/`
- `.claude/skills/`

使用指令 (或讓 Agent 使用)：
```python
boring_skill_discover()
```

### 2. 建立技能
您可以要求 Agent 為您建立技能：
> "Create a skill for reviewing python code security" (建立一個審查 python 代碼安全的技能)

或者使用上面的範本手動建立。

### 3. 下載技能 ("App Store")
您可以從受信任的社群存儲庫下載經過驗證的技能：

```python
boring_skill_download(url="https://github.com/boring-stack/skill-python-expert")
```

這將會：
1. 下載技能到 `.boring/skills/python-expert`
2. **自動同步**：將其複製到 `.gemini/skills/` 和 `.claude/skills/`，以便您的其他工具也能使用！

### 4. 直接激活
Agent 可以根據需求動態激活技能：

```python
boring_skill_activate(skill_name="code-reviewer")
```

---

## 最佳實踐

- **描述性名稱**：使用連字符命名法 (hyphen-case) (例如 `api-designer`, `bug-hunter`)。
- **清晰的描述**：前言中的 `description` 欄位是 **最重要** 的部分。這是 AI 在載入完整技能之前「看到」的內容。請務必精確。
- **原子化專業知識**：保持技能專注於單一領域或任務。

## 舊版目錄 (Legacy Catalog)
舊版的 `Boring Skills Catalog` (`boring_skills_install`) 仍然可用，以保持向後相容性，並用於發現基於外部工具的擴充功能。
