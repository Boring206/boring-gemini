import asyncio

import pytest

from boring.intelligence.agent_scorer import AgentScorer


@pytest.mark.asyncio
async def test_scorer_record_and_retrieve(tmp_path):
    db_path = tmp_path / "test_scores.db"
    scorer = AgentScorer(db_path=db_path)

    # Record some metrics
    await scorer.record_metric("agent_a", "latency_ms", 100.0)
    await scorer.record_metric("agent_a", "success", 1.0)  # 1 = True
    await scorer.record_metric("agent_a", "cost_usd", 0.01)

    # Record another run
    await scorer.record_metric("agent_a", "latency_ms", 200.0)
    await scorer.record_metric("agent_a", "success", 0.0)  # Fail

    stats = await scorer.get_agent_stats("agent_a")

    assert stats["avg_latency_ms"] == 150.0
    assert stats["success_rate"] == 0.5  # (1 success / 2 trials)
    # Update logic: Simple COUNT(*) in query counts ALL rows for agent_id + metric_type='success'
    # So if I recorded success=1 and success=0, count is 2. Sum is 1. Rate is 0.5. Correct.

    assert stats["total_cost_usd"] == 0.01


@pytest.mark.asyncio
async def test_scorer_concurrency(tmp_path):
    db_path = tmp_path / "concurrent.db"
    scorer = AgentScorer(db_path=db_path)

    # Run 50 concurrent writes
    tasks = []
    for _i in range(50):
        tasks.append(scorer.record_metric("agent_b", "success", 1.0))

    await asyncio.gather(*tasks)

    stats = await scorer.get_agent_stats("agent_b")
    # Actually success_rate logic divides successes/total
    # If I recorded 50 successes
    # count=50, sum=50, rate=1.0

    # Let's verify sample size
    # sample_size in get_agent_stats comes from success metric query
    assert stats["sample_size"] == 50
    assert stats["success_rate"] == 1.0
