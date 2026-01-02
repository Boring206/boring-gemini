from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Criterion:
    name: str
    description: str
    weight: float = 1.0

@dataclass
class Rubric:
    name: str
    description: str
    criteria: List[Criterion]
    strictness: str = "balanced"  # lenient, balanced, strict

# --- Predefined Rubrics ---

CODE_QUALITY_RUBRIC = Rubric(
    name="Code Quality",
    description="Evaluate code for readability, maintainability, and standard practices.",
    criteria=[
        Criterion("Readability", "Variable/function names are descriptive; logic is easy to follow.", 1.2),
        Criterion("Documentation", "Docstrings and comments explain 'why', not just 'what'.", 0.8),
        Criterion("Modularity", "Functions are small and focused; separation of concerns is respected.", 1.0),
        Criterion("Error Handling", "Exceptions are caught specifically; no silent failures.", 1.0)
    ]
)

SECURITY_RUBRIC = Rubric(
    name="Security Check",
    description="Check for common security vulnerabilities.",
    criteria=[
        Criterion("Secrets", "No hardcoded API keys, passwords, or tokens.", 2.0),
        Criterion("Input Validation", "External inputs are validated before use.", 1.5),
        Criterion("Injection Prevention", "No raw SQL/Shell construction from user input.", 1.5)
    ],
    strictness="strict"
)

ARCHITECTURE_RUBRIC = Rubric(
    name="Architecture",
    description="Evaluate high-level design and dependency flow.",
    criteria=[
        Criterion("Consistency", "Follows project patterns and directory structure.", 1.0),
        Criterion("Dependency Flow", "No circular imports; dependencies flow from high to low level.", 1.2),
        Criterion("Scalability", "Design supports future growth without massive refactoring.", 0.8)
    ]
)
