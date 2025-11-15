"""
memory.py - Persistent Memory System for Neo-Clone

Implements:
- JSON-based conversation history storage
- User preferences and session data
- Skill usage statistics
- Cross-session continuity
- Automatic backup and recovery
"""

import json
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
import threading
from datetime import timedelta
from dataclasses import dataclass, fields, asdict
from typing import Optional, Dict, Any, List

logger = logging.getLogger("neo.memory")

@dataclass
class MemoryEntry:
    timestamp: str
    session_id: str
    user_message: str
    assistant_response: str
    intent: Optional[str] = None
    skill_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class UserPreferences:
    theme: str = "light"  # light, dark, auto
    max_history: int = 50
    auto_save: bool = True
    log_level: str = "INFO"
    preferred_model: Optional[str] = None
    custom_commands: Dict[str, str] = None

    def __post_init__(self):
        if self.custom_commands is None:
            self.custom_commands = {}

class PersistentMemory:
    def __init__(self, memory_dir: str = "data/memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.conversations_file = self.memory_dir / "conversations.json"
        self.preferences_file = self.memory_dir / "preferences.json"
        self.stats_file = self.memory_dir / "usage_stats.json"
        self.backup_dir = self.memory_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self._lock = threading.Lock()
        self.session_id = self._generate_session_id()
        
        self._load_preferences()
        self._load_stats()
        
        # Auto-save on exit
        import atexit
        atexit.register(self.save_all)

    def _generate_session_id(self) -> str:
        """Generate unique session ID for tracking"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _load_preferences(self):
        """Load user preferences from JSON file"""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.preferences = UserPreferences(**data)
            else:
                self.preferences = UserPreferences()
                self.save_preferences()
        except Exception as e:
            logger.warning(f"Failed to load preferences: {e}")
            self.preferences = UserPreferences()

    def _load_stats(self):
        """Load usage statistics"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            else:
                self.stats = {
                    "total_conversations": 0,
                    "total_skill_usage": {},
                    "average_session_length": 0,
                    "most_used_skills": [],
                    "daily_usage": {}
                }
                self.save_stats()
        except Exception as e:
            logger.warning(f"Failed to load stats: {e}")
            self.stats = {
                "total_conversations": 0,
                "total_skill_usage": {},
                "average_session_length": 0,
                "most_used_skills": [],
                "daily_usage": {}
            }

    def _load_conversations(self) -> List[MemoryEntry]:
        """Load conversation history from JSON"""
        try:
            if self.conversations_file.exists():
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entries = []
                    for entry in data:
                        try:
                            # Handle field name mapping for backward compatibility
                            field_mapping = {
                                'user_input': 'user_message',  # Old field name -> new field name
                            }

                            # Apply field mapping
                            normalized_entry = {}
                            for k, v in entry.items():
                                # Skip the 'id' field which doesn't exist in MemoryEntry
                                if k == 'id':
                                    continue
                                # Map old field names to new ones
                                mapped_key = field_mapping.get(k, k)
                                normalized_entry[mapped_key] = v

                            # Filter out unknown fields to handle schema changes gracefully
                            valid_fields = {field.name for field in fields(MemoryEntry)}
                            filtered_entry = {k: v for k, v in normalized_entry.items() if k in valid_fields}

                            # Ensure required fields are present
                            required_fields = ['timestamp', 'session_id', 'user_message', 'assistant_response']
                            if not all(field in filtered_entry for field in required_fields):
                                logger.warning(f"Skipping entry missing required fields: {list(filtered_entry.keys())}")
                                continue

                            entries.append(MemoryEntry(**filtered_entry))
                        except Exception as e:
                            logger.warning(f"Skipping invalid memory entry: {e}")
                            continue
                    return entries
            return []
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
            # Return empty list on any error to prevent crashes
            return []

    def _save_conversations(self, entries: List[MemoryEntry]):
        """Save conversation history to JSON"""
        try:
            data = []
            for entry in entries:
                try:
                    data.append(asdict(entry))
                except Exception as e:
                    logger.warning(f"Skipping invalid memory entry during save: {e}")
                    continue
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")

    def save_preferences(self):
        """Save user preferences to JSON"""
        with self._lock:
            try:
                with open(self.preferences_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.preferences), f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save preferences: {e}")

    def save_stats(self):
        """Save usage statistics to JSON"""
        with self._lock:
            try:
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(self.stats, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save stats: {e}")

    def add_conversation(self, user_message: str, assistant_response: str, 
                        intent: Optional[str] = None, skill_used: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None):
        """Add a conversation entry with automatic backup"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            intent=intent,
            skill_used=skill_used,
            metadata=metadata
        )
        
        with self._lock:
            # Load current conversations
            conversations = self._load_conversations()
            
            # Add new entry
            conversations.append(entry)
            
            # Keep only max_history entries
            if len(conversations) > self.preferences.max_history:
                conversations = conversations[-self.preferences.max_history:]
            
            # Save updated conversations
            self._save_conversations(conversations)
            
            # Update statistics
            self._update_stats(entry)

    def _update_stats(self, entry: MemoryEntry):
        """Update usage statistics"""
        try:
            self.stats["total_conversations"] += 1
            
            # Track skill usage
            if entry.skill_used:
                if entry.skill_used not in self.stats["total_skill_usage"]:
                    self.stats["total_skill_usage"][entry.skill_used] = 0
                self.stats["total_skill_usage"][entry.skill_used] += 1
            
            # Track daily usage
            date_key = entry.timestamp.split('T')[0]  # YYYY-MM-DD
            if date_key not in self.stats["daily_usage"]:
                self.stats["daily_usage"][date_key] = 0
            self.stats["daily_usage"][date_key] += 1
            
            # Update most used skills
            self._update_most_used_skills()
            
            self.save_stats()
        except Exception as e:
            logger.warning(f"Failed to update stats: {e}")

    def _update_most_used_skills(self):
        """Update most used skills ranking"""
        try:
            skill_usage = self.stats["total_skill_usage"]
            sorted_skills = sorted(skill_usage.items(), key=lambda x: x[1], reverse=True)
            self.stats["most_used_skills"] = [skill for skill, count in sorted_skills[:5]]
        except Exception as e:
            logger.warning(f"Failed to update most used skills: {e}")

    def search_conversations(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search through conversation history"""
        conversations = self._load_conversations()
        query_lower = query.lower()
        
        # Simple substring matching
        results = []
        for entry in reversed(conversations):  # Most recent first
            if (query_lower in entry.user_message.lower() or 
                query_lower in entry.assistant_response.lower()):
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results

    def get_recent_conversations(self, count: int = 10) -> List[MemoryEntry]:
        """Get most recent conversations"""
        conversations = self._load_conversations()
        return conversations[-count:]

    def clear_conversations(self, older_than_days: Optional[int] = None):
        """Clear conversation history, optionally keeping recent ones"""
        conversations = self._load_conversations()
        
        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            filtered_conversations = [
                entry for entry in conversations 
                if datetime.fromisoformat(entry.timestamp) > cutoff_date
            ]
        else:
            filtered_conversations = []
        
        self._save_conversations(filtered_conversations)

    def export_conversations(self, output_file: str, format_type: str = "json"):
        """Export conversations to file"""
        conversations = self._load_conversations()
        
        if format_type.lower() == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(entry) for entry in conversations], f, indent=2)
        elif format_type.lower() == "txt":
            with open(output_file, 'w', encoding='utf-8') as f:
                for entry in conversations:
                    f.write(f"[{entry.timestamp}] Session: {entry.session_id}\n")
                    f.write(f"User: {entry.user_message}\n")
                    f.write(f"Assistant: {entry.assistant_response}\n")
                    if entry.skill_used:
                        f.write(f"Skill: {entry.skill_used}\n")
                    f.write("-" * 50 + "\n")

    def create_backup(self) -> str:
        """Create a timestamped backup of all data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # Copy all data files
            for file in [self.conversations_file, self.preferences_file, self.stats_file]:
                if file.exists():
                    shutil.copy2(file, backup_path / file.name)
            
            logger.info(f"Created backup: {backup_name}")
            return backup_name
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return ""

    def restore_from_backup(self, backup_name: str) -> bool:
        """Restore data from a backup"""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_name}")
            return False
        
        try:
            # Restore all data files
            for file in [self.conversations_file, self.preferences_file, self.stats_file]:
                backup_file = backup_path / file.name
                if backup_file.exists():
                    shutil.copy2(backup_file, file)
            
            # Reload data
            self._load_preferences()
            self._load_stats()
            
            logger.info(f"Restored from backup: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_conversations": self.stats["total_conversations"],
            "skill_usage": self.stats["total_skill_usage"],
            "most_used_skills": self.stats["most_used_skills"],
            "daily_usage": dict(list(self.stats["daily_usage"].items())[-30:]),  # Last 30 days
            "session_id": self.session_id,
            "memory_dir": str(self.memory_dir),
            "preferences": asdict(self.preferences)
        }

    def save_all(self):
        """Save all data to disk"""
        self.save_preferences()
        self.save_stats()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save_all()

# Global instance
_memory_instance = None

def get_memory() -> PersistentMemory:
    """Get global memory instance (singleton pattern)"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = PersistentMemory()
    return _memory_instance