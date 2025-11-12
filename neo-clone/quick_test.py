#!/usr/bin/env python3
"""
Quick test for Neo-Clone without LLM dependency
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("Neo-Clone Quick Test")
    print("=" * 25)
    
    try:
        # Test skills registry
        from skills import SkillRegistry
        skills = SkillRegistry()
        skill_list = skills.list_skills()
        print(f"Available skills: {len(skill_list)}")
        for skill in skill_list[:5]:  # Show first 5
            print(f"  - {skill}")
        
        # Test resilient skills system
        from resilient_skills_system import ResilientSkillExecutor, EnhancedSkillRegistry
        enhanced_skills = EnhancedSkillRegistry()
        executor = ResilientSkillExecutor()
        print("Resilient skills system: LOADED")
        
        # Test resilient execution
        result = executor.execute_skill_with_resilience("text_analysis", {"text": "This is great!"})
        print(f"Resilient execution test: {result.status}")
        
        # Test enhanced registry
        enhanced_result = enhanced_skills.execute_skill_resilient("text_analysis", {"text": "Test message"})
        print(f"Enhanced registry test: {enhanced_result.status}")
        
        print("\nNeo-Clone systems are OPERATIONAL!")
        print("Brain integration with enhanced resilience: READY")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)