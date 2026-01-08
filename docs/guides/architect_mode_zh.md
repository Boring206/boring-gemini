# 架構師模式指南 (Architect Mode Guide V10.16)

## 概述
架構師模式是透過 `PRODUCTION_RUBRIC` 啟動的特殊評估模式。它會將 AI 的人設從「友善的代碼審查員」切換為「嚴厲的首席架構師」。

## 如何使用
執行 `boring evaluate` 並加上 `--level production` 旗標：

```bash
boring evaluate src/core/database.py --level production
```

## 預期結果
這位嚴厲架構師 **不會** 在意：
- 變數命名
- PEP 8 格式問題
- 缺少的 docstrings (除非非常關鍵)

它 **會** 針對你的設計進行猛烈攻擊：
1.  **並發性 (Concurrency)**: "在高負載下，這個鎖的實作會導致死鎖 (Deadlock)。"
2.  **擴展性 (Scalability)**: "這個 N+1 查詢模式在 10k RPS 時會搞垮你的資料庫。"
3.  **韌性 (Resilience)**: "這個外部 API 呼叫的斷路器 (Circuit Breaker) 在哪裡？"
4.  **技術堆疊 (Tech Stack)**: "為什麼用 `requests` (blocking) 而不是 `httpx` (async)？"

## 設定
如果你覺得架構師太兇（或不夠兇），可以在 `src/boring/judge.py` 中自訂 Prompt。
