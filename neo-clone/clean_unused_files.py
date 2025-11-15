#!/usr/bin/env python3
"""
Clean up unused files from Neo-Clone directory
Removes test files, demo files, temporary files, and status reports that are not part of the core functionality
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

def clean_unused_files():
    """Clean up unused files and directories"""

    # Files to remove (status reports and documentation that are just historical)
    status_reports = [
        "INTEGRATION_STATUS_REPORT.md",
        "INTEGRATION_COMPLETE_REPORT.md",
        "ENHANCED_BRAIN_INTEGRATION_COMPLETE.md",
        "CODEBASE_CLEANUP_SUMMARY.md",
        "BRAIN_ENHANCEMENT_GUIDE.md",
        "ADVANCED_INTEGRATION_COMPLETE.md",
        "COMPREHENSIVE_SKILL_TESTING_REPORT.md",
        "BACKUP_INTEGRATION_FINAL_SUMMARY.md",
        "AGENT_FLOW_ANALYSIS.md",
        "SESSION_COMPLETE_SUMMARY.md",
        "PHASE2_INTEGRATION_COMPLETE.md",
        "SYSTEM_HEALER_INTEGRATION_COMPLETE.md",
        "SKILL_STANDARDIZATION_FIX.md",
        "SKILL_STANDARDIZATION_COMPLETE.md",
        "RESILIENCE_ENHANCEMENT_VALIDATION_REPORT.md",
        "EVOLUTION_ENGINE_DEPLOYMENT.md"
    ]

    # Test files that aren't imported by the main system
    test_files = [
        "comprehensive_functionality_tests.py"
    ]

    # Temporary files
    temp_files = [
        "evolution_monitor.log",
        "evolution_dashboard.html",
        "improvement_summary.txt"
    ]

    # Directories that contain demo/example content
    demo_dirs = [
        "repository_explorations"
    ]

    removed_count = 0

    # Remove status report files
    for report in status_reports:
        if safe_remove_file(report):
            removed_count += 1

    # Remove test files
    for test_file in test_files:
        if safe_remove_file(test_file):
            removed_count += 1

    # Remove temporary files
    for temp_file in temp_files:
        if safe_remove_file(temp_file):
            removed_count += 1

    # Remove demo directories
    for demo_dir in demo_dirs:
        if safe_remove_dir(demo_dir):
            removed_count += 1

    logger.info(f"Cleanup completed. Removed {removed_count} items.")

    # List remaining files to verify
    remaining_files = []
    for root, dirs, files in os.walk(".", topdown=True):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
        for file in files:
            filepath = os.path.join(root, file)
            remaining_files.append(filepath)

    logger.info(f"Remaining files: {len(remaining_files)}")
    return removed_count

if __name__ == "__main__":
    # Change to neo-clone directory if not already there
    if not os.path.exists("main.py"):
        os.chdir("neo-clone")

    clean_unused_files()