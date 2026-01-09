# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Vibe Engine (V10.23 Enhanced).

Core dispatcher that routes requests to appropriate language handlers.

V10.23 Enhancements:
- Performance tracking for all operations
- Analysis result caching (LRU with TTL)
- Handler performance statistics
- Integration with AdaptiveCache for cross-request optimization
"""

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .analysis import DocResult, ReviewResult, TestGenResult
from .handlers.base import BaseHandler


@dataclass
class VibePerformanceStats:
    """V10.23: Performance tracking for Vibe operations."""

    total_analyses: int = 0
    total_reviews: int = 0
    total_test_gens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time_ms: float = 0.0
    handler_times: dict = field(default_factory=dict)  # handler_name -> total_ms

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

    @property
    def avg_operation_time_ms(self) -> float:
        total_ops = self.total_analyses + self.total_reviews + self.total_test_gens
        return self.total_time_ms / total_ops if total_ops > 0 else 0.0


class VibeEngine:
    """
    Main engine for Vibe Coder Pro tools (V10.23 Enhanced).
    Uses Strategy Pattern to select the correct handler for a file.

    V10.23 Features:
    - LRU cache for analysis results (reduces repeated work)
    - Performance tracking per handler
    - Statistics for optimization insights
    """

    # V10.23: Cache configuration
    CACHE_MAX_SIZE = 50
    CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(self):
        self._handlers: dict[str, BaseHandler] = {}
        self._default_handler: Optional[BaseHandler] = None

        # V10.23: Analysis cache (key -> (result, timestamp))
        self._analysis_cache: dict[str, tuple] = {}
        self._review_cache: dict[str, tuple] = {}

        # V10.23: Performance tracking
        self._stats = VibePerformanceStats()

    def register_handler(self, handler: BaseHandler):
        """Register a language handler."""
        for ext in handler.supported_extensions:
            self._handlers[ext.lower()] = handler

    def get_handler(self, file_path: str) -> Optional[BaseHandler]:
        """Get the appropriate handler for a file path."""
        ext = Path(file_path).suffix.lower()
        return self._handlers.get(ext, self._default_handler)

    def _cache_key(self, file_path: str, source_code: str, operation: str) -> str:
        """V10.23: Generate cache key from file and content."""
        # Use sha256 for cache key (non-security)
        content_hash = hashlib.sha256(source_code.encode()).hexdigest()[:16]
        return f"{operation}:{file_path}:{content_hash}"

    def _get_cached(self, cache: dict, key: str):
        """V10.23: Get from cache if not expired."""
        if key in cache:
            result, timestamp = cache[key]
            if time.time() - timestamp < self.CACHE_TTL_SECONDS:
                self._stats.cache_hits += 1
                return result
            else:
                del cache[key]  # Expired
        self._stats.cache_misses += 1
        return None

    def _set_cached(self, cache: dict, key: str, result):
        """V10.23: Add to cache with LRU eviction."""
        if len(cache) >= self.CACHE_MAX_SIZE:
            # Remove oldest entry
            oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
            del cache[oldest_key]
        cache[key] = (result, time.time())

    def _track_time(self, handler_name: str, elapsed_ms: float):
        """V10.23: Track operation time per handler."""
        self._stats.total_time_ms += elapsed_ms
        if handler_name not in self._stats.handler_times:
            self._stats.handler_times[handler_name] = 0.0
        self._stats.handler_times[handler_name] += elapsed_ms

    def analyze_for_test_gen(self, file_path: str, source_code: str) -> TestGenResult:
        """Route test generation analysis to appropriate handler (V10.23: cached)."""
        handler = self.get_handler(file_path)
        if not handler:
            raise ValueError(
                f"Unsupported file type: {Path(file_path).suffix} (No handler registered)"
            )

        # V10.23: Check cache
        cache_key = self._cache_key(file_path, source_code, "test_gen")
        cached = self._get_cached(self._analysis_cache, cache_key)
        if cached:
            return cached

        # Execute with timing
        start = time.time()
        result = handler.analyze_for_test_gen(file_path, source_code)
        elapsed_ms = (time.time() - start) * 1000

        # V10.23: Track stats
        self._stats.total_analyses += 1
        self._track_time(handler.language_name, elapsed_ms)

        # V10.23: Cache result
        self._set_cached(self._analysis_cache, cache_key, result)

        return result

    def perform_code_review(
        self, file_path: str, source_code: str, focus: str = "all"
    ) -> ReviewResult:
        """Route code review to appropriate handler (V10.23: cached)."""
        handler = self.get_handler(file_path)
        if not handler:
            raise ValueError(
                f"Unsupported file type: {Path(file_path).suffix} (No handler registered)"
            )

        # V10.23: Check cache (include focus in key)
        cache_key = self._cache_key(file_path, source_code, f"review_{focus}")
        cached = self._get_cached(self._review_cache, cache_key)
        if cached:
            return cached

        # Execute with timing
        start = time.time()
        result = handler.perform_code_review(file_path, source_code, focus)
        elapsed_ms = (time.time() - start) * 1000

        # V10.23: Track stats
        self._stats.total_reviews += 1
        self._track_time(handler.language_name, elapsed_ms)

        # V10.23: Cache result
        self._set_cached(self._review_cache, cache_key, result)

        return result

    def generate_test_code(self, result: TestGenResult, project_root: str) -> str:
        """Route test generation string creation."""
        handler = self.get_handler(result.file_path)
        if not handler:
            raise ValueError(f"No handler found for {result.file_path}")

        start = time.time()
        code = handler.generate_test_code(result, project_root)
        elapsed_ms = (time.time() - start) * 1000

        # V10.23: Track stats
        self._stats.total_test_gens += 1
        self._track_time(handler.language_name, elapsed_ms)

        return code

    def extract_dependencies(self, file_path: str, source_code: str) -> list[str]:
        """Route dependency extraction."""
        handler = self.get_handler(file_path)
        if not handler:
            return []
        return handler.extract_dependencies(file_path, source_code)

    def extract_documentation(self, file_path: str, source_code: str) -> DocResult:
        """Identify documentation and comments in code."""
        handler = self.get_handler(file_path)
        if not handler:
            return DocResult(file_path=file_path, module_doc="", items=[])
        return handler.extract_documentation(file_path, source_code)

    # =========================================================================
    # V10.23: Statistics and Cache Management
    # =========================================================================

    def get_stats(self) -> dict:
        """V10.23: Get performance statistics."""
        return {
            "total_analyses": self._stats.total_analyses,
            "total_reviews": self._stats.total_reviews,
            "total_test_gens": self._stats.total_test_gens,
            "cache_hit_rate": round(self._stats.cache_hit_rate, 3),
            "cache_hits": self._stats.cache_hits,
            "cache_misses": self._stats.cache_misses,
            "avg_operation_time_ms": round(self._stats.avg_operation_time_ms, 2),
            "handler_times": self._stats.handler_times,
            "analysis_cache_size": len(self._analysis_cache),
            "review_cache_size": len(self._review_cache),
        }

    def clear_cache(self):
        """V10.23: Clear all caches."""
        self._analysis_cache.clear()
        self._review_cache.clear()

    def get_stats_report(self) -> str:
        """V10.23: Get human-readable performance report."""
        stats = self.get_stats()
        lines = [
            "🚀 **Vibe Engine Performance (V10.23)**",
            f"- Total Operations: {stats['total_analyses'] + stats['total_reviews'] + stats['total_test_gens']}",
            f"- Cache Hit Rate: {stats['cache_hit_rate']:.1%}",
            f"- Avg Operation Time: {stats['avg_operation_time_ms']:.1f}ms",
            "",
            "**Handler Breakdown:**",
        ]
        for handler, time_ms in stats["handler_times"].items():
            lines.append(f"  - {handler}: {time_ms:.1f}ms total")

        return "\n".join(lines)
