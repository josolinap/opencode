"""
Cache System for MiniMax Agent Architecture

This module provides a high-performance caching system with TTL management,
eviction policies, compression, and distributed cache support.

Author: MiniMax Agent
Version: 1.0
"""

import json
import pickle
import hashlib
import threading
import time
import gzip
import weakref
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"           # Least Recently Used
    LFU = "lfu"           # Least Frequently Used
    FIFO = "fifo"         # First In, First Out
    TTL = "ttl"           # Time To Live (priority)
    PRIORITY = "priority" # Priority-based eviction


class CompressionType(Enum):
    """Compression algorithms"""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"  # Future: if lz4 is available
    ZSTD = "zstd"  # Future: if zstd is available


@dataclass
class CacheEntry:
    """Individual cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[float] = None  # Time to live in seconds
    priority: float = 1.0
    compressed: bool = False
    compressed_size: int = 0
    original_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl
    
    def access(self) -> None:
        """Record cache access"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def get_age(self) -> float:
        """Get age in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_size_estimate(self) -> int:
        """Get approximate size of the entry"""
        if self.compressed:
            return self.compressed_size
        try:
            # Estimate size using pickle
            return len(pickle.dumps(self.value, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception:
            return self.original_size or 0


@dataclass
class CacheStatistics:
    """Cache performance statistics"""
    total_operations: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    compressions: int = 0
    decompressions: int = 0
    
    # Timing statistics
    total_get_time: float = 0.0
    total_set_time: float = 0.0
    
    # Size statistics
    current_memory_usage: int = 0
    peak_memory_usage: int = 0
    total_keys: int = 0
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_operations == 0:
            return 0.0
        return self.hits / self.total_operations
    
    def get_average_get_time(self) -> float:
        """Get average get operation time"""
        if self.hits + self.misses == 0:
            return 0.0
        return self.total_get_time / (self.hits + self.misses)
    
    def get_average_set_time(self) -> float:
        """Get average set operation time"""
        if self.total_operations - self.hits - self.misses == 0:
            return 0.0
        return self.total_set_time / (self.total_operations - self.hits - self.misses)


class CacheSystem:
    """
    High-performance cache system with advanced features:
    
    - Multiple eviction strategies (LRU, LFU, FIFO, TTL, Priority)
    - Automatic compression for large entries
    - TTL-based expiration with background cleanup
    - Memory usage tracking and limits
    - Thread-safe operations
    - Statistics and monitoring
    - Persistent storage support
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 100,
        strategy: CacheStrategy = CacheStrategy.LRU,
        compression: CompressionType = CompressionType.GZIP,
        compression_threshold: int = 1024,  # Compress entries > 1KB
        auto_cleanup: bool = True,
        cleanup_interval: int = 60,  # Cleanup every 60 seconds
        default_ttl: Optional[float] = 300.0,  # 5 minutes
        persistent_storage: Optional[str] = None
    ):
        """
        Initialize cache system
        
        Args:
            max_size: Maximum number of cache entries
            max_memory_mb: Maximum memory usage in MB
            strategy: Eviction strategy
            compression: Compression algorithm
            compression_threshold: Size threshold for compression
            auto_cleanup: Enable automatic cleanup
            cleanup_interval: Cleanup interval in seconds
            default_ttl: Default TTL for new entries
            persistent_storage: Path for persistent cache storage
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.strategy = strategy
        self.compression = compression
        self.compression_threshold = compression_threshold
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        self.default_ttl = default_ttl
        self.persistent_storage = Path(persistent_storage) if persistent_storage else None
        
        # Thread safety
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStatistics()
        
        # Eviction tracking for different strategies
        self._access_times: Dict[str, datetime] = {}
        self._access_frequencies: Dict[str, int] = {}
        self._creation_times: Dict[str, datetime] = {}
        
        # Load persistent cache if available
        if self.persistent_storage:
            self._load_persistent()
        
        # Start background cleanup
        if self.auto_cleanup:
            self._start_cleanup_thread()
        
        logger.info(f"Cache initialized: strategy={strategy.value}, max_size={max_size}, max_memory={max_memory_mb}MB")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        start_time = time.time()
        
        with self._lock:
            self._stats.total_operations += 1
            
            # Check if key exists
            if key not in self._cache:
                self._stats.misses += 1
                self._stats.total_get_time += time.time() - start_time
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._remove_from_eviction_tracking(key)
                self._stats.misses += 1
                self._stats.expirations += 1
                self._stats.total_get_time += time.time() - start_time
                return None
            
            # Record access
            entry.access()
            self._update_eviction_tracking(key, access=True)
            
            # Move to end for LRU (most recently used)
            if self.strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)
            
            self._stats.hits += 1
            self._stats.total_get_time += time.time() - start_time
            
            # Decompress if necessary
            value = entry.value
            if entry.compressed:
                value = self._decompress(value)
                self._stats.decompressions += 1
            
            return value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        priority: float = 1.0,
        force: bool = False
    ) -> bool:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for default)
            priority: Priority for eviction (higher = less likely to evict)
            force: Force set even if at capacity
        
        Returns:
            True if successfully cached
        """
        start_time = time.time()
        
        with self._lock:
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl or self.default_ttl,
                priority=priority,
                original_size=len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
            )
            
            # Compress if necessary
            if entry.original_size > self.compression_threshold:
                compressed_value = self._compress(value)
                if compressed_value:
                    entry.value = compressed_value
                    entry.compressed = True
                    entry.compressed_size = len(compressed_value)
                    self._stats.compressions += 1
            
            # Update cache statistics
            self._update_memory_usage()
            
            # Check if we need to evict entries
            if not force and self._should_evict():
                self._evict_entries()
            
            # Store in cache
            old_entry = self._cache.get(key)
            if old_entry:
                # Update existing entry
                self._remove_from_eviction_tracking(key)
            
            self._cache[key] = entry
            self._add_to_eviction_tracking(key)
            
            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)
            
            self._stats.total_keys = len(self._cache)
            self._stats.total_set_time += time.time() - start_time
            
            # Persist if enabled
            if self.persistent_storage:
                self._persist_entry(key, entry)
            
            logger.debug(f"Cache set: {key}, size={entry.original_size}, compressed={entry.compressed}")
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if entry was deleted
        """
        with self._lock:
            if key not in self._cache:
                return False
            
            del self._cache[key]
            self._remove_from_eviction_tracking(key)
            self._update_memory_usage()
            self._stats.total_keys = len(self._cache)
            
            # Remove from persistent storage
            if self.persistent_storage:
                self._remove_persistent_entry(key)
            
            logger.debug(f"Cache delete: {key}")
            return True
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._access_frequencies.clear()
            self._creation_times.clear()
            self._stats = CacheStatistics()
            
            # Clear persistent storage
            if self.persistent_storage:
                self._clear_persistent()
            
            logger.info("Cache cleared")
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._remove_from_eviction_tracking(key)
                return False
            
            return True
    
    def get_ttl(self, key: str) -> Optional[float]:
        """Get remaining TTL for a key"""
        with self._lock:
            entry = self._cache.get(key)
            if not entry or entry.ttl is None:
                return None
            
            age = entry.get_age()
            return max(0.0, entry.ttl - age)
    
    def extend_ttl(self, key: str, additional_ttl: float) -> bool:
        """Extend TTL for a key"""
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return False
            
            if entry.ttl is None:
                entry.ttl = additional_ttl
            else:
                entry.ttl += additional_ttl
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            self._update_memory_usage()
            
            stats_dict = {
                "strategy": self.strategy.value,
                "max_size": self.max_size,
                "max_memory_mb": self.max_memory_bytes // (1024 * 1024),
                "current_size": len(self._cache),
                "memory_usage_mb": self._stats.current_memory_usage / (1024 * 1024),
                "peak_memory_mb": self._stats.peak_memory_usage / (1024 * 1024),
                "hit_rate": self._stats.get_hit_rate(),
                "average_get_time_ms": self._stats.get_average_get_time() * 1000,
                "average_set_time_ms": self._stats.get_average_set_time() * 1000,
                "total_operations": self._stats.total_operations,
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "expirations": self._stats.expirations,
                "compressions": self._stats.compressions,
                "decompressions": self._stats.decompressions,
                "compression_algorithm": self.compression.value,
                "default_ttl_seconds": self.default_ttl,
                "persistent_storage": str(self.persistent_storage) if self.persistent_storage else None
            }
            
            return stats_dict
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Manually cleanup expired entries"""
        with self._lock:
            expired_keys = []
            current_time = datetime.now()
            
            for key, entry in list(self._cache.items()):
                if entry.is_expired():
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
                self._remove_from_eviction_tracking(key)
            
            self._stats.expirations += len(expired_keys)
            self._update_memory_usage()
            self._stats.total_keys = len(self._cache)
            
            result = {
                "expired_entries_removed": len(expired_keys),
                "remaining_entries": len(self._cache),
                "memory_freed_mb": 0  # Would calculate actual memory freed
            }
            
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
            return result
    
    def _should_evict(self) -> bool:
        """Check if eviction is needed"""
        if len(self._cache) >= self.max_size:
            return True
        
        if self._stats.current_memory_usage >= self.max_memory_bytes:
            return True
        
        return False
    
    def _evict_entries(self, count: Optional[int] = None) -> int:
        """Evict entries based on strategy"""
        if not self._cache:
            return 0
        
        if count is None:
            # Calculate how many to evict
            size_overflow = len(self._cache) - self.max_size
            memory_overflow = self._stats.current_memory_usage - self.max_memory_bytes
            count = max(1, size_overflow // 4, 1)  # Evict 25% of overflow or at least 1
        
        evicted_count = 0
        
        for _ in range(min(count, len(self._cache))):
            # Select eviction candidate based on strategy
            key_to_evict = self._select_eviction_candidate()
            
            if key_to_evict:
                del self._cache[key_to_evict]
                self._remove_from_eviction_tracking(key_to_evict)
                evicted_count += 1
            else:
                break
        
        self._stats.evictions += evicted_count
        self._update_memory_usage()
        self._stats.total_keys = len(self._cache)
        
        logger.debug(f"Evicted {evicted_count} entries")
        return evicted_count
    
    def _select_eviction_candidate(self) -> Optional[str]:
        """Select the best candidate for eviction based on strategy"""
        if not self._cache:
            return None
        
        candidates = list(self._cache.keys())
        
        if self.strategy == CacheStrategy.LRU:
            # Least recently used: return oldest accessed
            return min(candidates, key=lambda k: self._access_times.get(k, datetime.min))
        
        elif self.strategy == CacheStrategy.LFU:
            # Least frequently used: return least accessed
            return min(candidates, key=lambda k: self._access_frequencies.get(k, 0))
        
        elif self.strategy == CacheStrategy.FIFO:
            # First in first out: return oldest created
            return min(candidates, key=lambda k: self._creation_times.get(k, datetime.min))
        
        elif self.strategy == CacheStrategy.TTL:
            # Shortest TTL first
            return min(candidates, key=lambda k: self._cache[k].ttl or float('inf'))
        
        elif self.strategy == CacheStrategy.PRIORITY:
            # Lowest priority first
            return min(candidates, key=lambda k: self._cache[k].priority)
        
        else:
            # Default to LRU
            return min(candidates, key=lambda k: self._access_times.get(k, datetime.min))
    
    def _update_eviction_tracking(self, key: str, access: bool = False) -> None:
        """Update eviction tracking data structures"""
        now = datetime.now()
        self._access_times[key] = now
        
        if access:
            self._access_frequencies[key] = self._access_frequencies.get(key, 0) + 1
    
    def _add_to_eviction_tracking(self, key: str) -> None:
        """Add key to eviction tracking"""
        now = datetime.now()
        self._access_times[key] = now
        self._access_frequencies[key] = 0
        self._creation_times[key] = now
    
    def _remove_from_eviction_tracking(self, key: str) -> None:
        """Remove key from eviction tracking"""
        self._access_times.pop(key, None)
        self._access_frequencies.pop(key, None)
        self._creation_times.pop(key, None)
    
    def _update_memory_usage(self) -> None:
        """Update memory usage statistics"""
        total_size = sum(entry.get_size_estimate() for entry in self._cache.values())
        self._stats.current_memory_usage = total_size
        self._stats.peak_memory_usage = max(self._stats.peak_memory_usage, total_size)
    
    def _compress(self, data: Any) -> Optional[bytes]:
        """Compress data using specified algorithm"""
        try:
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            
            if self.compression == CompressionType.GZIP:
                return gzip.compress(serialized)
            elif self.compression == CompressionType.NONE:
                return serialized
            else:
                # Fallback to no compression
                return serialized
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return None
    
    def _decompress(self, data: bytes) -> Any:
        """Decompress data using specified algorithm"""
        try:
            if self.compression == CompressionType.GZIP:
                decompressed = gzip.decompress(data)
            else:
                decompressed = data
            
            return pickle.loads(decompressed)
        except Exception as e:
            logger.warning(f"Decompression failed: {e}")
            return None
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread"""
        self._running = True
        
        def cleanup_worker():
            """Background worker for cache cleanup"""
            while self._running:
                try:
                    time.sleep(self.cleanup_interval)
                    if not self._running:
                        break
                    
                    # Cleanup expired entries
                    self.cleanup_expired()
                    
                    # Check if we need to evict based on memory
                    if self._should_evict():
                        self._evict_entries()
                    
                    # Periodic persistence
                    if self.persistent_storage:
                        self._persist_all()
                    
                except Exception as e:
                    logger.error(f"Background cleanup error: {e}")
        
        self._cleanup_thread = threading.Thread(
            target=cleanup_worker,
            daemon=True,
            name="CacheCleanup"
        )
        self._cleanup_thread.start()
        logger.info("Started background cache cleanup")
    
    def _load_persistent(self) -> None:
        """Load cache from persistent storage"""
        if not self.persistent_storage or not self.persistent_storage.exists():
            return
        
        try:
            with open(self.persistent_storage, 'rb') as f:
                data = pickle.load(f)
            
            if isinstance(data, dict):
                for key, entry_data in data.items():
                    try:
                        # Reconstruct CacheEntry
                        entry = CacheEntry(
                            key=key,
                            value=entry_data.get('value'),
                            created_at=datetime.fromisoformat(entry_data.get('created_at', datetime.now().isoformat())),
                            last_accessed=datetime.fromisoformat(entry_data.get('last_accessed', datetime.now().isoformat())),
                            access_count=entry_data.get('access_count', 0),
                            ttl=entry_data.get('ttl'),
                            priority=entry_data.get('priority', 1.0),
                            compressed=entry_data.get('compressed', False),
                            compressed_size=entry_data.get('compressed_size', 0),
                            original_size=entry_data.get('original_size', 0),
                            metadata=entry_data.get('metadata', {})
                        )
                        
                        # Only add if not expired
                        if not entry.is_expired():
                            self._cache[key] = entry
                            self._add_to_eviction_tracking(key)
                        
                    except Exception as e:
                        logger.warning(f"Failed to load persistent entry {key}: {e}")
            
            self._stats.total_keys = len(self._cache)
            self._update_memory_usage()
            logger.info(f"Loaded {len(self._cache)} entries from persistent storage")
            
        except Exception as e:
            logger.warning(f"Failed to load persistent cache: {e}")
    
    def _persist_entry(self, key: str, entry: CacheEntry) -> None:
        """Persist individual entry (for future implementation)"""
        # This would implement incremental persistence
        pass
    
    def _persist_all(self) -> None:
        """Persist all entries to storage"""
        if not self.persistent_storage:
            return
        
        try:
            self.persistent_storage.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for key, entry in self._cache.items():
                data[key] = {
                    'value': entry.value,
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat(),
                    'access_count': entry.access_count,
                    'ttl': entry.ttl,
                    'priority': entry.priority,
                    'compressed': entry.compressed,
                    'compressed_size': entry.compressed_size,
                    'original_size': entry.original_size,
                    'metadata': entry.metadata
                }
            
            with open(self.persistent_storage, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            logger.debug(f"Persisted {len(data)} cache entries")
            
        except Exception as e:
            logger.warning(f"Failed to persist cache: {e}")
    
    def _remove_persistent_entry(self, key: str) -> None:
        """Remove entry from persistent storage"""
        # This would implement incremental removal
        pass
    
    def _clear_persistent(self) -> None:
        """Clear persistent storage"""
        if self.persistent_storage and self.persistent_storage.exists():
            try:
                self.persistent_storage.unlink()
            except Exception as e:
                logger.warning(f"Failed to clear persistent storage: {e}")
    
    def shutdown(self) -> None:
        """Shutdown cache system"""
        self._running = False
        
        # Wait for cleanup thread
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)
        
        # Final persistence
        if self.persistent_storage:
            self._persist_all()
        
        logger.info("Cache system shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.shutdown()
        except:
            pass


# Singleton cache instance
_cache_instance: Optional[CacheSystem] = None
_cache_lock = threading.Lock()


def get_cache(
    max_size: int = 1000,
    max_memory_mb: int = 100,
    strategy: CacheStrategy = CacheStrategy.LRU
) -> CacheSystem:
    """
    Get singleton cache instance
    
    Args:
        max_size: Maximum cache entries
        max_memory_mb: Maximum memory usage
        strategy: Eviction strategy
    
    Returns:
        CacheSystem singleton instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = CacheSystem(max_size, max_memory_mb, strategy)
    
    return _cache_instance


def reset_cache() -> None:
    """Reset the cache instance"""
    global _cache_instance
    with _cache_lock:
        if _cache_instance:
            try:
                _cache_instance.shutdown()
            except Exception:
                pass
        _cache_instance = None
    logger.info("Cache instance reset")


def create_cache_instance(
    max_size: int = 1000,
    max_memory_mb: int = 100,
    strategy: CacheStrategy = CacheStrategy.LRU,
    compression: CompressionType = CompressionType.GZIP
) -> CacheSystem:
    """
    Create a new cache instance
    
    Args:
        max_size: Maximum cache entries
        max_memory_mb: Maximum memory usage
        strategy: Eviction strategy
        compression: Compression algorithm
    
    Returns:
        New CacheSystem instance
    """
    return CacheSystem(max_size, max_memory_mb, strategy, compression)