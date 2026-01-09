# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Dynamic Rubric Generator - Advanced Evaluation V10.25

Generates detailed evaluation rubrics with level descriptions and edge cases.
Based on the Advanced Evaluation skill framework.

Features:
1. Dynamic rubric generation by domain
2. Detailed level descriptions (1-5 scale)
3. Edge case guidance
4. Strictness calibration (lenient, balanced, strict)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RubricLevel:
    """A level in the rubric with detailed description."""

    score: int
    label: str
    description: str
    characteristics: list[str] = field(default_factory=list)


@dataclass
class EdgeCase:
    """Edge case guidance for consistent evaluation."""

    situation: str
    guidance: str


@dataclass
class DetailedCriterion:
    """A criterion with detailed level descriptions."""

    name: str
    description: str
    weight: float = 1.0
    levels: list[RubricLevel] = field(default_factory=list)
    edge_cases: list[EdgeCase] = field(default_factory=list)


@dataclass
class DetailedRubric:
    """A complete rubric with all level descriptions and edge cases."""

    name: str
    description: str
    domain: str
    scale: str  # "1-3", "1-5", "1-10"
    strictness: str  # "lenient", "balanced", "strict"
    criteria: list[DetailedCriterion] = field(default_factory=list)
    general_edge_cases: list[EdgeCase] = field(default_factory=list)
    scoring_guidelines: list[str] = field(default_factory=list)


# ==============================================================================
# Level Description Templates
# ==============================================================================

# Templates for different domains
LEVEL_TEMPLATES = {
    "code_quality": {
        1: {
            "label": "Poor",
            "description": "Code is difficult to understand without significant effort",
            "characteristics": [
                "No meaningful variable or function names",
                "No comments or documentation",
                "Deeply nested or convoluted logic",
                "Violates language conventions",
            ],
        },
        2: {
            "label": "Below Average",
            "description": "Code has significant issues but is somewhat understandable",
            "characteristics": [
                "Some variables have unclear names",
                "Minimal or misleading comments",
                "Complex logic without clear structure",
                "Inconsistent style",
            ],
        },
        3: {
            "label": "Adequate",
            "description": "Code is understandable with some effort",
            "characteristics": [
                "Most variables have meaningful names",
                "Basic comments present for complex sections",
                "Logic is followable but could be cleaner",
                "Generally follows conventions",
            ],
        },
        4: {
            "label": "Good",
            "description": "Code is well-written and maintainable",
            "characteristics": [
                "Clear, descriptive naming throughout",
                "Helpful comments explaining 'why'",
                "Clean logical structure",
                "Consistent with language idioms",
            ],
        },
        5: {
            "label": "Excellent",
            "description": "Code is immediately clear and highly maintainable",
            "characteristics": [
                "All names are self-documenting",
                "Comprehensive documentation",
                "Clean, modular, elegant design",
                "Exemplary use of language features",
            ],
        },
    },
    "security": {
        1: {
            "label": "Critical Risk",
            "description": "Severe security vulnerabilities present",
            "characteristics": [
                "Hardcoded secrets or credentials",
                "No input validation",
                "SQL/Command injection possible",
                "Unsafe deserialization",
            ],
        },
        2: {
            "label": "High Risk",
            "description": "Significant security issues that need immediate attention",
            "characteristics": [
                "Weak authentication mechanisms",
                "Insufficient access controls",
                "Missing encryption for sensitive data",
                "Verbose error messages exposing internals",
            ],
        },
        3: {
            "label": "Moderate Risk",
            "description": "Some security concerns that should be addressed",
            "characteristics": [
                "Basic validation but incomplete",
                "Some logging of sensitive data",
                "Using outdated dependencies",
                "Missing rate limiting",
            ],
        },
        4: {
            "label": "Low Risk",
            "description": "Generally secure with minor improvements possible",
            "characteristics": [
                "Input validation present",
                "Proper authentication",
                "Sensitive data protected",
                "Good error handling",
            ],
        },
        5: {
            "label": "Secure",
            "description": "Follows security best practices",
            "characteristics": [
                "Defense in depth",
                "Principle of least privilege",
                "Secure defaults",
                "Comprehensive logging and monitoring",
            ],
        },
    },
    "performance": {
        1: {
            "label": "Poor",
            "description": "Severe performance issues",
            "characteristics": [
                "O(n²) or worse where O(n) is possible",
                "Memory leaks present",
                "Blocking operations in async context",
                "N+1 query problems",
            ],
        },
        2: {
            "label": "Below Average",
            "description": "Noticeable performance problems",
            "characteristics": [
                "Inefficient algorithms",
                "Unnecessary data copying",
                "Missing connection pooling",
                "No caching where beneficial",
            ],
        },
        3: {
            "label": "Average",
            "description": "Acceptable performance for typical loads",
            "characteristics": [
                "Reasonable algorithm choices",
                "Basic resource management",
                "Some optimization opportunities",
                "Works for current scale",
            ],
        },
        4: {
            "label": "Good",
            "description": "Well-optimized for expected workloads",
            "characteristics": [
                "Efficient algorithms",
                "Proper async patterns",
                "Good caching strategy",
                "Optimized database queries",
            ],
        },
        5: {
            "label": "Excellent",
            "description": "Highly optimized, scalable implementation",
            "characteristics": [
                "Optimal algorithm complexity",
                "Comprehensive caching",
                "Horizontal scaling ready",
                "Measured and profiled",
            ],
        },
    },
    "documentation": {
        1: {
            "label": "Missing",
            "description": "No meaningful documentation",
            "characteristics": [
                "No docstrings or comments",
                "No README or usage guide",
                "No type hints",
                "No examples",
            ],
        },
        2: {
            "label": "Minimal",
            "description": "Token documentation that doesn't help",
            "characteristics": [
                "Comments just restate code",
                "Missing critical information",
                "Outdated or wrong documentation",
                "No API reference",
            ],
        },
        3: {
            "label": "Adequate",
            "description": "Basic documentation present",
            "characteristics": [
                "Main functions documented",
                "Basic README exists",
                "Some type hints",
                "Key concepts explained",
            ],
        },
        4: {
            "label": "Good",
            "description": "Comprehensive documentation",
            "characteristics": [
                "All public APIs documented",
                "Usage examples provided",
                "Complete type hints",
                "Clear installation guide",
            ],
        },
        5: {
            "label": "Excellent",
            "description": "Exceptional documentation",
            "characteristics": [
                "Tutorials and guides",
                "Architecture documentation",
                "Contributing guide",
                "Versioned documentation",
            ],
        },
    },
}

