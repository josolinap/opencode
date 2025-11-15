#!/usr/bin/env python3
"""
Comprehensive Model Database - 36+ Free AI Models

This module provides a comprehensive database of 36+ free AI models
from multiple providers including OpenRouter, Groq, Together, Replicate,
Ollama, HuggingFace, and more.

Author: Neo-Clone Enhanced
Version: 2.0
"""

import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Model provider types"""
    OPENROUTER = "openrouter"
    GROQ = "groq"
    TOGETHER = "together"
    REPLICATE = "replicate"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    OPENCODE = "opencode"
    LOCAL = "local"
    CUSTOM = "custom"

@dataclass
class ModelInfo:
    """Model information structure"""
    provider: str
    model_id: str
    name: str
    description: str
    capabilities: Dict[str, bool]
    limits: Dict[str, Any]
    pricing: Dict[str, Any]
    integration_score: float
    integration_ready: bool
    recommended_uses: List[str]
    integration_complexity: str
    release_date: Optional[str] = None
    model_size: Optional[str] = None
    quantization: Optional[str] = None

class ComprehensiveModelDatabase:
    """
    Comprehensive database of 36+ free AI models
    """
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self._initialize_model_database()
    
    def _initialize_model_database(self):
        """Initialize the comprehensive model database"""
        
        # OpenRouter Models
        openrouter_models = [
            {
                "model_id": "meta-llama/llama-3.2-3b-instruct:free",
                "name": "Llama 3.2 3B Instruct (Free)",
                "description": "Meta's Llama 3.2 3B parameter instruction-tuned model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "3B"
            },
            {
                "model_id": "meta-llama/llama-3.2-1b-instruct:free",
                "name": "Llama 3.2 1B Instruct (Free)",
                "description": "Meta's Llama 3.2 1B parameter instruction-tuned model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 2048},
                "model_size": "1B"
            },
            {
                "model_id": "microsoft/phi-3-mini-128k-instruct:free",
                "name": "Phi-3 Mini 128K Instruct (Free)",
                "description": "Microsoft's Phi-3 Mini with 128K context window",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 128000, "output": 4096},
                "model_size": "3.8B"
            },
            {
                "model_id": "google/gemma-2-9b-it:free",
                "name": "Gemma 2 9B Instruct (Free)",
                "description": "Google's Gemma 2 9B parameter instruction-tuned model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "9B"
            },
            {
                "model_id": "qwen/qwen-2.5-7b-instruct:free",
                "name": "Qwen 2.5 7B Instruct (Free)",
                "description": "Alibaba's Qwen 2.5 7B parameter instruction-tuned model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 8192},
                "model_size": "7B"
            }
        ]
        
        # Groq Models
        groq_models = [
            {
                "model_id": "llama-3.1-8b-instant",
                "name": "Llama 3.1 8B Instant",
                "description": "Meta's Llama 3.1 8B optimized for speed on Groq",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 131072, "output": 4096},
                "model_size": "8B"
            },
            {
                "model_id": "llama-3.2-3b-preview",
                "name": "Llama 3.2 3B Preview",
                "description": "Meta's Llama 3.2 3B preview on Groq",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 131072, "output": 4096},
                "model_size": "3B"
            },
            {
                "model_id": "llama-3.2-1b-preview",
                "name": "Llama 3.2 1B Preview",
                "description": "Meta's Llama 3.2 1B preview on Groq",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 131072, "output": 4096},
                "model_size": "1B"
            },
            {
                "model_id": "mixtral-8x7b-32768",
                "name": "Mixtral 8x7B 32K",
                "description": "Mistral's Mixtral 8x7B with 32K context on Groq",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 4096},
                "model_size": "8x7B"
            },
            {
                "model_id": "gemma2-9b-it",
                "name": "Gemma 2 9B IT",
                "description": "Google's Gemma 2 9B instruction-tuned on Groq",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "9B"
            }
        ]
        
        # Together AI Models
        together_models = [
            {
                "model_id": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                "name": "Llama 3.2 3B Instruct Turbo",
                "description": "Meta's Llama 3.2 3B optimized for speed on Together",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "3B"
            },
            {
                "model_id": "meta-llama/Llama-3.2-1B-Instruct-Turbo",
                "name": "Llama 3.2 1B Instruct Turbo",
                "description": "Meta's Llama 3.2 1B optimized for speed on Together",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 2048},
                "model_size": "1B"
            },
            {
                "model_id": "Qwen/Qwen2.5-7B-Instruct-Turbo",
                "name": "Qwen 2.5 7B Instruct Turbo",
                "description": "Alibaba's Qwen 2.5 7B optimized on Together",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 8192},
                "model_size": "7B"
            },
            {
                "model_id": "mistralai/Mistral-7B-Instruct-v0.2",
                "name": "Mistral 7B Instruct v0.2",
                "description": "Mistral's 7B instruction-tuned model on Together",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 4096},
                "model_size": "7B"
            },
            {
                "model_id": "google/gemma-2-9b-it",
                "name": "Gemma 2 9B IT",
                "description": "Google's Gemma 2 9B instruction-tuned on Together",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "9B"
            }
        ]
        
        # Replicate Models
        replicate_models = [
            {
                "model_id": "meta/meta-llama-3.1-8b-instruct",
                "name": "Llama 3.1 8B Instruct",
                "description": "Meta's Llama 3.1 8B on Replicate",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 131072, "output": 4096},
                "model_size": "8B"
            },
            {
                "model_id": "mistralai/mistral-7b-instruct-v0.2",
                "name": "Mistral 7B Instruct v0.2",
                "description": "Mistral's 7B instruction-tuned on Replicate",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 4096},
                "model_size": "7B"
            },
            {
                "model_id": "google/gemma-2-9b-it",
                "name": "Gemma 2 9B IT",
                "description": "Google's Gemma 2 9B on Replicate",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "9B"
            }
        ]
        
        # Ollama Models
        ollama_models = [
            {
                "model_id": "llama3.2:3b",
                "name": "Llama 3.2 3B",
                "description": "Meta's Llama 3.2 3B on Ollama",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "3B"
            },
            {
                "model_id": "llama3.2:1b",
                "name": "Llama 3.2 1B",
                "description": "Meta's Llama 3.2 1B on Ollama",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 2048},
                "model_size": "1B"
            },
            {
                "model_id": "qwen2.5:7b",
                "name": "Qwen 2.5 7B",
                "description": "Alibaba's Qwen 2.5 7B on Ollama",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 8192},
                "model_size": "7B"
            },
            {
                "model_id": "gemma2:9b",
                "name": "Gemma 2 9B",
                "description": "Google's Gemma 2 9B on Ollama",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "9B"
            },
            {
                "model_id": "mistral:7b",
                "name": "Mistral 7B",
                "description": "Mistral's 7B on Ollama",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 4096},
                "model_size": "7B"
            }
        ]
        
        # HuggingFace Models
        huggingface_models = [
            {
                "model_id": "microsoft/DialoGPT-medium",
                "name": "DialoGPT Medium",
                "description": "Microsoft's conversational GPT model",
                "capabilities": {
                    "reasoning": False,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 1024, "output": 512},
                "model_size": "345M"
            },
            {
                "model_id": "facebook/blenderbot-400M-distill",
                "name": "BlenderBot 400M Distill",
                "description": "Facebook's BlenderBot distilled version",
                "capabilities": {
                    "reasoning": False,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 128, "output": 128},
                "model_size": "400M"
            },
            {
                "model_id": "google/flan-t5-base",
                "name": "FLAN-T5 Base",
                "description": "Google's FLAN-T5 base model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 512, "output": 512},
                "model_size": "220M"
            }
        ]
        
        # Additional OpenCode Models (existing + new)
        opencode_models = [
            {
                "model_id": "big-pickle",
                "name": "Big Pickle",
                "description": "OpenCode's Big Pickle model for complex reasoning",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 200000, "output": 128000},
                "model_size": "Large"
            },
            {
                "model_id": "grok-code",
                "name": "Grok Code Fast 1",
                "description": "OpenCode's Grok Code model with multimodal capabilities",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": True
                },
                "limits": {"context": 256000, "output": 256000},
                "model_size": "Large"
            },
            {
                "model_id": "neo-clone-reasoner",
                "name": "Neo-Clone Reasoner",
                "description": "Neo-Clone's specialized reasoning model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 128000, "output": 64000},
                "model_size": "Medium"
            },
            {
                "model_id": "neo-clone-coder",
                "name": "Neo-Clone Coder",
                "description": "Neo-Clone's specialized code generation model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": True
                },
                "limits": {"context": 64000, "output": 32000},
                "model_size": "Medium"
            }
        ]
        
        # Custom/Community Models
        custom_models = [
            {
                "model_id": "deepseek-coder-6.7b-base",
                "name": "DeepSeek Coder 6.7B Base",
                "description": "DeepSeek's specialized code generation model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 16384, "output": 4096},
                "model_size": "6.7B"
            },
            {
                "model_id": "starcoder2-3b",
                "name": "StarCoder2 3B",
                "description": "BigCode's StarCoder2 3B code model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 16384, "output": 4096},
                "model_size": "3B"
            },
            {
                "model_id": "codegemma-7b",
                "name": "CodeGemma 7B",
                "description": "Google's CodeGemma 7B specialized for code",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "7B"
            }
        ]
        
        # Local Models
        local_models = [
            {
                "model_id": "local-llama-3.2-3b",
                "name": "Local Llama 3.2 3B",
                "description": "Locally hosted Llama 3.2 3B model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 4096},
                "model_size": "3B"
            },
            {
                "model_id": "local-phi-3-mini",
                "name": "Local Phi-3 Mini",
                "description": "Locally hosted Phi-3 Mini model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 4096, "output": 2048},
                "model_size": "3.8B"
            },
            {
                "model_id": "local-qwen-2.5-1.5b",
                "name": "Local Qwen 2.5 1.5B",
                "description": "Locally hosted Qwen 2.5 1.5B model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 32768, "output": 2048},
                "model_size": "1.5B"
            },
            {
                "model_id": "local-gemma-2-2b",
                "name": "Local Gemma 2 2B",
                "description": "Locally hosted Gemma 2 2B model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": True,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 8192, "output": 2048},
                "model_size": "2B"
            },
            {
                "model_id": "local-stablelm-2-1.6b",
                "name": "Local StableLM 2 1.6B",
                "description": "Locally hosted StableLM 2 1.6B model",
                "capabilities": {
                    "reasoning": True,
                    "tool_call": False,
                    "temperature": True,
                    "attachment": False
                },
                "limits": {"context": 4096, "output": 2048},
                "model_size": "1.6B"
            }
        ]
        
        # Process all models
        all_models = [
            (ProviderType.OPENROUTER.value, openrouter_models),
            (ProviderType.GROQ.value, groq_models),
            (ProviderType.TOGETHER.value, together_models),
            (ProviderType.REPLICATE.value, replicate_models),
            (ProviderType.OLLAMA.value, ollama_models),
            (ProviderType.HUGGINGFACE.value, huggingface_models),
            (ProviderType.OPENCODE.value, opencode_models),
            (ProviderType.CUSTOM.value, custom_models),
            (ProviderType.LOCAL.value, local_models)
        ]
        
        for provider, models in all_models:
            for model_data in models:
                model_info = ModelInfo(
                    provider=provider,
                    model_id=model_data["model_id"],
                    name=model_data["name"],
                    description=model_data["description"],
                    capabilities=model_data["capabilities"],
                    limits=model_data["limits"],
                    pricing={
                        "input": 0,
                        "output": 0,
                        "cache_read": 0,
                        "cache_write": 0,
                        "is_free": True,
                        "tier": "free"
                    },
                    integration_score=85.0,
                    integration_ready=True,
                    recommended_uses=[
                        "General conversation",
                        "Code generation",
                        "Text analysis",
                        "Problem solving",
                        "Content creation"
                    ],
                    integration_complexity="low",
                    model_size=model_data.get("model_size"),
                    quantization=model_data.get("quantization")
                )
                
                full_id = f"{provider}/{model_data['model_id']}"
                self.models[full_id] = model_info
        
        logger.info(f"Initialized comprehensive model database with {len(self.models)} models")
    
    def get_all_models(self) -> Dict[str, ModelInfo]:
        """Get all models in the database"""
        return self.models.copy()
    
    def get_models_by_provider(self, provider: str) -> Dict[str, ModelInfo]:
        """Get models by provider"""
        return {
            model_id: model_info 
            for model_id, model_info in self.models.items() 
            if model_info.provider == provider
        }
    
    def get_models_with_capability(self, capability: str) -> Dict[str, ModelInfo]:
        """Get models with specific capability"""
        return {
            model_id: model_info 
            for model_id, model_info in self.models.items() 
            if model_info.capabilities.get(capability, False)
        }
    
    def get_free_models_only(self) -> Dict[str, ModelInfo]:
        """Get only free models"""
        return {
            model_id: model_info 
            for model_id, model_info in self.models.items() 
            if model_info.pricing.get("is_free", False)
        }
    
    def get_model_count(self) -> int:
        """Get total model count"""
        return len(self.models)
    
    def get_provider_counts(self) -> Dict[str, int]:
        """Get model count by provider"""
        counts = {}
        for model_info in self.models.values():
            counts[model_info.provider] = counts.get(model_info.provider, 0) + 1
        return counts
    
    def export_to_cache_format(self) -> Dict:
        """Export models in cache format compatible with existing system"""
        models_list = []
        
        for model_info in self.models.values():
            model_dict = {
                "provider": model_info.provider,
                "model": model_info.model_id,
                "name": model_info.name,
                "cost": model_info.pricing,
                "capabilities": model_info.capabilities,
                "limits": model_info.limits,
                "release_date": model_info.release_date or "2024-01-01",
                "integration_score": model_info.integration_score,
                "integration_ready": model_info.integration_ready,
                "recommended_uses": model_info.recommended_uses,
                "integration_complexity": model_info.integration_complexity
            }
            
            if model_info.model_size:
                model_dict["model_size"] = model_info.model_size
            if model_info.quantization:
                model_dict["quantization"] = model_info.quantization
                
            models_list.append(model_dict)
        
        return {
            "models": models_list,
            "timestamp": datetime.now().timestamp(),
            "version": "2.0.0",
            "total_models": len(models_list)
        }

# Global instance
_comprehensive_db = None

def get_comprehensive_model_database() -> ComprehensiveModelDatabase:
    """Get singleton comprehensive model database instance"""
    global _comprehensive_db
    if _comprehensive_db is None:
        _comprehensive_db = ComprehensiveModelDatabase()
    return _comprehensive_db

def update_free_models_cache():
    """Update the free models cache with comprehensive database"""
    db = get_comprehensive_model_database()
    cache_data = db.export_to_cache_format()
    
    cache_file = "free_models_cache.json"
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    logger.info(f"Updated free models cache with {cache_data['total_models']} models")
    return cache_data

if __name__ == "__main__":
    # Test the database
    db = get_comprehensive_model_database()
    print(f"Total models: {db.get_model_count()}")
    print("Provider counts:", db.get_provider_counts())
    
    # Update cache
    update_free_models_cache()
    print("Cache updated successfully!")