#!/usr/bin/env python3
"""
Directory cleanup script for Neo-Clone
Removes unnecessary files and directories to keep the workspace clean
"""

import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_directory():
    """Clean up unnecessary files and directories"""

    # Files and directories to remove
    to_remove = [
        "__pycache__",  # Python bytecode cache
        "backups",      # Backup files
        "*.pyc",        # Individual pyc files
        "*.pyo",        # Optimized bytecode
        ".DS_Store",    # macOS system files
        "Thumbs.db",    # Windows system files
    ]

    removed_count = 0

    # Remove directories
    for item in to_remove:
        if item.endswith("/"):
            # Directory
            if os.path.exists(item):
                try:
                    shutil.rmtree(item)
                    logger.info(f"Removed directory: {item}")
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove directory {item}: {e}")
        else:
            # Files with pattern
            if "*" in item:
                # Simple glob - remove files matching pattern in current directory
                for filename in os.listdir("."):
                    if filename.endswith(item.replace("*", "")):
                        try:
                            os.remove(filename)
                            logger.info(f"Removed file: {filename}")
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove file {filename}: {e}")
            else:
                # Single file
                if os.path.exists(item):
                    try:
                        if os.path.isdir(item):
                            shutil.rmtree(item)
                        else:
                            os.remove(item)
                        logger.info(f"Removed: {item}")
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove {item}: {e}")

    # Remove __pycache__ directories recursively
    for root, dirs, files in os.walk(".", topdown=False):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                pycache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(pycache_path)
                    logger.info(f"Removed __pycache__: {pycache_path}")
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove __pycache__ {pycache_path}: {e}")

    logger.info(f"Directory cleanup completed. Removed {removed_count} items.")

if __name__ == "__main__":
    # Change to neo-clone directory if not already there
    if not os.path.exists("main.py"):
        os.chdir("neo-clone")

    clean_directory()