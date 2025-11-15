#!/usr/bin/env python3
"""
Simple brain test for Neo-Clone
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_simple_brain():
    """Test simple brain functionality without external dependencies"""
    print("Simple Neo-Clone Brain Test")
    print("=" * 30)

    try:
        from skills import SkillRegistry, SkillResult
        from simple_config import load_config

        # Simple mock brain class
        class SimpleBrain:
            def __init__(self, config, skills):
                self.config = config
                self.skills = skills

            def send_message(self, message):
                # Simple skill-based response
                message_lower = message.lower()

                if "generate" in message_lower and "code" in message_lower:
                    skill = self.skills.get("code_generation")
                    if skill:
                        result = skill.execute({"prompt": message})
                        return f"[Code Generation] {result.output}"

                if "analyze" in message_lower and "text" in message_lower:
                    skill = self.skills.get("text_analysis")
                    if skill:
                        result = skill.execute({"text": message})
                        return f"[Text Analysis] {result.output}"

                if "data" in message_lower:
                    skill = self.skills.get("data_inspector")
                    if skill:
                        result = skill.execute({"text": message})
                        return f"[Data Inspector] {result.output}"

                return f"[Neo-Clone] I received your message: {message}"

        # Test initialization
        config = load_config()
        skills = SkillRegistry()
        brain = SimpleBrain(config, skills)

        print("+ Simple brain initialized successfully")
        print(f"+ Available skills: {len(skills.list_skills())}")

        # Test basic functionality
        test_messages = [
            "Hello Neo-Clone!",
            "Generate Python code for a neural network",
            "Analyze the sentiment of this text: I love AI!",
            "Help me understand this dataset",
        ]

        for msg in test_messages:
            response = brain.send_message(msg)
            print(f"\nInput: {msg}")
            print(f"Output: {response[:100]}...")

        print("\n+ Simple brain test PASSED")
        return True

    except Exception as e:
        print(f"Simple brain test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_simple_brain()
    sys.exit(0 if success else 1)
