from dataclasses import dataclass
from typing import Optional


@dataclass
class Criterion:
    name: str
    description: str
    weight: float = 1.0


@dataclass
class Rubric:
    name: str
    description: str
    criteria: list[Criterion]
    strictness: str = "balanced"  # lenient, balanced, strict


# --- Predefined Rubrics ---

CODE_QUALITY_RUBRIC = Rubric(
    name="Code Quality",
    description="Evaluate code for readability, maintainability, and standard practices.",
    criteria=[
        Criterion(
            "Readability",
            "Variable/function names are descriptive; logic is easy to follow; idiomatic standards are followed.",
            1.2,
        ),
        Criterion("Documentation", "Docstrings and comments explain 'why', not just 'what'.", 0.8),
        Criterion(
            "Modularity",
            "Functions are small and focused; separation of concerns is respected.",
            1.0,
        ),
        Criterion("Error Handling", "Exceptions are caught specifically; no silent failures.", 1.0),
    ],
)

SECURITY_RUBRIC = Rubric(
    name="Security Check",
    description="Check for common security vulnerabilities.",
    criteria=[
        Criterion("Secrets", "No hardcoded API keys, passwords, or tokens.", 2.0),
        Criterion("Input Validation", "External inputs are validated before use.", 1.5),
        Criterion("Injection Prevention", "No raw SQL/Shell construction from user input.", 1.5),
    ],
    strictness="strict",
)

ARCHITECTURE_RUBRIC = Rubric(
    name="Architecture",
    description="Evaluate high-level design and dependency flow.",
    criteria=[
        Criterion("Consistency", "Follows project patterns and directory structure.", 1.0),
        Criterion(
            "Dependency Flow", "No circular imports; dependencies flow from high to low level.", 1.2
        ),
        Criterion("Scalability", "Design supports future growth without massive refactoring.", 0.8),
    ],
)

# --- Additional Predefined Rubrics ---

IMPLEMENTATION_PLAN_RUBRIC = Rubric(
    name="Implementation Plan",
    description="Evaluate the quality of an implementation plan or technical design document.",
    criteria=[
        Criterion(
            "Completeness",
            "All requirements are addressed; no missing features or edge cases.",
            1.5,
        ),
        Criterion(
            "Feasibility",
            "The plan can be realistically implemented with available resources.",
            1.2,
        ),
        Criterion(
            "Clarity", "Steps are clear and unambiguous; no room for misinterpretation.", 1.0
        ),
        Criterion(
            "Risk Assessment", "Potential risks and mitigation strategies are identified.", 0.8
        ),
        Criterion(
            "Dependencies", "External dependencies and integration points are clearly defined.", 1.0
        ),
        Criterion("Timeline", "Reasonable time estimates with prioritized deliverables.", 0.8),
    ],
)

TESTING_RUBRIC = Rubric(
    name="Testing",
    description="Evaluate test coverage and test quality.",
    criteria=[
        Criterion("Coverage", "Tests cover happy path, edge cases, and error scenarios.", 1.5),
        Criterion(
            "Isolation", "Tests are independent; no shared state that causes flakiness.", 1.2
        ),
        Criterion(
            "Assertions", "Assertions are specific and meaningful, not just 'no error'.", 1.0
        ),
        Criterion(
            "Maintainability", "Tests are readable and easy to update when code changes.", 0.8
        ),
        Criterion(
            "Performance", "Tests run quickly; no unnecessary delays or resource consumption.", 0.8
        ),
    ],
    strictness="balanced",
)

DOCUMENTATION_RUBRIC = Rubric(
    name="Documentation",
    description="Evaluate code and API documentation quality.",
    criteria=[
        Criterion("Completeness", "All public APIs, functions, and classes are documented.", 1.2),
        Criterion("Examples", "Usage examples are provided for complex functionality.", 1.0),
        Criterion("Accuracy", "Documentation matches actual implementation behavior.", 1.5),
        Criterion("Accessibility", "Written for the target audience; no undefined jargon.", 0.8),
        Criterion(
            "Formatting", "Consistent formatting; proper use of headings, lists, code blocks.", 0.8
        ),
    ],
)

