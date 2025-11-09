"""
examples/sample_workflows.py - Example usage of skills and brain (non-TUI)

Demonstrates:
- Loading config
- Instantiating Brain and SkillRegistry
- Calling a skill programmatically
"""

from pathlib import Path
from config import load_config
from brain import Brain, LLMClient
from skills import SkillRegistry

def sample():
    cfg = load_config()
    llm = LLMClient(cfg)
    brain = Brain(cfg, llm_client=llm)
    skills = SkillRegistry(skills_path=str(Path(__file__).resolve().parent.parent / "skills"))
    print("Available skills:", skills.list_skills())
    out = skills.execute("text_analysis", {"text": "I love this product. It's great!"})
    print("Text analysis:", out)
    reply = brain.send_message("Hello Neo, please summarize the last message.")
    print("LLM reply (may fail if Ollama not running):", reply)

if __name__ == "__main__":
    sample()
