# Revised bootstrap_create.py - fixed syntax error and streamlined smoke tests
"""
Bootstrap script to create the neo-clone project structure and files.

This script:
- Creates directory /app/neo_tui_assistant_1544/neo-clone and subfiles
- Writes core modules: main.py, brain.py, config.py, utils.py
- Writes skills package and four skill stubs
- Writes requirements.txt, README.md, ARCHITECTURE.md, ARCHITECTURE_ANALYSIS.md,
  launch_windows.bat, examples/sample_workflows.py
- Runs a small smoke test: compile modules and import them by file location
- Exits with non-zero code on failure so executor catches errors
"""

import os
import sys
import json
import textwrap
from pathlib import Path
import traceback

ROOT = Path("/app/neo_tui_assistant_1544")
PROJECT_DIR = ROOT / "neo-clone"

TEMPLATES = {}

TEMPLATES["__init__"] = """# neo-clone package initializer
# This project intentionally uses filesystem imports for dynamic loading of skill modules.
"""

TEMPLATES["config.py"] = '''"""
config.py - Configuration management for neo-clone

Uses pydantic to validate configuration and supports loading from environment
variables or a JSON/YAML config file. Ollama (local) is the default provider.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

class Config(BaseModel):
    provider: str = Field("ollama", description="LLM provider: 'ollama'|'hf'|'api'")
    model_name: str = Field("ggml-neural-chat", description="Default model name to use")
    api_endpoint: Optional[str] = Field("http://localhost:11434", description="API endpoint for local providers (ollama)")
    max_tokens: int = Field(1024, description="Max tokens to request from model")
    temperature: float = Field(0.2, description="Sampling temperature")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to guide assistant")

    @validator("temperature")
    def check_temperature(cls, v):
        if not (0.0 <= v <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v

def load_config(path: Optional[str] = None) -> Config:
    """
    Load configuration from a JSON file or environment variables.
    Priority: explicit path -> NEOCONFIG env var -> defaults
    """
    try:
        cfg_path = path or os.getenv("NEOCONFIG")
        if cfg_path and os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                raw = f.read()
            # Try JSON first
            try:
                data = json.loads(raw)
            except Exception:
                # Fallback: treat as simple key=value lines
                data = {}
                for line in raw.splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        data[k.strip()] = v.strip()
            logger.info(f"Loaded configuration from {cfg_path}")
            return Config(**data)
        # Build from environment
        env = {
            "provider": os.getenv("NEO_PROVIDER", "ollama"),
            "model_name": os.getenv("NEO_MODEL", "ggml-neural-chat"),
            "api_endpoint": os.getenv("NEO_API_ENDPOINT", "http://localhost:11434"),
            "max_tokens": int(os.getenv("NEO_MAX_TOKENS", "1024")),
            "temperature": float(os.getenv("NEO_TEMPERATURE", "0.2")),
            "system_prompt": os.getenv("NEO_SYSTEM_PROMPT", None),
        }
        logger.info("Loaded configuration from environment/defaults")
        return Config(**env)
    except Exception as e:
        logger.exception("Failed to load config")
        raise
'''

TEMPLATES["utils.py"] = '''"""
utils.py - helper utilities for neo-clone

Provides logging setup, message formatting, simple file helpers and JSON validation.
"""

import logging
import sys
import json
from typing import Any, Optional
import time
import os
from pathlib import Path

def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, handlers=[handler])

def format_message(role: str, content: str) -> str:
    """
    Simple role + content formatter used by the TUI and logs.
    """
    return f"[{role}] {content}"

def truncate_text(text: str, max_length: int = 1000) -> str:
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."

def validate_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except Exception:
        return None

def read_json(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
'''

