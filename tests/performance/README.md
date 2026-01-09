# Performance Testing Configuration

## Overview
This directory contains performance benchmarks to prevent performance regressions and validate performance improvements.

## Installation
```bash
pip install pytest-benchmark psutil
```

## Running Benchmarks

### Run all benchmarks
```bash
pytest tests/performance/ --benchmark-only -v
```

### Run specific benchmark
```bash
pytest tests/performance/test_benchmarks.py::TestCorePerformance::test_module_import_time -v
```

### Generate benchmark report
```bash
pytest tests/performance/ --benchmark-only --benchmark-autosave
```

### Compare with baseline
```bash
pytest tests/performance/ --benchmark-only --benchmark-compare=0001
```

## Performance Baselines

Current performance targets:

| Metric | Target | Notes |
|--------|--------|-------|
| Module Import | < 2s | Initial import time |
| Config Loading | < 0.5s | Configuration initialization |
| Code Search | < 100ms | Mock search operation |
| Memory Footprint | < 50MB | Basic configuration memory |

## Adding New Benchmarks

1. Create test function with `benchmark` fixture
2. Use `benchmark(function, *args)` to measure
3. Add assertions for performance targets
4. Document baseline in `PERFORMANCE_BASELINES`

Example:
```python
def test_new_operation(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert benchmark.stats.stats.mean < 1.0  # < 1 second
```

## CI Integration

Performance tests run in CI on every PR to prevent regressions.
See `.github/workflows/quality-gates.yml` for configuration.

## Tracking Performance Over Time

Use `pytest-benchmark` storage to track trends:
```bash
# Save baseline
pytest tests/performance/ --benchmark-save=baseline

# Compare later
pytest tests/performance/ --benchmark-compare=baseline
```
