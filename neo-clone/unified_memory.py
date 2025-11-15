"""
Unified Memory System for Neo-Clone Architecture

This module provides a single, unified interface for all memory operations,
combining persistent storage and vector search capabilities into one cohesive system.

Author: Neo-Clone Enhanced
Version: 1.0 Unified
"""

import asyncio
import json
import uuid
import threading
import time
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

# Import data models
from data_models import MemoryType, MemoryEntry, MessageRole, MemoryVector, SearchResult

# Import existing memory systems
from persistent_memory import PersistentMemory
from vector_memory import VectorMemoryOptimized, MemoryQuery

# Configure logging
logger = logging.getLogger(__name__)


class MemoryOperation(Enum):
    """Types of memory operations"""
    STORE = "store"
    RETRIEVE = "retrieve"
    SEARCH = "search"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class UnifiedMemoryConfig:
    """Configuration for unified memory system"""
    persistent_dir: str = "data/memory"
    vector_dir: str = "data/vector_memory"
    max_persistent_history: int = 1000
    max_vector_entries: int = 10000
    auto_save: bool = True
    backup_enabled: bool = True
    max_backups: int = 10
    vector_dimensions: int = 384  # Default embedding dimensions
    similarity_threshold: float = 0.6
    cache_enabled: bool = True
    cache_size: int = 1000