TEMPLATES["brain.py"] = '''"""
brain.py - Central reasoning engine and LLM integration

Implements:
- ConversationHistory: rolling window of messages
- LLMClient: simple abstraction for Ollama (HTTP) and fallback behavior
- Brain: high-level interface for sending messages, parsing intents, and routing to skills
"""

from typing import List, Dict, Optional
import requests
import logging
import time
from dataclasses import dataclass, field
from .config import Config
from .utils import validate_json

logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str
    content: str

class ConversationHistory:
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._messages: List[Message] = []

    def add(self, role: str, content: str):
        self._messages.append(Message(role=role, content=content))
        # trim to last N messages
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]

    def to_list(self) -> List[Dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self._messages]

    def clear(self):
        self._messages = []

class LLMClient:
    """
    Very small abstraction that currently supports Ollama (local HTTP).
    For Ollama, we POST to {api_endpoint}/api/chat with a JSON payload.
    """
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session = requests.Session()

    def chat(self, messages: List[Dict[str, str]], timeout: int = 15) -> str:
        provider = self.cfg.provider.lower()
        if provider == "ollama":
            url = self.cfg.api_endpoint.rstrip("/") + "/api/chat"
            payload = {
                "model": self.cfg.model_name,
                "messages": messages,
                "max_tokens": self.cfg.max_tokens,
                "temperature": self.cfg.temperature,
            }
            try:
                resp = self.session.post(url, json=payload, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    if "text" in data:
                        return data["text"]
                    if "output" in data:
                        return data["output"]
                    if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                        c = data["choices"][0]
                        if isinstance(c, dict) and "message" in c:
                            return c["message"].get("content", "")
                return str(data)
            except Exception as e:
                logger.debug("Ollama request failed: %s", e)
                raise
        else:
            raise NotImplementedError(f"Provider {provider} not implemented")

class Brain:
    def __init__(self, cfg: Config, llm_client: Optional[LLMClient] = None):
        self.cfg = cfg
        self.history = ConversationHistory(max_messages=20)
        self.llm = llm_client or LLMClient(cfg)

    def parse_intent(self, user_text: str) -> Dict[str, str]:
        text = user_text.lower()
        if text.startswith("analyze") or "analyze" in text or "inspect" in text or "profile" in text:
            return {"intent": "skill", "skill": "data_inspector"}
        if "sentiment" in text or "toxic" in text or "toxicity" in text:
            return {"intent": "skill", "skill": "text_analysis"}
        if "train" in text or "recommend" in text or "simulate" in text or "churn" in text:
            return {"intent": "skill", "skill": "ml_training"}
        if "generate code" in text or "write code" in text or "explain code" in text:
            return {"intent": "skill", "skill": "code_generation"}
        return {"intent": "chat", "skill": None}

    def send_message(self, user_text: str) -> str:
        self.history.add("user", user_text)
        messages = self.history.to_list()
        if self.cfg.system_prompt:
            messages = [{"role": "system", "content": self.cfg.system_prompt}] + messages
        try:
            start = time.time()
            reply = self.llm.chat(messages)
            elapsed = time.time() - start
            logger.info("LLM reply received in %.2fs", elapsed)
        except Exception as e:
            logger.exception("LLM call failed, using fallback")
            reply = "Sorry, I could not reach the LLM provider. Error: " + str(e)
        self.history.add("assistant", reply)
        return reply
'''

TEMPLATES["skills___init__py"] = '''"""
skills/__init__.py - BaseSkill interface and dynamic registry

This module provides:
- BaseSkill abstract class
- SkillRegistry to register and discover skills by scanning the skills directory
- A simple dynamic loader that imports skill modules by path and registers any BaseSkill subclasses
"""

import abc
import os
import sys
import logging
import importlib.util
from typing import Dict, Type, Optional, Any, List
from pathlib import Path

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

    @abc.abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def validate_params(self, params: Dict[str, Any]) -> bool:
        # Default: accept any params
        return True

class SkillRegistry:
    def __init__(self, skills_path: Optional[str] = None):
        self.skills: Dict[str, BaseSkill] = {}
        self.skills_path = skills_path or os.path.join(os.path.dirname(__file__), ".")
        self.discover_skills()

    def register(self, skill: BaseSkill):
        self.skills[skill.name] = skill

    def get(self, name: str) -> BaseSkill:
        if name not in self.skills:
            raise KeyError(f"Skill not found: {name}")
        return self.skills[name]

    def list_skills(self) -> List[str]:
        return list(self.skills.keys())

    def execute(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.get(name)
        if not skill.validate_params(params):
            raise ValueError("Invalid parameters for skill: " + name)
        return skill.execute(params)

    def discover_skills(self):
        """
        Attempts to load python modules in the skills directory and register any
        BaseSkill subclasses named '*Skill'.
        """
        skills_dir = Path(self.skills_path)
        if not skills_dir.exists():
            logger.warning("Skills directory does not exist: %s", skills_dir)
            return
        for py in skills_dir.glob("*.py"):
            if py.name == "__init__.py":
                continue
            try:
                spec = importlib.util.spec_from_file_location(py.stem, str(py))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                # Find classes that subclass BaseSkill
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    try:
                        if isinstance(obj, type) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            inst = obj()
                            self.register(inst)
                    except Exception:
                        continue
            except Exception as e:
                logger.exception("Failed to load skill module %s: %s", py, e)
'''

