#!/usr/bin/env python3
"""
Model Discovery Module - Dynamic AI Model Selection and Integration

This module provides intelligent model discovery, registry management, and orchestration
capabilities for the MiniMax Agent architecture. It seamlessly integrates with both
free and paid models while maintaining provider-agnostic flexibility.

Key Features:
- Dynamic model discovery from multiple providers
- Intelligent model selection based on task requirements  
- Model registry with comprehensive metadata
- Multi-model orchestration and switching
- Real-time monitoring and health checks
- Integration scoring system (0-100%)
- Enhanced Brain integration

Author: MiniMax Agent
Created: 2025-11-13
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model availability status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class CapabilityType(Enum):
    """Supported model capabilities"""
    REASONING = "reasoning"
    TOOL_CALLING = "tool_calling"
    TEMPERATURE = "temperature"
    ATTACHMENTS = "attachments"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    MULTIMODAL = "multimodal"
    FINE_TUNED = "fine_tuned"
    REALTIME = "realtime"


class ProviderType(Enum):
    """Supported model provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"
    OPENCODE = "opencode"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    TOGETHER = "together"
    CUSTOM = "custom"


@dataclass
class ModelCapabilities:
    """Model capabilities configuration"""
    reasoning: bool = False
    tool_calling: bool = False
    temperature: bool = False
    attachments: bool = False
    streaming: bool = False
    function_calling: bool = False
    vision: bool = False
    multimodal: bool = False
    fine_tuned: bool = False
    realtime: bool = False

    def __post_init__(self):
        """Validate capabilities consistency"""
        if self.vision and not self.multimodal:
            self.multimodal = True
        if self.function_calling and not self.tool_calling:
            self.tool_calling = True

    def to_dict(self) -> Dict[str, bool]:
        """Convert capabilities to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> 'ModelCapabilities':
        """Create capabilities from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ModelLimits:
    """Model usage limits and constraints"""
    context_tokens: int = 8192
    output_tokens: int = 4096
    requests_per_minute: int = 60
    requests_per_day: int = 1000
    max_file_size_mb: int = 50
    custom_limits: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert limits to dictionary"""
        return asdict(self)


@dataclass
class ModelPricing:
    """Model pricing information"""
    cost_per_token: float = 0.0
    cost_per_request: float = 0.0
    monthly_limit: Optional[float] = None
    currency: str = "USD"
    is_free: bool = True
    provider_subsidized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert pricing to dictionary"""
        return asdict(self)


@dataclass
class ModelMetadata:
    """Comprehensive model metadata"""
    name: str
    provider: str
    version: str = "1.0"
    description: str = ""
    release_date: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    github_url: Optional[str] = None
    paper_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        data = asdict(self)
        data['release_date'] = self.release_date.isoformat() if self.release_date else None
        data['last_updated'] = self.last_updated.isoformat()
        return data


