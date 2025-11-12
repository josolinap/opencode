"""
task_free_manager.py - Task-Free Model Management System

Implements task-free model management with zero-shot generalization capabilities.
Based on cutting-edge research in task-agnostic learning and cross-domain adaptation.

Key Features:
- Task-free model architecture with universal representation
- Zero-shot generalization across domains
- Cross-model knowledge transfer
- Dynamic capability synthesis
- Meta-learning for rapid adaptation
- Continual learning without catastrophic forgetting
"""

import asyncio
import time
import json
import numpy as np
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import pickle
import hashlib
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

class GeneralizationMode(Enum):
    """Generalization modes for task-free models"""
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    META_LEARNING = "meta_learning"
    TRANSFER_LEARNING = "transfer_learning"
    CONTINUAL_LEARNING = "continual_learning"

class CapabilityType(Enum):
    """Types of capabilities that can be synthesized"""
    REASONING = "reasoning"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    SYNTHESIS = "synthesis"

@dataclass
class UniversalCapability:
    """Universal capability representation"""
    name: str
    embedding: np.ndarray
    domain: str
    complexity: float
    transferability: float
    prerequisites: List[str] = field(default_factory=list)
    learned_examples: List[Dict] = field(default_factory=list)
    performance_history: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class TaskFreeModel:
    """Task-free model with universal capabilities"""
    name: str
    base_model: str
    universal_capabilities: Dict[str, UniversalCapability] = field(default_factory=dict)
    knowledge_graph: Dict[str, List[str]] = field(default_factory=dict)
    meta_parameters: Dict[str, Any] = field(default_factory=dict)
    adaptation_history: List[Dict] = field(default_factory=list)
    generalization_score: float = 0.5
    versatility_score: float = 0.5
    last_adaptation: Optional[datetime] = None

@dataclass
class GeneralizationRequest:
    """Request for zero-shot generalization"""
    target_task: str
    target_domain: str
    input_examples: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    expected_output_format: Optional[str] = None
    confidence_threshold: float = 0.7

@dataclass
class AdaptationResult:
    """Result of model adaptation"""
    success: bool
    adapted_capabilities: List[str]
    generalization_confidence: float
    adaptation_time: float
    meta_learning_updates: Dict[str, Any]
    transfer_efficiency: float

