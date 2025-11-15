"""
Persistent Memory System for MiniMax Agent Architecture

This module provides JSON-based persistent conversation storage with
session management, search capabilities, and export features.

Author: MiniMax Agent
Version: 1.0
"""

import json
import uuid
import shutil
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict
import logging

# Import data models
from data_models import MemoryType, MemoryEntry, MessageRole

# Configure logging
logger = logging.getLogger(__name__)


class PersistentMemory:
    """
    Persistent memory system with JSON storage
    
    Features:
    - Conversation history storage
    - Session management
    - User preferences
    - Search and retrieval
    - Export capabilities
    - Automatic backups
    - Statistics tracking
    - Thread-safe operations
    """
    
    def __init__(
        self,
        memory_dir: str = "data/memory",
        max_history: int = 1000,
        auto_save: bool = True,
        backup_enabled: bool = True,
        max_backups: int = 10
    ):
        """
        Initialize persistent memory
        
        Args:
            memory_dir: Directory for memory storage
            max_history: Maximum conversation entries
            auto_save: Auto-save after each operation
            backup_enabled: Enable automatic backups
            max_backups: Maximum number of backup files to keep
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_history = max_history
        self.auto_save = auto_save
        self.backup_enabled = backup_enabled
        self.max_backups = max_backups
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Current session
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Storage files
        self.conversations_file = self.memory_dir / "conversations.json"
        self.preferences_file = self.memory_dir / "preferences.json"
        self.stats_file = self.memory_dir / "statistics.json"
        self.sessions_file = self.memory_dir / "sessions.json"
        
        # Create subdirectories
        self.backup_dir = self.memory_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self.exports_dir = self.memory_dir / "exports"
        self.exports_dir.mkdir(exist_ok=True)
        
        # Load existing data
        self.conversations: List[Dict[str, Any]] = self._load_conversations()
        self.preferences: Dict[str, Any] = self._load_preferences()
        self.statistics: Dict[str, Any] = self._load_statistics()
        self.sessions: Dict[str, Dict[str, Any]] = self._load_sessions()
        
        # Initialize session
        self._create_session()
        
        logger.info(f"Initialized persistent memory: session={self.session_id}")
        logger.info(f"Memory directory: {self.memory_dir}")
        logger.info(f"Loaded {len(self.conversations)} conversations")
    
    def _create_session(self) -> None:
        """Create a new session entry"""
        with self._lock:
            session_data = {
                "session_id": self.session_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "conversation_count": 0,
                "metadata": {}
            }
            self.sessions[self.session_id] = session_data
    
    def add_conversation(
        self,
        user_input: str,
        assistant_response: str,
        intent: Optional[str] = None,
        skill_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add conversation entry
        
        Args:
            user_input: User's input
            assistant_response: Assistant's response
            intent: Detected intent
            skill_used: Skill that handled the request
            metadata: Additional metadata
        
        Returns:
            Entry ID
        """
        with self._lock:
            entry_id = uuid.uuid4().hex
            
            entry = {
                "id": entry_id,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "assistant_response": assistant_response,
                "intent": intent,
                "skill_used": skill_used,
                "metadata": metadata or {}
            }
            
            self.conversations.append(entry)
            
            # Update session statistics
            self.sessions[self.session_id]["last_activity"] = datetime.now().isoformat()
            self.sessions[self.session_id]["conversation_count"] += 1
            
            # Trim if exceeds max
            if len(self.conversations) > self.max_history:
                # Remove oldest entries but keep session boundaries
                removed_count = len(self.conversations) - self.max_history
                self.conversations = self.conversations[-self.max_history:]
                logger.debug(f"Trimmed {removed_count} oldest conversations")
            
            # Update statistics
            self._update_statistics(entry)
            
            # Auto-save
            if self.auto_save:
                self.save()
            
            logger.debug(f"Added conversation: {entry_id}")
            return entry_id
    
    def get_recent_conversations(
        self,
        limit: int = 10,
        session_id: Optional[str] = None,
        intent_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversations with optional filtering
        
        Args:
            limit: Maximum number of entries
            session_id: Filter by session ID (None for all)
            intent_filter: Filter by intent type
        
        Returns:
            List of conversation entries
        """
        with self._lock:
            conversations = self.conversations.copy()
            
            # Filter by session if specified
            if session_id:
                conversations = [c for c in conversations if c["session_id"] == session_id]
            
            # Filter by intent if specified
            if intent_filter:
                conversations = [c for c in conversations if c.get("intent") == intent_filter]
            
            # Return most recent
            return conversations[-limit:] if limit > 0 else conversations
    
    def search_conversations(
        self,
        query: str,
        limit: int = 10,
        search_in: str = "all",  # "all", "user", "assistant"
        case_sensitive: bool = False,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search conversations by keyword with advanced options
        
        Args:
            query: Search query
            limit: Maximum results
            search_in: Where to search ("all", "user", "assistant")
            case_sensitive: Whether search is case sensitive
            date_range: Optional date range filter (start, end)
        
        Returns:
            Matching conversation entries
        """
        with self._lock:
            query_text = query if case_sensitive else query.lower()
            results = []
            
            for conv in reversed(self.conversations):  # Start from most recent
                match = False
                
                # Text search
                if search_in in ["all", "user"]:
                    user_text = conv["user_input"] if case_sensitive else conv["user_input"].lower()
                    if query_text in user_text:
                        match = True
                
                if search_in in ["all", "assistant"]:
                    assistant_text = conv["assistant_response"] if case_sensitive else conv["assistant_response"].lower()
                    if query_text in assistant_text:
                        match = True
                
                # Date range filter
                if match and date_range:
                    conv_time = datetime.fromisoformat(conv["timestamp"])
                    if not (date_range[0] <= conv_time <= date_range[1]):
                        match = False
                
                if match:
                    results.append(conv)
                    if len(results) >= limit:
                        break
            
            return results
    
    def get_session_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a specific session"""
        with self._lock:
            return [c for c in self.conversations if c["session_id"] == session_id]
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        with self._lock:
            return self.sessions.get(session_id)
    
    def list_sessions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all sessions"""
        with self._lock:
            sessions_list = [
                {
                    **session_data,
                    "conversation_count": len([c for c in self.conversations if c["session_id"] == session_id])
                }
                for session_id, session_data in self.sessions.items()
            ]
            
            # Sort by last activity (most recent first)
            sessions_list.sort(key=lambda x: x["last_activity"], reverse=True)
            
            if limit:
                return sessions_list[:limit]
            return sessions_list
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its conversations"""
        with self._lock:
            if session_id not in self.sessions:
                return False
            
            # Remove conversations for this session
            self.conversations = [c for c in self.conversations if c["session_id"] != session_id]
            
            # Remove session
            del self.sessions[session_id]
            
            if self.auto_save:
                self.save()
            
            logger.info(f"Deleted session: {session_id}")
            return True
    
    def export_conversations(
        self,
        output_file: str,
        format: str = "json",  # "json" or "markdown"
        session_id: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> None:
        """
        Export conversations to file with filtering options
        
        Args:
            output_file: Output file path
            format: Export format ("json" or "markdown")
            session_id: Optional session filter
            date_range: Optional date range filter
        """
        with self._lock:
            # Get conversations to export
            conversations = self.conversations.copy()
            
            # Apply filters
            if session_id:
                conversations = [c for c in conversations if c["session_id"] == session_id]
            
            if date_range:
                conversations = [
                    c for c in conversations
                    if date_range[0] <= datetime.fromisoformat(c["timestamp"]) <= date_range[1]
                ]
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                export_data = {
                    "export_info": {
                        "timestamp": datetime.now().isoformat(),
                        "total_conversations": len(conversations),
                        "session_filter": session_id,
                        "date_range": [d.isoformat() for d in date_range] if date_range else None
                    },
                    "conversations": conversations
                }
                
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif format == "markdown":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("# Conversation History Export\n\n")
                    f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"**Total Conversations:** {len(conversations)}\n\n")
                    
                    if session_id:
                        f.write(f"**Session Filter:** {session_id}\n\n")
                    
                    if date_range:
                        f.write(f"**Date Range:** {date_range[0].date()} to {date_range[1].date()}\n\n")
                    
                    f.write("---\n\n")
                    
                    for conv in conversations:
                        timestamp = datetime.fromisoformat(conv["timestamp"])
                        f.write(f"## {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(f"**Session:** {conv['session_id']}\n\n")
                        f.write(f"**User:** {conv['user_input']}\n\n")
                        f.write(f"**Assistant:** {conv['assistant_response']}\n\n")
                        
                        if conv.get('intent'):
                            f.write(f"*Intent:* {conv['intent']}\n\n")
                        if conv.get('skill_used'):
                            f.write(f"*Skill:* {conv['skill_used']}\n\n")
                        
                        f.write("---\n\n")
            
            logger.info(f"Exported {len(conversations)} conversations to {output_path}")
    
    def import_conversations(
        self,
        input_file: str,
        merge: bool = True
    ) -> int:
        """
        Import conversations from file
        
        Args:
            input_file: Input file path
            merge: Whether to merge with existing conversations
        
        Returns:
            Number of imported conversations
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Import file not found: {input_file}")
        
        with self._lock:
            try:
                with open(input_path, 'r') as f:
                    data = json.load(f)
                
                # Handle both formats (direct list or wrapped with export_info)
                if "conversations" in data:
                    imported_conversations = data["conversations"]
                else:
                    imported_conversations = data
                
                if not merge:
                    # Clear existing conversations
                    self.conversations = []
                
                # Add imported conversations with new IDs to avoid conflicts
                imported_count = 0
                for conv in imported_conversations:
                    # Create new ID and session if needed
                    new_conv = conv.copy()
                    new_conv["id"] = uuid.uuid4().hex
                    new_conv["imported_at"] = datetime.now().isoformat()
                    new_conv["original_id"] = conv.get("id")
                    
                    self.conversations.append(new_conv)
                    imported_count += 1
                
                # Trim if exceeds max
                if len(self.conversations) > self.max_history:
                    self.conversations = self.conversations[-self.max_history:]
                
                if self.auto_save:
                    self.save()
                
                logger.info(f"Imported {imported_count} conversations from {input_path}")
                return imported_count
                
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to import conversations: {e}")
                raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        with self._lock:
            now = datetime.now()
            
            # Calculate session statistics
            session_stats = {}
            for session_id, session_data in self.sessions.items():
                session_conversations = [c for c in self.conversations if c["session_id"] == session_id]
                session_stats[session_id] = {
                    "conversation_count": len(session_conversations),
                    "created_at": session_data["created_at"],
                    "last_activity": session_data["last_activity"],
                    "age_hours": (now - datetime.fromisoformat(session_data["created_at"])).total_seconds() / 3600
                }
            
            # Recent activity (last 24 hours)
            recent_cutoff = now - timedelta(hours=24)
            recent_conversations = [
                c for c in self.conversations
                if datetime.fromisoformat(c["timestamp"]) >= recent_cutoff
            ]
            
            return {
                "total_conversations": len(self.conversations),
                "current_session": self.session_id,
                "session_count": len(self.sessions),
                "memory_dir": str(self.memory_dir),
                "max_history": self.max_history,
                "recent_conversations_24h": len(recent_conversations),
                "session_statistics": session_stats,
                **self.statistics,
                "last_updated": now.isoformat()
            }
    
    def save(self) -> None:
        """Save all data to disk with error handling"""
        try:
            with self._lock:
                # Save conversations
                with open(self.conversations_file, 'w', encoding='utf-8') as f:
                    json.dump(self.conversations, f, indent=2, ensure_ascii=False)
                
                # Save preferences
                with open(self.preferences_file, 'w', encoding='utf-8') as f:
                    json.dump(self.preferences, f, indent=2, ensure_ascii=False)
                
                # Save statistics
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(self.statistics, f, indent=2, ensure_ascii=False)
                
                # Save sessions
                with open(self.sessions_file, 'w', encoding='utf-8') as f:
                    json.dump(self.sessions, f, indent=2, ensure_ascii=False)
                
                # Create backup
                if self.backup_enabled:
                    self._create_backup()
                
                logger.debug("Saved persistent memory")
                
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            raise
    
    def _load_conversations(self) -> List[Dict[str, Any]]:
        """Load conversations from disk with error handling"""
        if self.conversations_file.exists():
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load conversations: {e}")
        return []
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load preferences from disk"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load preferences: {e}")
        return {
            "theme": "dark",
            "max_history": 1000,
            "auto_save": True,
            "backup_enabled": True
        }
    
    def _load_statistics(self) -> Dict[str, Any]:
        """Load statistics from disk"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load statistics: {e}")
        return {}
    
    def _load_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Load sessions from disk"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load sessions: {e}")
        return {}
    
    def _update_statistics(self, entry: Dict[str, Any]) -> None:
        """Update statistics with new entry"""
        with self._lock:
            if "intent_distribution" not in self.statistics:
                self.statistics["intent_distribution"] = {}
            
            if "skill_usage" not in self.statistics:
                self.statistics["skill_usage"] = {}
            
            if "daily_stats" not in self.statistics:
                self.statistics["daily_stats"] = {}
            
            # Update intent distribution
            intent = entry.get("intent", "unknown")
            self.statistics["intent_distribution"][intent] = \
                self.statistics["intent_distribution"].get(intent, 0) + 1
            
            # Update skill usage
            skill = entry.get("skill_used", "unknown")
            self.statistics["skill_usage"][skill] = \
                self.statistics["skill_usage"].get(skill, 0) + 1
            
            # Update daily stats
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.statistics["daily_stats"]:
                self.statistics["daily_stats"][today] = {
                    "conversations": 0,
                    "intents": {},
                    "skills": {}
                }
            
            self.statistics["daily_stats"][today]["conversations"] += 1
            
            # Add intent and skill to daily stats
            if intent in self.statistics["daily_stats"][today]["intents"]:
                self.statistics["daily_stats"][today]["intents"][intent] += 1
            else:
                self.statistics["daily_stats"][today]["intents"][intent] = 1
            
            if skill in self.statistics["daily_stats"][today]["skills"]:
                self.statistics["daily_stats"][today]["skills"][skill] += 1
            else:
                self.statistics["daily_stats"][today]["skills"][skill] = 1
    
    def _create_backup(self) -> None:
        """Create backup of current data"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"conversations_{timestamp}.json"
            
            # Keep only the specified number of backups
            backups = sorted(self.backup_dir.glob("conversations_*.json"))
            if len(backups) >= self.max_backups:
                for old_backup in backups[:-self.max_backups + 1]:
                    old_backup.unlink()
            
            # Create new backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Created backup: {backup_file}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def maintenance(self) -> Dict[str, Any]:
        """Perform maintenance operations"""
        with self._lock:
            results = {
                "backup_files_cleaned": 0,
                "expired_conversations_removed": 0,
                "total_backups": 0,
                "disk_usage_mb": 0
            }
            
            # Clean old backups
            if self.backup_enabled:
                backups = sorted(self.backup_dir.glob("conversations_*.json"))
                results["total_backups"] = len(backups)
                
                if len(backups) > self.max_backups:
                    for old_backup in backups[:-self.max_backups]:
                        try:
                            old_backup.unlink()
                            results["backup_files_cleaned"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove backup {old_backup}: {e}")
            
            # Calculate disk usage
            total_size = 0
            for file_path in self.memory_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except OSError:
                        pass
            results["disk_usage_mb"] = total_size / (1024 * 1024)
            
            logger.info(f"Maintenance completed: {results}")
            return results


# Singleton instance management
_memory_instance: Optional[PersistentMemory] = None
_memory_lock = threading.Lock()


def get_memory(
    memory_dir: str = "data/memory",
    max_history: int = 1000,
    auto_save: bool = True
) -> PersistentMemory:
    """
    Get singleton memory instance (thread-safe)
    
    Args:
        memory_dir: Memory storage directory
        max_history: Maximum conversation history
        auto_save: Auto-save after each operation
    
    Returns:
        PersistentMemory singleton instance
    """
    global _memory_instance
    
    if _memory_instance is None:
        with _memory_lock:
            if _memory_instance is None:  # Double-check locking
                _memory_instance = PersistentMemory(memory_dir, max_history, auto_save)
    
    return _memory_instance


def reset_memory() -> None:
    """Reset the memory instance (for testing)"""
    global _memory_instance
    with _memory_lock:
        if _memory_instance:
            try:
                _memory_instance.save()  # Save before reset
            except Exception:
                pass
        _memory_instance = None
    logger.info("Memory instance reset")


def create_memory_instance(
    memory_dir: str = "data/memory",
    max_history: int = 1000,
    auto_save: bool = True,
    backup_enabled: bool = True
) -> PersistentMemory:
    """
    Create a new memory instance (bypasses singleton)
    
    Args:
        memory_dir: Memory storage directory
        max_history: Maximum conversation history
        auto_save: Auto-save after each operation
        backup_enabled: Enable automatic backups
    
    Returns:
        New PersistentMemory instance
    """
    return PersistentMemory(memory_dir, max_history, auto_save, backup_enabled)