TEMPLATES["skills_ml_training.py"] = '''"""
ml_training.py - MLTrainingSkill stub

Simulates a recommender/training run and returns mock metrics.
"""

from typing import Dict, Any
from . import BaseSkill

class MLTrainingSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "ml_training"

    @property
    def description(self) -> str:
        return "Simulate ML training and return mock evaluation metrics."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Basic parameter handling
        rounds = int(params.get("rounds", 3))
        model = params.get("model", "sim-model")
        # Simulate training
        results = {
            "model": model,
            "rounds": rounds,
            "metrics": {
                "accuracy": 0.75 + 0.01 * rounds,
                "f1": 0.70 + 0.01 * rounds
            },
            "status": "ok"
        }
        return {"result": results}
'''

TEMPLATES["skills_text_analysis.py"] = '''"""
text_analysis.py - TextAnalysisSkill stub

Performs basic sentiment heuristics and length-based toxicity signaling.
"""

from typing import Dict, Any
from . import BaseSkill

class TextAnalysisSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "text_analysis"

    @property
    def description(self) -> str:
        return "Perform simple sentiment and toxicity checks."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("text", "")
        if not isinstance(text, str):
            return {"error": "text parameter required", "status": "error"}
        sentiment = "neutral"
        score = 0.0
        if any(w in text.lower() for w in ["good", "great", "excellent", "love"]):
            sentiment = "positive"; score = 0.8
        if any(w in text.lower() for w in ["bad", "terrible", "hate", "awful"]):
            sentiment = "negative"; score = -0.6
        toxicity = "low" if len(text) < 200 else "medium"
        return {"result": {"sentiment": sentiment, "score": score, "toxicity": toxicity}, "status": "ok"}
'''

TEMPLATES["skills_data_inspector.py"] = '''"""
data_inspector.py - DataInspectorSkill stub

Loads a CSV path (if provided) and returns simple statistics. If no file, returns
a sample mock profile.
"""

from typing import Dict, Any
from . import BaseSkill
import csv
import os
from statistics import mean, median

class DataInspectorSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "data_inspector"

    @property
    def description(self) -> str:
        return "Inspect CSV/JSON data and return basic summaries."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = params.get("path")
        if not path or not os.path.exists(path):
            # Return mock profile
            profile = {
                "rows": 100,
                "columns": ["id", "value", "timestamp"],
                "missing_values": {"value": 2},
                "stats": {"value": {"mean": 42.5, "median": 40}}
            }
            return {"result": profile, "status": "ok", "note": "mock profile (file not provided)"}
        # Minimal CSV numeric column analysis (first numeric column)
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            nums = []
            rows = 0
            for r in reader:
                rows += 1
                for v in r.values():
                    try:
                        nums.append(float(v))
                        break
                    except Exception:
                        continue
            stats = {"rows": rows}
            if nums:
                stats["mean"] = mean(nums)
                stats["median"] = median(nums)
            return {"result": stats, "status": "ok"}
'''

