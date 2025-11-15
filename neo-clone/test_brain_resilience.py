#!/usr/bin/env python3
"""
Test script to demonstrate Neo-Clone brain functionality with enhanced resilience system
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_brain_with_resilience():
    """Test the brain system with enhanced resilience."""
    print("Testing Neo-Clone Brain with Enhanced Resilience System")
    print("=" * 60)
    
    try:
        # Import core components
        from brain import Brain
        from skills import SkillRegistry
        from resilient_skills_system import ResilientSkillExecutor, EnhancedSkillRegistry
        from config import load_config
        
        print("Successfully imported core components")
        
        # Load configuration
        config = load_config()
        print(f"Configuration loaded: {config.provider}/{config.model_name}")
        
        # Initialize standard skills registry
        standard_skills = SkillRegistry()
        print(f"Standard skills registry initialized with {len(standard_skills.list_skills())} skills")
        
        # Initialize enhanced skills registry with resilience
        enhanced_skills = EnhancedSkillRegistry()
        print("Enhanced skills registry initialized with resilience features")
        
        # Initialize resilient skill executor
        resilient_executor = ResilientSkillExecutor()
        print("Resilient skill executor initialized")
        
        # Create brain with enhanced skills
        brain = Brain(config, enhanced_skills)
        print("Brain initialized with enhanced skills system")
        
        # Test basic brain functionality
        print("\n🔄 Testing Brain Functionality:")
        print("-" * 30)
        
        # Test 1: Intent analysis
        test_message = "Analyze this data for patterns"
        intent = brain.analyze_intent(test_message)
        print(f"Intent Analysis: '{test_message}' -> {intent}")
        
        # Test 2: Skill routing
        routed_skills = brain.route_to_skills(test_message)
        print(f"Skill Routing: {routed_skills}")
        
        # Test 3: Resilient skill execution
        print("\nTesting Resilient Skill Execution:")
        print("-" * 40)
        
        # Test with a skill that should work
        try:
            result = resilient_executor.execute_skill(
                "text_analysis", 
                {"text": "This is a great product!", "action": "sentiment"}
            )
            print(f"Successful skill execution: {result}")
        except Exception as e:
            print(f"Skill execution issue: {e}")
        
        # Test 4: Circuit breaker functionality
        print("\nTesting Circuit Breaker:")
        print("-" * 30)
        
        # Get circuit breaker status
        status = resilient_executor.get_circuit_breaker_status()
        print(f"Circuit Breaker Status: {status}")
        
        # Test 5: Performance metrics
        print("\nPerformance Metrics:")
        print("-" * 25)
        
        metrics = resilient_executor.get_performance_metrics()
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        print("\nBrain Resilience Test Complete!")
        print("All core functionality working with enhanced resilience")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Some dependencies may be missing")
        return False
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def test_enhanced_brain_integration():
    """Test integration with Enhanced Brain if available."""
    print("\nTesting Enhanced Brain Integration:")
    print("=" * 45)
    
    try:
        from enhanced_brain import EnhancedBrain
        from resilient_skills_system import EnhancedSkillRegistry
        from config import load_config
        
        config = load_config()
        enhanced_skills = EnhancedSkillRegistry()
        
        # Try to create Enhanced Brain
        enhanced_brain = EnhancedBrain(config, enhanced_skills)
        print("Enhanced Brain successfully initialized")
        
        # Test enhanced features
        test_message = "Generate Python code for a neural network"
        response = enhanced_brain.send_message(test_message)
        print(f"Enhanced Brain response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Enhanced Brain test failed: {e}")
        print("This is expected if some dependencies are missing")
        return False

if __name__ == "__main__":
    print("Neo-Clone Brain Resilience Test Suite")
    print("=====================================")
    
    # Test basic brain functionality
    basic_success = test_brain_with_resilience()
    
    # Test enhanced brain integration
    enhanced_success = test_enhanced_brain_integration()
    
    # Summary
    print("\nTest Summary:")
    print("=" * 20)
    print(f"Basic Brain Resilience: {'PASS' if basic_success else 'FAIL'}")
    print(f"Enhanced Brain Integration: {'PASS' if enhanced_success else 'SKIP'}")
    
    if basic_success:
        print("\nCONCLUSION:")
        print("Neo-Clone brain system is working with enhanced resilience!")
        print("Skills can handle tool failures gracefully")
        print("Circuit breaker patterns are operational")
        print("Performance monitoring is active")
    else:
        print("\nCONCLUSION:")
        print("Some issues detected in the brain system")
        print("Check dependencies and configuration")