class TaskFreeManager:
    """
    Task-Free Model Management System
    
    This system implements cutting-edge research in:
    - Task-free learning with universal representations
    - Zero-shot generalization across domains
    - Meta-learning for rapid adaptation
    - Cross-model knowledge transfer
    - Continual learning without forgetting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Task-free models registry
        self.task_free_models: Dict[str, TaskFreeModel] = {}
        self.universal_capability_space: Dict[str, UniversalCapability] = {}
        
        # Knowledge management
        self.knowledge_graph: Dict[str, List[str]] = defaultdict(list)
        self.capability_embeddings: Dict[str, np.ndarray] = {}
        self.domain_mappings: Dict[str, List[str]] = defaultdict(list)
        
        # Meta-learning components
        self.meta_learner = MetaLearner()
        self.adaptation_strategies: Dict[GeneralizationMode, Callable] = {}
        self.transfer_mechanisms: Dict[str, Callable] = {}
        
        # Performance tracking
        self.generalization_history: List[Dict] = []
        self.adaptation_metrics: Dict[str, List[float]] = defaultdict(list)
        self.capability_usage: Dict[str, int] = defaultdict(int)
        
        # Continual learning
        self.memory_buffer = ExperienceReplay()
        self.forgetting_protection = ForgettingProtection()
        
        # Background processes
        self.adaptation_lock = threading.Lock()
        self.learning_active = True
        
        # Initialize system
        self._initialize_universal_capabilities()
        self._initialize_adaptation_strategies()
        self._initialize_task_free_models()
        self._start_background_learning()
        
        logger.info("Task-Free Manager initialized with universal capabilities")
    
    def _initialize_universal_capabilities(self):
        """Initialize universal capability space"""
        # Define core universal capabilities
        core_capabilities = [
            {
                "name": "text_understanding",
                "domain": "language",
                "complexity": 0.3,
                "transferability": 0.9
            },
            {
                "name": "pattern_recognition",
                "domain": "cognitive",
                "complexity": 0.5,
                "transferability": 0.8
            },
            {
                "name": "logical_reasoning",
                "domain": "cognitive",
                "complexity": 0.7,
                "transferability": 0.7
            },
            {
                "name": "knowledge_synthesis",
                "domain": "cognitive",
                "complexity": 0.8,
                "transferability": 0.6
            },
            {
                "name": "creative_generation",
                "domain": "creative",
                "complexity": 0.6,
                "transferability": 0.5
            },
            {
                "name": "analogical_thinking",
                "domain": "cognitive",
                "complexity": 0.7,
                "transferability": 0.8
            },
            {
                "name": "causal_inference",
                "domain": "reasoning",
                "complexity": 0.8,
                "transferability": 0.7
            },
            {
                "name": "abstraction_reasoning",
                "domain": "cognitive",
                "complexity": 0.9,
                "transferability": 0.6
            }
        ]
        
        for cap_config in core_capabilities:
            embedding = self._generate_capability_embedding(cap_config)
            capability = UniversalCapability(
                name=cap_config["name"],
                embedding=embedding,
                domain=cap_config["domain"],
                complexity=cap_config["complexity"],
                transferability=cap_config["transferability"]
            )
            
            self.universal_capability_space[cap_config["name"]] = capability
            self.capability_embeddings[cap_config["name"]] = embedding
            
            # Add to knowledge graph
            self.knowledge_graph[cap_config["domain"]].append(cap_config["name"])
            self.domain_mappings[cap_config["domain"]].append(cap_config["name"])
        
        logger.info(f"Initialized {len(core_capabilities)} universal capabilities")
    
    def _initialize_adaptation_strategies(self):
        """Initialize adaptation strategies for different generalization modes"""
        self.adaptation_strategies = {
            GeneralizationMode.ZERO_SHOT: self._zero_shot_adaptation,
            GeneralizationMode.FEW_SHOT: self._few_shot_adaptation,
            GeneralizationMode.META_LEARNING: self._meta_learning_adaptation,
            GeneralizationMode.TRANSFER_LEARNING: self._transfer_learning_adaptation,
            GeneralizationMode.CONTINUAL_LEARNING: self._continual_learning_adaptation
        }
        
        # Initialize transfer mechanisms
        self.transfer_mechanisms = {
            "knowledge_distillation": self._knowledge_distillation,
            "parameter_transfer": self._parameter_transfer,
            "feature_reuse": self._feature_reuse,
            "analogical_transfer": self._analogical_transfer
        }
    
    def _initialize_task_free_models(self):
        """Initialize task-free models with universal capabilities"""
        # Create base task-free models
        base_models = [
            {
                "name": "universal_reasoner",
                "base_model": "gpt-4-turbo",
                "initial_capabilities": ["text_understanding", "logical_reasoning", "pattern_recognition"]
            },
            {
                "name": "universal_generator",
                "base_model": "claude-3-sonnet",
                "initial_capabilities": ["text_understanding", "creative_generation", "knowledge_synthesis"]
            },
            {
                "name": "universal_analyzer",
                "base_model": "gemini-pro",
                "initial_capabilities": ["text_understanding", "pattern_recognition", "causal_inference"]
            }
        ]
        
        for model_config in base_models:
            model = TaskFreeModel(
                name=model_config["name"],
                base_model=model_config["base_model"]
            )
            
            # Add initial capabilities
            for cap_name in model_config["initial_capabilities"]:
                if cap_name in self.universal_capability_space:
                    model.universal_capabilities[cap_name] = self.universal_capability_space[cap_name]
            
            # Initialize knowledge graph
            model.knowledge_graph = dict(self.knowledge_graph)
            
            # Set initial scores
            model.generalization_score = 0.7
            model.versatility_score = len(model.universal_capabilities) / len(self.universal_capability_space)
            
            self.task_free_models[model_config["name"]] = model
        
        logger.info(f"Initialized {len(base_models)} task-free models")
    
    def _start_background_learning(self):
        """Start background continual learning"""
        def background_learning():
            while self.learning_active:
                try:
                    # Update meta-learner
                    self.meta_learner.update_from_experience(self.generalization_history)
                    
                    # Consolidate knowledge
                    self._consolidate_knowledge()
                    
                    # Prevent catastrophic forgetting
                    self._update_forgetting_protection()
                    
                    # Sleep for learning interval
                    time.sleep(300)  # 5 minutes
                    
                except Exception as e:
                    logger.error(f"Background learning error: {e}")
                    time.sleep(600)  # 10 minutes on error
        
        threading.Thread(target=background_learning, daemon=True).start()
        logger.info("Background continual learning started")
    
    async def generalize_to_task(self, request: GeneralizationRequest, model_name: Optional[str] = None) -> AdaptationResult:
        """
        Generalize task-free model to new task using zero-shot learning
        """
        start_time = time.time()
        
        try:
            # Select best model for generalization
            if model_name is None:
                model_name = await self._select_best_model_for_task(request)
            
            if model_name not in self.task_free_models:
                raise ValueError(f"Task-free model {model_name} not found")
            
            model = self.task_free_models[model_name]
            
            # Analyze task requirements
            task_analysis = self._analyze_task_requirements(request)
            
            # Determine generalization mode
            generalization_mode = self._determine_generalization_mode(request, task_analysis)
            
            # Execute adaptation
            adaptation_result = await self._execute_adaptation(
                model, request, task_analysis, generalization_mode
            )
            
            # Update model
            with self.adaptation_lock:
                self._update_model_after_adaptation(model, adaptation_result, request)
            
            # Record generalization
            self._record_generalization(model_name, request, adaptation_result, time.time() - start_time)
            
            return adaptation_result
            
        except Exception as e:
            logger.error(f"Task generalization failed: {e}")
            return AdaptationResult(
                success=False,
                adapted_capabilities=[],
                generalization_confidence=0.0,
                adaptation_time=time.time() - start_time,
                meta_learning_updates={},
                transfer_efficiency=0.0
            )
    
    async def _select_best_model_for_task(self, request: GeneralizationRequest) -> str:
        """Select best task-free model for the given task"""
        model_scores = []
        
        for model_name, model in self.task_free_models.items():
            score = self._calculate_model_task_fitness(model, request)
            model_scores.append((model_name, score))
        
        model_scores.sort(key=lambda x: x[1], reverse=True)
        return model_scores[0][0]
    
    def _calculate_model_task_fitness(self, model: TaskFreeModel, request: GeneralizationRequest) -> float:
        """Calculate fitness score of model for task"""
        score = 0.0
        
        # Base generalization capability
        score += model.generalization_score * 0.3
        
        # Versatility
        score += model.versatility_score * 0.2
        
        # Domain relevance
        domain_relevance = self._calculate_domain_relevance(model, request.target_domain)
        score += domain_relevance * 0.3
        
        # Capability overlap
        capability_overlap = self._calculate_capability_overlap(model, request)
        score += capability_overlap * 0.2
        
        return score
    
    def _calculate_domain_relevance(self, model: TaskFreeModel, target_domain: str) -> float:
        """Calculate domain relevance score"""
        domain_capabilities = self.domain_mappings.get(target_domain, [])
        model_capabilities = list(model.universal_capabilities.keys())
        
        if not domain_capabilities:
            return 0.5  # Neutral for unknown domains
        
        overlap = len(set(domain_capabilities) & set(model_capabilities))
        return overlap / len(domain_capabilities)
    
    def _calculate_capability_overlap(self, model: TaskFreeModel, request: GeneralizationRequest) -> float:
        """Calculate capability overlap with task requirements"""
        # Extract required capabilities from task description
        required_caps = self._extract_required_capabilities(request.target_task)
        model_caps = set(model.universal_capabilities.keys())
        
        if not required_caps:
            return 0.5  # Neutral for unknown requirements
        
        overlap = len(required_caps & model_caps)
        return overlap / len(required_caps)
    
    def _extract_required_capabilities(self, task_description: str) -> set:
        """Extract required capabilities from task description"""
        task_lower = task_description.lower()
        required_caps = set()
        
        # Simple keyword-based extraction
        capability_keywords = {
            "text_understanding": ["understand", "comprehend", "read", "interpret"],
            "pattern_recognition": ["pattern", "recognize", "identify", "detect"],
            "logical_reasoning": ["reason", "logic", "deduce", "infer"],
            "knowledge_synthesis": ["synthesize", "combine", "integrate", "merge"],
            "creative_generation": ["create", "generate", "produce", "design"],
            "analogical_thinking": ["analogy", "similar", "compare", "metaphor"],
            "causal_inference": ["cause", "effect", "because", "reason"],
            "abstraction_reasoning": ["abstract", "generalize", "concept", "principle"]
        }
        
        for cap, keywords in capability_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_caps.add(cap)
        
        return required_caps
    
    def _analyze_task_requirements(self, request: GeneralizationRequest) -> Dict[str, Any]:
        """Analyze task requirements and constraints"""
        analysis = {
            "complexity": self._estimate_task_complexity(request),
            "domain_familiarity": self._estimate_domain_familiarity(request.target_domain),
            "required_capabilities": self._extract_required_capabilities(request.target_task),
            "transfer_difficulty": self._estimate_transfer_difficulty(request),
            "adaptation_strategy": None
        }
        
        return analysis
    
    def _estimate_task_complexity(self, request: GeneralizationRequest) -> float:
        """Estimate task complexity"""
        complexity = 0.3  # Base complexity
        
        # Length-based complexity
        complexity += min(len(request.target_task) / 500, 0.3)
        
        # Example-based complexity
        if request.input_examples:
            complexity += min(len(request.input_examples) / 10, 0.2)
        
        # Constraint-based complexity
        complexity += min(len(request.constraints) / 5, 0.2)
        
        return min(complexity, 1.0)
    
    def _estimate_domain_familiarity(self, domain: str) -> float:
        """Estimate familiarity with domain"""
        # Count how many models have capabilities in this domain
        domain_capabilities = self.domain_mappings.get(domain, [])
        if not domain_capabilities:
            return 0.1  # Very low familiarity
        
        total_domain_coverage = 0
        for model in self.task_free_models.values():
            model_caps = set(model.universal_capabilities.keys())
            domain_caps = set(domain_capabilities)
            overlap = len(model_caps & domain_caps)
            total_domain_coverage += overlap / len(domain_caps) if domain_caps else 0
        
        return total_domain_coverage / len(self.task_free_models)
    
    def _estimate_transfer_difficulty(self, request: GeneralizationRequest) -> float:
        """Estimate difficulty of knowledge transfer"""
        difficulty = 0.5  # Base difficulty
        
        # Domain novelty
        domain_familiarity = self._estimate_domain_familiarity(request.target_domain)
        difficulty += (1 - domain_familiarity) * 0.3
        
        # Task novelty
        task_complexity = self._estimate_task_complexity(request)
        difficulty += task_complexity * 0.2
        
        return min(difficulty, 1.0)
    
    def _determine_generalization_mode(self, request: GeneralizationRequest, task_analysis: Dict) -> GeneralizationMode:
        """Determine best generalization mode"""
        # If we have examples, use few-shot
        if request.input_examples:
            return GeneralizationMode.FEW_SHOT
        
        # If task is complex and domain is unfamiliar, use meta-learning
        if task_analysis["complexity"] > 0.7 and task_analysis["domain_familiarity"] < 0.3:
            return GeneralizationMode.META_LEARNING
        
        # If domain is familiar, use transfer learning
        if task_analysis["domain_familiarity"] > 0.6:
            return GeneralizationMode.TRANSFER_LEARNING
        
        # Default to zero-shot
        return GeneralizationMode.ZERO_SHOT
    
    async def _execute_adaptation(self, model: TaskFreeModel, request: GeneralizationRequest, 
                                 task_analysis: Dict, mode: GeneralizationMode) -> AdaptationResult:
        """Execute model adaptation using specified strategy"""
        adaptation_strategy = self.adaptation_strategies.get(mode)
        if not adaptation_strategy:
            raise ValueError(f"Unknown generalization mode: {mode}")
        
        return await adaptation_strategy(model, request, task_analysis)
    
    async def _zero_shot_adaptation(self, model: TaskFreeModel, request: GeneralizationRequest, 
                                  task_analysis: Dict) -> AdaptationResult:
        """Zero-shot adaptation using universal capabilities"""
        start_time = time.time()
        
        # Select relevant universal capabilities
        relevant_caps = self._select_relevant_capabilities(model, request.target_task)
        
        # Synthesize new capability combination
        synthesized_capability = self._synthesize_capability(relevant_caps, request.target_task)
        
        # Calculate confidence
        confidence = self._calculate_zero_shot_confidence(model, relevant_caps, request)
        
        # Update model capabilities
        adapted_capabilities = []
        if confidence > request.confidence_threshold:
            model.universal_capabilities[synthesized_capability.name] = synthesized_capability
            adapted_capabilities.append(synthesized_capability.name)
        
        return AdaptationResult(
            success=len(adapted_capabilities) > 0,
            adapted_capabilities=adapted_capabilities,
            generalization_confidence=confidence,
            adaptation_time=time.time() - start_time,
            meta_learning_updates={"synthesized_capability": synthesized_capability.name},
            transfer_efficiency=confidence
        )
    
    async def _few_shot_adaptation(self, model: TaskFreeModel, request: GeneralizationRequest, 
                                 task_analysis: Dict) -> AdaptationResult:
        """Few-shot adaptation using provided examples"""
        start_time = time.time()
        
        # Learn from examples
        learned_patterns = self._learn_from_examples(request.input_examples, request.target_task)
        
        # Adapt universal capabilities
        adapted_capabilities = []
        for pattern in learned_patterns:
            adapted_cap = self._adapt_capability_with_pattern(model, pattern)
            if adapted_cap:
                model.universal_capabilities[adapted_cap.name] = adapted_cap
                adapted_capabilities.append(adapted_cap.name)
        
        # Calculate confidence based on example quality
        confidence = self._calculate_few_shot_confidence(learned_patterns, request.input_examples)
        
        return AdaptationResult(
            success=len(adapted_capabilities) > 0,
            adapted_capabilities=adapted_capabilities,
            generalization_confidence=confidence,
            adaptation_time=time.time() - start_time,
            meta_learning_updates={"learned_patterns": len(learned_patterns)},
            transfer_efficiency=confidence * 0.9
        )
    
    async def _meta_learning_adaptation(self, model: TaskFreeModel, request: GeneralizationRequest, 
                                      task_analysis: Dict) -> AdaptationResult:
        """Meta-learning adaptation using learned optimization strategies"""
        start_time = time.time()
        
        # Get meta-learning strategy
        meta_strategy = self.meta_learner.get_adaptation_strategy(request.target_task, model.name)
        
        # Apply meta-learning updates
        meta_updates = self._apply_meta_learning(model, meta_strategy, request)
        
        # Adapt capabilities based on meta-learning
        adapted_capabilities = []
        for update in meta_updates:
            if update["type"] == "capability_adaptation":
                adapted_cap = self._apply_capability_update(model, update)
                if adapted_cap:
                    model.universal_capabilities[adapted_cap.name] = adapted_cap
                    adapted_capabilities.append(adapted_cap.name)
        
        # Calculate confidence based on meta-learning performance
        confidence = self._calculate_meta_learning_confidence(meta_updates, model)
        
        return AdaptationResult(
            success=len(adapted_capabilities) > 0,
            adapted_capabilities=adapted_capabilities,
            generalization_confidence=confidence,
            adaptation_time=time.time() - start_time,
            meta_learning_updates=meta_updates,
            transfer_efficiency=confidence * 0.85
        )
    
    async def _transfer_learning_adaptation(self, model: TaskFreeModel, request: GeneralizationRequest, 
                                         task_analysis: Dict) -> AdaptationResult:
        """Transfer learning adaptation from similar domains"""
        start_time = time.time()
        
        # Find similar domains and capabilities
        similar_domains = self._find_similar_domains(request.target_domain)
        transferable_capabilities = self._find_transferable_capabilities(model, similar_domains)
        
        # Execute knowledge transfer
        transferred_capabilities = []
        for cap_name in transferable_capabilities:
            transferred = await self._transfer_knowledge(model, cap_name, request.target_task)
            if transferred:
                transferred_capabilities.append(cap_name)
        
        # Calculate transfer efficiency
        transfer_efficiency = len(transferred_capabilities) / len(transferable_capabilities) if transferable_capabilities else 0
        confidence = transfer_efficiency * 0.9
        
        return AdaptationResult(
            success=len(transferred_capabilities) > 0,
            adapted_capabilities=transferred_capabilities,
            generalization_confidence=confidence,
            adaptation_time=time.time() - start_time,
            meta_learning_updates={"transferred_from": similar_domains},
            transfer_efficiency=transfer_efficiency
        )
    
    async def _continual_learning_adaptation(self, model: TaskFreeModel, request: GeneralizationRequest, 
                                           task_analysis: Dict) -> AdaptationResult:
        """Continual learning adaptation with forgetting protection"""
        start_time = time.time()
        
        # Store current experience
        self.memory_buffer.add_experience({
            "task": request.target_task,
            "domain": request.target_domain,
            "examples": request.input_examples,
            "timestamp": datetime.now()
        })
        
        # Learn from experience buffer
        learned_insights = self._learn_from_experience_buffer(model)
        
        # Apply forgetting protection
        protected_capabilities = self.forgetting_protection.protect_capabilities(model)
        
        # Update capabilities with new learning
        adapted_capabilities = []
        for insight in learned_insights:
            adapted_cap = self._apply_insight_to_capability(model, insight, protected_capabilities)
            if adapted_cap:
                model.universal_capabilities[adapted_cap.name] = adapted_cap
                adapted_capabilities.append(adapted_cap.name)
        
        # Calculate confidence
        confidence = self._calculate_continual_learning_confidence(learned_insights, model)
        
        return AdaptationResult(
            success=len(adapted_capabilities) > 0,
            adapted_capabilities=adapted_capabilities,
            generalization_confidence=confidence,
            adaptation_time=time.time() - start_time,
            meta_learning_updates={"experience_buffer_size": len(self.memory_buffer.buffer)},
            transfer_efficiency=confidence * 0.8
        )
    
    def _select_relevant_capabilities(self, model: TaskFreeModel, task: str) -> List[UniversalCapability]:
        """Select relevant universal capabilities for task"""
        task_embedding = self._generate_task_embedding(task)
        relevant_caps = []
        
        for cap in model.universal_capabilities.values():
            similarity = self._calculate_embedding_similarity(task_embedding, cap.embedding)
            if similarity > 0.5:  # Relevance threshold
                relevant_caps.append((cap, similarity))
        
        # Sort by similarity
        relevant_caps.sort(key=lambda x: x[1], reverse=True)
        return [cap for cap, _ in relevant_caps[:5]]  # Top 5 capabilities
    
    def _synthesize_capability(self, relevant_caps: List[UniversalCapability], task: str) -> UniversalCapability:
        """Synthesize new capability from relevant ones"""
        # Combine embeddings
        combined_embedding = np.mean([cap.embedding for cap in relevant_caps], axis=0)
        
        # Create synthesized capability
        synthesized_name = f"synthesized_{hashlib.md5(task.encode()).hexdigest()[:8]}"
        
        return UniversalCapability(
            name=synthesized_name,
            embedding=combined_embedding,
            domain="synthesized",
            complexity=np.mean([cap.complexity for cap in relevant_caps]),
            transferability=np.mean([cap.transferability for cap in relevant_caps]),
            prerequisites=[cap.name for cap in relevant_caps]
        )
    
    def _calculate_zero_shot_confidence(self, model: TaskFreeModel, relevant_caps: List[UniversalCapability], 
                                      request: GeneralizationRequest) -> float:
        """Calculate confidence for zero-shot adaptation"""
        if not relevant_caps:
            return 0.1
        
        # Base confidence from model generalization score
        confidence = model.generalization_score * 0.4
        
        # Capability relevance
        avg_transferability = np.mean([cap.transferability for cap in relevant_caps])
        confidence += avg_transferability * 0.3
        
        # Model versatility
        confidence += model.versatility_score * 0.3
        
        return min(confidence, 1.0)
    
    def _learn_from_examples(self, examples: List[str], task: str) -> List[Dict]:
        """Learn patterns from provided examples"""
        patterns = []
        
        for example in examples:
            # Extract pattern (simplified)
            pattern = {
                "type": "example_pattern",
                "content": example,
                "task": task,
                "confidence": 0.8
            }
            patterns.append(pattern)
        
        return patterns
    
    def _adapt_capability_with_pattern(self, model: TaskFreeModel, pattern: Dict) -> Optional[UniversalCapability]:
        """Adapt capability based on learned pattern"""
        # Find most relevant capability
        relevant_caps = self._select_relevant_capabilities(model, pattern["task"])
        
        if not relevant_caps:
            return None
        
        base_cap = relevant_caps[0]
        
        # Create adapted capability
        adapted_name = f"adapted_{base_cap.name}_{hashlib.md5(pattern['content'].encode()).hexdigest()[:6]}"
        
        return UniversalCapability(
            name=adapted_name,
            embedding=base_cap.embedding * 0.8 + np.random.random(base_cap.embedding.shape) * 0.2,
            domain=base_cap.domain,
            complexity=base_cap.complexity * 1.1,  # Slightly more complex
            transferability=base_cap.transferability * 0.9,  # Slightly less transferable
            prerequisites=base_cap.prerequisites,
            learned_examples=[pattern]
        )
    
    def _calculate_few_shot_confidence(self, learned_patterns: List[Dict], examples: List[str]) -> float:
        """Calculate confidence for few-shot adaptation"""
        if not learned_patterns or not examples:
            return 0.1
        
        # Base confidence from pattern quality
        avg_pattern_confidence = np.mean([p["confidence"] for p in learned_patterns])
        confidence = avg_pattern_confidence * 0.6
        
        # Example quality factor
        example_quality = min(len(examples) / 5, 1.0)  # More examples = higher quality
        confidence += example_quality * 0.4
        
        return min(confidence, 1.0)
    
    def _generate_capability_embedding(self, cap_config: Dict) -> np.ndarray:
        """Generate embedding for capability"""
        # Simplified embedding generation
        embedding = np.random.random(128)  # 128-dimensional embedding
        
        # Adjust based on capability properties
        embedding *= cap_config["complexity"]
        embedding *= cap_config["transferability"]
        
        return embedding / np.linalg.norm(embedding)  # Normalize
    
    def _generate_task_embedding(self, task: str) -> np.ndarray:
        """Generate embedding for task"""
        # Simplified task embedding
        words = task.lower().split()
        embedding = np.zeros(128)
        
        for i, word in enumerate(words[:50]):  # Limit to first 50 words
            word_hash = hash(word) % 1000
            embedding[i % 128] += word_hash / 1000.0
        
        return embedding / (np.linalg.norm(embedding) + 1e-8)
    
    def _calculate_embedding_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8)
    
    def _update_model_after_adaptation(self, model: TaskFreeModel, result: AdaptationResult, request: GeneralizationRequest):
        """Update model after successful adaptation"""
        if result.success:
            # Update scores
            model.generalization_score = model.generalization_score * 0.9 + result.generalization_confidence * 0.1
            model.versatility_score = len(model.universal_capabilities) / len(self.universal_capability_space)
            model.last_adaptation = datetime.now()
            
            # Record adaptation
            model.adaptation_history.append({
                "task": request.target_task,
                "domain": request.target_domain,
                "adapted_capabilities": result.adapted_capabilities,
                "confidence": result.generalization_confidence,
                "timestamp": datetime.now()
            })
    
    def _record_generalization(self, model_name: str, request: GeneralizationRequest, 
                             result: AdaptationResult, adaptation_time: float):
        """Record generalization for learning"""
        record = {
            "model_name": model_name,
            "task": request.target_task,
            "domain": request.target_domain,
            "success": result.success,
            "confidence": result.generalization_confidence,
            "adaptation_time": adaptation_time,
            "transfer_efficiency": result.transfer_efficiency,
            "timestamp": datetime.now()
        }
        
        self.generalization_history.append(record)
        
        # Update capability usage
        for cap in result.adapted_capabilities:
            self.capability_usage[cap] += 1
        
        # Keep history manageable
        if len(self.generalization_history) > 1000:
            self.generalization_history = self.generalization_history[-1000:]
    
    def _consolidate_knowledge(self):
        """Consolidate learned knowledge across models"""
        # Find common patterns across models
        common_patterns = self._find_common_patterns()
        
        # Update universal capabilities
        for pattern in common_patterns:
            if pattern["name"] not in self.universal_capability_space:
                self._create_universal_capability_from_pattern(pattern)
    
    def _find_common_patterns(self) -> List[Dict]:
        """Find common patterns across models"""
        # Simplified pattern detection
        capability_counts = defaultdict(int)
        
        for model in self.task_free_models.values():
            for cap_name in model.universal_capabilities:
                capability_counts[cap_name] += 1
        
        # Find capabilities used by multiple models
        common_patterns = []
        for cap_name, count in capability_counts.items():
            if count >= 2:  # Used by at least 2 models
                common_patterns.append({
                    "name": cap_name,
                    "frequency": count,
                    "type": "common_capability"
                })
        
        return common_patterns
    
    def _create_universal_capability_from_pattern(self, pattern: Dict):
        """Create universal capability from common pattern"""
        # Get capability from first model that has it
        for model in self.task_free_models.values():
            if pattern["name"] in model.universal_capabilities:
                base_cap = model.universal_capabilities[pattern["name"]]
                
                # Create universal version
                universal_cap = UniversalCapability(
                    name=pattern["name"],
                    embedding=base_cap.embedding.copy(),
                    domain=base_cap.domain,
                    complexity=base_cap.complexity,
                    transferability=min(base_cap.transferability * 1.1, 1.0),  # Slightly more transferable
                    prerequisites=base_cap.prerequisites.copy()
                )
                
                self.universal_capability_space[pattern["name"]] = universal_cap
                break
    
    def _update_forgetting_protection(self):
        """Update forgetting protection mechanisms"""
        # Identify important capabilities to protect
        for cap_name, usage_count in self.capability_usage.items():
            if usage_count > 5:  # Frequently used
                self.forgetting_protection.protect_capability(cap_name, importance=usage_count / 10)
    
    def get_task_free_status(self) -> Dict[str, Any]:
        """Get comprehensive task-free system status"""
        return {
            "task_free_models": {
                name: {
                    "base_model": model.base_model,
                    "capabilities_count": len(model.universal_capabilities),
                    "generalization_score": model.generalization_score,
                    "versatility_score": model.versatility_score,
                    "adaptation_count": len(model.adaptation_history),
                    "last_adaptation": model.last_adaptation.isoformat() if model.last_adaptation else None
                }
                for name, model in self.task_free_models.items()
            },
            "universal_capabilities": {
                "total_count": len(self.universal_capability_space),
                "domains": list(set(cap.domain for cap in self.universal_capability_space.values())),
                "average_complexity": np.mean([cap.complexity for cap in self.universal_capability_space.values()]),
                "average_transferability": np.mean([cap.transferability for cap in self.universal_capability_space.values()])
            },
            "generalization_metrics": {
                "total_generalizations": len(self.generalization_history),
                "success_rate": sum(1 for g in self.generalization_history if g["success"]) / max(len(self.generalization_history), 1),
                "average_confidence": np.mean([g["confidence"] for g in self.generalization_history]) if self.generalization_history else 0,
                "average_adaptation_time": np.mean([g["adaptation_time"] for g in self.generalization_history]) if self.generalization_history else 0
            },
            "learning_status": {
                "experience_buffer_size": len(self.memory_buffer.buffer),
                "protected_capabilities": len(self.forgetting_protection.protected_caps),
                "meta_learning_updates": len(self.meta_learner.learned_strategies)
            }
        }
    
    def shutdown(self):
        """Graceful shutdown"""
        self.learning_active = False
        logger.info("Task-Free Manager shutdown complete")


class MetaLearner:
    """Meta-learning component for rapid adaptation"""
    
    def __init__(self):
        self.learned_strategies: Dict[str, Dict] = {}
        self.performance_history: List[Dict] = []
    
    def get_adaptation_strategy(self, task: str, model_name: str) -> Dict:
        """Get adaptation strategy for task and model"""
        task_key = f"{task}_{model_name}"
        
        if task_key in self.learned_strategies:
            return self.learned_strategies[task_key]
        
        # Return default strategy
        return {
            "type": "default",
            "learning_rate": 0.01,
            "adaptation_steps": 10,
            "regularization": 0.001
        }
    
    def update_from_experience(self, experience_history: List[Dict]):
        """Update meta-learner from experience"""
        # Simplified meta-learning update
        for experience in experience_history[-100:]:  # Last 100 experiences
            if experience["success"]:
                self._learn_from_success(experience)
    
    def _learn_from_success(self, experience: Dict):
        """Learn from successful experience"""
        task_key = f"{experience['task']}_{experience['model_name']}"
        
        if task_key not in self.learned_strategies:
            self.learned_strategies[task_key] = {
                "type": "learned",
                "learning_rate": 0.01,
                "adaptation_steps": 10,
                "success_count": 0
            }
        
        self.learned_strategies[task_key]["success_count"] += 1
        
        # Adjust parameters based on performance
        if experience["confidence"] > 0.8:
            self.learned_strategies[task_key]["learning_rate"] *= 0.95  # Reduce learning rate


class ExperienceReplay:
    """Experience replay buffer for continual learning"""
    
    def __init__(self, capacity: int = 1000):
        self.buffer: List[Dict] = []
        self.capacity = capacity
    
    def add_experience(self, experience: Dict):
        """Add experience to buffer"""
        self.buffer.append(experience)
        
        # Maintain capacity
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)
    
    def sample_experiences(self, batch_size: int = 32) -> List[Dict]:
        """Sample random experiences from buffer"""
        if len(self.buffer) < batch_size:
            return self.buffer.copy()
        
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]


class ForgettingProtection:
    """Protection against catastrophic forgetting"""
    
    def __init__(self):
        self.protected_caps: Dict[str, float] = {}  # capability -> importance score
    
    def protect_capability(self, cap_name: str, importance: float):
        """Protect capability with importance score"""
        self.protected_caps[cap_name] = max(self.protected_caps.get(cap_name, 0), importance)
    
    def protect_capabilities(self, model: TaskFreeModel) -> List[str]:
        """Protect important capabilities in model"""
        protected = []
        
        for cap_name in model.universal_capabilities:
            if cap_name in self.protected_caps:
                protected.append(cap_name)
        
        return protected


# Factory function
def create_task_free_manager(config: Optional[Dict] = None) -> TaskFreeManager:
    """Create task-free manager instance"""
    return TaskFreeManager(config)