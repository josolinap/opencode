import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from skills import SkillRegistry, BaseSkill

def test_skill_discovery():
    reg = SkillRegistry()
    found_skills = reg.list_skills()
    expected = {'ml_training', 'text_analysis', 'data_inspector', 'code_generation'}
    print("Skills found:", found_skills)
    assert set(found_skills) == expected, f"Missing or extra skills: {found_skills}"

    for name in expected:
        skill = reg.get(name)
        assert isinstance(skill, BaseSkill), f"{name} does not subclass BaseSkill"
        assert hasattr(skill, "description")
        assert hasattr(skill, "parameters")
        assert hasattr(skill, "example_usage")
        assert hasattr(skill, "execute")
        print(f"{name}: PASS")

if __name__ == "__main__":
    test_skill_discovery()
    print("All skill discovery tests passed.")