@dataclass
class ModelHealth:
    """Model health and monitoring information"""
    status: ModelStatus = ModelStatus.AVAILABLE
    response_time_ms: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    last_check: datetime = field(default_factory=datetime.now)
    health_score: float = 1.0
    maintenance_window: Optional[datetime] = None
    api_version: str = "v1"

    def to_dict(self) -> Dict[str, Any]:
        """Convert health to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_check'] = self.last_check.isoformat()
        data['maintenance_window'] = self.maintenance_window.isoformat() if self.maintenance_window else None
        return data


@dataclass
class ModelEntry:
    """Complete model entry with all information"""
    model_id: str
    provider: str
    name: str
    capabilities: ModelCapabilities
    limits: ModelLimits
    pricing: ModelPricing
    metadata: ModelMetadata
    health: ModelHealth = field(default_factory=ModelHealth)
    integration_score: float = 0.0
    
    def __post_init__(self):
        """Calculate integration score after initialization"""
        self.integration_score = self.calculate_integration_score()

    def calculate_integration_score(self) -> float:
        """Calculate model integration readiness score (0-100%)"""
        score = 0.0
        
        # Capability matching (45 points)
        cap_score = 0
        total_caps = len(ModelCapabilities.__annotations__)
        for cap, enabled in self.capabilities.to_dict().items():
            if enabled:
                cap_score += 1
        capability_score = (cap_score / total_caps) * 45
        score += capability_score
        
        # Context length (15 points)
        if self.limits.context_tokens >= 200000:
            score += 15
        elif self.limits.context_tokens >= 100000:
            score += 10
        elif self.limits.context_tokens >= 50000:
            score += 5
        
        # Provider bonus (25 points)
        if self.provider.lower() == "opencode":
            score += 25  # Full bonus for opencode provider
        elif self.provider.lower() in ["openai", "anthropic", "google"]:
            score += 20  # Major provider bonus
        elif self.provider.lower() in ["huggingface", "groq", "together"]:
            score += 15  # Good provider bonus
        
        # Integration ready (10 points)
        if self.health.status == ModelStatus.AVAILABLE:
            score += 10
        elif self.health.status == ModelStatus.EXPERIMENTAL:
            score += 5
        
        # Pricing bonus (5 points)
        if self.pricing.is_free:
            score += 5
        elif self.pricing.cost_per_token < 0.01:
            score += 3
        
        # Experimental penalty (-10 points)
        if self.health.status == ModelStatus.EXPERIMENTAL:
            score -= 10
        
        return min(100.0, max(0.0, score))

    def get_full_id(self) -> str:
        """Get the full model identifier (provider/model)"""
        return f"{self.provider}/{self.model_id}"

    def is_suitable_for_task(self, task_requirements: Dict[str, Any]) -> bool:
        """Check if model is suitable for specific task requirements"""
        required_caps = task_requirements.get('capabilities', [])
        max_cost = task_requirements.get('max_cost_per_token', float('inf'))
        min_context = task_requirements.get('min_context_tokens', 0)
        prefer_free = task_requirements.get('prefer_free', False)
        
        # Check capabilities
        caps_dict = self.capabilities.to_dict()
        for cap in required_caps:
            if not caps_dict.get(cap, False):
                return False
        
        # Check cost
        if self.pricing.cost_per_token > max_cost:
            return False
        
        # Check context
        if self.limits.context_tokens < min_context:
            return False
        
        # Check free preference
        if prefer_free and not self.pricing.is_free:
            return False
        
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert model entry to dictionary"""
        return {
            'model_id': self.model_id,
            'provider': self.provider,
            'name': self.name,
            'full_id': self.get_full_id(),
            'capabilities': self.capabilities.to_dict(),
            'limits': self.limits.to_dict(),
            'pricing': self.pricing.to_dict(),
            'metadata': self.metadata.to_dict(),
            'health': self.health.to_dict(),
            'integration_score': self.integration_score,
            'suitable_for': []  # Will be populated by discovery engine
        }