PERFORMANCE_RUBRIC = Rubric(
    name="Performance",
    description="Evaluate code performance and efficiency.",
    criteria=[
        Criterion(
            "Algorithmic Efficiency",
            "Appropriate data structures and algorithms for the task.",
            1.5,
        ),
        Criterion("Resource Usage", "No memory leaks; resources are properly released.", 1.2),
        Criterion("Caching", "Appropriate use of caching to avoid redundant computation.", 0.8),
        Criterion(
            "Async/Concurrency",
            "I/O bound operations use async; CPU bound use threading/multiprocessing.",
            1.0,
        ),
        Criterion(
            "Database Queries",
            "Queries are optimized; no N+1 problems; proper indexing assumed.",
            1.0,
        ),
    ],
    strictness="strict",
)

API_DESIGN_RUBRIC = Rubric(
    name="API Design",
    description="Evaluate RESTful API or function interface design.",
    criteria=[
        Criterion(
            "Consistency", "Naming conventions and patterns are uniform across the API.", 1.2
        ),
        Criterion(
            "Intuitiveness", "API is easy to understand without extensive documentation.", 1.0
        ),
        Criterion(
            "Versioning",
            "API versioning strategy is clear and supports backward compatibility.",
            0.8,
        ),
        Criterion(
            "Error Responses", "Error responses are informative with proper HTTP status codes.", 1.0
        ),
        Criterion(
            "Idempotency",
            "Safe methods are idempotent; unsafe methods handle duplicates gracefully.",
            1.0,
        ),
    ],
)

PRODUCTION_RUBRIC = Rubric(
    name="Production Readiness",
    description="Hostile architectural review for high-concurrency, scalable systems.",
    criteria=[
        Criterion(
            "Concurrency & Thread Safety",
            "Race conditions, deadlocks, shared state management, and async patterns.",
            2.0,
        ),
        Criterion(
            "Scalability & Performance",
            "N+1 queries, horizontal scaling bottlenecks, caching strategies, and resource efficiency.",
            2.0,
        ),
        Criterion(
            "Resilience & Fault Tolerance",
            "Circuit breakers, retries, graceful degradation, and error recovery.",
            1.5,
        ),
        Criterion(
            "Observability",
            "Structured logging, metrics (Prometheus/StatsD), and tracing readiness.",
            1.5,
        ),
        Criterion(
            "Data & Storage",
            "Schema design, indexing, database constraints, and connection pooling.",
            1.5,
        ),
        Criterion(
            "Modern Tech Stack",
            "Utilization of modern, efficient libraries and patterns (e.g. Pydantic v2, Ruff, uv).",
            1.0,
        ),
    ],
    strictness="hostile",
)

# --- Rubric Registry for easy lookup ---

RUBRIC_REGISTRY = {
    "code_quality": CODE_QUALITY_RUBRIC,
    "security": SECURITY_RUBRIC,
    "architecture": ARCHITECTURE_RUBRIC,
    "implementation_plan": IMPLEMENTATION_PLAN_RUBRIC,
    "testing": TESTING_RUBRIC,
    "documentation": DOCUMENTATION_RUBRIC,
    "performance": PERFORMANCE_RUBRIC,
    "api_design": API_DESIGN_RUBRIC,
    "production": PRODUCTION_RUBRIC,
}


def get_rubric(name: str) -> Optional[Rubric]:
    """Get a rubric by name from the registry."""
    return RUBRIC_REGISTRY.get(name.lower().replace(" ", "_"))


def list_rubrics() -> list[str]:
    """List all available rubric names."""
    return list(RUBRIC_REGISTRY.keys())
