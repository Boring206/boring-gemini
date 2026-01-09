"""
Prompt Templates and Building Logic for Judge
"""

import os

from ..config import settings
from .rubrics import Rubric


def build_grade_prompt(
    filename: str, content: str, rubric: Rubric, adapter_type: str = "GeminiCLIAdapter"
) -> str:
    """Build the prompt for grading code quality."""
    criteria_text = "\n".join(
        [f"- {c.name}: {c.description} (Weight: {c.weight})" for c in rubric.criteria]
    )

    # Dimensions for JSON output
    dimensions_json = ",\n".join(
        [
            f'                "{c.name.lower().replace(" ", "_")}": {{ "score": <int>, "comment": "..." }}'
            for c in rubric.criteria
        ]
    )

    # Optimize Content Size
    is_cli = "GeminiCLIAdapter" in adapter_type
    max_chars = 8000 if is_cli else 20000
    truncated_content = content[:max_chars]

    # Persona Selection
    if rubric.strictness == "hostile":
        persona = """You are a Principal Software Architect with an elite, critical eye.
        Evaluate this code/design across any programming language.
        Focus EXCLUSIVELY on:
        1. Concurrency & Thread Safety (Race conditions, deadlocks)
        2. Scalability & Performance Bottlenecks
        3. Error Handling & System Resilience
        4. Security Vulnerabilities

        Be brutal. Identify deep architectural flaws that standard linters miss."""
    elif rubric.strictness == "strict":
        persona = "You are a Senior Security and Performance Engineer. Be rigorous and demanding."
    else:
        persona = "You are a Senior Code Reviewer. Be balanced, helpful, and follow language-specific idioms."

    # Language-Aware Guidelines
    ext = os.path.splitext(filename)[1].lower()
    lang_guidelines = {
        ".py": "Follow PEP 8, highly idiomatic Python (list comprehensions where appropriate), proper type hinting.",
        ".go": "Follow 'Effective Go'. proper error handling (if err != nil), Go routines usage, strict formatting.",
        ".js": "Follow idiomatic JS/Node patterns. Async/await over callbacks, no var, use const/let.",
        ".ts": "Strict typing, interfaces vs types usage, proper generic constraints.",
        ".rs": "Idiomatic Rust: proper borrowing/ownership, Option/Result handling, no unwrap() in production.",
        ".java": "Standard Java conventions, proper OOP design patterns, Effective Java principles.",
        ".cpp": "Modern C++ (17/20) standards, RAII, smart pointers over raw pointers.",
    }
    specific_guidance = lang_guidelines.get(
        ext, "Follow standard best practices for this language."
    )

    # Check for override
    custom_prompt = settings.PROMPTS.get("grade_code")
    if custom_prompt:
        return custom_prompt.format(
            persona=persona,
            lang_guidelines=specific_guidance,
            criteria_text=criteria_text,
            filename=filename,
            content=truncated_content,
            dimensions_json=dimensions_json,
        )

    return f"""{persona}

LANGUAGE GUIDELINES ({ext}):
{specific_guidance}

RUBRIC:
{criteria_text}

CODE ({filename}):
```
{truncated_content}
```

INSTRUCTIONS:
1. Rate EACH dimension (1-5) based on the language's best practices.
2. Provide specific, actionable improvement suggestions.
3. Assign a CONFIDENCE score (0.0-1.0) reflecting your certainty.
4. Provide "Strategic Advice" (Long-term architectural direction).
5. Provide a "First Step" (Immediate, concrete action to take right now).

BIAS MITIGATION:
- Avoid Length Bias: Do not score higher just because the code is longer. Concise is often better.
- Avoid Verbosity Bias: High quality code is clean and idiomatic, not necessarily complex.
- Avoid Authority Bias: Do not assume code is correct just because it looks professional; verify the logic.

OUTPUT JSON ONLY.

{{
    "score": <float 1-5>,
    "confidence": <float 0.0-1.0>,
    "summary": "<summary>",
    "dimensions": {{
{dimensions_json}
    }},
    "suggestions": ["fix 1", "fix 2"],
    "strategic_advice": "<High-level advice for long-term health>",
    "first_step": "<The single most important immediate action>"
}}"""


