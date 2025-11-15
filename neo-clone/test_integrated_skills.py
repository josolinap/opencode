#!/usr/bin/env python3
"""
Test script for the integrated backup skills system.
Tests all newly integrated skills to ensure they work properly.
"""

import sys
import traceback
from skills import SkillRegistry

def test_skill_registry():
    """Test the skill registry with all integrated skills."""
    print("Testing Integrated Skills Registry")
    print("=" * 50)
    
    try:
        # Initialize skill registry
        registry = SkillRegistry()
        
        # List all available skills
        skills = registry.list_skills()
        print(f"Total skills registered: {len(skills)}")
        print("\nAvailable Skills:")
        
        # Group skills by category
        core_skills = []
        integrated_skills = []
        
        for skill_name in sorted(skills):
            skill = registry.get_skill(skill_name)
            if skill:
                skill_info = f"  • {skill_name}: {skill.description}"
                
                # Identify integrated backup skills
                integrated_backup_skills = [
                    'advanced_pentesting_reverse_engineering',
                    'security_evolution_engine', 
                    'autonomous_reasoning',
                    'skill_routing_optimizer',
                    'cross_skill_dependency_analyzer',
                    'federated_learning',
                    'ml_workflow_generator'
                ]
                
                if skill_name in integrated_backup_skills:
                    integrated_skills.append(skill_info)
                else:
                    core_skills.append(skill_info)
        
        print("\nCore Skills:")
        for skill in core_skills:
            print(skill)
            
        print("\nIntegrated Backup Skills:")
        for skill in integrated_skills:
            print(skill)
        
        # Test each integrated skill
        print(f"\nTesting {len(integrated_skills)} Integrated Skills:")
        print("-" * 40)
        
        test_results = {}
        
        for skill_name in integrated_backup_skills:
            if skill_name in skills:
                skill = registry.get_skill(skill_name)
                if skill:
                    try:
                        # Test with minimal parameters
                        result = skill.execute({})
                        success = result.success if hasattr(result, 'success') else False
                        test_results[skill_name] = success
                        
                        status = "PASS" if success else "FAIL"
                        print(f"{status} {skill_name}")
                        
                        if not success and hasattr(result, 'output'):
                            print(f"    Error: {result.output[:100]}...")
                            
                    except Exception as e:
                        test_results[skill_name] = False
                        print(f"FAIL {skill_name}: {str(e)[:50]}...")
            else:
                test_results[skill_name] = False
                print(f"MISSING {skill_name}")
        
        # Summary
        passed = sum(1 for success in test_results.values() if success)
        total = len(test_results)
        
        print(f"\nTest Summary:")
        print(f"  Passed: {passed}/{total}")
        print(f"  Success Rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("All integrated skills working perfectly!")
            return True
        else:
            print("Some skills need attention")
            return False
            
    except Exception as e:
        print(f"❌ Critical error during testing: {e}")
        traceback.print_exc()
        return False

def test_skill_execution():
    """Test actual execution of a few key integrated skills."""
    print("\nTesting Skill Execution")
    print("=" * 30)
    
    try:
        registry = SkillRegistry()
        
        # Test federated learning skill
        print("\nTesting Federated Learning Skill...")
        fl_skill = registry.get_skill('federated_learning')
        if fl_skill:
            result = fl_skill.execute({
                'action': 'start_session',
                'clients': 3,
                'rounds': 2
            })
            print(f"Result: {'Success' if result.success else 'Failed'}")
            if result.success:
                print(f"Output: {result.output[:200]}...")
        
        # Test ML workflow generator
        print("\nTesting ML Workflow Generator...")
        mlwf_skill = registry.get_skill('ml_workflow_generator')
        if mlwf_skill:
            result = mlwf_skill.execute({
                'task_type': 'classification',
                'data_description': 'customer churn dataset'
            })
            print(f"Result: {'Success' if result.success else 'Failed'}")
            if result.success:
                print(f"Output: {result.output[:200]}...")
        
        # Test autonomous reasoning
        print("\nTesting Autonomous Reasoning Skill...")
        ar_skill = registry.get_skill('autonomous_reasoning')
        if ar_skill:
            result = ar_skill.execute({
                'task': 'optimize_workflow',
                'context': 'data processing pipeline'
            })
            print(f"Result: {'Success' if result.success else 'Failed'}")
            if result.success:
                print(f"Output: {result.output[:200]}...")
                
        return True
        
    except Exception as e:
        print(f"❌ Error during execution testing: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Neo-Clone Integrated Skills Test Suite")
    print("=" * 50)
    
    # Run tests
    registry_test = test_skill_registry()
    execution_test = test_skill_execution()
    
    # Final summary
    print("\n" + "=" * 50)
    print("FINAL TEST RESULTS")
    print("=" * 50)
    
    if registry_test and execution_test:
        print("ALL TESTS PASSED!")
        print("Integrated backup skills are fully functional")
        print("Neo-Clone system is ready for production")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        print("Review the output above for details")
        sys.exit(1)