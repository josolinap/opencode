"""
vector_memory.py - Advanced Vector Memory System with Redis-like Capabilities

Inspired by Redis Vector Search and modern vector databases:
- High-performance vector storage and retrieval
- Semantic search capabilities
- Real-time memory operations
- Hybrid search (vector + keyword)
- Memory persistence and indexing
- Multi-modal memory support

Features:
1. Vector embeddings storage
2. Similarity search with multiple metrics
3. Real-time indexing
4. Memory layers (short-term, long-term, episodic)
5. Cross-session memory continuity
6. Intelligent memory consolidation
"""

import json
import os
import pickle
import hashlib
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict
import sqlite3
import math

logger = logging.getLogger(__name__)

@dataclass
class MemoryVector:
    """Vector memory entry with metadata"""
    id: str
    vector: List[float]
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    memory_type: str = "episodic"  # episodic, semantic, procedural
    importance: float = 1.0
    tags: List[str] = field(default_factory=list)

@dataclass
class MemoryQuery:
    """Query for vector memory search"""
    query: str
    vector: Optional[List[float]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    threshold: float = 0.7
    memory_types: List[str] = field(default_factory=lambda: ["episodic", "semantic", "procedural"])
    hybrid_search: bool = True

class VectorMemory:
    """
    Advanced Vector Memory System
    Redis-like performance with AI-native capabilities
    """
    
    def __init__(self, memory_dir: str = "data/vector_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Database files
        self.vector_db_path = self.memory_dir / "vectors.db"
        self.metadata_db_path = self.memory_dir / "metadata.db"
        self.index_path = self.memory_dir / "vector_index.pkl"
        
        # Memory layers
        self.short_term_memory: Dict[str, MemoryVector] = {}
        self.long_term_memory: Dict[str, MemoryVector] = {}
        self.episodic_memory: Dict[str, MemoryVector] = {}
        
        # Indexing and search
        self.vector_index: Dict[str, List[float]] = {}
        self.inverted_index: Dict[str, List[str]] = defaultdict(list)
        
        # Performance optimization
        self.cache_size = 1000
        self.cache: Dict[str, MemoryVector] = {}
        self.access_history: List[str] = []
        
        # Threading
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize databases
        self._init_databases()
        self._load_memories()
        
        # Background tasks
        self._start_background_tasks()
    
    def _init_databases(self):
        """Initialize SQLite databases for vector storage"""
        try:
            # Vector database
            conn = sqlite3.connect(self.vector_db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vectors (
                    id TEXT PRIMARY KEY,
                    vector BLOB,
                    content TEXT,
                    metadata TEXT,
                    timestamp TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    memory_type TEXT,
                    importance REAL DEFAULT 1.0,
                    tags TEXT
                )
            ''')
            conn.commit()
            conn.close()
            
            # Metadata database for indexes
            conn = sqlite3.connect(self.metadata_db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS indexes (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            ''')
            conn.commit()
            conn.close()
            
            logger.info("Vector memory databases initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
    
    def _load_memories(self):
        """Load existing memories from databases"""
        try:
            conn = sqlite3.connect(self.vector_db_path)
            cursor = conn.execute('SELECT * FROM vectors')
            
            for row in cursor:
                vector = pickle.loads(row[1])
                metadata = json.loads(row[3]) if row[3] else {}
                tags = json.loads(row[8]) if row[8] else []
                
                memory = MemoryVector(
                    id=row[0],
                    vector=vector,
                    content=row[2],
                    metadata=metadata,
                    timestamp=row[4],
                    access_count=row[5],
                    last_accessed=row[6],
                    memory_type=row[7],
                    importance=row[8] if len(row) > 8 else 1.0,
                    tags=tags
                )
                
                # Store in appropriate memory layer
                if memory.memory_type == "episodic":
                    self.episodic_memory[memory.id] = memory
                elif memory.memory_type == "semantic":
                    self.long_term_memory[memory.id] = memory
                else:
                    self.short_term_memory[memory.id] = memory
                
                # Update indexes
                self.vector_index[memory.id] = memory.vector
                self._update_inverted_index(memory)
            
            conn.close()
            logger.info(f"Loaded {len(self.vector_index)} memories from database")
            
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
    
    def _update_inverted_index(self, memory: MemoryVector):
        """Update inverted index for keyword search"""
        words = memory.content.lower().split()
        for word in words:
            if len(word) > 2:  # Skip very short words
                self.inverted_index[word].append(memory.id)
    
    def _start_background_tasks(self):
        """Start background memory management tasks"""
        def memory_consolidation():
            while True:
                try:
                    self._consolidate_memories()
                    time.sleep(300)  # Every 5 minutes
                except Exception as e:
                    logger.error(f"Memory consolidation error: {e}")
        
        self._executor.submit(memory_consolidation)
    
    def add_memory(self, content: str, vector: Optional[List[float]] = None, 
                   memory_type: str = "episodic", importance: float = 1.0,
                   tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a new memory vector"""
        try:
            # Generate ID
            memory_id = hashlib.md5(f"{content}_{datetime.now().isoformat()}".encode()).hexdigest()
            
            # Generate vector if not provided (simplified - would use actual embedding model)
            if vector is None:
                vector = self._generate_embedding(content)
            
            # Create memory
            memory = MemoryVector(
                id=memory_id,
                vector=vector,
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            with self._lock:
                # Store in appropriate memory layer
                if memory_type == "episodic":
                    self.episodic_memory[memory_id] = memory
                elif memory_type == "semantic":
                    self.long_term_memory[memory_id] = memory
                else:
                    self.short_term_memory[memory_id] = memory
                
                # Update indexes
                self.vector_index[memory_id] = vector
                self._update_inverted_index(memory)
                
                # Update cache
                self._update_cache(memory_id, memory)
                
                # Persist to database
                self._persist_memory(memory)
            
            logger.info(f"Added memory {memory_id} of type {memory_type}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return ""
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (simplified implementation)"""
        # In a real implementation, this would use a proper embedding model
        # For now, create a simple hash-based embedding
        words = text.lower().split()
        embedding = []
        
        for i in range(128):  # 128-dimensional embedding
            if i < len(words):
                # Simple hash-based embedding
                word_hash = hash(words[i] + str(i))
                embedding.append((word_hash % 1000) / 1000.0)
            else:
                embedding.append(0.0)
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding
    
    def _persist_memory(self, memory: MemoryVector):
        """Persist memory to database"""
        try:
            conn = sqlite3.connect(self.vector_db_path)
            conn.execute('''
                INSERT OR REPLACE INTO vectors 
                (id, vector, content, metadata, timestamp, access_count, 
                 last_accessed, memory_type, importance, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.id,
                pickle.dumps(memory.vector),
                memory.content,
                json.dumps(memory.metadata),
                memory.timestamp,
                memory.access_count,
                memory.last_accessed,
                memory.memory_type,
                memory.importance,
                json.dumps(memory.tags)
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to persist memory {memory.id}: {e}")
    
    def search(self, query: MemoryQuery) -> List[MemoryVector]:
        """Search memories using vector similarity and/or keywords"""
        try:
            results = []
            
            # Generate query vector if not provided
            if query.vector is None:
                query.vector = self._generate_embedding(query.query)
            
            # Vector similarity search
            if query.vector:
                vector_results = self._vector_similarity_search(query)
                results.extend(vector_results)
            
            # Keyword search (for hybrid search)
            if query.hybrid_search and query.query:
                keyword_results = self._keyword_search(query)
                # Merge with vector results, avoiding duplicates
                existing_ids = {r.id for r in results}
                for result in keyword_results:
                    if result.id not in existing_ids:
                        results.append(result)
            
            # Apply filters
            if query.filters:
                results = [r for r in results if self._matches_filters(r, query.filters)]
            
            # Filter by memory types
            results = [r for r in results if r.memory_type in query.memory_types]
            
            # Sort by relevance and limit
            results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
            results = results[:query.limit]
            
            # Update access statistics
            for result in results:
                self._update_access_stats(result.id)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _vector_similarity_search(self, query: MemoryQuery) -> List[MemoryVector]:
        """Perform vector similarity search"""
        results = []
        query_vector = np.array(query.vector)
        
        for memory_id, vector in self.vector_index.items():
            memory_vector = np.array(vector)
            
            # Calculate cosine similarity
            similarity = np.dot(query_vector, memory_vector)
            
            if similarity >= query.threshold:
                # Get the full memory
                memory = self._get_memory_by_id(memory_id)
                if memory:
                    memory.metadata["similarity"] = float(similarity)
                    results.append(memory)
        
        return results
    
    def _keyword_search(self, query: MemoryQuery) -> List[MemoryVector]:
        """Perform keyword search using inverted index"""
        results = []
        query_words = query.query.lower().split()
        
        # Find memories containing query words
        matching_ids = set()
        for word in query_words:
            if len(word) > 2 and word in self.inverted_index:
                matching_ids.update(self.inverted_index[word])
        
        # Get full memories
        for memory_id in matching_ids:
            memory = self._get_memory_by_id(memory_id)
            if memory:
                results.append(memory)
        
        return results
    
    def _get_memory_by_id(self, memory_id: str) -> Optional[MemoryVector]:
        """Get memory by ID from any layer"""
        # Check cache first
        if memory_id in self.cache:
            return self.cache[memory_id]
        
        # Check all memory layers
        for memory_layer in [self.episodic_memory, self.long_term_memory, self.short_term_memory]:
            if memory_id in memory_layer:
                return memory_layer[memory_id]
        
        return None
    
    def _matches_filters(self, memory: MemoryVector, filters: Dict[str, Any]) -> bool:
        """Check if memory matches filters"""
        for key, value in filters.items():
            if key == "tags":
                if not any(tag in memory.tags for tag in value):
                    return False
            elif key == "importance_min":
                if memory.importance < value:
                    return False
            elif key == "date_after":
                if memory.timestamp < value:
                    return False
            elif hasattr(memory, key):
                if getattr(memory, key) != value:
                    return False
        
        return True
    
    def _update_access_stats(self, memory_id: str):
        """Update memory access statistics"""
        try:
            memory = self._get_memory_by_id(memory_id)
            if memory:
                memory.access_count += 1
                memory.last_accessed = datetime.now().isoformat()
                
                # Update in database
                conn = sqlite3.connect(self.vector_db_path)
                conn.execute('''
                    UPDATE vectors SET access_count = ?, last_accessed = ? WHERE id = ?
                ''', (memory.access_count, memory.last_accessed, memory_id))
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to update access stats: {e}")
    
    def _update_cache(self, memory_id: str, memory: MemoryVector):
        """Update LRU cache"""
        if memory_id in self.cache:
            self.access_history.remove(memory_id)
        elif len(self.cache) >= self.cache_size:
            # Remove oldest entry
            oldest_id = self.access_history.pop(0)
            del self.cache[oldest_id]
        
        self.cache[memory_id] = memory
        self.access_history.append(memory_id)
    
    def _consolidate_memories(self):
        """Consolidate and optimize memory storage"""
        try:
            # Move old episodic memories to long-term if important
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for memory_id, memory in list(self.episodic_memory.items()):
                memory_date = datetime.fromisoformat(memory.timestamp)
                
                if memory_date < cutoff_date and memory.importance > 0.7:
                    # Move to long-term memory
                    del self.episodic_memory[memory_id]
                    memory.memory_type = "semantic"
                    self.long_term_memory[memory_id] = memory
                    self._persist_memory(memory)
            
            logger.info("Memory consolidation completed")
            
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            "total_memories": len(self.vector_index),
            "episodic_count": len(self.episodic_memory),
            "long_term_count": len(self.long_term_memory),
            "short_term_count": len(self.short_term_memory),
            "cache_size": len(self.cache),
            "index_size": len(self.inverted_index),
            "memory_types": {
                "episodic": len(self.episodic_memory),
                "semantic": len(self.long_term_memory),
                "procedural": len(self.short_term_memory)
            }
        }
    
    def export_memories(self, output_file: str, memory_type: Optional[str] = None):
        """Export memories to file"""
        try:
            memories = []
            
            if memory_type == "episodic":
                memories = list(self.episodic_memory.values())
            elif memory_type == "semantic":
                memories = list(self.long_term_memory.values())
            elif memory_type == "procedural":
                memories = list(self.short_term_memory.values())
            else:
                # All memories
                memories = (list(self.episodic_memory.values()) + 
                          list(self.long_term_memory.values()) + 
                          list(self.short_term_memory.values()))
            
            # Export as JSON
            export_data = [asdict(memory) for memory in memories]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(memories)} memories to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export memories: {e}")
    
    def clear_memory(self, memory_type: Optional[str] = None, older_than_days: Optional[int] = None):
        """Clear memories with optional filters"""
        try:
            if memory_type:
                if memory_type == "episodic":
                    self.episodic_memory.clear()
                elif memory_type == "semantic":
                    self.long_term_memory.clear()
                elif memory_type == "procedural":
                    self.short_term_memory.clear()
            else:
                # Clear all
                self.episodic_memory.clear()
                self.long_term_memory.clear()
                self.short_term_memory.clear()
            
            # Rebuild indexes
            self.vector_index.clear()
            self.inverted_index.clear()
            self.cache.clear()
            self.access_history.clear()
            
            # Reload from database if needed
            if not memory_type:
                self._load_memories()
            
            logger.info(f"Cleared {memory_type or 'all'} memories")
            
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")

# Global vector memory instance
_vector_memory_instance = None

def get_vector_memory() -> VectorMemory:
    """Get global vector memory instance"""
    global _vector_memory_instance
    if _vector_memory_instance is None:
        _vector_memory_instance = VectorMemory()
    return _vector_memory_instance