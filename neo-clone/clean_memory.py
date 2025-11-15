#!/usr/bin/env python3
"""
Memory System Cleanup Script for Neo-Clone

This script cleans up the memory system by:
1. Removing test conversations
2. Cleaning up orphaned sessions
3. Resetting statistics
4. Creating backups before cleanup
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryCleaner:
    def __init__(self, memory_dir: str = "data/memory"):
        self.memory_dir = Path(memory_dir)
        self.backup_dir = self.memory_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self) -> str:
        """Create a backup of all memory files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"memory_backup_{timestamp}"

        backup_path = self.backup_dir / backup_name
        backup_path.mkdir()

        # Backup all memory files
        memory_files = [
            "conversations.json",
            "sessions.json",
            "preferences.json",
            "usage_stats.json",
            "statistics.json"
        ]

        for filename in memory_files:
            src = self.memory_dir / filename
            if src.exists():
                dst = backup_path / filename
                shutil.copy2(src, dst)
                logger.info(f"Backed up {filename}")

        logger.info(f"Created backup: {backup_name}")
        return backup_name

    def clean_conversations(self) -> int:
        """Remove test conversations and return count of removed entries"""
        conversations_file = self.memory_dir / "conversations.json"

        if not conversations_file.exists():
            return 0

        with open(conversations_file, 'r', encoding='utf-8') as f:
            conversations = json.load(f)

        original_count = len(conversations)

        # Define test message patterns to remove
        test_patterns = [
            "Hello, this is a test message for Neo-Clone integration.",
            "I have completed the reasoning process with 0.00 confidence."
        ]

        # Filter out test conversations
        cleaned_conversations = []
        for conv in conversations:
            user_msg = conv.get('user_message', '')
            assistant_msg = conv.get('assistant_response', '')

            is_test = False
            for pattern in test_patterns:
                if pattern in user_msg or pattern in assistant_msg:
                    is_test = True
                    break

            if not is_test:
                cleaned_conversations.append(conv)

        removed_count = original_count - len(cleaned_conversations)

        # Save cleaned conversations
        with open(conversations_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_conversations, f, indent=2, ensure_ascii=False)

        logger.info(f"Removed {removed_count} test conversations")
        return removed_count

    def clean_sessions(self) -> int:
        """Remove orphaned sessions and return count of removed sessions"""
        sessions_file = self.memory_dir / "sessions.json"
        conversations_file = self.memory_dir / "conversations.json"

        if not sessions_file.exists():
            return 0

        with open(sessions_file, 'r', encoding='utf-8') as f:
            sessions = json.load(f)

        # Get active session IDs from conversations
        active_session_ids = set()
        if conversations_file.exists():
            with open(conversations_file, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
                for conv in conversations:
                    active_session_ids.add(conv.get('session_id'))

        original_count = len(sessions)

        # Filter out orphaned sessions
        cleaned_sessions = {}
        for session_id, session_data in sessions.items():
            if session_id in active_session_ids:
                cleaned_sessions[session_id] = session_data

        removed_count = original_count - len(cleaned_sessions)

        # Save cleaned sessions
        with open(sessions_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_sessions, f, indent=2, ensure_ascii=False)

        logger.info(f"Removed {removed_count} orphaned sessions")
        return removed_count

    def reset_statistics(self):
        """Reset usage statistics to clean state"""
        stats_file = self.memory_dir / "usage_stats.json"

        clean_stats = {
            "total_conversations": 0,
            "total_skill_usage": {},
            "average_session_length": 0,
            "most_used_skills": [],
            "daily_usage": {}
        }

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(clean_stats, f, indent=2, ensure_ascii=False)

        logger.info("Reset usage statistics")

    def get_cleanup_summary(self) -> dict:
        """Get summary of current memory state"""
        conversations_file = self.memory_dir / "conversations.json"
        sessions_file = self.memory_dir / "sessions.json"

        conversations_count = 0
        sessions_count = 0

        if conversations_file.exists():
            with open(conversations_file, 'r', encoding='utf-8') as f:
                conversations_count = len(json.load(f))

        if sessions_file.exists():
            with open(sessions_file, 'r', encoding='utf-8') as f:
                sessions_count = len(json.load(f))

        return {
            "conversations": conversations_count,
            "sessions": sessions_count,
            "backup_dir": str(self.backup_dir)
        }

    def cleanup_all(self) -> dict:
        """Perform complete memory cleanup"""
        logger.info("Starting memory system cleanup...")

        # Create backup first
        backup_name = self.create_backup()

        # Perform cleanup
        removed_conversations = self.clean_conversations()
        removed_sessions = self.clean_sessions()
        self.reset_statistics()

        # Get final summary
        final_summary = self.get_cleanup_summary()

        result = {
            "backup_created": backup_name,
            "conversations_removed": removed_conversations,
            "sessions_removed": removed_sessions,
            "final_state": final_summary
        }

        logger.info("Memory cleanup completed successfully")
        logger.info(f"Results: {result}")

        return result

def main():
    """Main cleanup function"""
    print("Neo-Clone Memory System Cleanup")
    print("=" * 50)

    cleaner = MemoryCleaner()

    # Show initial state
    initial_summary = cleaner.get_cleanup_summary()
    print("Initial Memory State:")
    print(f"  - Conversations: {initial_summary['conversations']}")
    print(f"  - Sessions: {initial_summary['sessions']}")
    print()

    # Perform cleanup
    result = cleaner.cleanup_all()

    # Show results
    print("\nCleanup Results:")
    print(f"  - Backup created: {result['backup_created']}")
    print(f"  - Conversations removed: {result['conversations_removed']}")
    print(f"  - Sessions removed: {result['sessions_removed']}")
    print()

    print("Final Memory State:")
    print(f"  - Conversations: {result['final_state']['conversations']}")
    print(f"  - Sessions: {result['final_state']['sessions']}")
    print()

    print("Memory cleanup completed successfully!")
    print(f"Backup location: {result['final_state']['backup_dir']}")

if __name__ == "__main__":
    main()