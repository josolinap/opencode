"""
test_opencode_integration.py - Comprehensive integration tests for Opencode compatibility

This test suite validates that Neo-Clone TUI works seamlessly with Opencode's
model selection system while maintaining all existing functionality.

Test Coverage:
- Model selection from Opencode config
- Brain integration and response handling
- Skills, TUI, memory, logging, and plugin systems
- Model switching functionality
- Backward compatibility
- Performance and error handling
"""

import unittest
import asyncio
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, List, Any

# Add neo-clone to path
sys.path.insert(0, str(Path(__file__).parent))

from config_opencode import (
    Config, OpencodeConfig, load_config, 
    find_opencode_config, read_opencode_config,
    translate_opencode_model_to_neo, get_current_opencode_model,
    is_opencode_available
)
from llm_client_opencode import LLMClient, OpencodeLLMClient, LLMResponse
from brain_opencode import OpencodeBrain, ConversationHistory
from enhanced_tui_opencode import NeoCloneApp, MessageData
from skills import SkillRegistry
from skills.minimax_agent import MiniMaxAgent

class TestOpencodeConfig(unittest.TestCase):
    """Test Opencode configuration integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "opencode.json")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_find_opencode_config(self):
        """Test finding Opencode config file"""
        # Test current directory
        with open(self.config_path, 'w') as f:
            json.dump({"model": "openai/gpt-3.5-turbo"}, f)
        
        result = find_opencode_config()
        self.assertEqual(result, self.config_path)
    
    def test_read_opencode_config(self):
        """Test reading Opencode configuration"""
        config_data = {
            "model": "anthropic/claude-3-sonnet",
            "provider_options": {"temperature": 0.7}
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        result = read_opencode_config(self.config_path)
        self.assertIsNotNone(result)
        self.assertEqual(result.model, "anthropic/claude-3-sonnet")
        self.assertEqual(result.provider_options["temperature"], 0.7)
    
    def test_translate_opencode_model_to_neo(self):
        """Test model format translation"""
        # Test OpenAI model
        provider, model = translate_opencode_model_to_neo("openai/gpt-4")
        self.assertEqual(provider, "api")
        self.assertEqual(model, "gpt-4")
        
        # Test Ollama model
        provider, model = translate_opencode_model_to_neo("ollama/llama2")
        self.assertEqual(provider, "ollama")
        self.assertEqual(model, "llama2")
        
        # Test invalid format
        provider, model = translate_opencode_model_to_neo("invalid")
        self.assertEqual(provider, "ollama")
        self.assertEqual(model, "ggml-neural-chat")

class TestLLMClient(unittest.TestCase):
    """Test Opencode-compatible LLM client"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(
            provider="ollama",
            model_name="test-model",
            api_endpoint="http://localhost:11434"
        )
        self.client = LLMClient(self.config)
    
    def test_client_initialization(self):
        """Test LLM client initialization"""
        self.assertEqual(self.client.cfg, self.config)
        self.assertIsNotNone(self.client.session)
    
    def test_model_operations(self):
        """Test model setting and retrieval"""
        # Test setting model
        test_model = "openai/gpt-3.5-turbo"
        self.client.set_model(test_model)
        self.assertEqual(self.client.get_current_model(), test_model)
        
        # Test getting available models
        models = self.client.get_available_models()
        self.assertIsInstance(models, list)
    
    @patch('subprocess.run')
    def test_model_discovery(self, mock_subprocess):
        """Test automatic model discovery"""
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "openai/gpt-3.5-turbo\nanthropic/claude-3-sonnet"
        mock_subprocess.return_value = mock_result
        
        client = LLMClient(self.config)
        models = client.get_available_models()
        self.assertIn("openai/gpt-3.5-turbo", models)

