# 評估指標指南 (Evaluation Metrics Guide)

boring-gemini V10.25 新增的 LLM-as-a-Judge 評估系統，提供完整的統計指標來驗證評估品質。

---

## 📊 核心指標總覽

| 指標 | 測量什麼 | 適用場景 | 範圍 |
|------|----------|----------|------|
| **Cohen's κ (Kappa)** | 兩個評審者的**一致性** | AI 評分 vs 人類評審 | -1 ~ 1 |
| **Spearman's ρ (Rho)** | 兩組排名的**相關性** | 分數的排序是否一致 | -1 ~ 1 |
| **F1 Score** | 分類的**準確度** | 通過/不通過 等二分類 | 0 ~ 1 |
| **Position Consistency** | 成對比較的**穩定性** | A vs B 比較是否有偏見 | 0 ~ 1 |

---

## 🎯 詳細說明

### 1️⃣ Cohen's Kappa (一致性指標)

**問題**：「AI 評分跟人類專家一致嗎？」

```python
from boring.judge.metrics import cohens_kappa

human_scores = [4, 3, 5, 2, 4]
ai_scores = [4, 3, 4, 2, 4]  # 第3個不同 (5 vs 4)

kappa = cohens_kappa(ai_scores, human_scores)
print(f"Kappa: {kappa:.2f}")  # 0.71 - 高度一致
```

**解讀標準**：

| κ 值 | 解讀 |
|------|------|
| > 0.8 | 幾乎完美一致 |
| 0.6-0.8 | **高度一致** ✅ |
| 0.4-0.6 | 中等一致 |
| 0.2-0.4 | 一般一致 |
| < 0.2 | 微弱一致 |

**用途**：驗證 AI 評估系統是否可以**取代人類審查**

---

### 2️⃣ Spearman's ρ (相關性指標)

**問題**：「AI 排名順序跟人類一樣嗎？」

```python
from boring.judge.metrics import spearmans_rho

human_ranks = [1, 2, 3, 4, 5]
ai_ranks = [1, 2, 3, 4, 5]  # 排名完全一致

rho, p_value = spearmans_rho(ai_ranks, human_ranks)
print(f"Spearman ρ: {rho:.2f}")  # 1.0 - 完美相關
```

**解讀標準**：

| ρ 值 | 解讀 |
|------|------|
| > 0.9 | **強相關** ✅ |
| 0.7-0.9 | 中相關 |
| 0.5-0.7 | 弱相關 |
| < 0.5 | 無顯著相關 |

**用途**：即使分數數值不同，驗證**排序是否正確**

> [!TIP]
> Spearman 適合序數資料（如 1-5 分評分），因為它只看排名順序，不受分數絕對值影響。

---

### 3️⃣ F1 Score (分類準確度)

**問題**：「AI 判斷通過/不通過準確嗎？」

```python
from boring.judge.metrics import f1_score

actual = [1, 1, 0, 1]    # 1=通過, 0=不通過
predicted = [1, 0, 0, 1]  # AI 預測

f1 = f1_score(predicted, actual)
print(f"F1: {f1:.2f}")  # 0.80
```

**公式**：

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

**用途**：評估**二分類判斷**的準確性

---

### 4️⃣ Position Consistency (位置一致性)

**問題**：「成對比較有沒有位置偏見？」

```python
from boring.judge.metrics import pairwise_metrics

comparisons = [
    {"winner": "A", "position_consistent": True},
    {"winner": "B", "position_consistent": True},
    {"winner": "A", "position_consistent": False},  # 位置不一致
]

metrics = pairwise_metrics(comparisons)
print(f"Position Consistency: {metrics.position_consistency:.0%}")  # 67%
```

**用途**：檢測**位置偏見**（第一個選項被偏好的傾向）

---

## 📈 何時使用哪個指標？

| 你的評估任務 | 推薦指標 |
|--------------|----------|
| 給程式碼打 1-5 分 | **Kappa** + **Spearman** |
| 判斷程式碼 好/壞 | **F1 Score** |
| 比較兩段程式碼誰更好 | **Position Consistency** |
| 檢查 AI 評分有沒有偏見 | **Bias Report** |

---

## 🔧 MCP 工具使用

### 查看評估指標

```
boring_evaluation_metrics
```

### 查看偏見報告

```
boring_bias_report
```

### 自然語言觸發

```
boring "show evaluation metrics"
boring "評估指標"
boring "show me the bias report"
boring "查看偏見報告"
```

---

## 📚 進階資源

- [LLM-as-a-Judge 論文](https://arxiv.org/abs/2306.05685)
- [Cohen's Kappa 詳解](https://en.wikipedia.org/wiki/Cohen%27s_kappa)
- [Spearman 相關係數](https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient)
