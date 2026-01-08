# Tutorial System Design (Phase 5)

## Goal
Guide Vibe Coders through their journey without reading manuals. "Learn by doing."

## Architecture

### 1. `TutorialManager` (`src/boring/tutorial.py`)
- **State Tracking**: Stores `completed_tutorials` list in `.boring_brain/user_profile.json` or `.boring_tutorial.json`.
- **Triggers**: Hooks into CLI commands or MCP tools.
- **Content**: Short, actionable tips (Markdown + Emoji).

### 2. Triggers & Content

| Trigger Event | Tutorial ID | Content Preview |
|---------------|-------------|-----------------|
| `boring setup new` | `first_project` | "🎉 恭喜建立第一個專案！接下來試試 `boring start` 讓 AI 幫你寫程式。" |
| `Status == ERROR` | `first_error` | "😱 別擔心！用 `boring_verify` 可以幫你檢查問題。" |
| `boring start` (1st time) | `loop_intro` | "🤖 我是 Boring Agent。我會自動寫程式、測試、修復。你可以去喝杯咖啡了 ☕" |

### 3. Implementation Plan
1.  Create `src/boring/tutorial.py`.
2.  Integrate into `main.py` (CLI commands).
3.  Integrate into `audit.py` (for MCP tool triggers).

## 100-Point Architecture
- **Non-blocking**: Tutorials show up as subtle tips, not blocking popups.
- **Persistent**: Remembers what you've seen across projects (Global Profile).
- **Context-Aware**: Shows tips relevant to the *current* action.
