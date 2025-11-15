"""
Vector Memory System for MiniMax Agent Architecture

This module provides semantic search capabilities with vector embeddings,
keyword-based indexing, and optimized search performance.

Author: MiniMax Agent
Version: 1.0
"""

import json
import uuid
import threading
import time
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import hashlib

# Import data models
from data_models import MemoryVector, MemoryType, SearchResult

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MemoryQuery:
    """Query for memory search with multiple options"""
    query: str = ""
    text: str = ""  # Alias for query
    limit: int = 10
    threshold: float = 0.6
    hybrid_search: bool = True
    memory_type: Optional[MemoryType] = None
    tags: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    date_range: Optional[Tuple[datetime, datetime]] = None
    min_importance: float = 0.0
    max_age_days: Optional[float] = None


class VectorMemoryOptimized:
    """
    Optimized vector memory with advanced features:
    
    - Keyword-based indexing for fast search
    - Background consolidation tasks
    - Semantic search with embeddings
    - Importance-based retention
    - Memory compression and cleanup
    - Hybrid search capabilities
    - Thread-safe operations
    """
    
    def __init__(
        self,
        memory_dir: str = "data/vector_memory",
        cache_size: int = 1000,
        consolidation_interval: int = 300,  # 5 minutes
        max_vectors: int = 10000,
        embedding_dimensions: int = 100,
        compression_enabled: bool = True
    ):
        """
        Initialize vector memory system
        
        Args:
            memory_dir: Storage directory for vector data
            cache_size: Maximum vectors to keep in memory cache
            consolidation_interval: Background consolidation interval (seconds)
            max_vectors: Maximum number of vectors to store
            embedding_dimensions: Dimensionality of embeddings
            compression_enabled: Enable vector compression
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_size = cache_size
        self.consolidation_interval = consolidation_interval
        self.max_vectors = max_vectors
        self.embedding_dimensions = embedding_dimensions
        self.compression_enabled = compression_enabled
        
        # Thread safety
        self._lock = threading.RLock()
        self._running = False
        self._consolidation_thread: Optional[threading.Thread] = None
        
        # Storage structures
        self.vectors: List[Dict[str, Any]] = []
        self.index: Optional[Dict[str, Any]] = None
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.metadata_index: Dict[str, List[int]] = {}
        
        # Performance tracking
        self.search_stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "average_response_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # File paths
        self.vectors_file = self.memory_dir / "vectors.json"
        self.index_file = self.memory_dir / "index.json"
        self.metadata_file = self.memory_dir / "metadata.json"
        
        # Initialize from storage
        self._load_vectors()
        self._build_index()
        self._start_background_tasks()
        
        logger.info(f"Initialized vector memory: {len(self.vectors)} vectors loaded")
    
    def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Add memory entry with optional pre-computed embedding
        
        Args:
            content: Memory content text
            memory_type: Type of memory (episodic, semantic, etc.)
            importance: Importance score (0.0 to 1.0)
            tags: Optional tags for categorization
            metadata: Additional metadata
            embedding: Pre-computed embedding vector (optional)
        
        Returns:
            Memory ID
        """
        with self._lock:
            memory_id = str(uuid.uuid4())
            
            # Generate embedding if not provided
            if embedding is None:
                embedding = self._generate_embedding(content)
            
            # Ensure embedding dimensions
            embedding = self._normalize_embedding(embedding)
            
            memory = {
                "id": memory_id,
                "content": content,
                "embedding": embedding,
                "memory_type": memory_type.value,
                "importance": max(0.0, min(1.0, importance)),
                "tags": tags or [],
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0,
                "search_relevance": 0.0
            }
            
            # Add to vectors
            self.vectors.append(memory)
            
            # Update indexes
            if self.index:
                self._add_to_index(memory, len(self.vectors) - 1)
            
            self._add_to_metadata_index(memory, len(self.vectors) - 1)
            
            # Check if we need to consolidate (too many vectors)
            if len(self.vectors) > self.max_vectors:
                self._consolidate_vectors()
            
            # Auto-save periodically
            if len(self.vectors) % 100 == 0:  # Save every 100 entries
                self._save_to_disk()
            
            logger.debug(f"Added memory: {memory_id} (type: {memory_type.value})")
            return memory_id
    
    def search(
        self,
        query: Union[str, MemoryQuery],
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
        hybrid_search: Optional[bool] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        case_sensitive: bool = False,
        min_importance: float = 0.0
    ) -> List[SearchResult]:
        """
        Search memory using query with advanced filtering
        
        Args:
            query: Search query (string or MemoryQuery object)
            limit: Maximum results (overrides query.limit)
            threshold: Similarity threshold (overrides query.threshold)
            hybrid_search: Enable hybrid search (overrides query.hybrid_search)
            memory_type: Filter by memory type
            tags: Filter by tags
            case_sensitive: Case sensitive search
            min_importance: Minimum importance threshold
        
        Returns:
            List of SearchResult objects
        """
        start_time = time.time()
        
        with self._lock:
            self.search_stats["total_searches"] += 1
            
            # Handle string query
            if isinstance(query, str):
                query_obj = MemoryQuery(
                    query=query,
                    text=query,
                    limit=limit or 10,
                    threshold=threshold or 0.6,
                    hybrid_search=hybrid_search if hybrid_search is not None else True,
                    memory_type=memory_type,
                    tags=tags or [],
                    case_sensitive=case_sensitive,
                    min_importance=min_importance
                )
            else:
                # Override MemoryQuery with additional parameters
                query_obj = query
                if limit is not None:
                    query_obj.limit = limit
                if threshold is not None:
                    query_obj.threshold = threshold
                if hybrid_search is not None:
                    query_obj.hybrid_search = hybrid_search
                if memory_type is not None:
                    query_obj.memory_type = memory_type
                if tags is not None:
                    query_obj.tags = tags
                if case_sensitive:
                    query_obj.case_sensitive = case_sensitive
                if min_importance > 0.0:
                    query_obj.min_importance = min_importance
            
            # Get query text
            query_text = query_obj.query or query_obj.text
            
            if not query_text.strip():
                logger.warning("Empty search query")
                return []
            
            # Perform search
            search_results = self._perform_search(query_obj)
            
            # Update performance stats
            response_time = time.time() - start_time
            self._update_search_stats(search_results, response_time)
            
            # Convert to SearchResult objects
            results = []
            for vector, similarity in search_results:
                result = SearchResult(
                    content=vector["content"],
                    relevance_score=similarity,
                    source="vector_memory",
                    metadata={
                        "id": vector["id"],
                        "memory_type": vector["memory_type"],
                        "importance": vector["importance"],
                        "tags": vector["tags"],
                        "created_at": vector["created_at"],
                        "access_count": vector["access_count"]
                    }
                )
                results.append(result)
            
            logger.debug(f"Search completed: {len(results)} results in {response_time:.3f}s")
            return results
    
    def _perform_search(self, query: MemoryQuery) -> List[Tuple[Dict[str, Any], float]]:
        """Perform the actual search based on query parameters"""
        query_text = query.query or query.text
        search_limit = query.limit
        threshold = query.threshold
        
        if not query.hybrid_search:
            return self._semantic_search(query_text, search_limit, threshold)
        
        # Hybrid search: combine semantic and keyword approaches
        semantic_results = self._semantic_search(query_text, search_limit * 2, threshold * 0.8)
        keyword_results = self._keyword_search(query_text, search_limit * 2, 0.3)
        
        # Combine and deduplicate results
        combined_results = self._merge_search_results(semantic_results, keyword_results)
        
        # Apply filters
        filtered_results = self._apply_filters(combined_results, query)
        
        # Sort by relevance and return top results
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        return filtered_results[:search_limit]
    
    def _semantic_search(
        self,
        query: str,
        limit: int,
        threshold: float
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Perform semantic search using embeddings"""
        if not self.index or not self.vectors:
            return []
        
        query_embedding = self._generate_embedding(query)
        results = []
        
        for idx, vector in enumerate(self.vectors):
            # Skip if no embedding
            if not vector.get("embedding"):
                continue
            
            similarity = self._cosine_similarity(query_embedding, vector["embedding"])
            
            if similarity >= threshold:
                # Update access tracking
                vector["access_count"] += 1
                vector["last_accessed"] = datetime.now().isoformat()
                
                results.append((vector, similarity))
        
        # Sort by similarity and importance
        results.sort(key=lambda x: (x[1], x[0]["importance"]), reverse=True)
        return results[:limit]
    
    def _keyword_search(
        self,
        query: str,
        limit: int,
        min_overlap: float = 0.3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Perform keyword-based search"""
        if not self.index:
            return []
        
        query_words = set(query.lower().split())
        if not query_words:
            return []
        
        # Find vectors containing query words
        candidate_indices = set()
        for word in query_words:
            if word in self.index.get("keywords", {}):
                candidate_indices.update(self.index["keywords"][word])
        
        if not candidate_indices:
            return []
        
        # Calculate overlap scores
        results = []
        query_word_count = len(query_words)
        
        for idx in candidate_indices:
            if idx >= len(self.vectors):
                continue
            
            vector = self.vectors[idx]
            content_words = set(vector["content"].lower().split())
            
            if content_words:
                overlap = len(query_words & content_words)
                overlap_score = overlap / query_word_count
                
                if overlap_score >= min_overlap:
                    # Update access tracking
                    vector["access_count"] += 1
                    vector["last_accessed"] = datetime.now().isoformat()
                    
                    results.append((vector, overlap_score))
        
        # Sort by overlap score and importance
        results.sort(key=lambda x: (x[1], x[0]["importance"]), reverse=True)
        return results[:limit]
    
    def _merge_search_results(
        self,
        semantic_results: List[Tuple[Dict[str, Any], float]],
        keyword_results: List[Tuple[Dict[str, Any], float]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Merge semantic and keyword search results"""
        # Create combined results with improved scoring
        combined = {}
        
        # Add semantic results with weight
        for vector, semantic_score in semantic_results:
            vector_id = vector["id"]
            combined[vector_id] = (vector, semantic_score * 0.7)
        
        # Add keyword results with weight and merge
        for vector, keyword_score in keyword_results:
            vector_id = vector["id"]
            if vector_id in combined:
                # Average the scores
                current_score = combined[vector_id][1]
                combined[vector_id] = (vector, (current_score + keyword_score * 0.6) / 2)
            else:
                combined[vector_id] = (vector, keyword_score * 0.6)
        
        return list(combined.values())
    
    def _apply_filters(
        self,
        results: List[Tuple[Dict[str, Any], float]],
        query: MemoryQuery
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Apply additional filters to search results"""
        filtered = []
        
        for vector, score in results:
            # Memory type filter
            if query.memory_type and vector["memory_type"] != query.memory_type.value:
                continue
            
            # Tags filter
            if query.tags and not any(tag in vector["tags"] for tag in query.tags):
                continue
            
            # Importance filter
            if vector["importance"] < query.min_importance:
                continue
            
            # Date range filter
            if query.date_range:
                created_at = datetime.fromisoformat(vector["created_at"])
                if not (query.date_range[0] <= created_at <= query.date_range[1]):
                    continue
            
            # Age filter
            if query.max_age_days:
                created_at = datetime.fromisoformat(vector["created_at"])
                age_days = (datetime.now() - created_at).days
                if age_days > query.max_age_days:
                    continue
            
            filtered.append((vector, score))
        
        return filtered
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using improved bag-of-words approach.
        
        In production, this would use actual embedding models like:
        - OpenAI text-embedding models
        - Sentence Transformers
        - Local models via sentence-transformers library
        """
        # Improved bag-of-words with TF-IDF-like weighting
        words = text.lower().split()
        word_freq = {}
        
        # Count word frequencies
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Create weighted vector
        vector = [0.0] * self.embedding_dimensions
        
        for word, freq in word_freq.items():
            # Hash word to get consistent index
            word_hash = hashlib.md5(word.encode()).digest()
            # Use first 4 bytes to get index
            idx = int.from_bytes(word_hash[:4], 'big') % self.embedding_dimensions
            
            # Weight by frequency (log-scaled to reduce impact of very common words)
            weight = math.log(1 + freq)
            vector[idx] += weight
        
        return self._normalize_embedding(vector)
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding vector to unit length"""
        if not embedding:
            return [0.0] * self.embedding_dimensions
        
        # Pad or truncate to target dimensions
        if len(embedding) < self.embedding_dimensions:
            embedding = embedding + [0.0] * (self.embedding_dimensions - len(embedding))
        elif len(embedding) > self.embedding_dimensions:
            embedding = embedding[:self.embedding_dimensions]
        
        # Normalize to unit length
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude == 0:
            return [0.0] * self.embedding_dimensions
        
        return [x / magnitude for x in embedding]
    
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        return max(0.0, min(1.0, dot_product))  # Already normalized
    
    def _build_index(self) -> None:
        """Build keyword index for fast search"""
        with self._lock:
            self.index = {
                "keywords": {},
                "tags": {},
                "metadata": {
                    "built_at": datetime.now().isoformat(),
                    "vector_count": len(self.vectors),
                    "index_version": "1.0"
                }
            }
            
            for idx, vector in enumerate(self.vectors):
                self._add_to_index(vector, idx)
                self._add_to_metadata_index(vector, idx)
    
    def _add_to_index(self, vector: Dict[str, Any], idx: int) -> None:
        """Add vector to keyword index"""
        content = vector.get("content", "")
        words = set(content.lower().split())
        
        for word in words:
            if word not in self.index["keywords"]:
                self.index["keywords"][word] = []
            self.index["keywords"][word].append(idx)
        
        # Add tags to index
        for tag in vector.get("tags", []):
            if tag not in self.index["tags"]:
                self.index["tags"][tag] = []
            self.index["tags"][tag].append(idx)
    
    def _add_to_metadata_index(self, vector: Dict[str, Any], idx: int) -> None:
        """Add vector to metadata index"""
        memory_type = vector.get("memory_type", "unknown")
        if memory_type not in self.metadata_index:
            self.metadata_index[memory_type] = []
        self.metadata_index[memory_type].append(idx)
    
    def _consolidate_vectors(self) -> None:
        """Consolidate vectors to maintain performance"""
        logger.info("Starting vector consolidation")
        
        # Remove least important/frequently accessed vectors
        vectors_to_keep = int(self.max_vectors * 0.8)  # Keep 80%
        
        # Sort by importance and access frequency
        self.vectors.sort(key=lambda v: (v["importance"], v["access_count"]), reverse=True)
        
        # Keep only the most important vectors
        consolidated = self.vectors[:vectors_to_keep]
        removed_count = len(self.vectors) - len(consolidated)
        
        self.vectors = consolidated
        
        # Rebuild indexes
        self._build_index()
        
        logger.info(f"Consolidated vectors: removed {removed_count}, kept {len(self.vectors)}")
    
    def _update_search_stats(self, results: List, response_time: float) -> None:
        """Update search performance statistics"""
        self.search_stats["successful_searches"] += 1
        
        # Update average response time
        total_searches = self.search_stats["total_searches"]
        current_avg = self.search_stats["average_response_time"]
        self.search_stats["average_response_time"] = (
            (current_avg * (total_searches - 1) + response_time) / total_searches
        )
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory entry by ID"""
        with self._lock:
            for vector in self.vectors:
                if vector["id"] == memory_id:
                    # Update access tracking
                    vector["access_count"] += 1
                    vector["last_accessed"] = datetime.now().isoformat()
                    return vector
        return None
    
    def update_memory_importance(self, memory_id: str, new_importance: float) -> bool:
        """Update importance score of a memory entry"""
        with self._lock:
            for vector in self.vectors:
                if vector["id"] == memory_id:
                    vector["importance"] = max(0.0, min(1.0, new_importance))
                    return True
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory entry by ID"""
        with self._lock:
            for idx, vector in enumerate(self.vectors):
                if vector["id"] == memory_id:
                    del self.vectors[idx]
                    # Rebuild indexes
                    self._build_index()
                    return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive vector memory statistics"""
        with self._lock:
            # Memory type distribution
            type_distribution = {}
            for vector in self.vectors:
                memory_type = vector.get("memory_type", "unknown")
                type_distribution[memory_type] = type_distribution.get(memory_type, 0) + 1
            
            # Importance distribution
            importance_ranges = {
                "very_high": 0,    # 0.8-1.0
                "high": 0,         # 0.6-0.8
                "medium": 0,       # 0.4-0.6
                "low": 0,          # 0.2-0.4
                "very_low": 0      # 0.0-0.2
            }
            
            for vector in self.vectors:
                importance = vector.get("importance", 0.5)
                if importance >= 0.8:
                    importance_ranges["very_high"] += 1
                elif importance >= 0.6:
                    importance_ranges["high"] += 1
                elif importance >= 0.4:
                    importance_ranges["medium"] += 1
                elif importance >= 0.2:
                    importance_ranges["low"] += 1
                else:
                    importance_ranges["very_low"] += 1
            
            # Access statistics
            total_accesses = sum(v.get("access_count", 0) for v in self.vectors)
            avg_accesses = total_accesses / len(self.vectors) if self.vectors else 0
            
            return {
                "total_vectors": len(self.vectors),
                "memory_directory": str(self.memory_dir),
                "memory_type_distribution": type_distribution,
                "importance_distribution": importance_ranges,
                "total_accesses": total_accesses,
                "average_accesses_per_vector": avg_accesses,
                "index_keywords": len(self.index.get("keywords", {})) if self.index else 0,
                "search_statistics": self.search_stats.copy(),
                "performance_config": {
                    "cache_size": self.cache_size,
                    "max_vectors": self.max_vectors,
                    "embedding_dimensions": self.embedding_dimensions,
                    "compression_enabled": self.compression_enabled
                }
            }
    
    def _save_to_disk(self) -> None:
        """Save vectors and index to disk"""
        try:
            with self._lock:
                # Save vectors
                with open(self.vectors_file, 'w', encoding='utf-8') as f:
                    json.dump(self.vectors, f, indent=2, ensure_ascii=False)
                
                # Save index
                if self.index:
                    with open(self.index_file, 'w', encoding='utf-8') as f:
                        json.dump(self.index, f, indent=2, ensure_ascii=False)
                
                # Save metadata index
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata_index, f, indent=2, ensure_ascii=False)
                
                logger.debug("Saved vector memory to disk")
                
        except Exception as e:
            logger.error(f"Failed to save vector memory: {e}")
    
    def _load_vectors(self) -> None:
        """Load vectors from disk"""
        try:
            if self.vectors_file.exists():
                with open(self.vectors_file, 'r', encoding='utf-8') as f:
                    self.vectors = json.load(f)
                logger.info(f"Loaded {len(self.vectors)} vectors from disk")
        except Exception as e:
            logger.warning(f"Failed to load vectors: {e}")
            self.vectors = []
    
    def _load_index(self) -> None:
        """Load index from disk"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load index: {e}")
            self.index = None
    
    def _load_metadata(self) -> None:
        """Load metadata index from disk"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata_index = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            self.metadata_index = {}
    
    def _load_vectors(self) -> None:
        """Load vectors and related data from disk"""
        try:
            if self.vectors_file.exists():
                with open(self.vectors_file, 'r', encoding='utf-8') as f:
                    self.vectors = json.load(f)
                logger.info(f"Loaded {len(self.vectors)} vectors from disk")
            
            self._load_index()
            self._load_metadata()
            
        except Exception as e:
            logger.warning(f"Failed to load vector memory: {e}")
            self.vectors = []
            self.index = None
            self.metadata_index = {}
    
    def _start_background_tasks(self) -> None:
        """Start background consolidation and maintenance tasks"""
        self._running = True
        
        def consolidation_worker():
            """Background worker for consolidation and maintenance"""
            while self._running:
                try:
                    time.sleep(self.consolidation_interval)
                    if not self._running:
                        break
                    
                    # Perform consolidation if needed
                    if len(self.vectors) > self.max_vectors * 0.9:  # 90% threshold
                        self._consolidate_vectors()
                    
                    # Periodic save
                    self._save_to_disk()
                    
                except Exception as e:
                    logger.error(f"Background consolidation error: {e}")
        
        self._consolidation_thread = threading.Thread(
            target=consolidation_worker,
            daemon=True,
            name="VectorMemoryConsolidation"
        )
        self._consolidation_thread.start()
        logger.info("Started background consolidation tasks")
    
    def shutdown(self) -> None:
        """Shutdown vector memory system and cleanup"""
        self._running = False
        
        # Wait for background thread to finish
        if self._consolidation_thread and self._consolidation_thread.is_alive():
            self._consolidation_thread.join(timeout=5.0)
        
        # Final save
        self._save_to_disk()
        
        logger.info("Vector memory system shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.shutdown()
        except:
            pass


# Singleton instance management
_vector_memory_instance: Optional[VectorMemoryOptimized] = None
_vector_memory_lock = threading.Lock()


def get_vector_memory(
    memory_dir: str = "data/vector_memory",
    cache_size: int = 1000
) -> VectorMemoryOptimized:
    """
    Get singleton vector memory instance
    
    Args:
        memory_dir: Memory storage directory
        cache_size: Cache size for vectors
    
    Returns:
        VectorMemoryOptimized singleton instance
    """
    global _vector_memory_instance
    
    if _vector_memory_instance is None:
        with _vector_memory_lock:
            if _vector_memory_instance is None:
                _vector_memory_instance = VectorMemoryOptimized(memory_dir, cache_size)
    
    return _vector_memory_instance


def reset_vector_memory() -> None:
    """Reset the vector memory instance"""
    global _vector_memory_instance
    with _vector_memory_lock:
        if _vector_memory_instance:
            try:
                _vector_memory_instance.shutdown()
            except Exception:
                pass
        _vector_memory_instance = None
    logger.info("Vector memory instance reset")


def create_vector_memory_instance(
    memory_dir: str = "data/vector_memory",
    cache_size: int = 1000,
    max_vectors: int = 10000
) -> VectorMemoryOptimized:
    """
    Create a new vector memory instance
    
    Args:
        memory_dir: Memory storage directory
        cache_size: Cache size for vectors
        max_vectors: Maximum number of vectors
    
    Returns:
        New VectorMemoryOptimized instance
    """
    return VectorMemoryOptimized(memory_dir, cache_size, max_vectors=max_vectors)