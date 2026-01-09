"""
Judge Package - V10.25 Advanced Evaluation

Provides LLM-as-a-Judge evaluation capabilities including:
- Code quality grading with customizable rubrics
- Pairwise comparison with position bias detection
- Evaluation metrics (Kappa, Spearman, F1)
- Bias monitoring and reporting
"""

from ..config import settings
from .bias_monitor import (
    BiasMonitor,
    BiasReport,
    LengthBiasResult,
    PositionBiasResult,
    format_bias_report,
    get_bias_monitor,
)
from .core import LLMJudge
from .factory import create_judge_provider

# V10.25: Advanced Evaluation exports
from .metrics import (
    agreement_metrics,
    classification_metrics,
    cohens_kappa,
    correlation_metrics,
    f1_score,
    format_metrics_report,
    generate_metrics_report,
    kendalls_tau,
    pairwise_metrics,
    pearsons_r,
    precision,
    recall,
    spearmans_rho,
    weighted_kappa,
)
from .rubric_generator import (
    DetailedCriterion,
    DetailedRubric,
    EdgeCase,
    RubricLevel,
    format_rubric_json,
    generate_code_quality_rubric,
    generate_rubric,
    generate_security_rubric,
    rubric_to_prompt,
)

# V10.26 Reorganized Modules (moved from root)
from .rubrics import CODE_QUALITY_RUBRIC, SECURITY_RUBRIC, Criterion, Rubric

__all__ = [
    # Core
    "LLMJudge",
    "create_judge_provider",
    "settings",
    # Metrics
    "cohens_kappa",
    "weighted_kappa",
    "spearmans_rho",
    "kendalls_tau",
    "pearsons_r",
    "f1_score",
    "precision",
    "recall",
    "classification_metrics",
    "agreement_metrics",
    "correlation_metrics",
    "pairwise_metrics",
    "generate_metrics_report",
    "format_metrics_report",
    # Bias Monitor
    "BiasMonitor",
    "BiasReport",
    "PositionBiasResult",
    "LengthBiasResult",
    "get_bias_monitor",
    "format_bias_report",
    # Rubric Generator
    "DetailedRubric",
    "DetailedCriterion",
    "RubricLevel",
    "EdgeCase",
    "generate_rubric",
    "generate_code_quality_rubric",
    "generate_security_rubric",
    "rubric_to_prompt",
    "format_rubric_json",
    # V10.26 Reorganized (simple rubrics)
    "Rubric",
    "Criterion",
    "CODE_QUALITY_RUBRIC",
    "SECURITY_RUBRIC",
]