# Edge case templates
EDGE_CASE_TEMPLATES = {
    "code_quality": [
        EdgeCase(
            situation="Code is well-structured but uses domain-specific abbreviations",
            guidance="Score based on readability for domain experts, not general audience",
        ),
        EdgeCase(
            situation="Code uses unconventional but effective patterns",
            guidance="Evaluate effectiveness over convention compliance if justified",
        ),
        EdgeCase(
            situation="Code is auto-generated or configuration-heavy",
            guidance="Focus on the non-generated parts; configuration correctness matters more",
        ),
    ],
    "security": [
        EdgeCase(
            situation="Code handles sensitive data in test environment only",
            guidance="Still flag hardcoded secrets but note the test context",
        ),
        EdgeCase(
            situation="Security measures seem excessive for the use case",
            guidance="Defense in depth is positive; don't penalize extra security",
        ),
    ],
    "performance": [
        EdgeCase(
            situation="Code prioritizes readability over micro-optimizations",
            guidance="Favor clarity unless performance is critical path",
        ),
        EdgeCase(
            situation="Complex optimization with unclear benefit",
            guidance="Check if optimization is measured; premature optimization is negative",
        ),
    ],
}

# Scoring guidelines
SCORING_GUIDELINES = {
    "lenient": [
        "Give benefit of the doubt for ambiguous cases",
        "Focus on major issues, overlook minor style issues",
        "Score 3 is the default if requirements are met",
        "Reserve scores 1-2 for significant failures only",
    ],
    "balanced": [
        "Apply criteria as written without bias",
        "Weight issues by their impact",
        "Score 3 means adequate, meeting requirements",
        "Reserve 5 for genuinely excellent work",
    ],
    "strict": [
        "High bar for passing scores (3+)",
        "Any security issue is a major deduction",
        "Require evidence for each criterion",
        "Excellent (5) requires near-perfection",
    ],
}


# ==============================================================================
# Rubric Generation Functions
# ==============================================================================


