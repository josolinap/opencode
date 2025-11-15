#!/usr/bin/env python3
"""
Final cleanup of Neo-Clone directory
Removes experimental, alternative implementation, and documentation files that are not part of core functionality
"""

import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_remove_file(filepath: str) -> bool:
    """Safely remove a file if it exists"""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"Removed file: {filepath}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove file {filepath}: {e}")
            return False
    return False

def safe_remove_dir(dirpath: str) -> bool:
    """Safely remove a directory if it exists"""
    if os.path.exists(dirpath):
        try:
            shutil.rmtree(dirpath)
            logger.info(f"Removed directory: {dirpath}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove directory {dirpath}: {e}")
            return False
    return False

def final_cleanup():
    """Final cleanup of non-essential files"""

    # Experimental/advanced files not used by core system
    experimental_files = [
        "quantum_optimization.py",
        "pocketflow.py",
        "self_improvement_analysis.py",
        "evolution_monitor.py",
        "evolution_status.jsonl",
        "upgrade_implementations.py"
    ]

    # Alternative implementations not used by main system
    alternative_files = [
        "skills_fixed.py",
        "skills_clean.py"
    ]

    # Demo/example data files
    demo_files = [
        "ml_project_workflow.json",
        "security_knowledge.db"
    ]

    # Documentation directories (setup guides and integration docs)
    doc_dirs = [
        "local_llm_setup",
        "llm_integrations"
    ]

    removed_count = 0

    # Remove experimental files
    for exp_file in experimental_files:
        if safe_remove_file(exp_file):
            removed_count += 1

    # Remove alternative implementation files
    for alt_file in alternative_files:
        if safe_remove_file(alt_file):
            removed_count += 1

    # Remove demo files
    for demo_file in demo_files:
        if safe_remove_file(demo_file):
            removed_count += 1

    # Remove documentation directories
    for doc_dir in doc_dirs:
        if safe_remove_dir(doc_dir):
            removed_count += 1

    logger.info(f"Final cleanup completed. Removed {removed_count} items.")

    # Count remaining files
    remaining_files = []
    for root, dirs, files in os.walk(".", topdown=True):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__']]
        for file in files:
            remaining_files.append(os.path.join(root, file))

    logger.info(f"Remaining files: {len(remaining_files)}")
    return removed_count

if __name__ == "__main__":
    # Change to neo-clone directory if not already there
    if not os.path.exists("main.py"):
        os.chdir("neo-clone")

    final_cleanup()