TEMPLATES["skills_code_generation.py"] = '''"""
code_generation.py - CodeGenerationSkill stub

Generates small Python code snippets or explains provided code.
"""

from typing import Dict, Any
from . import BaseSkill

class CodeGenerationSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "code_generation"

    @property
    def description(self) -> str:
        return "Generate simple Python snippets or explain code."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task = params.get("task", "hello_world")
        if task == "hello_world":
            code = "def greet(name):\\n    return f'Hello, {name}'\\n"
            return {"result": {"code": code}, "status": "ok"}
        if task == "explain":
            snippet = params.get("code", "print('hi')")
            explanation = f"This code prints a greeting: {snippet[:100]}"
            return {"result": {"explanation": explanation}, "status": "ok"}
        return {"error": "unknown task", "status": "error"}
'''

TEMPLATES["main.py"] = '''"""
main.py - Entry point and TUI launcher for neo-clone

Usage:
    python main.py [--config path] [--debug]

This script keeps top-level imports minimal to allow python -m py_compile
to succeed even when optional TUI dependency 'textual' is not installed.
"""

import argparse
import logging
import asyncio
import sys
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(prog="neo-clone", description="Neo-like TUI assistant (Python)")
    p.add_argument("--config", help="Path to config file (JSON)", default=None)
    p.add_argument("--debug", help="Enable debug logging", action="store_true")
    return p.parse_args()

def main():
    args = parse_args()
    # Lazy import utilities to avoid hard dependency during static checks
    from .utils import setup_logging, format_message
    from .config import load_config
    setup_logging(debug=args.debug)
    logger = logging.getLogger("neo.main")
    cfg = load_config(args.config)
    logger.info("Configuration loaded: provider=%s model=%s", cfg.provider, cfg.model_name)

    # Try to import textual for the TUI. If not available, provide CLI fallback.
    try:
        from textual.app import App, ComposeResult
        from textual.widgets import Header, Footer, TextArea, Static
        from textual.containers import Vertical
        from textual import events
    except Exception as e:
        logger.warning("Textual library not available. Running in simple CLI mode.")
        run_cli(cfg)
        return

    # Minimal Textual TUI implementation
    class ChatApp(App):
        CSS_PATH = None
        BINDINGS = [("c", "quit", "Quit"), ("l", "clear", "Clear")]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True, tall=False)
            yield Static("Welcome to Neo AI Assistant (Textual TUI). Type a message in the console fallback if TUI not working.", id="welcome")
            yield Footer()

        async def on_load(self, event) -> None:
            self.log("Neo TUI loaded")

    # Launch the TUI
    app = ChatApp()
    app.run()

def run_cli(cfg):
    """
    Simple synchronous CLI loop used when Textual is not present.
    Demonstrates end-to-end integration with the Brain without a TUI dependency.
    """
    from .brain import Brain, LLMClient
    from .skills import SkillRegistry
    brain = Brain(cfg, llm_client=LLMClient(cfg))
    skills = SkillRegistry(skills_path=str(Path(__file__).resolve().parent / "skills"))
    print("Neo CLI mode. Type 'exit' to quit. Type 'skills' to list skills.")
    while True:
        try:
            text = input("You> ").strip()
            if not text:
                continue
            if text.lower() in ("exit", "quit"):
                break
            if text.lower() == "skills":
                print("Available skills:", skills.list_skills())
                continue
            # Intent parse
            intent = brain.parse_intent(text)
            if intent.get("intent") == "skill" and intent.get("skill"):
                name = intent["skill"]
                print(f"Routing to skill: {name}")
                out = skills.execute(name, {"text": text, "task": "hello_world", "path": None})
                print("Skill result:", out)
            else:
                reply = brain.send_message(text)
                print("Neo>", reply)
        except KeyboardInterrupt:
            print("\\nExiting.")
            break
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()
'''

TEMPLATES["requirements.txt"] = """textual>=0.18.0
pydantic>=1.10.0
requests>=2.28.0
pyyaml>=6.0
typing-extensions>=4.0
"""