class UnifiedMemoryManager:
    """
    Unified memory manager that provides a single interface for all memory operations.

    Features:
    - Persistent conversation storage
    - Vector-based semantic search
    - Automatic data routing (persistent vs vector)
    - Performance caching
    - Thread-safe operations
    - Backup and recovery
    - Statistics and monitoring
    """

    def __init__(self, config: Optional[UnifiedMemoryConfig] = None):
        self.config = config or UnifiedMemoryConfig()

        # Initialize underlying memory systems
        self.persistent_memory = PersistentMemory(
            memory_dir=self.config.persistent_dir,
            max_history=self.config.max_persistent_history,
            auto_save=self.config.auto_save,
            backup_enabled=self.config.backup_enabled,
            max_backups=self.config.max_backups
        )

        self.vector_memory = VectorMemoryOptimized(
            memory_dir=self.config.vector_dir,
            max_vectors=self.config.max_vector_entries,
            embedding_dimensions=self.config.vector_dimensions
        )

        # Thread safety
        self._lock = threading.RLock()

        # Performance cache
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Statistics
        self.stats = {
            "operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "persistent_operations": 0,
            "vector_operations": 0,
            "errors": 0
        }

        # Session ID property (delegate to persistent memory)
        self.session_id = self.persistent_memory.session_id

        logger.info("Unified Memory Manager initialized")

    def _get_cache_key(self, operation: str, *args, **kwargs) -> str:
        """Generate cache key for operation"""
        key_data = f"{operation}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get result from cache if valid"""
        if not self.config.cache_enabled:
            return None

        if cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key)
            if timestamp and (datetime.now() - timestamp).seconds < 300:  # 5 minute cache
                self.stats["cache_hits"] += 1
                return self._cache[cache_key]

        self.stats["cache_misses"] += 1
        return None

    def _set_cached_result(self, cache_key: str, result: Any):
        """Store result in cache"""
        if not self.config.cache_enabled:
            return

        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = datetime.now()

        # Maintain cache size
        if len(self._cache) > self.config.cache_size:
            # Remove oldest entries
            oldest_keys = sorted(self._cache_timestamps.keys(),
                               key=lambda k: self._cache_timestamps[k])[:100]
            for key in oldest_keys:
                del self._cache[key]
                del self._cache_timestamps[key]

    def _route_operation(self, data: Dict[str, Any]) -> str:
        """Determine which memory system should handle the operation"""
        # Route based on data type and content
        memory_type = data.get('memory_type', MemoryType.EPISODIC)

        # Vector memory for semantic search content
        if memory_type in [MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            return "vector"

        # Persistent memory for conversations and structured data
        if memory_type in [MemoryType.EPISODIC, MemoryType.WORKING]:
            return "persistent"

        # Default to persistent for structured data
        if 'conversation_id' in data or 'session_id' in data:
            return "persistent"

        # Use vector for text-heavy content
        if 'content' in data and len(str(data.get('content', ''))) > 100:
            return "vector"

        return "persistent"

    async def store(self, data: Dict[str, Any]) -> str:
        """Store data in the appropriate memory system"""
        with self._lock:
            try:
                self.stats["operations"] += 1

                # Determine routing
                target_system = self._route_operation(data)

                if target_system == "vector":
                    self.stats["vector_operations"] += 1
                    memory_id = await self.vector_memory.store_memory(data)
                else:
                    self.stats["persistent_operations"] += 1
                    # For persistent memory, use add_conversation with appropriate parameters
                    user_input = data.get('user_input', data.get('content', ''))
                    assistant_response = data.get('assistant_response', data.get('response', ''))
                    memory_id = self.persistent_memory.add_conversation(
                        user_input=user_input,
                        assistant_response=assistant_response,
                        intent=data.get('intent'),
                        skill_used=data.get('skill_used'),
                        metadata=data.get('metadata', {})
                    )

                # Clear relevant cache entries
                cache_prefix = f"search:{data.get('content', '')[:50]}"
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(cache_prefix)]
                for key in keys_to_remove:
                    self._cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)

                logger.debug(f"Stored memory in {target_system} system: {memory_id}")
                return memory_id

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to store memory: {e}")
                raise

    def add_conversation(self, user_input: str, assistant_response: str = "",
                        intent: Optional[str] = None, skill_used: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a conversation to memory (synchronous wrapper for store)"""
        import asyncio

        data = {
            "user_input": user_input,
            "assistant_response": assistant_response,
            "intent": intent,
            "skill_used": skill_used,
            "metadata": metadata or {},
            "memory_type": MemoryType.EPISODIC,
            "conversation_id": f"conv_{int(asyncio.get_event_loop().time() * 1000000)}"
        }

        # Run the async store method in a synchronous context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, we need to handle this differently
                # For now, delegate directly to persistent memory
                return self.persistent_memory.add_conversation(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    intent=intent,
                    skill_used=skill_used,
                    metadata=metadata or {}
                )
            else:
                return loop.run_until_complete(self.store(data))
        except RuntimeError:
            # No event loop, delegate to persistent memory
            return self.persistent_memory.add_conversation(
                user_input=user_input,
                assistant_response=assistant_response,
                intent=intent,
                skill_used=skill_used,
                metadata=metadata or {}
            )

    async def retrieve(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by ID from either memory system"""
        with self._lock:
            try:
                self.stats["operations"] += 1

                # Try vector memory first
                result = await self.vector_memory.get_memory_by_id(memory_id)
                if result:
                    self.stats["vector_operations"] += 1
                    return result

                # Try persistent memory - search for the conversation
                conversations = self.persistent_memory.search_conversations("", limit=1000)
                for conv in conversations:
                    if conv.get('id') == memory_id:
                        self.stats["persistent_operations"] += 1
                        return conv

                return None

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to retrieve memory {memory_id}: {e}")
                return None

    async def search(self, query: Union[str, MemoryQuery], **kwargs) -> List[SearchResult]:
        """Search across both memory systems"""
        with self._lock:
            try:
                self.stats["operations"] += 1

                # Create unified query
                if isinstance(query, str):
                    memory_query = MemoryQuery(query=query, **kwargs)
                else:
                    memory_query = query

                cache_key = self._get_cache_key("search", str(memory_query))
                cached_result = self._get_cached_result(cache_key)
                if cached_result is not None:
                    return cached_result

                # Search both systems
                results = []

                # Vector search (semantic)
                try:
                    vector_results = self.vector_memory.search(memory_query)
                    results.extend(vector_results)
                    self.stats["vector_operations"] += 1
                except Exception as e:
                    logger.warning(f"Vector search failed: {e}")

                # Persistent search (keyword-based) - simplified for now
                try:
                    # Search in all conversations for the query
                    query_text = (memory_query.query or memory_query.text or "").lower()
                    if query_text:
                        persistent_results = self.persistent_memory.search_conversations(
                            query_text,
                            limit=memory_query.limit
                        )
                        # Convert to SearchResult format
                        for item in persistent_results:
                            if isinstance(item, dict):
                                content = item.get('user_input', '') + ' ' + item.get('assistant_response', '')
                                result = SearchResult(
                                    content=content,
                                    relevance_score=0.6,  # Default relevance for keyword matches
                                    source="persistent_memory",
                                    metadata={
                                        "id": item.get('id', ''),
                                        "memory_type": MemoryType.EPISODIC.value,
                                        **item
                                    }
                                )
                                results.append(result)
                        self.stats["persistent_operations"] += 1
                except Exception as e:
                    logger.warning(f"Persistent search failed: {e}")

                # Sort by relevance_score and limit results
                results.sort(key=lambda x: x.relevance_score, reverse=True)
                final_results = results[:memory_query.limit]

                # Cache results
                self._set_cached_result(cache_key, final_results)

                return final_results

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Search failed: {e}")
                return []

    async def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory entry"""
        with self._lock:
            try:
                self.stats["operations"] += 1

                # Try vector memory first
                success = await self.vector_memory.update_memory(memory_id, updates)
                if success:
                    self.stats["vector_operations"] += 1
                    return True

                # Persistent memory doesn't support updates - return False
                # (Could be implemented by modifying the conversation list directly)
                self.stats["persistent_operations"] += 1
                return False

                return False

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to update memory {memory_id}: {e}")
                return False

    async def delete(self, memory_id: str) -> bool:
        """Delete memory entry"""
        with self._lock:
            try:
                self.stats["operations"] += 1

                # Try both systems
                vector_deleted = await self.vector_memory.delete_memory(memory_id)
                # Persistent memory doesn't have delete_conversation method
                # Could be implemented by removing from conversations list
                persistent_deleted = False

                success = vector_deleted or persistent_deleted
                if success:
                    # Clear cache
                    keys_to_remove = [k for k in self._cache.keys() if memory_id in k]
                    for key in keys_to_remove:
                        self._cache.pop(key, None)
                        self._cache_timestamps.pop(key, None)

                return success

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to delete memory {memory_id}: {e}")
                return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        with self._lock:
            persistent_stats = self.persistent_memory.get_statistics()
            vector_stats = self.vector_memory.get_statistics()

            return {
                "unified_stats": self.stats.copy(),
                "persistent_memory": persistent_stats,
                "vector_memory": vector_stats,
                "total_entries": persistent_stats.get("total_conversations", 0) + vector_stats.get("total_entries", 0),
                "cache_info": {
                    "enabled": self.config.cache_enabled,
                    "size": len(self._cache),
                    "max_size": self.config.cache_size,
                    "hit_rate": self.stats["cache_hits"] / max(self.stats["operations"], 1)
                },
                "timestamp": datetime.now().isoformat()
            }

    def clear_cache(self):
        """Clear the memory cache"""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("Memory cache cleared")

    def optimize(self):
        """Optimize memory systems"""
        with self._lock:
            try:
                # Optimize persistent memory
                self.persistent_memory.optimize_storage()

                # Optimize vector memory
                self.vector_memory.optimize_index()

                # Clear old cache entries
                cutoff = datetime.now() - timedelta(hours=1)
                old_keys = [k for k, ts in self._cache_timestamps.items() if ts < cutoff]
                for key in old_keys:
                    self._cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)

                logger.info("Memory systems optimized")

            except Exception as e:
                logger.error(f"Memory optimization failed: {e}")

    def backup(self) -> bool:
        """Create backup of all memory systems"""
        try:
            # Backup persistent memory
            persistent_backup = self.persistent_memory.create_backup()

            # Backup vector memory
            vector_backup = self.vector_memory.create_backup()

            logger.info("Unified memory backup completed")
            return persistent_backup and vector_backup

        except Exception as e:
            logger.error(f"Memory backup failed: {e}")
            return False

    def restore(self, backup_path: str) -> bool:
        """Restore memory systems from backup"""
        try:
            # This would need to be implemented based on backup format
            logger.warning("Restore functionality not yet implemented")
            return False

        except Exception as e:
            logger.error(f"Memory restore failed: {e}")
            return False

    # Compatibility methods for existing code
    def store_conversation(self, data: Dict[str, Any]) -> str:
        """Compatibility method for persistent memory interface"""
        return asyncio.run(self.store(data))

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Compatibility method for persistent memory interface"""
        return asyncio.run(self.retrieve(conversation_id))

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Compatibility method for persistent memory interface"""
        results = asyncio.run(self.search(query, limit=limit))
        return [{"content": r.content, "id": r.metadata.get("id", ""), "relevance": r.relevance_score, "metadata": r.metadata} for r in results]

    async def store_memory(self, data: Dict[str, Any]) -> str:
        """Compatibility method for vector memory interface"""
        return await self.store(data)

    def search_memory(self, query: MemoryQuery) -> List[SearchResult]:
        """Compatibility method for vector memory interface"""
        return self.vector_memory.search(query)


# Global instance
_unified_memory = UnifiedMemoryManager()

def get_unified_memory() -> UnifiedMemoryManager:
    """Get the global unified memory manager instance"""
    return _unified_memory

# Backward compatibility aliases
def get_memory() -> UnifiedMemoryManager:
    """Backward compatibility for persistent memory interface"""
    return _unified_memory

def get_vector_memory() -> UnifiedMemoryManager:
    """Backward compatibility for vector memory interface"""
    return _unified_memory