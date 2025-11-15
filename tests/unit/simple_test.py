#!/usr/bin/env python3
"""
Simple test for integrated skills without complex registry.
"""

import sys
import traceback

# Add current directory to path for imports
sys.path.insert(0, '.')

def test_individual_skills():
    """Test individual integrated skills directly."""
    print("Testing Individual Integrated Skills")
    print("=" * 40)
    
    skills_to_test = [
        ('federated_learning', 'FederatedLearningSkill'),
        ('ml_workflow_generator', 'MLWorkflowGenerator'),
        ('autonomous_reasoning_skill', 'AutonomousReasoningSkill'),
        ('advanced_pentesting_reverse_engineering', 'AdvancedPentestingReverseEngineeringSkill'),
        ('security_evolution_engine', 'SecurityEvolutionEngineSkill')
    ]
    
    results = {}
    
    for module_name, class_name in skills_to_test:
        print(f"\nTesting {class_name}...")
        try:
            # Import the module
            module = __import__(module_name)
            skill_class = getattr(module, class_name)
            
            # Create instance
            skill = skill_class()
            print(f"  ✓ Created {skill_class.__name__}")
            
            # Test execution
            result = skill.execute({})
            success = result.success if hasattr(result, 'success') else False
            
            results[module_name] = {
                'class': class_name,
                'success': success,
                'output': result.output if hasattr(result, 'output') else str(result)
            }
            
            status = "PASS" if success else "FAIL"
            print(f"  {status}: {status == 'PASS'}")
            
            if not success:
                print(f"  Error: {results[module_name]['output'][:100]}...")
                
        except Exception as e:
            results[module_name] = {
                'class': class_name,
                'success': False,
                'error': str(e)
            }
            print(f"  FAIL: {e}")
    
    # Summary
    print(f"\n{'='*40}")
    print("SUMMARY")
    print(f"{'='*40}")
    
    passed = sum(1 for r in results.values() if r.get('success', False))
    total = len(results)
    
    print(f"Total skills tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for module, result in results.items():
        status = "PASS" if result.get('success', False) else "FAIL"
        print(f"  {status} {module}: {result['class']}")
    
    return passed == total

if __name__ == "__main__":
    print("Neo-Clone Simple Skills Test")
    print("=" * 40)
    
    success = test_individual_skills()
    
    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)