TEMPLATES["README.md"] = """# Neo-Clone (Python TUI Edition)

Overview
--------
Neo-Clone is a self-hosted, Python-based Terminal User Interface (TUI) assistant inspired by the opencode project.
This repository provides the foundational infrastructure: a reasoning 'brain', a modular skills framework, a
configuration layer, and a minimal TUI (Textual) or CLI fallback.

Quickstart (CLI fallback)
-------------------------
1. Install Python 3.9+
2. (Optional) pip install -r requirements.txt
3. Run: python main.py
   - If 'textual' is installed you get a TUI. Otherwise a CLI loop is used.

Configuration
-------------
Set environment variables or provide a JSON config:
- NEO_PROVIDER (default: 'ollama')
- NEO_MODEL (default: 'ggml-neural-chat')
- NEO_API_ENDPOINT (default: 'http://localhost:11434')

Skills
------
Skills are modular in the `skills/` directory. Implementations must subclass BaseSkill and will be auto-discovered.

Adding a skill:
- Create a .py file in skills/
- Define a class inheriting from BaseSkill implementing name, description, execute()

Architecture
------------
See ARCHITECTURE.md for a mapping between the Neo reasoning pipeline and the code base.

License & Notes
----------------
Educational/demo purpose. No production SLA. See ARCHITECTURE_ANALYSIS.md for notes from the opencode analysis.
"""

TEMPLATES["ARCHITECTURE.md"] = """ARCHITECTURE - Neo-Clone (Python TUI)

Data Flow (high-level)
- User input -> main.py (TUI/CLI) -> Brain.send_message()
- Brain maintains ConversationHistory, decides intent
- If skill intent: SkillRegistry executes the selected skill
- Otherwise Brain forwards conversation to LLM via LLMClient
- Response returned to TUI/CLI and displayed

Core Components
- main.py: entry point, TUI/CLI orchestration
- config.py: pydantic-based configuration loader
- brain.py: conversation/context management and LLM client
- skills/: modular skill implementations and registry
- utils.py: logging, helpers

Extensibility
- Add skills by creating a new .py under skills/ that defines a BaseSkill subclass.
- Swap LLM provider by changing provider and api_endpoint in config or environment.

Notes
- The project intentionally keeps LLM calls and heavy deps optional so tools like `python -m py_compile` work in environments without textual/torch installed.
"""

TEMPLATES["ARCHITECTURE_ANALYSIS.md"] = """OPENCODE REPOSITORY ANALYSIS (summary)

Files referenced from provided opencode repository:
- packages/console/core/src/model.ts
- infra/app.ts
- packages/console/app/src/app.tsx

Key architecture patterns observed and mapped to Python:
1. Provider Abstraction - opencode defines model/provider configuration centrally. We mirror this with config.py + LLMClient.
2. Skill Registration - opencode loads 'skills' (functions) and exposes them; we implement SkillRegistry to discover and register BaseSkill subclasses.
3. Client/Server separation - opencode uses a console client that talks to services; our Brain and LLMClient separate reasoning from UI.
4. Context management - opencode maintains message context; we implement ConversationHistory to manage a rolling window.
5. TUI Rendering - opencode uses a web-based console; we provide a Textual TUI and a CLI fallback for environments without graphical terminal libs.

This is a concise analysis focused on mapping core patterns to the Python code in this cycle.
"""

TEMPLATES["launch_windows.bat"] = r'''@echo off
REM launch_windows.bat - simple launcher for neo-clone (Windows)
SETLOCAL
python -c "import sys; print('Python', sys.version)"
IF %ERRORLEVEL% NEQ 0 (
  echo Python is not found in PATH. Please install Python 3.9+ and add to PATH.
  exit /b 1
)
REM Pass all args to main.py
python "%~dp0\main.py" %*
ENDLOCAL
'''

TEMPLATES["examples_sample_workflows.py"] = '''"""
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
'''

def safe_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(content)