def generate_rubric(
    name: str,
    description: str,
    domain: str,
    criteria_names: list[str],
    scale: str = "1-5",
    strictness: str = "balanced",
    weights: Optional[dict[str, float]] = None,
) -> DetailedRubric:
    """
    Generate a detailed rubric with level descriptions.

    Args:
        name: Name of the rubric
        description: Description of what this rubric evaluates
        domain: Domain for level templates (code_quality, security, performance, documentation)
        criteria_names: List of criterion names
        scale: Rating scale (1-3, 1-5, 1-10)
        strictness: Strictness level (lenient, balanced, strict)
        weights: Optional weights for each criterion

    Returns:
        DetailedRubric with complete level descriptions
    """
    weights = weights or {}

    # Get level template for domain
    levels_template = LEVEL_TEMPLATES.get(domain, LEVEL_TEMPLATES["code_quality"])

    # Generate criteria with levels
    criteria = []
    for criterion_name in criteria_names:
        # Build levels based on scale
        levels = []
        if scale == "1-5":
            for score in [1, 2, 3, 4, 5]:
                template = levels_template.get(
                    score, {"label": f"Level {score}", "description": "", "characteristics": []}
                )
                levels.append(
                    RubricLevel(
                        score=score,
                        label=template["label"],
                        description=template["description"],
                        characteristics=template["characteristics"],
                    )
                )
        elif scale == "1-3":
            for score, template_score in [(1, 1), (2, 3), (3, 5)]:
                template = levels_template.get(
                    template_score,
                    {"label": f"Level {score}", "description": "", "characteristics": []},
                )
                levels.append(
                    RubricLevel(
                        score=score,
                        label=template["label"],
                        description=template["description"],
                        characteristics=template["characteristics"],
                    )
                )
        elif scale == "1-10":
            for score in range(1, 11):
                # Map to 1-5 templates
                template_score = min(5, max(1, (score + 1) // 2))
                template = levels_template.get(
                    template_score,
                    {"label": f"Level {score}", "description": "", "characteristics": []},
                )
                levels.append(
                    RubricLevel(
                        score=score,
                        label=f"{template['label']} ({score}/10)",
                        description=template["description"],
                        characteristics=template["characteristics"],
                    )
                )

        criterion = DetailedCriterion(
            name=criterion_name,
            description=f"Evaluate {criterion_name.lower()}",
            weight=weights.get(criterion_name, 1.0),
            levels=levels,
            edge_cases=EDGE_CASE_TEMPLATES.get(domain, []),
        )
        criteria.append(criterion)

    return DetailedRubric(
        name=name,
        description=description,
        domain=domain,
        scale=scale,
        strictness=strictness,
        criteria=criteria,
        general_edge_cases=EDGE_CASE_TEMPLATES.get(domain, []),
        scoring_guidelines=SCORING_GUIDELINES.get(strictness, SCORING_GUIDELINES["balanced"]),
    )


def generate_code_quality_rubric(strictness: str = "balanced") -> DetailedRubric:
    """Generate a standard code quality rubric."""
    return generate_rubric(
        name="Code Quality",
        description="Comprehensive evaluation of code quality",
        domain="code_quality",
        criteria_names=["Readability", "Documentation", "Modularity", "Error Handling"],
        scale="1-5",
        strictness=strictness,
        weights={
            "Readability": 1.2,
            "Documentation": 0.8,
            "Modularity": 1.0,
            "Error Handling": 1.0,
        },
    )


def generate_security_rubric(strictness: str = "strict") -> DetailedRubric:
    """Generate a security-focused rubric."""
    return generate_rubric(
        name="Security Audit",
        description="Security vulnerability assessment",
        domain="security",
        criteria_names=["Secrets Management", "Input Validation", "Injection Prevention"],
        scale="1-5",
        strictness=strictness,
        weights={"Secrets Management": 2.0, "Input Validation": 1.5, "Injection Prevention": 1.5},
    )


def rubric_to_prompt(rubric: DetailedRubric) -> str:
    """
    Convert a DetailedRubric to a prompt string for LLM evaluation.

    Args:
        rubric: The rubric to convert

    Returns:
        Formatted prompt string
    """
    lines = [f"# {rubric.name}", "", rubric.description, ""]

    lines.append("## Criteria")
    lines.append("")
    for criterion in rubric.criteria:
        lines.append(f"### {criterion.name} (Weight: {criterion.weight})")
        lines.append("")
        for level in criterion.levels:
            lines.append(f"**{level.score} - {level.label}**: {level.description}")
            if level.characteristics:
                for char in level.characteristics:
                    lines.append(f"  - {char}")
        lines.append("")

    if rubric.general_edge_cases:
        lines.append("## Edge Cases")
        lines.append("")
        for ec in rubric.general_edge_cases:
            lines.append(f"- **{ec.situation}**: {ec.guidance}")
        lines.append("")

    if rubric.scoring_guidelines:
        lines.append("## Scoring Guidelines")
        lines.append("")
        for guideline in rubric.scoring_guidelines:
            lines.append(f"- {guideline}")
        lines.append("")

    return "\n".join(lines)


def format_rubric_json(rubric: DetailedRubric) -> dict:
    """Convert rubric to JSON-serializable dict."""
    return {
        "name": rubric.name,
        "description": rubric.description,
        "domain": rubric.domain,
        "scale": rubric.scale,
        "strictness": rubric.strictness,
        "criteria": [
            {
                "name": c.name,
                "description": c.description,
                "weight": c.weight,
                "levels": [
                    {
                        "score": l.score,
                        "label": l.label,
                        "description": l.description,
                        "characteristics": l.characteristics,
                    }
                    for l in c.levels
                ],
            }
            for c in rubric.criteria
        ],
        "edge_cases": [
            {"situation": e.situation, "guidance": e.guidance} for e in rubric.general_edge_cases
        ],
        "scoring_guidelines": rubric.scoring_guidelines,
    }
