# Isolated skill discovery test runner for debugging
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def main():
    try:
        print("Importing SkillRegistry...")
        from skills import SkillRegistry
        skills_path = str(Path(__file__).parent / "skills")
        reg = SkillRegistry(skills_path=skills_path)
        print("Registered skills:", reg.list_skills())
        for name, meta in reg.skills.items():
            print(f"Skill: {name}")
            print("  Description:", getattr(meta, "description", "N/A"))
            print("  Params:", getattr(meta, "parameters", "N/A"))
            print("  Example:", getattr(meta, "example_usage", "N/A"))
            print()
    except Exception as e:
        print("Exception during skill discovery:")
        traceback.print_exc()

if __name__ == "__main__":
    main()