class TestBrainIntegration(unittest.TestCase):
    """Test Opencode brain integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(
            provider="ollama",
            model_name="test-model"
        )
        self.skills = SkillRegistry()
        self.brain = OpencodeBrain(self.config, self.skills)
    
    def test_brain_initialization(self):
        """Test brain initialization with Opencode integration"""
        self.assertEqual(self.brain.cfg, self.config)
        self.assertIsInstance(self.brain.history, ConversationHistory)
        self.assertIsNotNone(self.brain.llm)
    
    def test_intent_parsing(self):
        """Test intent parsing including model switching"""
        # Test model switching intent
        result = self.brain.parse_intent("/model gpt-3.5-turbo")
        self.assertEqual(result["intent"], "model_switch")
        self.assertEqual(result["action"], "switch_model")
        
        # Test skill intent
        result = self.brain.parse_intent("analyze this text")
        self.assertEqual(result["intent"], "skill")
        self.assertEqual(result["skill"], "text_analysis")
        
        # Test minimax intent
        result = self.brain.parse_intent("minimax analyze this")
        self.assertEqual(result["intent"], "minimax")
        self.assertEqual(result["skill"], "minimax_agent")
    
    def test_model_switching(self):
        """Test model switching functionality"""
        # Test successful model switch
        result = self.brain.switch_model("openai/gpt-3.5-turbo")
        self.assertIn("✅ Model switched", result)
        self.assertEqual(self.brain.llm.get_current_model(), "openai/gpt-3.5-turbo")
    
    def test_status_reporting(self):
        """Test brain status reporting"""
        status = self.brain.get_status()
        
        self.assertIn("current_model", status)
        self.assertIn("provider", status)
        self.assertIn("available_skills", status)
        self.assertIn("config_source", status)

class TestSkillsIntegration(unittest.TestCase):
    """Test skills system integration with Opencode"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(provider="ollama", model_name="test-model")
        self.skills = SkillRegistry()
        self.brain = OpencodeBrain(self.config, self.skills)
    
    def test_skill_discovery(self):
        """Test that skills are properly discovered"""
        available_skills = list(self.skills._skills.keys())
        self.assertIn("minimax_agent", available_skills)
        self.assertIn("text_analysis", available_skills)
        self.assertIn("code_generation", available_skills)
    
    def test_skill_execution(self):
        """Test skill execution through brain"""
        # Test MiniMax Agent execution
        result = self.brain.route_to_skill("minimax_agent", "analyze test")
        self.assertIn("chosen_skill", result)
        self.assertEqual(result["chosen_skill"], "minimax_agent")
        self.assertIn("output", result)

class TestMiniMaxAgentIntegration(unittest.TestCase):
    """Test MiniMax Agent integration with Opencode"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(provider="ollama", model_name="test-model")
        self.skills = SkillRegistry()
        self.brain = OpencodeBrain(self.config, self.skills)
    
    def test_minimax_agent_execution(self):
        """Test MiniMax Agent execution"""
        # Test intent analysis
        minimax_skill = self.skills.get("minimax_agent")
        result = minimax_skill.execute({"text": "analyze the intent of 'switch to gpt-4'"})
        
        self.assertIn("intent_analysis", result)
        self.assertIn("confidence", result["intent_analysis"])
    
    def test_dynamic_skill_generation(self):
        """Test dynamic skill generation through MiniMax Agent"""
        minimax_skill = self.skills.get("minimax_agent")
        result = minimax_skill.execute({
            "text": "generate a skill for file operations",
            "mode": "generate"
        })
        
        self.assertIn("generated_skill", result)

class TestTUIIntegration(unittest.TestCase):
    """Test TUI integration with Opencode"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(provider="ollama", model_name="test-model")
        # Don't initialize the full app in tests
        self.app = None
    
    @patch('enhanced_tui_opencode.load_config')
    @patch('enhanced_tui_opencode.SkillRegistry')
    def test_app_initialization(self, mock_skills, mock_config):
        """Test TUI app initialization"""
        mock_config.return_value = self.config
        mock_skills.return_value = SkillRegistry()
        
        # Test that app can be created without errors
        app = NeoCloneApp()
        self.assertIsNotNone(app)
        self.assertEqual(app.config, self.config)
    
    def test_message_data_structure(self):
        """Test MessageData structure with Opencode fields"""
        message = MessageData(
            role="assistant",
            content="Test response",
            model_used="openai/gpt-3.5-turbo",
            response_time=1.5
        )
        
        self.assertEqual(message.role, "assistant")
        self.assertEqual(message.model_used, "openai/gpt-3.5-turbo")
        self.assertEqual(message.response_time, 1.5)

class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with original Neo-Clone"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(provider="ollama", model_name="test-model")
    
    def test_config_compatibility(self):
        """Test that config still works as before"""
        # Test default values
        self.assertEqual(self.config.provider, "ollama")
        self.assertEqual(self.config.model_name, "test-model")
        self.assertEqual(self.config.temperature, 0.2)
    
    def test_brain_compatibility(self):
        """Test brain backward compatibility"""
        skills = SkillRegistry()
        
        # Should be able to create original Brain class
        from brain import Brain
        brain = Brain(self.config, skills)
        self.assertIsNotNone(brain)
    
    def test_llm_client_compatibility(self):
        """Test LLM client backward compatibility"""
        # Should be able to create original LLM client
        from brain import LLMClient
        client = LLMClient(self.config)
        self.assertIsNotNone(client)

