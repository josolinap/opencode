"""
Performance optimization and caching system for Neo-Clone
Provides multi-level caching, connection pooling, and performance monitoring
"""

import time
import hashlib
import json
import logging
import threading
from typing import Any, Dict, Optional, List, Callable, Union
from dataclasses import dataclass, field
from collections import OrderedDict
from functools import wraps
import concurrent.futures
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    value: Any
    timestamp: float
    ttl: float
    hit_count: int = 0
    size_bytes: int = 0


class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry.timestamp + entry.ttl

    def _evict_if_needed(self):
        """Evict entries if cache is full"""
        while len(self._cache) >= self.max_size:
            # Remove expired entries first
            expired_keys = [
                key for key, entry in self._cache.items() if self._is_expired(entry)
            ]
            for key in expired_keys:
                del self._cache[key]
                self._evictions += 1

            # If still full, remove oldest entry
            if len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache"""
        with self._lock:
            # Calculate size (rough estimation)
            try:
                size_bytes = len(json.dumps(value, default=str).encode())
            except:
                size_bytes = len(str(value).encode())

            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl,
                size_bytes=size_bytes,
            )

            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._evict_if_needed()

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            total_size = sum(entry.size_bytes for entry in self._cache.values())

            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "total_size_bytes": total_size,
                "average_entry_size": total_size / len(self._cache)
                if self._cache
                else 0,
            }


class MultiLevelCache:
    """Multi-level cache with memory and disk storage"""

    def __init__(
        self,
        memory_size: int = 100,
        disk_cache_dir: str = "cache",
        disk_size: int = 1000,
    ):
        self.memory_cache = LRUCache(memory_size, default_ttl=1800)  # 30 minutes
        self.disk_cache_dir = Path(disk_cache_dir)
        self.disk_cache_dir.mkdir(exist_ok=True)
        self.disk_cache = LRUCache(disk_size, default_ttl=86400)  # 24 hours
        self._lock = threading.RLock()

    def _get_disk_cache_key(self, key: str) -> Path:
        """Get disk cache file path for key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.disk_cache_dir / f"{safe_key}.cache"

    def _load_from_disk(self, key: str) -> Optional[Any]:
        """Load value from disk cache"""
        try:
            cache_file = self._get_disk_cache_key(key)
            if not cache_file.exists():
                return None

            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                entry = data.get("entry")

                if entry and time.time() < entry["timestamp"] + entry["ttl"]:
                    return entry["value"]
                else:
                    # Expired, remove file
                    cache_file.unlink()
                    return None
        except Exception as e:
            logger.warning(f"Failed to load from disk cache: {e}")
            return None

    def _save_to_disk(self, key: str, value: Any, ttl: float):
        """Save value to disk cache"""
        try:
            cache_file = self._get_disk_cache_key(key)
            entry = {"value": value, "timestamp": time.time(), "ttl": ttl}

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f)
        except Exception as e:
            logger.warning(f"Failed to save to disk cache: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Try disk cache
        with self._lock:
            value = self.disk_cache.get(key)
            if value is not None:
                # Promote to memory cache
                self.memory_cache.set(key, value)
                return value

            # Try loading from disk file
            value = self._load_from_disk(key)
            if value is not None:
                # Store in both caches
                self.memory_cache.set(key, value)
                self.disk_cache.set(key, value)
                return value

        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in multi-level cache"""
        ttl = ttl or 3600  # Default 1 hour

        # Store in both levels
        self.memory_cache.set(key, value, ttl)
        self.disk_cache.set(key, value, ttl)
        self._save_to_disk(key, value, ttl)

    def clear(self):
        """Clear all cache levels"""
        self.memory_cache.clear()
        self.disk_cache.clear()

        # Clear disk cache files
        try:
            for cache_file in self.disk_cache_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to clear disk cache files: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.disk_cache.get_stats()

        return {
            "memory_cache": memory_stats,
            "disk_cache": disk_stats,
            "total_hit_rate": (
                memory_stats["hit_rate"] * 0.7 + disk_stats["hit_rate"] * 0.3
            ),  # Weight memory higher
        }


class ConnectionPool:
    """Thread-safe connection pool for HTTP clients"""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_connections)
        self._active_connections = 0
        self._lock = threading.Lock()

    def execute(self, func: Callable, *args, **kwargs):
        """Execute function in connection pool"""
        with self._lock:
            if self._active_connections >= self.max_connections:
                logger.warning("Connection pool exhausted, blocking")

        try:
            with self._lock:
                self._active_connections += 1

            future = self._pool.submit(func, *args, **kwargs)
            return future.result(timeout=30)  # 30 second timeout
        finally:
            with self._lock:
                self._active_connections -= 1

    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics"""
        with self._lock:
            return {
                "active_connections": self._active_connections,
                "max_connections": self.max_connections,
                "available_connections": self.max_connections
                - self._active_connections,
            }


class PerformanceMonitor:
    """Monitor and track performance metrics"""

    def __init__(self):
        self._metrics = {}
        self._lock = threading.Lock()

    def record_timing(self, operation: str, duration: float, success: bool = True):
        """Record timing for an operation"""
        with self._lock:
            if operation not in self._metrics:
                self._metrics[operation] = {
                    "total_time": 0.0,
                    "call_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "min_time": float("inf"),
                    "max_time": 0.0,
                    "avg_time": 0.0,
                }

            metrics = self._metrics[operation]
            metrics["total_time"] += duration
            metrics["call_count"] += 1

            if success:
                metrics["success_count"] += 1
            else:
                metrics["error_count"] += 1

            metrics["min_time"] = min(metrics["min_time"], duration)
            metrics["max_time"] = max(metrics["max_time"], duration)
            metrics["avg_time"] = metrics["total_time"] / metrics["call_count"]

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all performance metrics"""
        with self._lock:
            return self._metrics.copy()

    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get stats for specific operation"""
        with self._lock:
            return self._metrics.get(operation, {}).copy()


# Global performance components
memory_cache = LRUCache(max_size=500, default_ttl=1800)  # 30 minutes
disk_cache = MultiLevelCache(memory_size=100, disk_cache_dir="cache/performance")
connection_pool = ConnectionPool(max_connections=5)
performance_monitor = PerformanceMonitor()


def cached(ttl: Optional[float] = None, cache_level: str = "memory"):
    """Decorator for caching function results"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Choose cache level
            if cache_level == "memory":
                cache = memory_cache
            elif cache_level == "disk":
                cache = disk_cache
            else:
                cache = memory_cache  # Default

            # Try cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                result = e
                success = False
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record_timing(func.__name__, duration, success)

            # Cache result
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, result cached")

            return result

        return wrapper

    return decorator


def pooled(max_workers: Optional[int] = None):
    """Decorator for executing function in connection pool"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return connection_pool.execute(func, *args, **kwargs)

        return wrapper

    return decorator


def timed(operation_name: Optional[str] = None):
    """Decorator for timing function execution"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                result = e
                success = False
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record_timing(op_name, duration, success)

        return wrapper

    return decorator


def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics"""
    return {
        "cache_stats": {
            "memory": memory_cache.get_stats(),
            "disk": disk_cache.get_stats(),
        },
        "connection_pool": connection_pool.get_stats(),
        "performance_metrics": performance_monitor.get_metrics(),
    }


def optimize_for_memory():
    """Optimize system for memory usage"""
    # Clear caches if they're getting large
    memory_stats = memory_cache.get_stats()
    if memory_stats["total_size_bytes"] > 50 * 1024 * 1024:  # 50MB
        logger.info("Clearing memory cache to free up space")
        memory_cache.clear()

    # Trigger garbage collection
    import gc

    gc.collect()


def cleanup_old_cache():
    """Clean up old cache files"""
    try:
        cache_dir = Path("cache/performance")
        if cache_dir.exists():
            current_time = time.time()
            for cache_file in cache_dir.glob("*.cache"):
                if current_time - cache_file.stat().st_mtime > 86400:  # 24 hours
                    cache_file.unlink()
                    logger.debug(f"Removed old cache file: {cache_file}")
    except Exception as e:
        logger.warning(f"Failed to cleanup old cache: {e}")
