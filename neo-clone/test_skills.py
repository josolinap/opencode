#!/usr/bin/env python3
"""
Simple test for skills registry
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_skills():
    try:
        from skills import SkillRegistry

        registry = SkillRegistry()
        print(f"Skills registry created successfully")
        print(f"Available skills: {registry.list_skills()}")
        print(f"Total skills: {len(registry.list_skills())}")

        # Test getting a skill
        skill = registry.get("code_generation")
        if skill:
            print(f"Code generation skill: {skill.description}")
        else:
            print("Code generation skill not found")

        return True
    except Exception as e:
        print(f"Skills test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_skills()
    sys.exit(0 if success else 1)
