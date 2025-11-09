#!/usr/bin/env python3
"""
test_tui.py - Test script for Neo-Clone TUI functionality.

This tests the TUI components without running the full interactive interface.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import load_config
from skills import SkillRegistry
from brain import Brain
from tui import NeoTUI

def test_integration():
    """Test the core integration between components."""
    print("🧪 Testing Neo-Clone TUI Integration...")
    
    # Test 1: Configuration loading
    print("1. Testing configuration loading...")
    try:
        config = load_config()
        print(f"   ✅ Config loaded: provider={config.provider}, model={config.model_name}")
    except Exception as e:
        print(f"   ❌ Config loading failed: {e}")
        return False
    
    # Test 2: Skills registry
    print("2. Testing skills registry...")
    try:
        skills = SkillRegistry()
        skill_list = skills.list_skills()
        print(f"   ✅ Skills loaded: {len(skill_list)} skills found")
        for skill in skill_list:
            print(f"      - {skill}")
    except Exception as e:
        print(f"   ❌ Skills loading failed: {e}")
        return False
    
    # Test 3: Brain initialization
    print("3. Testing brain initialization...")
    try:
        brain = Brain(config, skills)
        print("   ✅ Brain initialized successfully")
    except Exception as e:
        print(f"   ❌ Brain initialization failed: {e}")
        return False
    
    # Test 4: TUI component creation
    print("4. Testing TUI component creation...")
    try:
        app = NeoTUI(config)
        print("   ✅ TUI app created successfully")
        # Note: TUI has key bindings defined in BINDINGS list
    except Exception as e:
        print(f"   ❌ TUI creation failed: {e}")
        return False
    
    # Test 5: Intent parsing and skill routing
    print("5. Testing intent parsing and skill routing...")
    try:
        # Test skill intent detection
        test_messages = [
            "train a model",
            "analyze sentiment of this text",
            "show me data summary",
            "generate Python code"
        ]
        
        for msg in test_messages:
            intent = brain.parse_intent(msg)
            print(f"   Intent for '{msg[:30]}...': {intent}")
        
        print("   ✅ Intent parsing working")
    except Exception as e:
        print(f"   ❌ Intent parsing failed: {e}")
        return False
    
    # Test 6: Skill execution
    print("6. Testing skill execution...")
    try:
        result = brain.route_to_skill("code_generation", "generate a classifier")
        print(f"   ✅ Skill execution: {result['chosen_skill']}")
    except Exception as e:
        print(f"   ❌ Skill execution failed: {e}")
        return False
    
    print("🎉 All tests passed!")
    return True

def test_skill_functions():
    """Test individual skills."""
    print("\n🔧 Testing Individual Skills...")
    
    skills = SkillRegistry()
    
    # Test each skill
    skill_tests = [
        ("code_generation", "generate Python code for machine learning"),
        ("text_analysis", "analyze sentiment of positive text"),
        ("data_inspector", "analyze CSV data summary"),
        ("ml_training", "train a recommendation model")
    ]
    
    for skill_name, test_input in skill_tests:
        print(f"Testing {skill_name}...")
        try:
            result = skills.get(skill_name).execute({"text": test_input})
            print(f"   ✅ {skill_name}: {type(result)}")
        except Exception as e:
            print(f"   ❌ {skill_name}: {e}")

def main():
    """Main test function."""
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    print("🚀 Neo-Clone TUI Self-Test")
    print("=" * 50)
    
    # Run integration tests
    if test_integration():
        test_skill_functions()
        print("\n" + "=" * 50)
        print("✅ Neo-Clone TUI is ready to use!")
        print("\nTo start the TUI:")
        print("  python main.py --tui")
        print("\nTo start CLI mode:")
        print("  python main.py --cli")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)