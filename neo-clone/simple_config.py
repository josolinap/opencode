"""
Simple configuration for Neo-Clone testing
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    provider: str = "ollama"
    model_name: str = "llama3.2:latest"
    api_endpoint: str = "http://localhost:11434"
    max_tokens: int = 1000
    temperature: float = 0.7


def load_config(config_path=None):
    """Load configuration from file or return defaults"""
    return Config()
