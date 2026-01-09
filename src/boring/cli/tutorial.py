import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console(stderr=True)


class TutorialManager:
    """Manages interactive tutorials for Vibe Coders."""

    TUTORIALS = {
        "first_project": {
            "title": "🎉 恭喜建立第一個專案！",
            "content": "接下來試試 `boring start` 讓 AI 幫你寫程式，\n或是用 `boring start --cli` 使用隱私模式 (不需 API Key)。",
            "emoji": "🚀",
        },
        "loop_start": {
            "title": "🤖 自駕模式啟動",
            "content": "我會自動分析需求、寫程式、跑測試。\n你可以隨時按 `Ctrl+C` 暫停我，或是喝杯咖啡等我完成 ☕",
            "emoji": "🏎️",
        },
        "first_error": {
            "title": "😱 別擔心錯誤",
            "content": "遇到錯誤是正常的！\n試試看 `boring verify` 來診斷問題，或者讓我自動修復它。",
            "emoji": "🛡️",
        },
        "mcp_intro": {
            "title": "🔌 什麼是 MCP？",
            "content": "MCP 是我的擴充介面。\n透過 MCP，我可以操作你的檔案、搜尋資料庫，甚至上網查資料。",
            "emoji": "🔗",
        },
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.state_file = self.project_root / ".boring_tutorial.json"
        self._state: dict[str, bool] = self._load_state()
        self.enabled = os.environ.get("BORING_TUTORIAL", "1") == "1"

    def _load_state(self) -> dict[str, bool]:
        if not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
        except Exception:
            pass  # Fail silently

    def show_tutorial(self, tutorial_id: str, force: bool = False):
        """Show a tutorial tip if not already seen."""
        if not self.enabled and not force:
            return

        if tutorial_id in self._state and not force:
            return

        tutorial = self.TUTORIALS.get(tutorial_id)
        if not tutorial:
            return

        # Display tutorial
        title = f"{tutorial['emoji']} {tutorial['title']}"
        content = tutorial["content"]

        console.print(
            Panel(content, title=title, title_align="left", border_style="magenta", padding=(1, 2))
        )

        # Mark as seen
        self._state[tutorial_id] = True
        self._save_state()

    def reset_tutorials(self):
        """Reset all tutorial progress."""
        self._state = {}
        self._save_state()

    def generate_learning_note(self) -> Path:
        """Generate a learning note based on activity."""
        from collections import Counter

        from boring.audit import AuditLogger

        # Analyze Audit Logs for Skills
        skills = Counter()
        logger = AuditLogger.get_instance(self.project_root / "logs")
        logs = logger.get_recent_logs(limit=1000)

        for log in logs:
            if "tool" in log:
                skills[log["tool"]] += 1

        # Generate Report
        content = [
            "# 🎓 Vibe Coder 學習筆記",
            "",
            f"產生時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 🏅 解鎖成就 (Completed Tutorials)",
        ]

        # Achievements
        for key, completed in self._state.items():
            if completed:
                tut = self.TUTORIALS.get(key)
                if tut:
                    content.append(f"- {tut['emoji']} **{tut['title']}**")

        if not self._state:
            content.append("- (尚無成就，快去探索吧！)")

        # Skills
        content.append("")
        content.append("## 🛠️ 技能樹 (Tools Mastery)")
        if skills:
            for tool, count in skills.most_common(5):
                level = "⭐" * (min(count, 15) // 5 + 1)
                content.append(f"- **{tool}**: {level} ({count} 次)")
        else:
            content.append("- (尚未收集到技能數據)")

        # Recommendations
        content.append("")
        content.append("## 💡 下一步建議")
        recommendations = []
        if "speckit_plan" not in skills:
            recommendations.append("- 試試 **speckit_plan** 來規劃專案架構")
        if "boring_verify" not in skills:
            recommendations.append("- 試試 **boring_verify** 來檢查程式碼品質")

        if recommendations:
            content.extend(recommendations)
        else:
            content.append("- 你已經是 Vibe Coder 大師了！試試開發更複雜的專案吧。")

        # Save File
        note_path = self.project_root / "LEARNING.md"
        with open(note_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return note_path