class ModelRegistry:
    """Central registry for all available models"""
    
    def __init__(self):
        self._models: Dict[str, ModelEntry] = {}
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._cache: Dict[str, Any] = {}
        self._last_cache_update = None
        self._cache_duration = timedelta(hours=1)
        
    def register_model(self, model: ModelEntry) -> None:
        """Register a new model in the registry"""
        self._models[model.get_full_id()] = model
        logger.info(f"Registered model: {model.get_full_id()}")
    
    def unregister_model(self, model_id: str) -> bool:
        """Unregister a model from the registry"""
        if model_id in self._models:
            del self._models[model_id]
            logger.info(f"Unregistered model: {model_id}")
            return True
        return False
    
    def get_model(self, model_id: str) -> Optional[ModelEntry]:
        """Get model by full identifier"""
        return self._models.get(model_id)
    
    def list_models(self, 
                   provider: Optional[str] = None,
                   status: Optional[ModelStatus] = None,
                   min_score: float = 0.0,
                   free_only: bool = False,
                   capabilities: Optional[List[str]] = None) -> List[ModelEntry]:
        """List models with filtering options"""
        models = []
        
        for model in self._models.values():
            # Apply filters
            if provider and model.provider.lower() != provider.lower():
                continue
            
            if status and model.health.status != status:
                continue
            
            if model.integration_score < min_score:
                continue
            
            if free_only and not model.pricing.is_free:
                continue
            
            if capabilities:
                caps_dict = model.capabilities.to_dict()
                if not all(caps_dict.get(cap, False) for cap in capabilities):
                    continue
            
            models.append(model)
        
        return sorted(models, key=lambda m: m.integration_score, reverse=True)
    
    def get_free_models(self) -> List[ModelEntry]:
        """Get all free models"""
        return self.list_models(free_only=True)
    
    def get_models_by_capability(self, capability: CapabilityType) -> List[ModelEntry]:
        """Get models with specific capability"""
        return self.list_models(capabilities=[capability.value])
    
    def get_healthy_models(self) -> List[ModelEntry]:
        """Get all healthy models"""
        return self.list_models(status=ModelStatus.AVAILABLE)
    
    def get_provider_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics by provider"""
        stats = {}
        for model in self._models.values():
            provider = model.provider.lower()
            if provider not in stats:
                stats[provider] = {
                    'total': 0,
                    'free': 0,
                    'available': 0,
                    'experimental': 0
                }
            
            stats[provider]['total'] += 1
            if model.pricing.is_free:
                stats[provider]['free'] += 1
            if model.health.status == ModelStatus.AVAILABLE:
                stats[provider]['available'] += 1
            if model.health.status == ModelStatus.EXPERIMENTAL:
                stats[provider]['experimental'] += 1
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear the registry cache"""
        self._cache.clear()
        self._last_cache_update = None


