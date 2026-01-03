# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Pattern Mining - Extract and suggest patterns from .boring_brain.

Analyzes learned patterns to provide contextual suggestions
for what to do next based on project state.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Pattern:
    """A learned development pattern."""
    id: str
    name: str
    description: str
    trigger_conditions: List[str]  # Conditions when this pattern applies
    suggested_actions: List[str]   # What to do when pattern matches
    success_rate: float            # How often this pattern led to success
    usage_count: int
    last_used: Optional[datetime] = None


class PatternMiner:
    """
    Extracts patterns from .boring_brain and suggests next actions.
    
    Works by:
    1. Loading learned patterns from brain
    2. Analyzing current project state
    3. Matching patterns to current context
    4. Ranking suggestions by relevance and success rate
    """
    
    # Default patterns when brain is empty
    DEFAULT_PATTERNS = [
        Pattern(
            id="new_project",
            name="New Project Setup",
            description="When starting a new project, establish foundations first",
            trigger_conditions=["no existing code", "empty task.md"],
            suggested_actions=[
                "Run speckit_clarify to understand requirements",
                "Run speckit_constitution to establish principles",
                "Run speckit_plan to create implementation plan"
            ],
            success_rate=0.95,
            usage_count=0
        ),
        Pattern(
            id="verification_failed",
            name="Verification Failed",
            description="When verification fails, fix issues systematically",
            trigger_conditions=["boring_verify failed", "syntax errors", "lint errors"],
            suggested_actions=[
                "Run boring_auto_fix for automated repair",
                "Or run run_boring with specific fix task",
                "Then run boring_verify to confirm fixes"
            ],
            success_rate=0.88,
            usage_count=0
        ),
        Pattern(
            id="feature_complete",
            name="Feature Complete",
            description="After completing a feature, verify and learn",
            trigger_conditions=["all tasks completed", "tests passing"],
            suggested_actions=[
                "Run boring_verify level=FULL for thorough check",
                "Run boring_learn to extract successful patterns",
                "Commit changes with descriptive message"
            ],
            success_rate=0.92,
            usage_count=0
        ),
        Pattern(
            id="stuck_debugging",
            name="Stuck Debugging",
            description="When stuck on a bug, get fresh perspective",
            trigger_conditions=["same error repeated", "multiple failed attempts"],
            suggested_actions=[
                "Run speckit_analyze for consistency check",
                "Run boring_evaluate for code quality review",
                "Consider speckit_clarify to revisit requirements"
            ],
            success_rate=0.75,
            usage_count=0
        ),
        Pattern(
            id="code_review",
            name="Code Review Time",
            description="Before sharing code, ensure quality",
            trigger_conditions=["before PR", "before commit"],
            suggested_actions=[
                "Run boring_verify level=SEMANTIC for AI review",
                "Check speckit_checklist for feature completeness",
                "Run boring_hooks_install to prevent future issues"
            ],
            success_rate=0.90,
            usage_count=0
        )
    ]
    
    def __init__(self, brain_dir: Path):
        self.brain_dir = brain_dir
        self.patterns_dir = brain_dir / "learned_patterns"
        self.patterns: List[Pattern] = []
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns from brain directory."""
        # Start with defaults
        self.patterns = list(self.DEFAULT_PATTERNS)
        
        # Load custom patterns
        if self.patterns_dir.exists():
            for pattern_file in self.patterns_dir.glob("*.json"):
                try:
                    data = json.loads(pattern_file.read_text(encoding="utf-8"))
                    pattern = Pattern(
                        id=data["id"],
                        name=data["name"],
                        description=data.get("description", ""),
                        trigger_conditions=data.get("trigger_conditions", []),
                        suggested_actions=data.get("suggested_actions", []),
                        success_rate=data.get("success_rate", 0.5),
                        usage_count=data.get("usage_count", 0),
                        last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
                    )
                    self.patterns.append(pattern)
                except Exception:
                    continue
    
    def analyze_project_state(self, project_root: Path) -> Dict[str, Any]:
        """Analyze current project state to determine context."""
        state = {
            "has_code": False,
            "has_tests": False,
            "has_errors": False,
            "task_completion": 0.0,
            "recent_activity": None
        }
        
        # Check for code
        src_dir = project_root / "src"
        if src_dir.exists():
            py_files = list(src_dir.glob("**/*.py"))
            state["has_code"] = len(py_files) > 0
        
        # Check for tests
        tests_dir = project_root / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("**/test_*.py"))
            state["has_tests"] = len(test_files) > 0
        
        # Check task.md completion
        task_file = project_root / "task.md"
        if task_file.exists():
            content = task_file.read_text(encoding="utf-8")
            completed = content.count("[x]")
            total = completed + content.count("[ ]")
            if total > 0:
                state["task_completion"] = completed / total
        
        # Check for verification errors
        exit_signals = project_root / ".exit_signals"
        if exit_signals.exists():
            try:
                signals = json.loads(exit_signals.read_text())
                state["has_errors"] = signals.get("verification_failed", False)
            except Exception:
                pass
        
        return state
    
    def match_patterns(self, project_state: Dict[str, Any]) -> List[Pattern]:
        """Find patterns that match current project state."""
        matched = []
        
        for pattern in self.patterns:
            score = self._calculate_match_score(pattern, project_state)
            if score > 0.3:  # Threshold for relevance
                matched.append((pattern, score))
        
        # Sort by score * success_rate
        matched.sort(key=lambda x: x[1] * x[0].success_rate, reverse=True)
        
        return [p for p, _ in matched]
    
    def _calculate_match_score(self, pattern: Pattern, state: Dict[str, Any]) -> float:
        """Calculate how well a pattern matches current state."""
        score = 0.0
        
        conditions = " ".join(pattern.trigger_conditions).lower()
        
        # Match based on state
        if "new" in conditions and not state["has_code"]:
            score += 0.5
        if "failed" in conditions and state["has_errors"]:
            score += 0.6
        if "complete" in conditions and state["task_completion"] > 0.8:
            score += 0.5
        if "stuck" in conditions and state["has_errors"]:
            score += 0.4
        if "review" in conditions and state["task_completion"] > 0.5:
            score += 0.3
        
        return min(score, 1.0)
    
    def suggest_next(self, project_root: Path, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Suggest next actions based on project state and learned patterns.
        
        Args:
            project_root: Path to project
            limit: Maximum suggestions to return
        
        Returns:
            List of suggested actions with reasoning
        """
        state = self.analyze_project_state(project_root)
        matched = self.match_patterns(state)[:limit]
        
        suggestions = []
        for pattern in matched:
            suggestions.append({
                "pattern": pattern.name,
                "description": pattern.description,
                "suggested_actions": pattern.suggested_actions,
                "confidence": pattern.success_rate,
                "context": {
                    "task_completion": f"{state['task_completion']*100:.0f}%",
                    "has_code": state["has_code"],
                    "has_errors": state["has_errors"]
                }
            })
        
        if not suggestions:
            # Fallback suggestion
            suggestions.append({
                "pattern": "Getting Started",
                "description": "No specific pattern matched",
                "suggested_actions": [
                    "Run boring_quickstart for available tools",
                    "Run boring_status to check project state"
                ],
                "confidence": 0.5,
                "context": state
            })
        
        return suggestions


def get_pattern_miner(project_root: Path) -> PatternMiner:
    """Get a pattern miner for a project."""
    brain_dir = project_root / ".boring_brain"
    return PatternMiner(brain_dir)
