"""
Boring Intelligence Module V10.26

Advanced intelligence features that enhance all core modules.

Submodules:
- intelligent_ranker: Learning-based ranking for RAG retrieval
- predictive_analyzer: Error prediction and trend analysis
- context_optimizer: Smart context compression for LLM calls
- adaptive_cache: Predictive caching with usage pattern learning
- pattern_clustering: Pattern deduplication and clustering (V10.24 NEW)
- prediction_tracker: Accuracy tracking and A/B testing (V10.24 NEW)
- cache_warming: Startup optimization and prefetching (V10.24 NEW)

V10.26 Reorganization:
- brain_manager: Knowledge base management (moved from root)
- memory: Persistent memory system (moved from root)

- feedback_learner: Review feedback learning (moved from root)
- auto_learner: Automatic pattern learning (moved from root)
- pattern_mining: Pattern extraction and suggestions (moved from root)

V10.24 Key Enhancements:
- Pattern Clustering: Automatic deduplication of similar patterns
- Prediction Accuracy Tracking: Data-driven optimization
- A/B Testing Framework: Compare prediction strategies
- Cache Warming: 30%+ faster cold start
- Embedding Versioning: Safe migration support

V10.23 Features (maintained):
- Session-aware processing across all modules
- Incremental learning with pattern decay
- Multi-factor confidence scoring
- Sliding window memory management
"""

from typing import TYPE_CHECKING, Any, Optional  # noqa: F401

if TYPE_CHECKING:
    from .adaptive_cache import AdaptiveCache, CacheStats  # noqa: F401
    from .brain_manager import BrainManager, LearnedPattern  # noqa: F401
    from .cache_warming import CacheWarmer, StartupOptimizer, warm_on_startup  # noqa: F401
    from .context_optimizer import ContextOptimizer, ContextStats, SmartContextBuilder  # noqa: F401
    from .feedback_learner import FeedbackEntry, FeedbackLearner  # noqa: F401
    from .intelligent_ranker import IntelligentRanker, UsageRecord  # noqa: F401
    from .memory import LoopMemory, MemoryManager, ProjectMemory  # noqa: F401
    from .pattern_clustering import PatternCluster, PatternClusterer  # noqa: F401
    from .prediction_tracker import ABTestResult, AccuracyMetrics, PredictionTracker  # noqa: F401
    from .predictive_analyzer import ErrorPrediction, PredictiveAnalyzer  # noqa: F401

# Mapping of exported name -> (module_name, attribute_name)
_EXPORT_MAP = {
    # .adaptive_cache
    "AdaptiveCache": ("adaptive_cache", "AdaptiveCache"),
    "CacheStats": ("adaptive_cache", "CacheStats"),
    # .brain_manager
    "BrainManager": ("brain_manager", "BrainManager"),
    "LearnedPattern": ("brain_manager", "LearnedPattern"),
    # .cache_warming
    "CacheWarmer": ("cache_warming", "CacheWarmer"),
    "StartupOptimizer": ("cache_warming", "StartupOptimizer"),
    "warm_on_startup": ("cache_warming", "warm_on_startup"),
    # .context_optimizer
    "ContextOptimizer": ("context_optimizer", "ContextOptimizer"),
    "ContextStats": ("context_optimizer", "ContextStats"),
    "SmartContextBuilder": ("context_optimizer", "SmartContextBuilder"),
    # .feedback_learner
    "FeedbackLearner": ("feedback_learner", "FeedbackLearner"),
    "FeedbackEntry": ("feedback_learner", "FeedbackEntry"),
    # .intelligent_ranker
    "IntelligentRanker": ("intelligent_ranker", "IntelligentRanker"),
    "UsageRecord": ("intelligent_ranker", "UsageRecord"),
    # .memory
    "LoopMemory": ("memory", "LoopMemory"),
    "MemoryManager": ("memory", "MemoryManager"),
    "ProjectMemory": ("memory", "ProjectMemory"),
    # .pattern_clustering
    "PatternClusterer": ("pattern_clustering", "PatternClusterer"),
    "PatternCluster": ("pattern_clustering", "PatternCluster"),
    # .prediction_tracker
    "PredictionTracker": ("prediction_tracker", "PredictionTracker"),
    "AccuracyMetrics": ("prediction_tracker", "AccuracyMetrics"),
    "ABTestResult": ("prediction_tracker", "ABTestResult"),
    # .predictive_analyzer
    "PredictiveAnalyzer": ("predictive_analyzer", "PredictiveAnalyzer"),
    "ErrorPrediction": ("predictive_analyzer", "ErrorPrediction"),
}

# Legacy Legacy Map (Ghost Feature Resurrection)
_LEGACY_MAP = {
    "AutoLearner": ("feedback_learner", "FeedbackLearner"),
    "PatternMiner": ("pattern_clustering", "PatternClusterer"),
    "Pattern": ("pattern_clustering", "PatternCluster"),
}


def __getattr__(name: str):
    if name == "ErrorSolutionPair":
        from dataclasses import dataclass
        @dataclass
        class ErrorSolutionPair:
            error: str
            solution: str
        return ErrorSolutionPair

    if name in _EXPORT_MAP:
        module_name, attr_name = _EXPORT_MAP[name]
        module = __import__(f"{__name__}.{module_name}", fromlist=[attr_name])
        return getattr(module, attr_name)

    if name in _LEGACY_MAP:
        module_name, attr_name = _LEGACY_MAP[name]
        module = __import__(f"{__name__}.{module_name}", fromlist=[attr_name])
        return getattr(module, attr_name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(_EXPORT_MAP.keys()) + list(_LEGACY_MAP.keys()) + ["ErrorSolutionPair"]


__all__ = list(_EXPORT_MAP.keys()) + list(_LEGACY_MAP.keys()) + ["ErrorSolutionPair"]

