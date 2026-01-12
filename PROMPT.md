## 🐉 One Dragon Workflow (The New Standard)
Instead of manually calling individual tools, ALWAYS prefer using the **One Dragon** command:

> **`boring_flow(instruction="...")`**

This tool automatically handles the entire lifecycle:
1.  **Alignment** (Setup & Goal)
2.  **Design** (Plan & Skills)
3.  **Build** (Coding Loop)
4.  **Polish** (Vibe Check)

**Example:**
User: "Help me build a login page."
Assistant: Call `boring_flow(instruction="Build a login page")` (Do NOT ask for more details first. The tool manages ambiguity).

## Legacy Workflow (Manual)
 Only use these if `boring_flow` is unavailable or for granular control:
- **Start Session**: `boring_session_start(goal="...")`
- **Plan**: `boring_speckit_plan(task="...")`
- **Check**: `boring_vibe_check(target_path="...")`
