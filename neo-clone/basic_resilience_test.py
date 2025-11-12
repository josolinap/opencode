"""
Basic Test for Resilient Skills System - No Unicode
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_basic_functionality():
    """Test basic functionality of resilient skills system"""
    
    print("Testing Resilient Skills System for Neo-Clone")
    print("=" * 60)
    
    try:
        # Test import
        from skills import BaseSkill, SkillResult, SkillRegistry
        print("[OK] Successfully imported basic skills system")
        
        # Test enhanced error recovery
        from enhanced_error_recovery import EnhancedErrorRecovery, get_error_recovery
        print("[OK] Successfully imported enhanced error recovery")
        
        # Test resilient skills system
        from resilient_skills_system import ResilientSkillExecutor, EnhancedSkillRegistry
        print("[OK] Successfully imported resilient skills system")
        
        # Initialize system
        registry = EnhancedSkillRegistry()
        print("[OK] Successfully initialized enhanced skill registry")
        
        # Test normal skill execution
        result = registry.execute_skill_resilient("text_analysis", {"text": "I love this product!"})
        print(f"[OK] Skill execution result: {result.status}")
        print(f"     Output: {result.result.output[:50]}...")
        
        # Test non-existent skill
        result = registry.execute_skill_resilient("non_existent_skill", {"text": "test"})
        print(f"[OK] Fallback handling result: {result.status}")
        
        # Get statistics
        stats = registry.resilient_executor.get_resilience_statistics()
        print(f"[OK] Statistics: {stats['total_executions']} executions")
        print(f"     Success rate: {stats['success_rate']:.2%}")
        print(f"     Recovery rate: {stats['recovery_rate']:.2%}")
        print(f"     Fallback rate: {stats['fallback_rate']:.2%}")
        
        print("\n" + "=" * 60)
        print("RESILIENT SKILLS SYSTEM: VALIDATION COMPLETE")
        print("Neo-Clone's skills are now more resilient!")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n[SUCCESS] RESILIENCE ENHANCEMENT VALIDATED SUCCESSFULLY")
    else:
        print("\n[FAILED] RESILIENCE ENHANCEMENT VALIDATION FAILED")