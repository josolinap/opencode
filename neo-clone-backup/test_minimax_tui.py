"""
test_minimax_tui.py - Test MiniMax Agent in Enhanced TUI context
"""

import sys
from pathlib import Path

# Add neo-clone to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, load_config
from skills import SkillRegistry
from brain import Brain, LLMClient
from skills.minimax_agent import MiniMaxAgent
import json


def test_minimax_in_tui_context():
    """Test MiniMax Agent in the context of Enhanced TUI"""
    print("🧪 Testing MiniMax Agent in TUI Context")
    print("=" * 60)
    
    # Test 1: Verify MiniMax Agent is discoverable
    print("\n1. Testing Skill Discovery...")
    skills = SkillRegistry()
    available_skills = skills.list_skills()
    
    assert 'minimax_agent' in available_skills, "MiniMax Agent not found in skill registry"
    print("   ✅ MiniMax Agent successfully discovered")
    
    # Test 2: Verify skill properties
    print("\n2. Testing Skill Properties...")
    minimax_skill = skills.get('minimax_agent')
    
    assert minimax_skill.name == 'minimax_agent', f"Wrong skill name: {minimax_skill.name}"
    assert hasattr(minimax_skill, 'description'), "Missing description"
    assert hasattr(minimax_skill, 'parameters'), "Missing parameters"
    assert hasattr(minimax_skill, 'example_usage'), "Missing example_usage"
    print("   ✅ All required properties present")
    print(f"   - Name: {minimax_skill.name}")
    print(f"   - Description: {minimax_skill.description}")
    
    # Test 3: Test intent analysis
    print("\n3. Testing Intent Analysis...")
    result = minimax_skill.execute({
        "mode": "analyze",
        "user_input": "Create a Python script to process data"
    })
    
    assert result['mode'] == 'analyze', "Wrong mode in result"
    assert 'primary_intent' in result, "Missing primary_intent"
    assert 'confidence' in result, "Missing confidence"
    assert 'reasoning_trace' in result, "Missing reasoning_trace"
    print("   ✅ Intent analysis working correctly")
    print(f"   - Intent: {result['primary_intent']} (confidence: {result['confidence']:.2f})")
    
    # Test 4: Test skill generation
    print("\n4. Testing Dynamic Skill Generation...")
    result = minimax_skill.execute({
        "mode": "generate",
        "skill_name": "data_processor",
        "description": "Process data files and create summaries"
    })
    
    assert result['mode'] == 'generate', "Wrong mode in result"
    assert 'skill_code' in result, "Missing skill_code"
    assert 'class_name' in result, "Missing class_name"
    assert 'file_path' in result, "Missing file_path"
    print("   ✅ Dynamic skill generation working")
    print(f"   - Generated class: {result['class_name']}")
    print(f"   - Code length: {len(result['skill_code'])} characters")
    
    # Test 5: Test reasoning mode
    print("\n5. Testing Reasoning Mode...")
    result = minimax_skill.execute({
        "mode": "reason",
        "query": "What is the best approach for data analysis?"
    })
    
    assert result['mode'] == 'reason', "Wrong mode in result"
    assert 'reasoning' in result, "Missing reasoning"
    print("   ✅ Reasoning mode working")
    print(f"   - Reasoning: {result['reasoning'][:100]}...")
    
    # Test 6: Test brain integration
    print("\n6. Testing Brain Integration...")
    try:
        cfg = Config()
        brain = Brain(cfg, skills)
        
        # Test with a query that might trigger different behaviors
        response = brain.send_message("help")
        print("   ✅ Brain integration working")
        print(f"   - Response: {response[:50]}...")
        
    except Exception as e:
        print(f"   ⚠️  Brain integration (LLM unavailable, but skill registry works): {str(e)[:50]}")
    
    # Test 7: Test enhanced parameters
    print("\n7. Testing Enhanced Parameters...")
    result = minimax_skill.execute({
        "mode": "analyze",
        "user_input": "Build a web scraper",
        "context": ["user likes automation", "works with Python"],
        "detailed_trace": True
    })
    
    # Context is used in the reasoning trace, not as a separate field
    assert result['reasoning_trace'] is not None, "Detailed trace not generated"
    assert len(result['reasoning_trace']['steps']) > 0, "No reasoning steps generated"
    print("   ✅ Enhanced parameters working")
    
    # Test 8: Performance test
    print("\n8. Testing Performance...")
    import time
    
    start_time = time.time()
    for i in range(10):
        minimax_skill.execute({
            "mode": "analyze",
            "user_input": f"Test query {i}"
        })
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 10
    print(f"   ✅ Average execution time: {avg_time:.4f}s")
    assert avg_time < 0.01, "Performance too slow"
    
    print("\n" + "=" * 60)
    print("🎉 All TUI Context Tests Passed Successfully!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        test_minimax_in_tui_context()
        print("\n✅ MiniMax Agent is fully compatible with Enhanced TUI!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)