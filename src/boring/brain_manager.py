"""
Brain Manager Module for Boring V5.2

Manages the .boring_brain knowledge base with automatic learning capabilities.

Features:
- Extracts successful patterns from .boring_memory
- Generates evaluation rubrics
- Stores workflow adaptations

Directory Structure:
    .boring_brain/
    ├── workflow_adaptations/  # Evolution history
    ├── learned_patterns/      # Success patterns from memory
    └── rubrics/               # Evaluation criteria
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logger import log_status


@dataclass
class LearnedPattern:
    """A pattern learned from successful executions."""

    pattern_id: str
    pattern_type: str  # error_solution, workflow_optimization, code_fix
    description: str
    context: str
    solution: str
    success_count: int
    created_at: str
    last_used: str


@dataclass
class Rubric:
    """Evaluation rubric for quality assessment."""

    name: str
    description: str
    criteria: list[dict[str, str]]
    created_at: str


class BrainManager:
    """
    Manages .boring_brain knowledge base.

    Usage:
        brain = BrainManager(project_root)

        # Learn from successful loop
        brain.learn_from_success(loop_record)

        # Get patterns for context
        patterns = brain.get_relevant_patterns("authentication error")
    """

    def __init__(self, project_root: Path, log_dir: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.brain_dir = self.project_root / ".boring_brain"
        self.log_dir = log_dir or self.project_root / "logs"

        # Subdirectories
        self.adaptations_dir = self.brain_dir / "workflow_adaptations"
        self.patterns_dir = self.brain_dir / "learned_patterns"
        self.rubrics_dir = self.brain_dir / "rubrics"

        # Ensure structure exists
        self._ensure_structure()

    def _ensure_structure(self):
        """Create directory structure if not exists."""
        for d in [self.adaptations_dir, self.patterns_dir, self.rubrics_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _load_patterns(self) -> list[dict]:
        """Load all learned patterns."""
        patterns_file = self.patterns_dir / "patterns.json"
        if patterns_file.exists():
            try:
                return json.loads(patterns_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return []
        return []

    def _save_patterns(self, patterns: list[dict]):
        """Save patterns to file."""
        patterns_file = self.patterns_dir / "patterns.json"
        patterns_file.write_text(
            json.dumps(patterns, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def learn_from_memory(self, storage) -> dict[str, Any]:
        """
        Extract successful patterns from .boring_memory SQLite storage.

        Args:
            storage: SQLiteStorage instance

        Returns:
            Learning result with patterns extracted
        """
        try:
            # Get successful loops
            recent_loops = storage.get_recent_loops(limit=50)
            [l for l in recent_loops if l.get("status") == "SUCCESS"]

            # Get error patterns with solutions
            error_patterns = storage.get_top_errors(limit=20)
            solved_patterns = [e for e in error_patterns if e.get("solution")]

            # Extract patterns
            patterns = self._load_patterns()
            new_count = 0

            for err in solved_patterns:
                pattern_id = f"ERR_{err['error_type'][:20]}"

                # Check if pattern already exists
                existing = [p for p in patterns if p.get("pattern_id") == pattern_id]
                if existing:
                    # Update success count
                    existing[0]["success_count"] = existing[0].get("success_count", 0) + 1
                    existing[0]["last_used"] = datetime.now().isoformat()
                else:
                    # Create new pattern
                    new_pattern = LearnedPattern(
                        pattern_id=pattern_id,
                        pattern_type="error_solution",
                        description=f"Solution for {err['error_type']}",
                        context=err.get("error_message", "")[:200],
                        solution=err.get("solution", ""),
                        success_count=err.get("occurrence_count", 1),
                        created_at=datetime.now().isoformat(),
                        last_used=datetime.now().isoformat(),
                    )
                    patterns.append(asdict(new_pattern))
                    new_count += 1

            self._save_patterns(patterns)

            log_status(
                self.log_dir, "INFO", f"Learned {new_count} new patterns, total: {len(patterns)}"
            )

            return {"status": "SUCCESS", "new_patterns": new_count, "total_patterns": len(patterns)}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def get_relevant_patterns(self, context: str, limit: int = 5) -> list[dict]:
        """
        Get patterns relevant to given context.

        Simple keyword matching for now.
        Could be enhanced with vector similarity search.
        """
        patterns = self._load_patterns()

        if not context:
            return patterns[:limit]

        # Simple relevance scoring
        context_lower = context.lower()
        scored = []
        for p in patterns:
            score = 0
            if context_lower in p.get("context", "").lower():
                score += 2
            if context_lower in p.get("description", "").lower():
                score += 1
            if context_lower in p.get("solution", "").lower():
                score += 1
            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]

    def create_rubric(self, name: str, description: str, criteria: list[dict]) -> dict[str, Any]:
        """
        Create an evaluation rubric.

        Args:
            name: Rubric name (e.g., "implementation_plan")
            description: What this rubric evaluates
            criteria: List of {name, description, weight} dicts
        """
        rubric = Rubric(
            name=name,
            description=description,
            criteria=criteria,
            created_at=datetime.now().isoformat(),
        )

        rubric_file = self.rubrics_dir / f"{name}.json"
        rubric_file.write_text(
            json.dumps(asdict(rubric), indent=2, ensure_ascii=False), encoding="utf-8"
        )

        return {"status": "SUCCESS", "rubric": name}

    def get_rubric(self, name: str) -> Optional[dict]:
        """Load a rubric by name."""
        rubric_file = self.rubrics_dir / f"{name}.json"
        if rubric_file.exists():
            return json.loads(rubric_file.read_text(encoding="utf-8"))
        return None

    def create_default_rubrics(self) -> dict[str, Any]:
        """Create default evaluation rubrics for LLM-as-Judge evaluation."""
        rubrics_created = []

        # Implementation Plan Rubric
        self.create_rubric(
            name="implementation_plan",
            description="Evaluates quality of implementation plans",
            criteria=[
                {
                    "name": "completeness",
                    "description": "All components have file paths",
                    "weight": 25,
                },
                {"name": "dependencies", "description": "Dependencies are explicit", "weight": 20},
                {
                    "name": "testability",
                    "description": "Verification steps are defined",
                    "weight": 25,
                },
                {"name": "clarity", "description": "Steps are unambiguous", "weight": 15},
                {"name": "feasibility", "description": "Plan is technically sound", "weight": 15},
            ],
        )
        rubrics_created.append("implementation_plan")

        # Task List Rubric
        self.create_rubric(
            name="task_list",
            description="Evaluates quality of task breakdowns",
            criteria=[
                {
                    "name": "granularity",
                    "description": "Tasks are appropriately sized",
                    "weight": 30,
                },
                {"name": "ordering", "description": "Dependencies are respected", "weight": 25},
                {"name": "testability", "description": "Each task has verification", "weight": 25},
                {"name": "completeness", "description": "Covers all plan items", "weight": 20},
            ],
        )
        rubrics_created.append("task_list")

        # Code Quality Rubric
        self.create_rubric(
            name="code_quality",
            description="Evaluates code implementation quality",
            criteria=[
                {"name": "correctness", "description": "Code works as intended", "weight": 30},
                {"name": "readability", "description": "Code is easy to understand", "weight": 20},
                {"name": "maintainability", "description": "Code is easy to modify", "weight": 20},
                {"name": "testing", "description": "Tests are comprehensive", "weight": 20},
                {"name": "documentation", "description": "Comments and docs exist", "weight": 10},
            ],
        )
        rubrics_created.append("code_quality")

        # Security Rubric
        self.create_rubric(
            name="security",
            description="Evaluates code for security vulnerabilities",
            criteria=[
                {
                    "name": "secrets",
                    "description": "No hardcoded API keys, passwords, or tokens",
                    "weight": 40,
                },
                {
                    "name": "input_validation",
                    "description": "External inputs are validated before use",
                    "weight": 30,
                },
                {
                    "name": "injection_prevention",
                    "description": "No raw SQL/Shell construction from user input",
                    "weight": 30,
                },
            ],
        )
        rubrics_created.append("security")

        # Architecture Rubric
        self.create_rubric(
            name="architecture",
            description="Evaluates high-level design and dependency flow",
            criteria=[
                {
                    "name": "consistency",
                    "description": "Follows project patterns and directory structure",
                    "weight": 35,
                },
                {
                    "name": "dependency_flow",
                    "description": "No circular imports; dependencies flow correctly",
                    "weight": 35,
                },
                {
                    "name": "scalability",
                    "description": "Design supports future growth",
                    "weight": 30,
                },
            ],
        )
        rubrics_created.append("architecture")

        # API Design Rubric
        self.create_rubric(
            name="api_design",
            description="Evaluates API interface design quality",
            criteria=[
                {
                    "name": "consistency",
                    "description": "Naming conventions are uniform",
                    "weight": 25,
                },
                {
                    "name": "intuitiveness",
                    "description": "API is easy to use without docs",
                    "weight": 20,
                },
                {
                    "name": "versioning",
                    "description": "Supports backward compatibility",
                    "weight": 15,
                },
                {
                    "name": "error_responses",
                    "description": "Errors are informative with proper codes",
                    "weight": 20,
                },
                {"name": "idempotency", "description": "Safe methods are idempotent", "weight": 20},
            ],
        )
        rubrics_created.append("api_design")

        # Testing Rubric
        self.create_rubric(
            name="testing",
            description="Evaluates test coverage and quality",
            criteria=[
                {
                    "name": "coverage",
                    "description": "Tests cover happy path, edge cases, errors",
                    "weight": 30,
                },
                {"name": "isolation", "description": "Tests are independent", "weight": 25},
                {
                    "name": "assertions",
                    "description": "Assertions are specific and meaningful",
                    "weight": 20,
                },
                {
                    "name": "maintainability",
                    "description": "Tests are easy to update",
                    "weight": 15,
                },
                {"name": "performance", "description": "Tests run quickly", "weight": 10},
            ],
        )
        rubrics_created.append("testing")

        # Documentation Rubric
        self.create_rubric(
            name="documentation",
            description="Evaluates code and API documentation",
            criteria=[
                {
                    "name": "completeness",
                    "description": "All public APIs are documented",
                    "weight": 25,
                },
                {
                    "name": "examples",
                    "description": "Usage examples for complex functionality",
                    "weight": 20,
                },
                {
                    "name": "accuracy",
                    "description": "Docs match actual implementation",
                    "weight": 30,
                },
                {
                    "name": "accessibility",
                    "description": "Written for target audience",
                    "weight": 15,
                },
                {"name": "formatting", "description": "Consistent formatting", "weight": 10},
            ],
        )
        rubrics_created.append("documentation")

        log_status(self.log_dir, "INFO", f"Created {len(rubrics_created)} default rubrics")

        return {"status": "SUCCESS", "rubrics_created": rubrics_created}

    def get_brain_summary(self) -> dict[str, Any]:
        """Get summary of brain contents."""
        patterns = self._load_patterns()

        rubrics = []
        for f in self.rubrics_dir.glob("*.json"):
            rubrics.append(f.stem)

        adaptations = []
        for f in self.adaptations_dir.glob("*.json"):
            adaptations.append(f.stem)

        return {
            "patterns_count": len(patterns),
            "rubrics": rubrics,
            "adaptations": adaptations,
            "brain_dir": str(self.brain_dir),
        }


def create_brain_manager(project_root: Path, log_dir: Optional[Path] = None) -> BrainManager:
    """Factory function to create BrainManager instance."""
    return BrainManager(project_root, log_dir)
