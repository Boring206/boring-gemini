# Evaluation Metrics Guide

boring-gemini V10.25 introduces a comprehensive LLM-as-a-Judge evaluation system with statistical metrics to verify evaluation quality.

---

## 📊 Core Metrics Overview

| Metric | What It Measures | Use Case | Range |
|--------|------------------|----------|-------|
| **Cohen's κ (Kappa)** | Agreement between two raters | AI vs Human scoring | -1 ~ 1 |
| **Spearman's ρ (Rho)** | Rank correlation | Are rankings consistent? | -1 ~ 1 |
| **F1 Score** | Classification accuracy | Pass/Fail decisions | 0 ~ 1 |
| **Position Consistency** | Pairwise comparison stability | Is there position bias? | 0 ~ 1 |

---

## 🎯 Detailed Explanations

### 1️⃣ Cohen's Kappa (Agreement Metric)

**Question**: "Does AI scoring agree with human experts?"

```python
from boring.judge.metrics import cohens_kappa

human_scores = [4, 3, 5, 2, 4]
ai_scores = [4, 3, 4, 2, 4]  # 3rd differs (5 vs 4)

kappa = cohens_kappa(ai_scores, human_scores)
print(f"Kappa: {kappa:.2f}")  # 0.71 - Substantial agreement
```

**Interpretation**:

| κ Value | Interpretation |
|---------|----------------|
| > 0.8 | Almost perfect agreement |
| 0.6-0.8 | **Substantial agreement** ✅ |
| 0.4-0.6 | Moderate agreement |
| 0.2-0.4 | Fair agreement |
| < 0.2 | Slight agreement |

**Purpose**: Validate if AI evaluation can **replace human review**

---

### 2️⃣ Spearman's ρ (Correlation Metric)

**Question**: "Is AI ranking order same as human ranking?"

```python
from boring.judge.metrics import spearmans_rho

human_ranks = [1, 2, 3, 4, 5]
ai_ranks = [1, 2, 3, 4, 5]  # Perfect match

rho, p_value = spearmans_rho(ai_ranks, human_ranks)
print(f"Spearman ρ: {rho:.2f}")  # 1.0 - Perfect correlation
```

**Interpretation**:

| ρ Value | Interpretation |
|---------|----------------|
| > 0.9 | **Strong correlation** ✅ |
| 0.7-0.9 | Moderate correlation |
| 0.5-0.7 | Weak correlation |
| < 0.5 | No significant correlation |

**Purpose**: Verify **ranking is correct** even if absolute scores differ

> [!TIP]
> Spearman is ideal for ordinal data (like 1-5 ratings) because it only considers rank order, not absolute values.

---

### 3️⃣ F1 Score (Classification Accuracy)

**Question**: "Is AI pass/fail judgment accurate?"

```python
from boring.judge.metrics import f1_score

actual = [1, 1, 0, 1]    # 1=pass, 0=fail
predicted = [1, 0, 0, 1]  # AI predictions

f1 = f1_score(predicted, actual)
print(f"F1: {f1:.2f}")  # 0.80
```

**Formula**:

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

**Purpose**: Evaluate **binary classification** accuracy

---

### 4️⃣ Position Consistency

**Question**: "Is there position bias in pairwise comparison?"

```python
from boring.judge.metrics import pairwise_metrics

comparisons = [
    {"winner": "A", "position_consistent": True},
    {"winner": "B", "position_consistent": True},
    {"winner": "A", "position_consistent": False},  # Inconsistent
]

metrics = pairwise_metrics(comparisons)
print(f"Position Consistency: {metrics.position_consistency:.0%}")  # 67%
```

**Purpose**: Detect **position bias** (preference for first option)

---

## 📈 When to Use Which Metric?

| Your Evaluation Task | Recommended Metric |
|---------------------|-------------------|
| Rate code 1-5 | **Kappa** + **Spearman** |
| Judge code Good/Bad | **F1 Score** |
| Compare two code snippets | **Position Consistency** |
| Check for AI bias | **Bias Report** |

---

## 🔧 MCP Tool Usage

### View Evaluation Metrics

```
boring_evaluation_metrics
```

### View Bias Report

```
boring_bias_report
```

### Natural Language Triggers

```
boring "show evaluation metrics"
boring "評估指標"
boring "show me the bias report"
boring "查看偏見報告"
```

---

## 📚 Further Reading

- [LLM-as-a-Judge Paper](https://arxiv.org/abs/2306.05685)
- [Cohen's Kappa Explained](https://en.wikipedia.org/wiki/Cohen%27s_kappa)
- [Spearman Correlation](https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient)
