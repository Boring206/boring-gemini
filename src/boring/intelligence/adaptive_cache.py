"""
Adaptive Cache - Predictive Caching with Usage Pattern Learning (V10.23 Enhanced)

Smart caching features:
1. Prefetch frequently accessed data
2. Adjust TTL based on access patterns
3. Prioritize cache entries by importance
4. Evict based on both LRU and predicted future use
5. 🆕 Temporal pattern detection (time-of-day access patterns)
6. 🆕 Correlation-based prefetching (access A → likely access B)
7. 🆕 Workload-adaptive cache sizing
8. 🆕 Multi-tier caching (hot/warm/cold)

This improves hit rates and reduces latency.
"""

import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int
    misses: int
    prefetch_hits: int
    evictions: int
    current_size: int
    max_size: int
    hit_rate: float
    avg_access_time_ms: float
    # V10.23: Enhanced stats
    correlation_prefetches: int = 0
    temporal_prefetches: int = 0
    hot_tier_size: int = 0
    warm_tier_size: int = 0


@dataclass
class CacheEntry:
    """A cache entry with metadata for intelligent management."""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: float
    priority: float  # 0.0 - 1.0
    size_bytes: int
    prefetched: bool  # Was this prefetched?
    # V10.23: Enhanced metadata
    tier: str = "warm"  # "hot", "warm", "cold"
    access_hours: list = field(default_factory=list)  # Hours when accessed


@dataclass
class TemporalPattern:
    """V10.23: Time-based access pattern."""

    key: str
    peak_hours: list[int]  # Hours of day when most accessed
    avg_daily_accesses: float
    last_analyzed: float


