"""skills/__init__.py - Dynamic Skill Discovery and Registry

Loads all .py skill modules from this directory (ignores __init__.py)
Imports using importlib, logs and skips ImportError/AttributeError per file
Auto-registers any subclass of BaseSkill defined in a module
"""

import abc
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BaseSkill(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @property
    def parameters(self) -> dict:
        return {}

    @property
    @abc.abstractmethod
    def example_usage(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def validate_params(self, params: Dict[str, Any]) -> bool:
        return True


class SkillRegistry:
    def __init__(self, skills_path: Optional[str] = None):
        self.skills: Dict[str, BaseSkill] = {}
        if skills_path:
            self.skills_path = Path(skills_path)
        else:
            self.skills_path = Path(__file__).parent
        self.discover_skills()

    def register(self, skill: BaseSkill):
        if skill.name in self.skills:
            logger.warning(f"Overwriting existing skill registration: {skill.name}")
        self.skills[skill.name] = skill

    def get(self, name: str) -> BaseSkill:
        try:
            return self.skills[name]
        except KeyError:
            raise KeyError(f"Skill not found: {name}")

    def list_skills(self) -> List[str]:
        return list(self.skills.keys())

    def discover_skills(self):
        if not self.skills_path.exists() or not self.skills_path.is_dir():
            logger.debug(f"Skills path does not exist or is not a directory: {self.skills_path}")
            return

        project_root = str(self.skills_path.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        importlib.invalidate_caches()

        package_prefix = self.skills_path.name

        for py in sorted(self.skills_path.glob("*.py")):
            if py.name == "__init__.py":
                continue

            modname = py.stem
            pkg_name = f"{package_prefix}.{modname}"

            try:
                mod = importlib.import_module(pkg_name)
            except Exception:
                logger.exception(f"Failed to import module {pkg_name}")
                continue

            for attr_name in dir(mod):
                try:
                    obj = getattr(mod, attr_name)
                except Exception:
                    logger.exception(f"Failed to access attribute {attr_name} in {pkg_name}")
                    continue

                if isinstance(obj, type) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                    try:
                        instance = obj()
                        self.register(instance)
                        logger.info(f"Registered skill: {instance.name}")
                    except Exception:
                        logger.exception(f"Failed to instantiate/register skill class {obj} in {pkg_name}")


__all__ = ["BaseSkill", "SkillRegistry"]
