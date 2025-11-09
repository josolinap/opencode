"""
utils.py - helper utilities for neo-clone

Includes:
- Logging setup (with StreamHandler for sys.stdout)
- Message formatting (role+prefix)
- Text truncation
- Safe JSON loading
- Simple token (character) counting and truncation
- Error handling/logging wrapper
- Optional: prompt template loader
"""

import logging
import sys
import json
from typing import Any, Optional
import os
from pathlib import Path

def setup_logging(debug: bool = False):
    """Setup logging to stdout. Debug enables more verbose output."""
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, handlers=[handler])

def format_message(role: str, content: str) -> str:
    """Format a message from a user or the AI with a simple role prefix."""
    return f"[{role}] {content}"

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to a given length."""
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."

def count_tokens(text: str) -> int:
    """Very basic token count (by whitespace or chars) for demo purposes."""
    return len(text.split())

def truncate_tokens(text: str, max_tokens: int = 200) -> str:
    """Truncate to N tokens (whitespace) for local models."""
    toks = text.split()
    if len(toks) <= max_tokens:
        return text
    return " ".join(toks[:max_tokens])

def validate_json(text: str) -> Optional[Any]:
    """Safely parse JSON, returning None if error."""
    try:
        return json.loads(text)
    except Exception:
        return None

def read_json(path: str):
    """Read a JSON file safely."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str, data):
    """Write a JSON file safely, creating parent dirs."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def error_wrap(func):
    """Decorator: log and reraise errors from wrapped function."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

def load_prompt_template(name: str, template_dir: str = "prompts"):
    """
    Load a prompt template (e.g., system_prompt.txt) from a directory.
    Returns the string or empty string.
    """
    try:
        path = Path(template_dir) / name
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""