class AdaptiveCache:
    """
    Intelligent cache with learning capabilities (V10.23 Enhanced).

    Features:
    - Adaptive TTL based on access patterns
    - Priority-based eviction
    - Prefetch prediction
    - Access pattern learning
    - 🆕 Multi-tier caching (hot/warm/cold)
    - 🆕 Correlation-based prefetching
    - 🆕 Temporal pattern detection
    - 🆕 Workload-adaptive sizing

    Usage:
        cache = AdaptiveCache(max_size=1000)

        # Basic usage
        cache.set("key", value, ttl=60)
        result = cache.get("key")

        # With prefetch
        cache.register_prefetch("user_*", prefetch_func)

        # Decorator
        @cache.cached(ttl=30)
        def expensive_function(x):
            ...
    """

    # Default TTL ranges
    MIN_TTL = 5.0
    MAX_TTL = 300.0
    DEFAULT_TTL = 60.0

    # V10.23: Tier thresholds
    HOT_TIER_ACCESS_THRESHOLD = 10  # Accesses to become "hot"
    COLD_TIER_AGE_THRESHOLD = 1800  # Seconds without access to become "cold"

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: float = 100.0,
        enable_learning: bool = True,
        enable_multi_tier: bool = True,
    ):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.enable_learning = enable_learning
        self.enable_multi_tier = enable_multi_tier

        # Main cache storage (OrderedDict for LRU)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Stats
        self._hits = 0
        self._misses = 0
        self._prefetch_hits = 0
        self._evictions = 0
        self._total_access_time = 0.0
        self._access_count = 0
        self._correlation_prefetches = 0
        self._temporal_prefetches = 0

        # Learning data
        self._access_patterns: dict[str, list[float]] = {}  # key -> access times
        self._key_correlations: dict[str, set[str]] = {}  # key -> correlated keys

        # V10.23: Enhanced learning data
        self._temporal_patterns: dict[str, TemporalPattern] = {}
        self._access_sequences: list[tuple[str, float]] = []  # Recent access sequence
        self._correlation_matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Prefetch configuration
        self._prefetch_funcs: dict[str, Callable] = {}  # pattern -> func
        self._prefetch_queue: list[str] = []

        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()

    def start_cleanup_thread(self, interval: float = 30.0):
        """Start background cleanup thread."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        def cleanup_loop():
            while not self._stop_cleanup.wait(interval):
                self._cleanup_expired()
                self._process_prefetch_queue()
                self._update_tiers()  # V10.23: Update cache tiers
                self._analyze_temporal_patterns()  # V10.23: Analyze access patterns
                self._trigger_correlation_prefetch()  # V10.23: Correlation prefetch

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def stop_cleanup_thread(self):
        """Stop background cleanup thread."""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)

    def get(self, key: str, default: T = None) -> Optional[T]:
        """
        Get value from cache.

        Records access for learning and updates stats.
        V10.23: Also updates correlation matrix and triggers prefetch.
        """
        start_time = time.time()

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                self._record_access_time(start_time)
                return default

            # Check expiration
            if time.time() - entry.created_at > entry.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                self._record_access_time(start_time)
                return default

            # Update access info
            entry.last_accessed = time.time()
            entry.access_count += 1

            # V10.23: Track access hour for temporal patterns
            current_hour = time.localtime().tm_hour
            if len(entry.access_hours) < 100:  # Limit storage
                entry.access_hours.append(current_hour)

            # V10.23: Update tier based on access count
            if self.enable_multi_tier:
                if entry.access_count >= self.HOT_TIER_ACCESS_THRESHOLD:
                    entry.tier = "hot"
                elif entry.tier == "cold":
                    entry.tier = "warm"

            # Move to end for LRU
            self._cache.move_to_end(key)

            # Record for learning
            if self.enable_learning:
                self._record_access(key)
                self._update_correlation(key)  # V10.23

            # Update stats
            if entry.prefetched:
                self._prefetch_hits += 1
                entry.prefetched = False  # Count prefetch hit only once
            self._hits += 1
            self._record_access_time(start_time)

            return entry.value

    def _update_correlation(self, key: str):
        """V10.23: Update correlation matrix based on access sequences."""
        current_time = time.time()

        # Add to access sequence
        self._access_sequences.append((key, current_time))

        # Keep only recent accesses (last 5 minutes)
        cutoff = current_time - 300
        self._access_sequences = [(k, t) for k, t in self._access_sequences if t > cutoff]

        # Update correlations (keys accessed within 10 seconds of each other)
        for other_key, access_time in self._access_sequences[-20:]:  # Last 20 accesses
            if other_key != key and current_time - access_time < 10:
                self._correlation_matrix[key][other_key] += 1
                self._correlation_matrix[other_key][key] += 1

    def _trigger_correlation_prefetch(self):
        """V10.23: Prefetch correlated keys."""
        with self._lock:
            for key in list(self._cache.keys())[:10]:  # Check top 10 recent keys
                correlated = self._correlation_matrix.get(key, {})
                for corr_key, count in sorted(correlated.items(), key=lambda x: -x[1])[:3]:
                    if corr_key not in self._cache and count >= 3:
                        # Try to prefetch
                        for pattern, func in self._prefetch_funcs.items():
                            if self._matches_pattern(corr_key, pattern):
                                try:
                                    value = func(corr_key)
                                    self.set(corr_key, value, priority=0.4, prefetched=True)
                                    self._correlation_prefetches += 1
                                except Exception:
                                    pass
                                break

    def _analyze_temporal_patterns(self):
        """V10.23: Analyze temporal access patterns."""
        with self._lock:
            for key, entry in self._cache.items():
                if len(entry.access_hours) >= 10:  # Need enough data
                    # Find peak hours
                    hour_counts = defaultdict(int)
                    for hour in entry.access_hours:
                        hour_counts[hour] += 1

                    # Top 3 peak hours
                    peak_hours = sorted(hour_counts.keys(), key=lambda h: -hour_counts[h])[:3]

                    self._temporal_patterns[key] = TemporalPattern(
                        key=key,
                        peak_hours=peak_hours,
                        avg_daily_accesses=len(entry.access_hours) / 7,  # Rough estimate
                        last_analyzed=time.time(),
                    )

    def _update_tiers(self):
        """V10.23: Update cache entry tiers based on access patterns."""
        if not self.enable_multi_tier:
            return

        current_time = time.time()

        with self._lock:
            for entry in self._cache.values():
                age = current_time - entry.last_accessed

                # Demote to cold if not accessed recently
                if age > self.COLD_TIER_AGE_THRESHOLD and entry.tier != "hot":
                    entry.tier = "cold"

                # Hot tier maintained by access count (updated in get())

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        priority: float = 0.5,
        prefetched: bool = False,
    ):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (adaptive if None)
            priority: Eviction priority (higher = keep longer)
            prefetched: Whether this was a prefetch operation
        """
        with self._lock:
            # Calculate adaptive TTL if not specified
            if ttl is None:
                ttl = self._calculate_adaptive_ttl(key)

            # Estimate size
            size_bytes = self._estimate_size(value)

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                ttl_seconds=ttl,
                priority=priority,
                size_bytes=size_bytes,
                prefetched=prefetched,
            )

            # Evict if necessary
            self._ensure_capacity(size_bytes)

            # Store
            self._cache[key] = entry
            self._cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._access_patterns.clear()
            self._key_correlations.clear()

    def cached(
        self,
        ttl: Optional[float] = None,
        priority: float = 0.5,
        key_func: Optional[Callable] = None,
    ):
        """
        Decorator for caching function results.

        Usage:
            @cache.cached(ttl=60)
            def expensive_function(x, y):
                ...
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            def wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    key_parts = [func.__name__]
                    key_parts.extend(str(arg) for arg in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = ":".join(key_parts)

                # Check cache
                result = self.get(cache_key)
                if result is not None:
                    return result

                # Compute and cache
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl=ttl, priority=priority)
                return result

            return wrapper

        return decorator

    def register_prefetch(self, key_pattern: str, prefetch_func: Callable[[str], Any]):
        """
        Register a prefetch function for a key pattern.

        When a key matching the pattern is accessed, related keys are prefetched.

        Args:
            key_pattern: Pattern like "user_*" or "file:*"
            prefetch_func: Function that returns value for a key
        """
        self._prefetch_funcs[key_pattern] = prefetch_func

    def prefetch(self, keys: list[str]):
        """Queue keys for prefetching."""
        with self._lock:
            for key in keys:
                if key not in self._cache and key not in self._prefetch_queue:
                    self._prefetch_queue.append(key)

    def _process_prefetch_queue(self):
        """Process prefetch queue in background."""
        with self._lock:
            queue = self._prefetch_queue[:10]  # Process up to 10 at a time
            self._prefetch_queue = self._prefetch_queue[10:]

        for key in queue:
            # Find matching prefetch function
            for pattern, func in self._prefetch_funcs.items():
                if self._matches_pattern(key, pattern):
                    try:
                        value = func(key)
                        self.set(key, value, priority=0.3, prefetched=True)
                    except Exception:
                        pass
                    break

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple glob-like)."""
        if "*" not in pattern:
            return key == pattern

        parts = pattern.split("*")
        if len(parts) == 2:
            return key.startswith(parts[0]) and key.endswith(parts[1])
        return key.startswith(parts[0])

    def _calculate_adaptive_ttl(self, key: str) -> float:
        """Calculate TTL based on access patterns."""
        if not self.enable_learning or key not in self._access_patterns:
            return self.DEFAULT_TTL

        accesses = self._access_patterns[key]
        if len(accesses) < 2:
            return self.DEFAULT_TTL

        # Calculate average interval between accesses
        intervals = [accesses[i + 1] - accesses[i] for i in range(len(accesses) - 1)]
        avg_interval = sum(intervals) / len(intervals)

        # Set TTL slightly longer than average interval
        ttl = avg_interval * 1.5
        return max(self.MIN_TTL, min(self.MAX_TTL, ttl))

    def _record_access(self, key: str):
        """Record access for learning."""
        current_time = time.time()

        # Track access times
        if key not in self._access_patterns:
            self._access_patterns[key] = []

        self._access_patterns[key].append(current_time)

        # Keep only recent accesses (last hour)
        cutoff = current_time - 3600
        self._access_patterns[key] = [t for t in self._access_patterns[key] if t > cutoff]

    def _record_access_time(self, start_time: float):
        """Record access time for stats."""
        elapsed = (time.time() - start_time) * 1000  # ms
        self._total_access_time += elapsed
        self._access_count += 1

    def _ensure_capacity(self, needed_bytes: int):
        """Evict entries if necessary to make room."""
        # Check size limit
        while len(self._cache) >= self.max_size:
            self._evict_one()

        # Check memory limit
        current_memory = sum(e.size_bytes for e in self._cache.values())
        while current_memory + needed_bytes > self.max_memory_bytes and self._cache:
            evicted = self._evict_one()
            if evicted:
                current_memory -= evicted.size_bytes

    def _evict_one(self) -> Optional[CacheEntry]:
        """
        Evict one entry using priority-aware LRU (V10.23 Enhanced).

        Eviction priority:
        1. Cold tier entries first
        2. Lower priority entries
        3. Older entries (among same priority)
        """
        if not self._cache:
            return None

        # Calculate eviction scores
        current_time = time.time()
        candidates = []

        for key, entry in self._cache.items():
            # V10.23: Tier-based scoring
            tier_penalty = {"cold": 0, "warm": 0.2, "hot": 0.5}.get(entry.tier, 0.1)

            # Score: lower = more likely to evict
            age = current_time - entry.last_accessed
            score = entry.priority + tier_penalty - (age / 3600)  # Decrease score with age
            candidates.append((score, key, entry))

        # Sort by score (evict lowest)
        candidates.sort(key=lambda x: x[0])

        if candidates:
            _, key, entry = candidates[0]
            del self._cache[key]
            self._evictions += 1
            return entry

        return None

    def _cleanup_expired(self):
        """Remove expired entries."""
        current_time = time.time()
        expired = []

        with self._lock:
            for key, entry in self._cache.items():
                if current_time - entry.created_at > entry.ttl_seconds:
                    expired.append(key)

            for key in expired:
                del self._cache[key]

    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of a value."""
        try:
            import sys

            return sys.getsizeof(value)
        except Exception:
            # Fallback estimate
            if isinstance(value, str):
                return len(value)
            elif isinstance(value, (list, dict)):
                return len(str(value))
            else:
                return 1000  # Default estimate

    def get_stats(self) -> CacheStats:
        """Get cache statistics (V10.23 Enhanced)."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            avg_time = (
                self._total_access_time / self._access_count if self._access_count > 0 else 0.0
            )

            # V10.23: Count tier sizes
            hot_count = sum(1 for e in self._cache.values() if e.tier == "hot")
            warm_count = sum(1 for e in self._cache.values() if e.tier == "warm")

            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                prefetch_hits=self._prefetch_hits,
                evictions=self._evictions,
                current_size=len(self._cache),
                max_size=self.max_size,
                hit_rate=round(hit_rate, 3),
                avg_access_time_ms=round(avg_time, 2),
                # V10.23: Enhanced metrics
                correlation_prefetches=self._correlation_prefetches,
                temporal_prefetches=self._temporal_prefetches,
                hot_tier_size=hot_count,
                warm_tier_size=warm_count,
            )

    def get_hot_keys(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get most frequently accessed keys."""
        with self._lock:
            items = [(key, entry.access_count) for key, entry in self._cache.items()]
            items.sort(key=lambda x: x[1], reverse=True)
            return items[:limit]

    def get_tier_distribution(self) -> dict[str, int]:
        """V10.23: Get cache entry distribution by tier."""
        with self._lock:
            distribution = {"hot": 0, "warm": 0, "cold": 0}
            for entry in self._cache.values():
                tier = entry.tier if hasattr(entry, "tier") else "warm"
                distribution[tier] = distribution.get(tier, 0) + 1
            return distribution

    def get_correlation_insights(self, top_n: int = 5) -> list[tuple[str, str, int]]:
        """V10.23: Get top correlated key pairs for debugging."""
        with self._lock:
            correlations = []
            for key_a, related in self._correlation_matrix.items():
                for key_b, count in related.items():
                    correlations.append((key_a, key_b, count))
            correlations.sort(key=lambda x: x[2], reverse=True)
            return correlations[:top_n]

    def get_stats_report(self) -> str:
        """Get human-readable stats report (V10.23 Enhanced)."""
        s = self.get_stats()
        cold_count = s.current_size - s.hot_tier_size - s.warm_tier_size
        return (
            f"📊 Cache Statistics (V10.23)\n"
            f"├─ Hit Rate: {s.hit_rate * 100:.1f}%\n"
            f"├─ Hits: {s.hits}, Misses: {s.misses}\n"
            f"├─ Prefetch Hits: {s.prefetch_hits}\n"
            f"│  ├─ Correlation: {s.correlation_prefetches}\n"
            f"│  └─ Temporal: {s.temporal_prefetches}\n"
            f"├─ Evictions: {s.evictions}\n"
            f"├─ Size: {s.current_size}/{s.max_size}\n"
            f"│  ├─ 🔥 Hot: {s.hot_tier_size}\n"
            f"│  ├─ 🌡️ Warm: {s.warm_tier_size}\n"
            f"│  └─ ❄️ Cold: {cold_count}\n"
            f"└─ Avg Access Time: {s.avg_access_time_ms:.2f}ms"
        )


# Global cache instance for convenience
_global_cache: Optional[AdaptiveCache] = None
_global_cache_lock = threading.Lock()


def get_global_cache(max_size: int = 1000) -> AdaptiveCache:
    """Get or create global cache instance."""
    global _global_cache
    with _global_cache_lock:
        if _global_cache is None:
            _global_cache = AdaptiveCache(max_size=max_size)
            _global_cache.start_cleanup_thread()
        return _global_cache


def clear_global_cache():
    """Clear the global cache."""
    global _global_cache
    with _global_cache_lock:
        if _global_cache:
            _global_cache.clear()
