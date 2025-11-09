import sys
from config import load_config
from skills import SkillRegistry
from brain import Brain

def run_skill_tests(brain):
    skills = [
        ("Train a test model on sample data", "ml_training"),
        ("Analyze sentiment of 'I love Python!'", "text_analysis"),
        ("Summarize this CSV file", "data_inspector"),
        ("Generate a scikit-learn classifier code.", "code_generation")
    ]
    for text, skill in skills:
        print(f"\nTesting skill routing: {skill}")
        out = brain.send_message(text)
        print("[Skill Response]", out)

def run_llm_test(brain):
    print("\nTesting LLM fallback/conversational context:")
    queries = [
        "Hello Neo, who made you?",
        "Can you summarize your capabilities?",
        "Show me an example workflow."
    ]
    for text in queries:
        out = brain.send_message(text)
        print(f"User: {text}\nNeo: {out}")

def main():
    cfg = load_config()
    print(f"Config loaded: provider={cfg.provider}, model={cfg.model_name}")
    skills = SkillRegistry()
    print(f"Discovered skills: {skills.list_skills()}")
    brain = Brain(cfg, skills)
    run_skill_tests(brain)
    run_llm_test(brain)

if __name__ == "__main__":
    main()