class ModelDiscoveryEngine:
    """Engine for discovering and monitoring available models"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self._discovery_sources = {}
        self._monitoring_enabled = True
        self._last_discovery = None
        self._discovery_interval = timedelta(hours=6)
        
    def register_discovery_source(self, name: str, source_func: callable) -> None:
        """Register a new model discovery source"""
        self._discovery_sources[name] = source_func
        logger.info(f"Registered discovery source: {name}")
    
    async def discover_all_models(self) -> Dict[str, List[ModelEntry]]:
        """Discover models from all registered sources"""
        results = {}
        discovered_count = 0
        
        logger.info("Starting model discovery from all sources...")
        
        # Run all discovery sources concurrently using asyncio.gather
        tasks = {}
        for source_name, source_func in self._discovery_sources.items():
            tasks[source_name] = source_func()
        
        try:
            # Execute all discovery functions concurrently
            discovery_results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            # Process results
            for (source_name, source_func), result in zip(tasks.items(), discovery_results):
                if isinstance(result, Exception):
                    logger.error(f"Error discovering models from {source_name}: {result}")
                    results[source_name] = []
                else:
                    models = result
                    results[source_name] = models
                    discovered_count += len(models)
                    
                    # Register discovered models
                    for model in models:
                        self.registry.register_model(model)
                    
                    logger.info(f"Discovered {len(models)} models from {source_name}")
        
        except Exception as e:
            logger.error(f"Error in model discovery: {e}")
        
        self._last_discovery = datetime.now()
        logger.info(f"Total discovered models: {discovered_count}")
        return results
    
    async def update_model_health(self, model_id: str) -> ModelHealth:
        """Update health status for a specific model"""
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        # This would typically make an actual API call to check model health
        # For now, simulate health check
        health = model.health
        health.last_check = datetime.now()
        health.response_time_ms = 150.0  # Simulated
        health.success_rate = 0.98  # Simulated
        
        return health
    
    async def monitor_all_models(self) -> Dict[str, ModelHealth]:
        """Monitor health of all registered models"""
        logger.info("Starting health monitoring for all models...")
        health_status = {}
        
        # Get all model IDs
        model_ids = list(self.registry._models.keys())
        
        if not model_ids:
            logger.info("No models to monitor")
            return health_status
        
        # Create monitoring tasks
        tasks = {}
        for model_id in model_ids:
            tasks[model_id] = self.update_model_health(model_id)
        
        try:
            # Execute all monitoring tasks concurrently
            monitoring_results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            # Process results
            for (model_id, task), result in zip(tasks.items(), monitoring_results):
                if isinstance(result, Exception):
                    logger.error(f"Error monitoring {model_id}: {result}")
                    health_status[model_id] = ModelHealth(status=ModelStatus.UNAVAILABLE)
                else:
                    health = result
                    health_status[model_id] = health
                    model = self.registry.get_model(model_id)
                    if model:
                        model.health = health
        
        except Exception as e:
            logger.error(f"Error in health monitoring: {e}")
        
        return health_status
    
    def should_refresh_discovery(self) -> bool:
        """Check if discovery should be refreshed"""
        if not self._last_discovery:
            return True
        return datetime.now() - self._last_discovery > self._discovery_interval


class ModelSelector:
    """Intelligent model selection based on task requirements"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
    
    async def select_best_model(self, 
                               task_requirements: Dict[str, Any],
                               fallback_models: Optional[List[str]] = None) -> Optional[ModelEntry]:
        """Select the best model for given task requirements"""
        
        # Get candidate models
        candidates = self.registry.list_models(
            status=ModelStatus.AVAILABLE,
            min_score=50.0  # Only consider reasonably well-integrated models
        )
        
        # Filter by task requirements
        suitable_models = []
        for model in candidates:
            if model.is_suitable_for_task(task_requirements):
                suitable_models.append(model)
        
        # If no suitable models found, try fallback
        if not suitable_models and fallback_models:
            for fallback_id in fallback_models:
                model = self.registry.get_model(fallback_id)
                if model and model.health.status == ModelStatus.AVAILABLE:
                    suitable_models.append(model)
        
        # If still no models, return the highest-scoring available model
        if not suitable_models:
            suitable_models = [candidates[0]] if candidates else []
        
        # Select best model based on score and preferences
        if suitable_models:
            return self._rank_models(suitable_models, task_requirements)[0]
        
        return None
    
    def _rank_models(self, models: List[ModelEntry], requirements: Dict[str, Any]) -> List[ModelEntry]:
        """Rank models based on task requirements and preferences"""
        
        def calculate_rank_score(model: ModelEntry) -> float:
            score = model.integration_score
            
            # Boost free models if preferred
            if requirements.get('prefer_free', False) and model.pricing.is_free:
                score += 20
            
            # Boost models with higher context if needed
            min_context = requirements.get('min_context_tokens', 0)
            if model.limits.context_tokens >= min_context * 2:
                score += 10
            
            # Boost models with more capabilities
            cap_count = sum(1 for cap in model.capabilities.to_dict().values() if cap)
            score += cap_count * 2
            
            # Boost based on success rate
            score += model.health.success_rate * 10
            
            return score
        
        return sorted(models, key=calculate_rank_score, reverse=True)
    
    async def get_model_recommendations(self, 
                                       task_description: str,
                                       max_results: int = 5) -> List[Tuple[ModelEntry, float]]:
        """Get model recommendations based on task description"""
        
        # Simple keyword-based task analysis
        task_requirements = self._analyze_task_requirements(task_description)
        
        # Select best model
        best_model = await self.select_best_model(task_requirements)
        
        recommendations = []
        if best_model:
            # Get top models matching requirements
            candidates = self.registry.list_models(
                status=ModelStatus.AVAILABLE,
                min_score=30.0
            )
            
            suitable_models = []
            for model in candidates:
                if model.is_suitable_for_task(task_requirements):
                    suitable_models.append(model)
            
            # Rank and return top recommendations
            ranked_models = self._rank_models(suitable_models, task_requirements)
            for model in ranked_models[:max_results]:
                score = model.integration_score + (10 if model.pricing.is_free else 0)
                recommendations.append((model, score))
        
        return recommendations
    
    def _analyze_task_requirements(self, task_description: str) -> Dict[str, Any]:
        """Analyze task description to extract requirements"""
        requirements = {
            'capabilities': [],
            'min_context_tokens': 0,
            'max_cost_per_token': float('inf'),
            'prefer_free': True  # Default to free models
        }
        
        description_lower = task_description.lower()
        
        # Detect capability requirements
        if any(word in description_lower for word in ['reasoning', 'analysis', 'logic', 'problem']):
            requirements['capabilities'].append(CapabilityType.REASONING.value)
        
        if any(word in description_lower for word in ['tool', 'function', 'api', 'execute']):
            requirements['capabilities'].append(CapabilityType.TOOL_CALLING.value)
        
        if any(word in description_lower for word in ['image', 'visual', 'photo', 'chart', 'graph', 'content', 'picture', 'graphic']):
            requirements['capabilities'].append(CapabilityType.VISION.value)
        
        if any(word in description_lower for word in ['file', 'document', 'attachment', 'upload']):
            requirements['capabilities'].append(CapabilityType.ATTACHMENTS.value)
        
        # Detect context requirements
        if any(word in description_lower for word in ['large', 'long', 'big', 'huge', 'extensive']):
            requirements['min_context_tokens'] = 100000
        
        # Detect cost preferences
        if any(word in description_lower for word in ['free', 'cost', 'budget', 'cheap']):
            requirements['prefer_free'] = True
        
        return requirements


