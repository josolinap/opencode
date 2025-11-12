#!/usr/bin/env python3
"""
Model Discovery System for NEO-CLONE
Scans for free AI models, validates them, and integrates them seamlessly
"""

import json
import os
import time
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about a discovered AI model"""
    provider: str
    model_name: str
    api_endpoint: str
    api_key_required: bool = False
    context_length: int = 4096
    capabilities: Optional[List[str]] = None
    cost: str = "free"
    status: str = "unknown"  # unknown, testing, validated, failed
    response_time: float = 0.0
    error_message: str = ""

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["reasoning", "tool_calling"]

class ModelDiscovery:
    """System for discovering and validating AI models"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self.discovered_models: Dict[str, ModelInfo] = {}
        self.validated_models: Dict[str, ModelInfo] = {}

        # Known free model sources to scan
        self.model_sources = {
            "ollama": self._scan_ollama_models,
            "huggingface": self._scan_huggingface_models,
            "replicate": self._scan_replicate_models,
            "together": self._scan_together_free_models,
            "openai": self._scan_openai_free_models,
            "anthropic": self._scan_anthropic_free_models,
            "google": self._scan_google_free_models,
            "deepseek": self._scan_deepseek_models,
            "grok": self._scan_grok_models,
            "cohere": self._scan_cohere_models,
        }

    def _find_config_path(self) -> str:
        """Find the opencode.json config file"""
        current_dir = os.getcwd()
        for _ in range(10):
            config_path = os.path.join(current_dir, "opencode.json")
            if os.path.exists(config_path):
                return config_path
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir
        return "opencode.json"  # fallback

    def scan_all_sources(self) -> Dict[str, ModelInfo]:
        """Scan all known sources for free AI models"""
        logger.info("Starting comprehensive model discovery...")

        all_models = {}

        # Scan each source
        for source_name, scanner_func in self.model_sources.items():
            logger.info(f"Scanning {source_name}...")
            try:
                models = scanner_func()
                all_models.update(models)
                logger.info(f"Found {len(models)} models from {source_name}")
            except Exception as e:
                logger.warning(f"Failed to scan {source_name}: {e}")

        self.discovered_models = all_models
        logger.info(f"Total models discovered: {len(all_models)}")
        return all_models

    def _scan_ollama_models(self) -> Dict[str, ModelInfo]:
        """Scan for locally available Ollama models"""
        models = {}

        # Common Ollama models that might be available
        common_models = [
            "llama2", "llama2:13b", "llama2:70b",
            "codellama", "codellama:13b", "codellama:34b",
            "mistral", "mixtral",
            "neural-chat", "ggml-neural-chat",
            "orca-mini", "vicuna",
            "openchat", "zephyr"
        ]

        for model in common_models:
            models[f"ollama/{model}"] = ModelInfo(
                provider="ollama",
                model_name=model,
                api_endpoint="http://localhost:11434",
                context_length=4096,
                capabilities=["reasoning", "tool_calling", "code_generation"]
            )

        return models

    def _scan_huggingface_models(self) -> Dict[str, ModelInfo]:
        """Scan for free HuggingFace models"""
        models = {}

        # Free inference API models
        free_models = [
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "google/flan-t5-base",
            "microsoft/DialoGPT-small"
        ]

        for model in free_models:
            model_id = model.replace("/", "-")
            models[f"huggingface/{model_id}"] = ModelInfo(
                provider="huggingface",
                model_name=model,
                api_endpoint="https://api-inference.huggingface.co/models",
                api_key_required=True,  # Free tier available
                context_length=1024,
                capabilities=["reasoning"]
            )

        return models

    def _scan_replicate_models(self) -> Dict[str, ModelInfo]:
        """Scan for free Replicate models"""
        models = {}

        # Popular free models on Replicate
        free_models = [
            "meta/llama-2-7b-chat",
            "microsoft/wizardlm-2-8x22b",
            "mistralai/mistral-7b-instruct-v0.1"
        ]

        for model in free_models:
            model_id = model.replace("/", "-")
            models[f"replicate/{model_id}"] = ModelInfo(
                provider="replicate",
                model_name=model,
                api_endpoint="https://api.replicate.com/v1",
                api_key_required=True,
                context_length=4096,
                capabilities=["reasoning", "tool_calling"]
            )

        return models

    def _scan_together_free_models(self) -> Dict[str, ModelInfo]:
        """Scan for free Together.ai models"""
        models = {}

        # Free tier models
        free_models = [
            "togethercomputer/RedPajama-INCITE-7B-Chat",
            "togethercomputer/llama-2-7b-chat",
            "togethercomputer/mistral-7b-instruct-v0.1"
        ]

        for model in free_models:
            model_id = model.replace("/", "-")
            models[f"together/{model_id}"] = ModelInfo(
                provider="together",
                model_name=model,
                api_endpoint="https://api.together.xyz/v1",
                api_key_required=True,
                context_length=4096,
                capabilities=["reasoning", "tool_calling"]
            )

        return models

    def _scan_openai_free_models(self) -> Dict[str, ModelInfo]:
        """Scan for any free OpenAI models/tier"""
        models = {}

        # Note: OpenAI doesn't have truly free models, but they might have free tiers
        # This is more for completeness
        free_models = [
            "gpt-3.5-turbo",  # If free credits available
        ]

        for model in free_models:
            models[f"openai/{model}"] = ModelInfo(
                provider="openai",
                model_name=model,
                api_endpoint="https://api.openai.com/v1",
                api_key_required=True,
                context_length=16384,
                capabilities=["reasoning", "tool_calling", "code_generation"],
                cost="free_tier"
            )

        return models

    def _scan_anthropic_free_models(self) -> Dict[str, ModelInfo]:
        """Scan for free Anthropic models"""
        models = {}

        # Claude models (if free tier exists)
        free_models = [
            "claude-3-haiku",  # If free tier available
        ]

        for model in free_models:
            models[f"anthropic/{model}"] = ModelInfo(
                provider="anthropic",
                model_name=model,
                api_endpoint="https://api.anthropic.com/v1",
                api_key_required=True,
                context_length=200000,
                capabilities=["reasoning", "tool_calling", "code_generation"],
                cost="free_tier"
            )

        return models

    def _scan_google_free_models(self) -> Dict[str, ModelInfo]:
        """Scan for free Google AI models"""
        models = {}

        # Free Google AI models
        free_models = [
            "gemini-pro",
            "gemini-1.5-flash",
            "palm-2"
        ]

        for model in free_models:
            models[f"google/{model}"] = ModelInfo(
                provider="google",
                model_name=model,
                api_endpoint="https://generativelanguage.googleapis.com/v1beta",
                api_key_required=True,
                context_length=32768,
                capabilities=["reasoning", "tool_calling", "code_generation"],
                cost="free_tier"
            )

        return models

    def _scan_deepseek_models(self) -> Dict[str, ModelInfo]:
        """Scan for DeepSeek models"""
        models = {}

        # DeepSeek free models
        free_models = [
            "deepseek-chat",
            "deepseek-coder"
        ]

        for model in free_models:
            models[f"deepseek/{model}"] = ModelInfo(
                provider="deepseek",
                model_name=model,
                api_endpoint="https://api.deepseek.com/v1",
                api_key_required=True,
                context_length=32768,
                capabilities=["reasoning", "tool_calling", "code_generation"],
                cost="free_tier"
            )

        return models

    def _scan_grok_models(self) -> Dict[str, ModelInfo]:
        """Scan for Grok models"""
        models = {}

        # Grok free models
        free_models = [
            "grok-1",
            "grok-beta"
        ]

        for model in free_models:
            models[f"grok/{model}"] = ModelInfo(
                provider="grok",
                model_name=model,
                api_endpoint="https://api.x.ai/v1",
                api_key_required=True,
                context_length=128000,
                capabilities=["reasoning", "tool_calling", "code_generation"],
                cost="free_tier"
            )

        return models

    def _scan_cohere_models(self) -> Dict[str, ModelInfo]:
        """Scan for Cohere models"""
        models = {}

        # Cohere free models
        free_models = [
            "command",
            "command-light",
            "base"
        ]

        for model in free_models:
            models[f"cohere/{model}"] = ModelInfo(
                provider="cohere",
                model_name=model,
                api_endpoint="https://api.cohere.ai/v1",
                api_key_required=True,
                context_length=4096,
                capabilities=["reasoning", "tool_calling"],
                cost="free_tier"
            )

        return models

    def validate_models(self, models: Optional[Dict[str, ModelInfo]] = None,
                       max_workers: int = 3) -> Dict[str, ModelInfo]:
        """Validate discovered models by testing them"""
        if models is None:
            models = self.discovered_models

        logger.info(f"Starting validation of {len(models)} models...")

        validated = {}

        # Test models in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_model = {
                executor.submit(self._test_model, model_id, model_info): (model_id, model_info)
                for model_id, model_info in models.items()
            }

            for future in as_completed(future_to_model):
                model_id, model_info = future_to_model[future]
                try:
                    is_valid, response_time, error = future.result()
                    if is_valid:
                        model_info.status = "validated"
                        model_info.response_time = response_time
                        validated[model_id] = model_info
                        logger.info(f"[VALID] {model_id} - {response_time:.2f}s")
                    else:
                        model_info.status = "failed"
                        model_info.error_message = error
                        logger.warning(f"[FAILED] {model_id} - {error}")
                except Exception as e:
                    logger.error(f"Error validating {model_id}: {e}")

        self.validated_models = validated
        logger.info(f"Validation complete: {len(validated)}/{len(models)} models validated")
        return validated

    def _test_model(self, model_id: str, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test a single model to see if it's working"""
        start_time = time.time()

        try:
            if model_info.provider == "ollama":
                return self._test_ollama_model(model_info)
            elif model_info.provider == "huggingface":
                return self._test_huggingface_model(model_info)
            elif model_info.provider == "replicate":
                return self._test_replicate_model(model_info)
            elif model_info.provider == "together":
                return self._test_together_model(model_info)
            elif model_info.provider == "deepseek":
                return self._test_deepseek_model(model_info)
            elif model_info.provider == "grok":
                return self._test_grok_model(model_info)
            elif model_info.provider == "cohere":
                return self._test_cohere_model(model_info)
            else:
                # For other providers, just check if endpoint is reachable
                response = requests.get(model_info.api_endpoint.rstrip("/api/chat").rstrip("/v1"),
                                      timeout=5)
                response_time = time.time() - start_time
                return response.status_code == 200, response_time, ""

        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)

    def _test_ollama_model(self, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test Ollama model availability"""
        start_time = time.time()

        try:
            # Try to get model info
            response = requests.get(f"{model_info.api_endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_exists = any(m["name"] == model_info.model_name for m in models)
                if model_exists:
                    response_time = time.time() - start_time
                    return True, response_time, ""
                else:
                    return False, time.time() - start_time, "Model not available locally"
            else:
                return False, time.time() - start_time, f"HTTP {response.status_code}"
        except Exception as e:
            return False, time.time() - start_time, str(e)

    def _test_huggingface_model(self, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test HuggingFace model (simplified check)"""
        start_time = time.time()

        try:
            # Just check if the model page exists
            model_path = model_info.model_name.replace("/", "/")
            response = requests.get(f"https://huggingface.co/{model_path}", timeout=5)
            response_time = time.time() - start_time
            return response.status_code == 200, response_time, ""
        except Exception as e:
            return False, time.time() - start_time, str(e)

    def _test_replicate_model(self, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test Replicate model (simplified check)"""
        start_time = time.time()

        try:
            # Check if model exists on Replicate
            response = requests.get(f"https://replicate.com/{model_info.model_name}", timeout=5)
            response_time = time.time() - start_time
            return response.status_code == 200, response_time, ""
        except Exception as e:
            return False, time.time() - start_time, str(e)

    def _test_together_model(self, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test Together.ai model (simplified check)"""
        start_time = time.time()

        try:
            # Just check API endpoint responsiveness
            response = requests.get("https://api.together.xyz/models", timeout=5)
            response_time = time.time() - start_time
            return response.status_code == 200, response_time, ""
        except Exception as e:
            return False, time.time() - start_time, str(e)

    def _test_deepseek_model(self, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test DeepSeek model (simplified check)"""
        start_time = time.time()

        try:
            # Check if API endpoint is reachable
            response = requests.get("https://api.deepseek.com/v1/models", timeout=5)
            response_time = time.time() - start_time
            return response.status_code == 200, response_time, ""
        except Exception as e:
            return False, time.time() - start_time, str(e)

    def _test_grok_model(self, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test Grok model (simplified check)"""
        start_time = time.time()

        try:
            # Check if API endpoint is reachable
            response = requests.get("https://api.x.ai/v1/models", timeout=5)
            response_time = time.time() - start_time
            return response.status_code == 200, response_time, ""
        except Exception as e:
            return False, time.time() - start_time, str(e)

    def _test_cohere_model(self, model_info: ModelInfo) -> Tuple[bool, float, str]:
        """Test Cohere model (simplified check)"""
        start_time = time.time()

        try:
            # Check if API endpoint is reachable
            response = requests.get("https://api.cohere.ai/v1/models", timeout=5)
            response_time = time.time() - start_time
            return response.status_code == 200, response_time, ""
        except Exception as e:
            return False, time.time() - start_time, str(e)

    def add_to_config(self, models: Optional[Dict[str, ModelInfo]] = None) -> bool:
        """Add validated models to the opencode.json configuration"""
        if models is None:
            models = self.validated_models

        try:
            # Load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {"models": {}}

            # Add validated models
            if "models" not in config:
                config["models"] = {}

            for model_id, model_info in models.items():
                if model_info.status == "validated":
                    config["models"][model_id] = {
                        "provider": model_info.provider,
                        "model": model_info.model_name,
                        "endpoint": model_info.api_endpoint,
                        "context_length": model_info.context_length,
                        "capabilities": model_info.capabilities,
                        "cost": model_info.cost,
                        "response_time": model_info.response_time
                    }

            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Added {len(models)} validated models to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False

    def get_best_model(self, required_capabilities: Optional[List[str]] = None) -> Optional[ModelInfo]:
        """Get the best available model based on capabilities and performance"""
        if not self.validated_models:
            return None

        if required_capabilities is None:
            required_capabilities = ["reasoning"]

        # Filter models that have required capabilities
        suitable_models = []
        for model_info in self.validated_models.values():
            if model_info.capabilities and all(cap in model_info.capabilities for cap in required_capabilities):
                suitable_models.append(model_info)

        if not suitable_models:
            return None

        # Sort by response time (fastest first)
        suitable_models.sort(key=lambda m: m.response_time)

        return suitable_models[0]

    def auto_discover_and_integrate(self) -> Dict[str, ModelInfo]:
        """Complete workflow: discover, validate, and integrate models"""
        logger.info("Starting automatic model discovery and integration...")

        # 1. Discover models
        discovered = self.scan_all_sources()

        # 2. Validate models
        validated = self.validate_models(discovered)

        # 3. Add to config
        if validated:
            self.add_to_config(validated)

        # 4. Report results
        logger.info("=== Model Discovery Results ===")
        logger.info(f"Discovered: {len(discovered)} models")
        logger.info(f"Validated: {len(validated)} models")

        if validated:
            logger.info("Successfully integrated models:")
            for model_id, model_info in validated.items():
                logger.info(f"  - {model_id} ({model_info.response_time:.2f}s)")

        return validated