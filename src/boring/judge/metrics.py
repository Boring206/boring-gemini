# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Evaluation Metrics Module - Advanced Evaluation V10.25

Implements statistical metrics for LLM-as-a-Judge evaluation systems.
Based on the Advanced Evaluation skill framework.

Features:
1. Classification metrics (Precision, Recall, F1)
2. Agreement metrics (Cohen's Kappa, Weighted Kappa)
3. Correlation metrics (Spearman's ρ, Kendall's τ, Pearson's r)
4. Pairwise comparison metrics (Position Consistency, Agreement Rate)
5. Comprehensive metrics reporting
"""

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClassificationMetrics:
    """Metrics for binary/multi-class evaluation."""

    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


@dataclass
class AgreementMetrics:
    """Metrics for comparing automated evaluation with human judgment."""

    cohens_kappa: float
    weighted_kappa: Optional[float] = None
    observed_agreement: float = 0.0
    expected_agreement: float = 0.0
    interpretation: str = ""


@dataclass
class CorrelationMetrics:
    """Metrics for ordinal/continuous score correlation."""

    spearmans_rho: float
    kendalls_tau: float
    pearsons_r: float
    p_value_spearman: float = 0.0
    p_value_kendall: float = 0.0
    p_value_pearson: float = 0.0
    interpretation: str = ""


@dataclass
class PairwiseMetrics:
    """Metrics for pairwise comparison evaluation."""

    agreement_rate: float
    position_consistency: float
    tie_rate: float
    total_comparisons: int
    consistent_decisions: int


@dataclass
class EvaluationMetricsReport:
    """Comprehensive evaluation metrics report."""

    classification: Optional[ClassificationMetrics] = None
    agreement: Optional[AgreementMetrics] = None
    correlation: Optional[CorrelationMetrics] = None
    pairwise: Optional[PairwiseMetrics] = None
    sample_size: int = 0
    evaluation_type: str = ""
    warnings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


# ==============================================================================
# Classification Metrics
# ==============================================================================


def precision(predictions: list[int], ground_truth: list[int]) -> float:
    """
    Calculate precision: TP / (TP + FP)

    Args:
        predictions: List of predicted labels (1 = positive, 0 = negative)
        ground_truth: List of actual labels

    Returns:
        Precision score (0.0 to 1.0)
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")

    true_positives = sum(1 for p, g in zip(predictions, ground_truth) if p == 1 and g == 1)
    predicted_positives = sum(predictions)

    return true_positives / predicted_positives if predicted_positives > 0 else 0.0


def recall(predictions: list[int], ground_truth: list[int]) -> float:
    """
    Calculate recall: TP / (TP + FN)

    Args:
        predictions: List of predicted labels
        ground_truth: List of actual labels

    Returns:
        Recall score (0.0 to 1.0)
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")

    true_positives = sum(1 for p, g in zip(predictions, ground_truth) if p == 1 and g == 1)
    actual_positives = sum(ground_truth)

    return true_positives / actual_positives if actual_positives > 0 else 0.0


def f1_score(predictions: list[int], ground_truth: list[int]) -> float:
    """
    Calculate F1 score: 2 * (precision * recall) / (precision + recall)

    Args:
        predictions: List of predicted labels
        ground_truth: List of actual labels

    Returns:
        F1 score (0.0 to 1.0)
    """
    p = precision(predictions, ground_truth)
    r = recall(predictions, ground_truth)
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def classification_metrics(
    predictions: list[int], ground_truth: list[int]
) -> ClassificationMetrics:
    """
    Calculate all classification metrics.

    Args:
        predictions: List of predicted labels
        ground_truth: List of actual labels

    Returns:
        ClassificationMetrics with all metrics
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")

    tp = sum(1 for p, g in zip(predictions, ground_truth) if p == 1 and g == 1)
    fp = sum(1 for p, g in zip(predictions, ground_truth) if p == 1 and g == 0)
    fn = sum(1 for p, g in zip(predictions, ground_truth) if p == 0 and g == 1)
    tn = sum(1 for p, g in zip(predictions, ground_truth) if p == 0 and g == 0)

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    return ClassificationMetrics(
        precision=prec,
        recall=rec,
        f1_score=f1,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
    )


# ==============================================================================
# Agreement Metrics
# ==============================================================================


def cohens_kappa(judge1: list, judge2: list) -> float:
    """
    Calculate Cohen's Kappa for inter-rater agreement.

    κ = (Observed Agreement - Expected Agreement) / (1 - Expected Agreement)

    Args:
        judge1: Ratings from first judge
        judge2: Ratings from second judge

    Returns:
        Cohen's Kappa (-1.0 to 1.0)
    """
    if len(judge1) != len(judge2):
        raise ValueError("Judge ratings must have same length")

    n = len(judge1)
    if n == 0:
        return 0.0

    # Get all unique categories
    categories = list(set(judge1) | set(judge2))

    # Count agreements
    observed_agreement = sum(1 for j1, j2 in zip(judge1, judge2) if j1 == j2) / n

    # Calculate expected agreement by chance
    expected_agreement = 0.0
    for cat in categories:
        p1 = sum(1 for j in judge1 if j == cat) / n
        p2 = sum(1 for j in judge2 if j == cat) / n
        expected_agreement += p1 * p2

    # Calculate kappa
    if expected_agreement == 1.0:
        return 1.0 if observed_agreement == 1.0 else 0.0

    kappa = (observed_agreement - expected_agreement) / (1 - expected_agreement)
    return kappa


def weighted_kappa(judge1: list[int], judge2: list[int], weights: str = "quadratic") -> float:
    """
    Calculate weighted Cohen's Kappa for ordinal scales.

    Args:
        judge1: Ratings from first judge (ordinal integers)
        judge2: Ratings from second judge (ordinal integers)
        weights: Weighting scheme - 'linear' or 'quadratic'

    Returns:
        Weighted Kappa (-1.0 to 1.0)
    """
    if len(judge1) != len(judge2):
        raise ValueError("Judge ratings must have same length")

    n = len(judge1)
    if n == 0:
        return 0.0

    # Get all unique categories (ordered)
    categories = sorted(set(judge1) | set(judge2))
    k = len(categories)

    if k < 2:
        return 1.0 if all(j1 == j2 for j1, j2 in zip(judge1, judge2)) else 0.0

    # Create category index mapping
    cat_to_idx = {cat: i for i, cat in enumerate(categories)}

    # Calculate weight matrix
    weight_matrix = []
    for i in range(k):
        row = []
        for j in range(k):
            if weights == "linear":
                w = abs(i - j) / (k - 1)
            else:  # quadratic
                w = ((i - j) ** 2) / ((k - 1) ** 2)
            row.append(w)
        weight_matrix.append(row)

    # Count confusion matrix
    confusion = [[0] * k for _ in range(k)]
    for j1, j2 in zip(judge1, judge2):
        i1 = cat_to_idx[j1]
        i2 = cat_to_idx[j2]
        confusion[i1][i2] += 1

    # Calculate observed disagreement
    observed = sum(weight_matrix[i][j] * confusion[i][j] for i in range(k) for j in range(k)) / n

    # Calculate expected disagreement
    row_marginals = [sum(confusion[i]) / n for i in range(k)]
    col_marginals = [sum(confusion[i][j] for i in range(k)) / n for j in range(k)]

    expected = sum(
        weight_matrix[i][j] * row_marginals[i] * col_marginals[j]
        for i in range(k)
        for j in range(k)
    )

    # Calculate weighted kappa
    if expected == 0:
        return 1.0 if observed == 0 else 0.0

    return 1 - (observed / expected)


def interpret_kappa(kappa: float) -> str:
    """Interpret Cohen's Kappa value."""
    if kappa > 0.8:
        return "Almost perfect agreement"
    elif kappa > 0.6:
        return "Substantial agreement"
    elif kappa > 0.4:
        return "Moderate agreement"
    elif kappa > 0.2:
        return "Fair agreement"
    else:
        return "Poor agreement"


def agreement_metrics(judge1: list, judge2: list, ordinal: bool = False) -> AgreementMetrics:
    """
    Calculate all agreement metrics.

    Args:
        judge1: Ratings from first judge
        judge2: Ratings from second judge
        ordinal: If True, calculate weighted kappa for ordinal scales

    Returns:
        AgreementMetrics with all metrics
    """
    n = len(judge1)
    observed = sum(1 for j1, j2 in zip(judge1, judge2) if j1 == j2) / n if n > 0 else 0

    kappa = cohens_kappa(judge1, judge2)
    w_kappa = weighted_kappa(judge1, judge2) if ordinal else None

    # Calculate expected agreement
    categories = list(set(judge1) | set(judge2))
    expected = 0.0
    for cat in categories:
        p1 = sum(1 for j in judge1 if j == cat) / n if n > 0 else 0
        p2 = sum(1 for j in judge2 if j == cat) / n if n > 0 else 0
        expected += p1 * p2

    return AgreementMetrics(
        cohens_kappa=kappa,
        weighted_kappa=w_kappa,
        observed_agreement=observed,
        expected_agreement=expected,
        interpretation=interpret_kappa(kappa),
    )


# ==============================================================================
# Correlation Metrics
# ==============================================================================


def _rank(data: list[float]) -> list[float]:
    """Convert values to ranks, handling ties with average rank."""
    sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
    ranks = [0.0] * len(data)

    i = 0
    while i < len(sorted_indices):
        j = i
        # Find all elements with the same value
        while j < len(sorted_indices) and data[sorted_indices[j]] == data[sorted_indices[i]]:
            j += 1
        # Assign average rank to all tied elements
        avg_rank = (i + j + 1) / 2
        for k in range(i, j):
            ranks[sorted_indices[k]] = avg_rank
        i = j

    return ranks


def spearmans_rho(scores1: list[float], scores2: list[float]) -> tuple[float, float]:
    """
    Calculate Spearman's rank correlation coefficient.

    Args:
        scores1: First set of scores
        scores2: Second set of scores

    Returns:
        Tuple of (rho, p_value)
    """
    if len(scores1) != len(scores2):
        raise ValueError("Score lists must have same length")

    n = len(scores1)
    if n < 3:
        return 0.0, 1.0

    # Convert to ranks
    ranks1 = _rank(scores1)
    ranks2 = _rank(scores2)

    # Calculate Spearman's rho using Pearson on ranks
    mean1 = sum(ranks1) / n
    mean2 = sum(ranks2) / n

    numerator = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(ranks1, ranks2))
    denom1 = math.sqrt(sum((r1 - mean1) ** 2 for r1 in ranks1))
    denom2 = math.sqrt(sum((r2 - mean2) ** 2 for r2 in ranks2))

    if denom1 == 0 or denom2 == 0:
        return 0.0, 1.0

    rho = numerator / (denom1 * denom2)

    # Approximate p-value using t-distribution
    if abs(rho) == 1.0:
        p_value = 0.0
    else:
        t_stat = rho * math.sqrt((n - 2) / (1 - rho**2))
        # Simplified p-value approximation
        p_value = 2 * (1 - _cdf_t(abs(t_stat), n - 2))

    return rho, p_value


def kendalls_tau(scores1: list[float], scores2: list[float]) -> tuple[float, float]:
    """
    Calculate Kendall's tau correlation coefficient.

    Args:
        scores1: First set of scores
        scores2: Second set of scores

    Returns:
        Tuple of (tau, p_value)
    """
    if len(scores1) != len(scores2):
        raise ValueError("Score lists must have same length")

    n = len(scores1)
    if n < 2:
        return 0.0, 1.0

    concordant = 0
    discordant = 0

    for i in range(n):
        for j in range(i + 1, n):
            x_diff = scores1[i] - scores1[j]
            y_diff = scores2[i] - scores2[j]

            if x_diff * y_diff > 0:
                concordant += 1
            elif x_diff * y_diff < 0:
                discordant += 1
            # Ties are ignored

    total = concordant + discordant
    if total == 0:
        return 0.0, 1.0

    tau = (concordant - discordant) / total

    # Approximate p-value
    var = (2 * (2 * n + 5)) / (9 * n * (n - 1))
    z = tau / math.sqrt(var) if var > 0 else 0
    p_value = 2 * (1 - _cdf_normal(abs(z)))

    return tau, p_value


def pearsons_r(scores1: list[float], scores2: list[float]) -> tuple[float, float]:
    """
    Calculate Pearson's correlation coefficient.

    Args:
        scores1: First set of scores
        scores2: Second set of scores

    Returns:
        Tuple of (r, p_value)
    """
    if len(scores1) != len(scores2):
        raise ValueError("Score lists must have same length")

    n = len(scores1)
    if n < 3:
        return 0.0, 1.0

    mean1 = sum(scores1) / n
    mean2 = sum(scores2) / n

    numerator = sum((s1 - mean1) * (s2 - mean2) for s1, s2 in zip(scores1, scores2))
    denom1 = math.sqrt(sum((s1 - mean1) ** 2 for s1 in scores1))
    denom2 = math.sqrt(sum((s2 - mean2) ** 2 for s2 in scores2))

    if denom1 == 0 or denom2 == 0:
        return 0.0, 1.0

    r = numerator / (denom1 * denom2)

    # Approximate p-value
    if abs(r) == 1.0:
        p_value = 0.0
    else:
        t_stat = r * math.sqrt((n - 2) / (1 - r**2))
        p_value = 2 * (1 - _cdf_t(abs(t_stat), n - 2))

    return r, p_value


def _cdf_normal(z: float) -> float:
    """Approximate CDF of standard normal distribution."""
    # Approximation using error function
    return (1 + math.erf(z / math.sqrt(2))) / 2


def _cdf_t(t: float, df: int) -> float:
    """Approximate CDF of t-distribution."""
    # Simplified approximation for large df
    if df > 30:
        return _cdf_normal(t)
    # For smaller df, use rougher approximation
    x = df / (df + t**2)
    return 1 - 0.5 * (1 - math.sqrt(1 - x))


def interpret_correlation(rho: float) -> str:
    """Interpret correlation coefficient."""
    abs_rho = abs(rho)
    if abs_rho > 0.9:
        return "Very strong correlation"
    elif abs_rho > 0.7:
        return "Strong correlation"
    elif abs_rho > 0.5:
        return "Moderate correlation"
    elif abs_rho > 0.3:
        return "Weak correlation"
    else:
        return "Very weak or no correlation"


def correlation_metrics(scores1: list[float], scores2: list[float]) -> CorrelationMetrics:
    """
    Calculate all correlation metrics.

    Args:
        scores1: First set of scores
        scores2: Second set of scores

    Returns:
        CorrelationMetrics with all metrics
    """
    rho, p_rho = spearmans_rho(scores1, scores2)
    tau, p_tau = kendalls_tau(scores1, scores2)
    r, p_r = pearsons_r(scores1, scores2)

    return CorrelationMetrics(
        spearmans_rho=rho,
        kendalls_tau=tau,
        pearsons_r=r,
        p_value_spearman=p_rho,
        p_value_kendall=p_tau,
        p_value_pearson=p_r,
        interpretation=interpret_correlation(rho),
    )


# ==============================================================================
# Pairwise Comparison Metrics
# ==============================================================================


def position_consistency(comparisons: list[dict]) -> float:
    """
    Calculate position consistency rate.

    Args:
        comparisons: List of comparison results with 'position_consistent' field

    Returns:
        Proportion of consistent decisions (0.0 to 1.0)
    """
    if not comparisons:
        return 0.0

    consistent = sum(
        1 for c in comparisons if c.get("position_consistent", c.get("positionConsistency", False))
    )
    return consistent / len(comparisons)


def agreement_rate(decisions1: list[str], decisions2: list[str]) -> float:
    """
    Calculate simple agreement rate between two sets of decisions.

    Args:
        decisions1: First set of decisions (A/B/TIE)
        decisions2: Second set of decisions

    Returns:
        Proportion of matching decisions (0.0 to 1.0)
    """
    if len(decisions1) != len(decisions2):
        raise ValueError("Decision lists must have same length")

    if not decisions1:
        return 0.0

    matches = sum(1 for d1, d2 in zip(decisions1, decisions2) if d1 == d2)
    return matches / len(decisions1)


def pairwise_metrics(comparisons: list[dict]) -> PairwiseMetrics:
    """
    Calculate all pairwise comparison metrics.

    Args:
        comparisons: List of comparison results with 'winner' and 'position_consistent' fields

    Returns:
        PairwiseMetrics with all metrics
    """
    if not comparisons:
        return PairwiseMetrics(
            agreement_rate=0.0,
            position_consistency=0.0,
            tie_rate=0.0,
            total_comparisons=0,
            consistent_decisions=0,
        )

    total = len(comparisons)
    ties = sum(1 for c in comparisons if c.get("winner", "").upper() == "TIE")
    consistent = sum(
        1 for c in comparisons if c.get("position_consistent", c.get("positionConsistency", False))
    )

    return PairwiseMetrics(
        agreement_rate=consistent / total,
        position_consistency=consistent / total,
        tie_rate=ties / total,
        total_comparisons=total,
        consistent_decisions=consistent,
    )


# ==============================================================================
# Comprehensive Report Generation
# ==============================================================================


def generate_metrics_report(
    automated_scores: Optional[list[float]] = None,
    human_scores: Optional[list[float]] = None,
    predictions: Optional[list[int]] = None,
    ground_truth: Optional[list[int]] = None,
    pairwise_comparisons: Optional[list[dict]] = None,
    evaluation_type: str = "general",
) -> EvaluationMetricsReport:
    """
    Generate comprehensive evaluation metrics report.

    Args:
        automated_scores: Scores from automated evaluation
        human_scores: Scores from human evaluation
        predictions: Binary predictions (for classification)
        ground_truth: Ground truth labels (for classification)
        pairwise_comparisons: Pairwise comparison results
        evaluation_type: Type of evaluation (ordinal, binary, pairwise)

    Returns:
        EvaluationMetricsReport with all applicable metrics
    """
    report = EvaluationMetricsReport(evaluation_type=evaluation_type)
    warnings = []
    recommendations = []

    # Classification metrics
    if predictions is not None and ground_truth is not None:
        report.classification = classification_metrics(predictions, ground_truth)
        report.sample_size = len(predictions)

        if report.classification.precision < 0.7:
            warnings.append("Precision below 0.7 - high false positive rate")
        if report.classification.recall < 0.7:
            warnings.append("Recall below 0.7 - high false negative rate")

    # Correlation/Agreement metrics
    if automated_scores is not None and human_scores is not None:
        report.correlation = correlation_metrics(automated_scores, human_scores)
        report.sample_size = len(automated_scores)

        # Agreement for ordinal scales
        if evaluation_type == "ordinal":
            # Round to integers for agreement calculation
            j1 = [round(s) for s in automated_scores]
            j2 = [round(s) for s in human_scores]
            report.agreement = agreement_metrics(j1, j2, ordinal=True)

        if report.correlation.spearmans_rho < 0.6:
            warnings.append("Spearman's ρ below 0.6 - weak correlation with human judgment")
            recommendations.append("Review evaluation criteria for clarity")

    # Pairwise metrics
    if pairwise_comparisons is not None:
        report.pairwise = pairwise_metrics(pairwise_comparisons)
        report.sample_size = len(pairwise_comparisons)

        if report.pairwise.position_consistency < 0.8:
            warnings.append("Position consistency below 0.8 - position bias may be present")
            recommendations.append("Increase number of position swaps or use multiple passes")

        if report.pairwise.tie_rate > 0.3:
            warnings.append("High tie rate (>30%) - criteria may need refinement")

    # Sample size warning
    if report.sample_size < 50:
        warnings.append(f"Small sample size ({report.sample_size}) - metrics may be unreliable")
        recommendations.append("Collect more evaluation samples for reliable metrics")

    report.warnings = warnings
    report.recommendations = recommendations

    return report


def format_metrics_report(report: EvaluationMetricsReport) -> str:
    """Format metrics report as markdown."""
    lines = ["# 📊 Evaluation Metrics Report", ""]

    lines.append(f"**Evaluation Type**: {report.evaluation_type}")
    lines.append(f"**Sample Size**: {report.sample_size}")
    lines.append("")

    # Classification metrics
    if report.classification:
        lines.append("## Classification Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Precision | {report.classification.precision:.3f} |")
        lines.append(f"| Recall | {report.classification.recall:.3f} |")
        lines.append(f"| F1 Score | {report.classification.f1_score:.3f} |")
        lines.append("")

    # Correlation metrics
    if report.correlation:
        lines.append("## Correlation Metrics")
        lines.append("")
        lines.append("| Metric | Value | p-value |")
        lines.append("|--------|-------|---------|")
        lines.append(
            f"| Spearman's ρ | {report.correlation.spearmans_rho:.3f} | {report.correlation.p_value_spearman:.4f} |"
        )
        lines.append(
            f"| Kendall's τ | {report.correlation.kendalls_tau:.3f} | {report.correlation.p_value_kendall:.4f} |"
        )
        lines.append(
            f"| Pearson's r | {report.correlation.pearsons_r:.3f} | {report.correlation.p_value_pearson:.4f} |"
        )
        lines.append("")
        lines.append(f"**Interpretation**: {report.correlation.interpretation}")
        lines.append("")

    # Agreement metrics
    if report.agreement:
        lines.append("## Agreement Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Cohen's κ | {report.agreement.cohens_kappa:.3f} |")
        if report.agreement.weighted_kappa is not None:
            lines.append(f"| Weighted κ | {report.agreement.weighted_kappa:.3f} |")
        lines.append(f"| Observed Agreement | {report.agreement.observed_agreement:.3f} |")
        lines.append("")
        lines.append(f"**Interpretation**: {report.agreement.interpretation}")
        lines.append("")

    # Pairwise metrics
    if report.pairwise:
        lines.append("## Pairwise Comparison Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Position Consistency | {report.pairwise.position_consistency:.1%} |")
        lines.append(f"| Tie Rate | {report.pairwise.tie_rate:.1%} |")
        lines.append(f"| Total Comparisons | {report.pairwise.total_comparisons} |")
        lines.append("")

    # Warnings
    if report.warnings:
        lines.append("## ⚠️ Warnings")
        lines.append("")
        for warning in report.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("## 💡 Recommendations")
        lines.append("")
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    return "\n".join(lines)
