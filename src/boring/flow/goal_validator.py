"""
Goal Feasibility Validator

Analyzes user goal against project structure to detect impossible requests.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class GoalValidator:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.file_types = self._scan_file_types()

    def _scan_file_types(self) -> set[str]:
        """Scan project for existing file types."""
        types = set()
        # Limit depth to avoid deep node_modules or venv
        # Simple recursive search
        try:
            for path in self.root.rglob("*"):
                # Skip common ignore directories
                if any(
                    part.startswith(".")
                    or part in ("node_modules", "venv", "__pycache__", "dist", "build")
                    for part in path.parts
                ):
                    continue

                if path.is_file():
                    types.add(path.suffix.lower())
        except Exception as e:
            logger.warning(f"GoalValidator scan failed: {e}")
        return types

    def validate(self, goal: str) -> tuple[bool, str | None]:
        """
        Check if goal is feasible.
        Returns (is_valid, warning_message or None).
        """
        warnings = []
        goal_lower = goal.lower()

        # 1. Frontend Framework Mismatch
        frontend_keywords = ["vue", "react", "angular", "svelte", "next.js", "nuxt"]

        # Check if user is asking for frontend work
        is_frontend_request = any(kw in goal_lower for kw in frontend_keywords)

        # Check if project has frontend files
        has_frontend_files = any(
            ext in {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html", ".css"}
            for ext in self.file_types
        )

        if is_frontend_request and not has_frontend_files:
            # Check if project is empty (init scenario)
            # If completely empty, we assume it's a new project setup, so it's valid.
            if self.file_types:
                warnings.append(
                    "⚠️ 偵測到前端框架需求，但專案中沒有前端代碼 (JS/TS/HTML)。"
                    "請確認這是你想要的操作（例如：在現有後端專案中新增前端）。"
                )

        # 2. Language Mismatch (Python)
        if "python" in goal_lower and ".py" not in self.file_types:
            if self.file_types:  # Only warn if not empty
                warnings.append("⚠️ 提及 Python 但專案中沒有 .py 檔案。")

        # 3. TypeScript/JavaScript Mismatch
        if (
            "typescript" in goal_lower
            and ".ts" not in self.file_types
            and ".tsx" not in self.file_types
        ):
            if self.file_types:
                warnings.append("⚠️ 提及 TypeScript 但專案中沒有 .ts/.tsx 檔案。")

        # 4. Git Mismatch
        if "git" in goal_lower and ".git" not in [p.name for p in self.root.iterdir()]:
            # This check requires listing root dir names, scan_file_types only gets suffixes
            # Keep it simple for now or check root explicitly
            pass

        return (len(warnings) == 0, "\n".join(warnings) if warnings else None)