class TestPerformanceAndErrorHandling(unittest.TestCase):
    """Test performance and error handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(provider="ollama", model_name="test-model")
        self.skills = SkillRegistry()
        self.brain = OpencodeBrain(self.config, self.skills)
    
    def test_error_handling(self):
        """Test error handling in brain operations"""
        # Test invalid model switch
        result = self.brain.switch_model("")
        self.assertIn("❌", result)  # Should indicate error
    
    def test_conversation_history_limits(self):
        """Test conversation history size limits"""
        # Add many messages
        for i in range(25):
            self.brain.history.add("user", f"Message {i}")
        
        # Should be limited to max_messages (20)
        self.assertEqual(len(self.brain.history._messages), 20)

class TestIntegrationFlow(unittest.TestCase):
    """Test complete integration flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(provider="ollama", model_name="test-model")
        self.skills = SkillRegistry()
        self.brain = OpencodeBrain(self.config, self.skills)
    
    def test_complete_message_flow(self):
        """Test complete message processing flow"""
        # Test user input → intent parsing → skill routing → response
        message = "analyze the sentiment of this text"
        
        # Parse intent
        intent = self.brain.parse_intent(message)
        self.assertEqual(intent["intent"], "skill")
        self.assertEqual(intent["skill"], "text_analysis")
        
        # Route to skill
        result = self.brain.route_to_skill(intent["skill"], message)
        self.assertIn("chosen_skill", result)
        self.assertIn("output", result)
    
    def test_model_switching_flow(self):
        """Test model switching complete flow"""
        # Switch model
        result = self.brain.switch_model("anthropic/claude-3-sonnet")
        self.assertIn("✅", result)
        
        # Verify model is updated
        self.assertEqual(self.brain.llm.get_current_model(), "anthropic/claude-3-sonnet")
        
        # Test status shows correct info
        status = self.brain.get_status()
        self.assertIn("anthropic/claude-3-sonnet", status["current_model"])

def create_sample_queries():
    """Create sample queries for testing"""
    return [
        {
            "query": "analyze the sentiment of this text: 'I love this product!'",
            "expected_intent": "skill",
            "expected_skill": "text_analysis"
        },
        {
            "query": "/model openai/gpt-3.5-turbo",
            "expected_intent": "model_switch",
            "expected_action": "switch_model"
        },
        {
            "query": "minimax analyze the intent of user requests",
            "expected_intent": "minimax",
            "expected_skill": "minimax_agent"
        },
        {
            "query": "generate python code to sort a list",
            "expected_intent": "skill",
            "expected_skill": "code_generation"
        }
    ]

async def run_integration_tests():
    """Run async integration tests"""
    test_queries = create_sample_queries()
    
    config = Config(provider="ollama", model_name="test-model")
    skills = SkillRegistry()
    brain = OpencodeBrain(config, skills)
    
    print("🧪 Running Integration Tests...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {test_case['query']}")
        
        # Parse intent
        intent = brain.parse_intent(test_case["query"])
        print(f"   Intent: {intent}")
        
        # Validate intent
        expected_intent = test_case["expected_intent"]
        if intent["intent"] == expected_intent:
            print(f"   ✅ Intent validation passed")
        else:
            print(f"   ❌ Intent validation failed: expected {expected_intent}, got {intent['intent']}")
        
        # Handle model switching
        if intent["intent"] == "model_switch":
            result = brain.handle_model_switch(test_case["query"])
            print(f"   Model switch result: {result}")
        
        # Handle skill routing
        elif intent["intent"] == "skill":
            result = brain.route_to_skill(intent["skill"], test_case["query"])
            print(f"   Skill result: {result.get('output', 'No output')[:100]}...")
    
    print("\n" + "=" * 50)
    print("🎉 Integration tests completed!")

def main():
    """Main test runner"""
    print("🚀 Starting Opencode Integration Tests")
    print("=" * 60)
    
    # Run unit tests
    print("\n🧪 Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration tests
    print("\n🔗 Running Integration Tests...")
    asyncio.run(run_integration_tests())
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()