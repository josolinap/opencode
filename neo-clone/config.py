"""
Configuration management for neo-clone.

Provider abstraction pattern:
- provider: "ollama" (default, local, no key), "hf" (local transformers), or "api" (cloud/free tier)
- model_name: string identifier for the LLM to use
- api_endpoint: URL for Ollama or API-based models
- api_key: key for Together.ai or other paid/free APIs (not needed for Ollama/hf)
- max_tokens, temperature: model generation parameters
- system_prompt: optional startup/system prompt
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

class Config(BaseModel):
    provider: str = Field("ollama", description="LLM provider: 'ollama'|'hf'|'api'")
    model_name: str = Field("ggml-neural-chat", description="Default model, e.g. for Ollama or HF")
    api_endpoint: Optional[str] = Field("http://localhost:11434", description="API endpoint (for local Ollama, etc.)")
    api_key: Optional[str] = Field(None, description="API key if provider requires one (Together.ai, etc.)")
    max_tokens: int = Field(1024, description="Maximum tokens for model response")
    temperature: float = Field(0.2, description="Generation temperature (0.0 - 2.0)")
    system_prompt: Optional[str] = Field(None, description="Optional prompt for LLM")

    @validator("temperature")
    def check_temperature(cls, v):
        if not (0.0 <= v <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v

def load_config(path: Optional[str] = None) -> Config:
    """
    Load configuration from opencode.json, JSON file, or environment variables.
    Precedence: passed-in path > opencode.json > NEOCONFIG env var > defaults
    """
    try:
        # First try passed-in path
        cfg_path = path or os.getenv("NEOCONFIG")
        if cfg_path and os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded configuration from {cfg_path}")
            return Config(**data)

        # Try to read from opencode.json in current or parent directories
        opencode_config = None
        current_dir = os.getcwd()
        for _ in range(10):  # Check up to 10 levels up
            opencode_path = os.path.join(current_dir, "opencode.json")
            if os.path.exists(opencode_path):
                try:
                    with open(opencode_path, "r", encoding="utf-8") as f:
                        opencode_config = json.load(f)
                    logger.info(f"Loaded model configuration from {opencode_path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to parse opencode.json: {e}")
                    break
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir

        # Build config from opencode.json and environment variables
        env = {
            "provider": os.getenv("NEO_PROVIDER", "ollama"),
            "model_name": os.getenv("NEO_MODEL", "ggml-neural-chat"),
            "api_endpoint": os.getenv("NEO_API_ENDPOINT", "http://localhost:11434"),
            "api_key": os.getenv("NEO_API_KEY", None),
            "max_tokens": int(os.getenv("NEO_MAX_TOKENS", "1024")),
            "temperature": float(os.getenv("NEO_TEMPERATURE", "0.2")),
            "system_prompt": os.getenv("NEO_SYSTEM_PROMPT", None),
        }

        # Override with opencode.json model settings if available
        if opencode_config and "model" in opencode_config:
            model_spec = opencode_config["model"]
            if "/" in model_spec:
                provider, model = model_spec.split("/", 1)
                env["provider"] = provider
                env["model_name"] = model
                logger.info(f"Using model from opencode.json: {provider}/{model}")

        logger.info("Loaded configuration from opencode.json/environment/defaults")
        return Config(**env)
    except Exception as e:
        logger.exception("Failed to load config")
        raise