def create_files():
    try:
        # Create project dir
        PROJECT_DIR.mkdir(parents=True, exist_ok=True)
        # __init__.py
        safe_write(PROJECT_DIR / "__init__.py", TEMPLATES["__init__"])
        # core files
        safe_write(PROJECT_DIR / "config.py", TEMPLATES["config.py"])
        safe_write(PROJECT_DIR / "utils.py", TEMPLATES["utils.py"])
        safe_write(PROJECT_DIR / "brain.py", TEMPLATES["brain.py"])
        safe_write(PROJECT_DIR / "main.py", TEMPLATES["main.py"])
        # skills package files (as files inside PROJECT_DIR/skills)
        skills_dir = PROJECT_DIR / "skills"
        skills_dir.mkdir(exist_ok=True)
        safe_write(skills_dir / "__init__.py", TEMPLATES["skills___init__py"])
        safe_write(skills_dir / "ml_training.py", TEMPLATES["skills_ml_training.py"])
        safe_write(skills_dir / "text_analysis.py", TEMPLATES["skills_text_analysis.py"])
        safe_write(skills_dir / "data_inspector.py", TEMPLATES["skills_data_inspector.py"])
        safe_write(skills_dir / "code_generation.py", TEMPLATES["skills_code_generation.py"])
        # docs and scripts
        safe_write(PROJECT_DIR / "requirements.txt", TEMPLATES["requirements.txt"])
        safe_write(PROJECT_DIR / "README.md", TEMPLATES["README.md"])
        safe_write(PROJECT_DIR / "ARCHITECTURE.md", TEMPLATES["ARCHITECTURE.md"])
        safe_write(PROJECT_DIR / "ARCHITECTURE_ANALYSIS.md", TEMPLATES["ARCHITECTURE_ANALYSIS.md"])
        safe_write(PROJECT_DIR / "launch_windows.bat", TEMPLATES["launch_windows.bat"])
        examples_dir = PROJECT_DIR / "examples"
        examples_dir.mkdir(exist_ok=True)
        safe_write(examples_dir / "sample_workflows.py", TEMPLATES["examples_sample_workflows.py"])
        print("Created neo-clone project at", PROJECT_DIR)
    except Exception as e:
        print("Failed to create files:", e)
        traceback.print_exc()
        sys.exit(1)

def smoke_tests():
    """
    Run small smoke tests:
    - py_compile each module
    - import config and create Config by loading module from file path
    - instantiate SkillRegistry and ensure skills found
    """
    import py_compile
    files = [
        PROJECT_DIR / "__init__.py",
        PROJECT_DIR / "config.py",
        PROJECT_DIR / "utils.py",
        PROJECT_DIR / "brain.py",
        PROJECT_DIR / "main.py",
        PROJECT_DIR / "skills" / "__init__.py",
        PROJECT_DIR / "skills" / "ml_training.py",
        PROJECT_DIR / "skills" / "text_analysis.py",
        PROJECT_DIR / "skills" / "data_inspector.py",
        PROJECT_DIR / "skills" / "code_generation.py",
    ]
    for f in files:
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            print("Compilation failed for", f)
            raise

    # Import modules by path using importlib
    try:
        import importlib.util
        # config
        cfg_path = PROJECT_DIR / "config.py"
        spec = importlib.util.spec_from_file_location("neo_config", str(cfg_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        Config = getattr(mod, "Config")
        cfg = Config()
        print("Config object created with defaults:", cfg.dict())

        # Load skills registry using dynamic loader
        skills_init = PROJECT_DIR / "skills" / "__init__.py"
        spec = importlib.util.spec_from_file_location("skills_pkg", str(skills_init))
        skills_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(skills_mod)
        SkillRegistry = getattr(skills_mod, "SkillRegistry")
        registry = SkillRegistry(skills_path=str(PROJECT_DIR / "skills"))
        print("Discovered skills:", registry.list_skills())

        # instantiate brain
        brain_path = PROJECT_DIR / "brain.py"
        spec = importlib.util.spec_from_file_location("brain_mod", str(brain_path))
        brain_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(brain_mod)
        Brain = getattr(brain_mod, "Brain")
        LLMClient = getattr(brain_mod, "LLMClient")
        llm = LLMClient(cfg)
        brain = Brain(cfg, llm_client=llm)
        print("Brain instance created. Conversation history length:", len(brain.history.to_list()))
    except Exception as e:
        print("Smoke test import failed:", e)
        traceback.print_exc()
        raise

def main():
    create_files()
    try:
        smoke_tests()
    except Exception as e:
        print("Smoke tests failed:", e)
        sys.exit(2)
    print("Bootstrap creation and smoke tests completed successfully.")
    # List created files for verification
    for p in sorted(PROJECT_DIR.rglob("*")):
        print(p.relative_to(PROJECT_DIR.parent))

if __name__ == "__main__":
    main()