class ModelOrchestrator:
    """Orchestrates multiple models for complex workflows"""
    
    def __init__(self, registry: ModelRegistry, selector: ModelSelector):
        self.registry = registry
        self.selector = selector
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def create_orchestration_session(self, 
                                         session_id: str,
                                         primary_model: Optional[str] = None,
                                         backup_models: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new orchestration session"""
        
        session_config = {
            'session_id': session_id,
            'primary_model': primary_model,
            'backup_models': backup_models or [],
            'created_at': datetime.now(),
            'usage_stats': {
                'requests_made': 0,
                'successful_requests': 0,
                'fallback_used': 0,
                'models_switched': 0
            },
            'current_model': None
        }
        
        # Select primary model if not provided
        if not primary_model:
            best_model = await self.selector.select_best_model({'prefer_free': True})
            if best_model:
                session_config['primary_model'] = best_model.get_full_id()
        
        self.active_sessions[session_id] = session_config
        logger.info(f"Created orchestration session: {session_id}")
        
        return session_config
    
    async def execute_with_fallback(self, 
                                   session_id: str,
                                   task_requirements: Dict[str, Any],
                                   max_retries: int = 3) -> Tuple[ModelEntry, Any]:
        """Execute task with automatic fallback model switching"""
        
        if session_id not in self.active_sessions:
            await self.create_orchestration_session(session_id)
        
        session = self.active_sessions[session_id]
        session['usage_stats']['requests_made'] += 1
        
        # Try primary model first
        primary_model_id = session['primary_model']
        primary_model = self.registry.get_model(primary_model_id)
        
        if primary_model and primary_model.health.status == ModelStatus.AVAILABLE:
            try:
                session['current_model'] = primary_model
                session['usage_stats']['successful_requests'] += 1
                logger.info(f"Using primary model: {primary_model.get_full_id()}")
                return primary_model, await self._execute_model_task(primary_model, task_requirements)
            except Exception as e:
                logger.warning(f"Primary model failed: {e}")
                session['usage_stats']['fallback_used'] += 1
        
        # Try backup models
        for backup_model_id in session['backup_models']:
            backup_model = self.registry.get_model(backup_model_id)
            if backup_model and backup_model.health.status == ModelStatus.AVAILABLE:
                try:
                    session['current_model'] = backup_model
                    session['usage_stats']['models_switched'] += 1
                    logger.info(f"Switched to backup model: {backup_model.get_full_id()}")
                    return backup_model, await self._execute_model_task(backup_model, task_requirements)
                except Exception as e:
                    logger.warning(f"Backup model {backup_model_id} failed: {e}")
                    continue
        
        # Fallback to best available model
        best_model = await self.selector.select_best_model(task_requirements)
        if best_model:
            session['current_model'] = best_model
            session['usage_stats']['fallback_used'] += 1
            logger.info(f"Using fallback model: {best_model.get_full_id()}")
            return best_model, await self._execute_model_task(best_model, task_requirements)
        
        raise RuntimeError("No available models for task execution")
    
    async def _execute_model_task(self, model: ModelEntry, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using specific model (simulated)"""
        # This would integrate with actual model APIs
        # For now, return simulated execution result
        
        execution_result = {
            'model_used': model.get_full_id(),
            'execution_time_ms': 150.0,
            'tokens_used': 100,
            'success': True,
            'output_preview': f"Task completed using {model.name}",
            'capabilities_used': [cap for cap, enabled in model.capabilities.to_dict().items() if enabled][:3]
        }
        
        return execution_result
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for an orchestration session"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        stats = session['usage_stats'].copy()
        
        if stats['requests_made'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['requests_made']
        else:
            stats['success_rate'] = 0.0
        
        return stats


class ModelDiscoveryModule:
    """Main Model Discovery Module integrating all components"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.registry = ModelRegistry()
        self.discovery_engine = ModelDiscoveryEngine(self.registry)
        self.selector = ModelSelector(self.registry)
        self.orchestrator = ModelOrchestrator(self.registry, self.selector)
        
        self._initialized = False
        self._discoverer_tasks = []
        
        # Register default discovery sources
        self._register_default_sources()
    
    def _register_default_sources(self) -> None:
        """Register default model discovery sources"""
        
        # OpenCode free models source
        async def discover_opencode_models():
            """Discover models from OpenCode"""
            models = []
            
            # OpenCode Big Pickle model
            big_pickle = ModelEntry(
                model_id="big-pickle",
                provider="opencode",
                name="Big Pickle",
                capabilities=ModelCapabilities(
                    reasoning=True,
                    tool_calling=True,
                    temperature=True,
                    attachments=False,
                    streaming=True
                ),
                limits=ModelLimits(
                    context_tokens=200000,
                    output_tokens=128000,
                    requests_per_minute=100
                ),
                pricing=ModelPricing(
                    cost_per_token=0.0,
                    is_free=True,
                    provider_subsidized=True
                ),
                metadata=ModelMetadata(
                    name="Big Pickle",
                    provider="opencode",
                    description="High-performance reasoning model optimized for analysis tasks",
                    release_date=datetime(2024, 1, 1)
                )
            )
            models.append(big_pickle)
            
            # OpenCode Grok Code model
            grok_code = ModelEntry(
                model_id="grok-code",
                provider="opencode",
                name="Grok Code",
                capabilities=ModelCapabilities(
                    reasoning=True,
                    tool_calling=True,
                    temperature=True,
                    attachments=True,
                    streaming=True,
                    function_calling=True,
                    vision=True,
                    multimodal=True
                ),
                limits=ModelLimits(
                    context_tokens=256000,
                    output_tokens=128000,
                    requests_per_minute=100
                ),
                pricing=ModelPricing(
                    cost_per_token=0.0,
                    is_free=True,
                    provider_subsidized=True
                ),
                metadata=ModelMetadata(
                    name="Grok Code",
                    provider="opencode",
                    description="Multi-modal coding assistant with attachment support",
                    release_date=datetime(2024, 1, 15)
                )
            )
            models.append(grok_code)
            
            return models
        
        self.discovery_engine.register_discovery_source("opencode", discover_opencode_models)
        
        # Placeholder for other providers
        self.discovery_engine.register_discovery_source("huggingface", self._discover_huggingface_models)
        self.discovery_engine.register_discovery_source("local", self._discover_local_models)
    
    async def _discover_huggingface_models(self) -> List[ModelEntry]:
        """Discover popular Hugging Face models"""
        models = []
        
        # Example: Llama model
        llama = ModelEntry(
            model_id="llama-2-7b-chat",
            provider="huggingface",
            name="Llama 2 7B Chat",
            capabilities=ModelCapabilities(
                reasoning=True,
                tool_calling=False,
                temperature=True,
                attachments=False,
                streaming=True
            ),
            limits=ModelLimits(
                context_tokens=4096,
                output_tokens=1024,
                requests_per_minute=60
            ),
            pricing=ModelPricing(
                cost_per_token=0.0,
                is_free=True
            ),
            metadata=ModelMetadata(
                name="Llama 2 7B Chat",
                provider="meta",
                description="Meta's Llama 2 chat model via Hugging Face"
            )
        )
        models.append(llama)
        
        return models
    
    async def _discover_local_models(self) -> List[ModelEntry]:
        """Discover locally available models"""
        models = []
        
        # Example: Local Ollama model
        if self._check_ollama_available():
            ollama_model = ModelEntry(
                model_id="llama3:8b",
                provider="ollama",
                name="Llama 3 8B (Local)",
                capabilities=ModelCapabilities(
                    reasoning=True,
                    tool_calling=False,
                    temperature=True,
                    attachments=False,
                    streaming=True
                ),
                limits=ModelLimits(
                    context_tokens=8192,
                    output_tokens=2048,
                    requests_per_minute=10
                ),
                pricing=ModelPricing(
                    cost_per_token=0.0,
                    is_free=True
                ),
                metadata=ModelMetadata(
                    name="Llama 3 8B",
                    provider="meta",
                    description="Locally running Llama 3 model"
                )
            )
            models.append(ollama_model)
        
        return models
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available locally"""
        # This would check if Ollama service is running
        # For now, return False as it's just an example
        return False
    
    async def initialize(self) -> None:
        """Initialize the Model Discovery Module"""
        if self._initialized:
            return
        
        logger.info("Initializing Model Discovery Module...")
        
        # Discover models from all sources
        await self.discovery_engine.discover_all_models()
        
        # Start monitoring tasks
        if self.discovery_engine._monitoring_enabled:
            self._discoverer_tasks.append(
                asyncio.create_task(self._monitoring_loop())
            )
        
        self._initialized = True
        logger.info("Model Discovery Module initialized successfully")
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while True:
            try:
                if self.discovery_engine.should_refresh_discovery():
                    logger.info("Refreshing model discovery...")
                    await self.discovery_engine.discover_all_models()
                
                # Monitor model health
                await self.discovery_engine.monitor_all_models()
                
                # Wait before next cycle
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def shutdown(self) -> None:
        """Shutdown the Model Discovery Module"""
        logger.info("Shutting down Model Discovery Module...")
        
        # Cancel monitoring tasks
        for task in self._discoverer_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._discoverer_tasks, return_exceptions=True)
        
        self._initialized = False
        logger.info("Model Discovery Module shutdown complete")
    
    # Public API Methods
    
    async def get_best_model(self, 
                           task_requirements: Dict[str, Any],
                           fallback_models: Optional[List[str]] = None) -> Optional[ModelEntry]:
        """Get the best model for given task requirements"""
        await self._ensure_initialized()
        return await self.selector.select_best_model(task_requirements, fallback_models)
    
    async def get_model_recommendations(self, 
                                      task_description: str,
                                      max_results: int = 5) -> List[Tuple[ModelEntry, float]]:
        """Get model recommendations based on task description"""
        await self._ensure_initialized()
        return await self.selector.get_model_recommendations(task_description, max_results)
    
    def get_available_models(self, 
                           provider: Optional[str] = None,
                           free_only: bool = False,
                           capabilities: Optional[List[str]] = None) -> List[ModelEntry]:
        """Get list of available models with filtering"""
        return self.registry.list_models(
            provider=provider,
            status=ModelStatus.AVAILABLE,
            free_only=free_only,
            capabilities=capabilities
        )
    
    def get_free_models(self) -> List[ModelEntry]:
        """Get all free models"""
        return self.registry.get_free_models()
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelEntry]:
        """Get model by full identifier"""
        return self.registry.get_model(model_id)
    
    def get_provider_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics by provider"""
        return self.registry.get_provider_stats()
    
    async def create_orchestration_session(self, 
                                         session_id: str,
                                         primary_model: Optional[str] = None,
                                         backup_models: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create orchestration session for multi-model workflows"""
        await self._ensure_initialized()
        return await self.orchestrator.create_orchestration_session(
            session_id, primary_model, backup_models
        )
    
    async def execute_with_orchestration(self, 
                                       session_id: str,
                                       task_requirements: Dict[str, Any]) -> Tuple[ModelEntry, Dict[str, Any]]:
        """Execute task with automatic model orchestration"""
        await self._ensure_initialized()
        return await self.orchestrator.execute_with_fallback(session_id, task_requirements)
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get orchestration session statistics"""
        return self.orchestrator.get_session_stats(session_id)
    
    async def refresh_models(self) -> Dict[str, int]:
        """Manually refresh model discovery"""
        await self._ensure_initialized()
        results = await self.discovery_engine.discover_all_models()
        
        # Count results
        counts = {}
        for source, models in results.items():
            counts[source] = len(models)
        
        return counts
    
    async def _ensure_initialized(self) -> None:
        """Ensure module is initialized"""
        if not self._initialized:
            await self.initialize()


# Factory function for easy module creation
def create_model_discovery_module(config: Optional[Dict[str, Any]] = None) -> ModelDiscoveryModule:
    """Create and initialize a Model Discovery Module"""
    module = ModelDiscoveryModule(config)
    return module


# Example usage and demonstration
if __name__ == "__main__":
    async def main():
        """Demonstration of Model Discovery Module"""
        
        print("=" * 70)
        print("MODEL DISCOVERY MODULE DEMONSTRATION")
        print("=" * 70)
        
        # Create and initialize module
        model_discovery = create_model_discovery_module()
        await model_discovery.initialize()
        
        print("\n1. AVAILABLE MODELS")
        print("-" * 40)
        free_models = model_discovery.get_free_models()
        for model in free_models:
            print(f"• {model.get_full_id()}")
            print(f"  Score: {model.integration_score:.1f}%")
            caps = [cap for cap, enabled in model.capabilities.to_dict().items() if enabled]
            print(f"  Capabilities: {', '.join(caps[:3])}...")
            print(f"  Context: {model.limits.context_tokens:,} tokens")
            print()
        
        print("\n2. TASK-BASED RECOMMENDATIONS")
        print("-" * 40)
        recommendations = await model_discovery.get_model_recommendations(
            "Complex reasoning task with tool calling", max_results=3
        )
        
        for i, (model, score) in enumerate(recommendations, 1):
            print(f"{i}. {model.get_full_id()} (Score: {score:.1f})")
            print(f"   Why: {model.metadata.description}")
            print()
        
        print("\n3. ORCHESTRATION SESSION")
        print("-" * 40)
        session = await model_discovery.create_orchestration_session("demo-session")
        print(f"Created session: {session['session_id']}")
        print(f"Primary model: {session['primary_model']}")
        
        # Execute task with orchestration
        result_model, result = await model_discovery.execute_with_orchestration(
            "demo-session",
            {"capabilities": ["reasoning", "tool_calling"], "prefer_free": True}
        )
        
        print(f"\nExecuted using: {result_model.get_full_id()}")
        print(f"Success: {result['success']}")
        print(f"Execution time: {result['execution_time_ms']}ms")
        
        print("\n4. PROVIDER STATISTICS")
        print("-" * 40)
        stats = model_discovery.get_provider_stats()
        for provider, provider_stats in stats.items():
            print(f"{provider.upper()}:")
            print(f"  Total models: {provider_stats['total']}")
            print(f"  Free models: {provider_stats['free']}")
            print(f"  Available: {provider_stats['available']}")
            print()
        
        print("=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)
        
        # Cleanup
        await model_discovery.shutdown()
    
    # Run demonstration
    asyncio.run(main())