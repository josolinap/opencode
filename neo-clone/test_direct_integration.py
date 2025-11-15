#!/usr/bin/env python3
"""
Direct integration test for Neo-Clone brain system
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_direct_integration():
    """Test direct Neo-Clone brain integration."""
    print("Neo-Clone Direct Integration Test")
    print("=" * 40)
    
    try:
        # Test basic imports
        from brain import Brain
        from skills import SkillRegistry
        from config import load_config
        
        print("Core components imported successfully")
        
        # Load configuration
        config = load_config()
        print(f"Configuration loaded: {config.provider}/{config.model_name}")
        
        # Initialize skills and brain
        skills = SkillRegistry()
        brain = Brain(config, skills)
        print("Brain initialized successfully")
        
        # Test basic functionality
        test_message = "Hello Neo-Clone!"
        response = brain.send_message(test_message)
        print(f"Brain response: {response[:100]}...")
        
        print("\nDirect integration test PASSED")
        return True
        
    except Exception as e:
        print(f"Direct integration test FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_direct_integration()
    sys.exit(0 if success else 1)