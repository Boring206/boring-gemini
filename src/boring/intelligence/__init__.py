"""
Boring Intelligence Module V10.24

Advanced intelligence features that enhance all core modules.

Submodules:
- intelligent_ranker: Learning-based ranking for RAG retrieval
- predictive_analyzer: Error prediction and trend analysis
- context_optimizer: Smart context compression for LLM calls
- adaptive_cache: Predictive caching with usage pattern learning
- pattern_clustering: Pattern deduplication and clustering (V10.24 NEW)
- prediction_tracker: Accuracy tracking and A/B testing (V10.24 NEW)
- cache_warming: Startup optimization and prefetching (V10.24 NEW)

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

from .adaptive_cache import AdaptiveCache, CacheStats
from .cache_warming import CacheWarmer, StartupOptimizer, warm_on_startup
from .context_optimizer import ContextOptimizer, ContextStats, SmartContextBuilder
from .intelligent_ranker import IntelligentRanker, UsageRecord

# V10.24 New Modules
from .pattern_clustering import EmbeddingVersionManager, PatternCluster, PatternClusterer
from .prediction_tracker import ABTestResult, AccuracyMetrics, PredictionTracker
from .predictive_analyzer import ErrorPrediction, PredictiveAnalyzer

__all__ = [
    # V10.23 Core
    "IntelligentRanker",
    "UsageRecord",
    "PredictiveAnalyzer",
    "ErrorPrediction",
    "ContextOptimizer",
    "ContextStats",
    "SmartContextBuilder",
    "AdaptiveCache",
    "CacheStats",
    # V10.24 New
    "PatternClusterer",
    "PatternCluster",
    "EmbeddingVersionManager",
    "PredictionTracker",
    "AccuracyMetrics",
    "ABTestResult",
    "CacheWarmer",
    "StartupOptimizer",
    "warm_on_startup",
]