def build_comparison_prompt(
    first_plan: str, second_plan: str, first_label: str, second_label: str, context: str
) -> str:
    """Build the prompt for pairwise plan comparison."""
    # Check for override
    custom_prompt = settings.PROMPTS.get("compare_plans")
    if custom_prompt:
        # Simple formatting with keywords
        return custom_prompt.format(
            context=context,
            first_plan=first_plan,
            second_plan=second_plan,
            first_label=first_label,
            second_label=second_label,
        )

    return f'''You are an expert Software Architect Judge comparing two implementation plans.

## Critical Instructions
- Do NOT prefer plans because they are longer
- Do NOT prefer plans based on position (first vs second)
- Focus ONLY on quality according to the specified criteria
- Ties are acceptable when plans are genuinely equivalent

## Context
{context}

## Plan {first_label} (First Position)
{first_plan}

## Plan {second_label} (Second Position)
{second_plan}

## Comparison Criteria
1. **Feasibility**: Can this plan be realistically implemented?
2. **Simplicity**: Is the approach straightforward without unnecessary complexity?
3. **Completeness**: Does the plan address all requirements?
4. **Maintainability**: Will the result be easy to maintain?

## Instructions
1. Analyze each plan independently first
2. Compare them on each criterion
3. Determine overall winner with confidence level

## Output Format (JSON ONLY)
{{
    "winner": "{first_label}" or "{second_label}" or "TIE",
    "confidence": <float 0.0-1.0>,
    "criteria_comparison": {{
        "feasibility": {{ "winner": "...", "reasoning": "..." }},
        "simplicity": {{ "winner": "...", "reasoning": "..." }},
        "completeness": {{ "winner": "...", "reasoning": "..." }},
        "maintainability": {{ "winner": "...", "reasoning": "..." }}
    }},
    "overall_reasoning": "..."
}}'''


def build_code_comparison_prompt(
    first_code: str, second_code: str, first_label: str, second_label: str, context: str = None
) -> str:
    """Build the prompt for pairwise code comparison."""
    # Check for override
    custom_prompt = settings.PROMPTS.get("compare_code")
    if custom_prompt:
        return custom_prompt.format(
            context=context or "Compare these two implementations.",
            first_code=first_code,
            second_code=second_code,
            first_label=first_label,
            second_label=second_label,
        )

    return f'''You are a Senior Principal Engineer performing a Code Review A/B Test.

## Context
{context or "Compare these two implementations for the same functionality."}

## Implementation {first_label} (First Position)
```
{first_code}
```

## Implementation {second_label} (Second Position)
```
{second_code}
```

## Comparison Criteria
1. **Correctness**: Does it handle edge cases and errors correctly?
2. **Efficiency**: algorithmic complexity and resource usage.
3. **Readability**: Is it clean, idiomatic, and maintainable?
4. **Safety**: Type safety, memory safety, and security.

## Instructions
1. Analyze each implementation independently.
2. Compare them strictly on the criteria.
3. Ignore formatting differences unless they affect readability.
4. Select the superior implementation.

## Output Format (JSON ONLY)
{{
    "winner": "{first_label}" or "{second_label}" or "TIE",
    "confidence": <float 0.0-1.0>,
    "criteria_comparison": {{
        "correctness": {{ "winner": "...", "reasoning": "..." }},
        "efficiency": {{ "winner": "...", "reasoning": "..." }},
        "readability": {{ "winner": "...", "reasoning": "..." }},
        "safety": {{ "winner": "...", "reasoning": "..." }}
    }},
    "overall_reasoning": "..."
}}'''
