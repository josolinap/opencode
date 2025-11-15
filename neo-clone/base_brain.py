"""
Base Brain System for MiniMax Agent Architecture

This module provides the foundational reasoning and coordination system
that manages intent recognition, skill routing, and response generation.

Author: MiniMax Agent
Version: 1.0
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from enum import Enum
import logging

# Import foundational modules
from config import get_config
from data_models import (
    Message, MessageRole, ConversationHistory, MemoryEntry, MemoryType,
    IntentType, SkillCategory, SkillResult, SkillContext, ReasoningStep,
    MiniMaxReasoningTrace, PerformanceMetrics
)
from unified_memory import get_unified_memory
from cache_system import get_cache

# Configure logging
logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Brain processing modes"""
    STANDARD = "standard"      # Basic processing
    ENHANCED = "enhanced"      # Advanced reasoning
    COLLABORATIVE = "collaborative"  # Multi-skill collaboration
    OPTIMIZED = "optimized"    # Performance optimized


class ReasoningStrategy(Enum):
    """Reasoning strategies"""
    DIRECT = "direct"              # Direct response
    REASONING_CHAIN = "chain"      # Step-by-step reasoning
    TREE_SEARCH = "tree"          # Tree-based exploration
    BACKTRACKING = "backtrack"    # Backtracking search


class BaseBrain:
    """
    Base Brain system for intelligent coordination and reasoning
    
    Responsibilities:
    - Intent recognition and classification
    - Skill routing and coordination
    - Memory management and retrieval
    - Response generation
    - Performance monitoring
    """
    
    def __init__(
        self,
        processing_mode: ProcessingMode = ProcessingMode.STANDARD,
        reasoning_strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
        max_reasoning_steps: int = 10,
        confidence_threshold: float = 0.7,
        enable_learning: bool = True,
        enable_optimization: bool = True
    ):
        """
        Initialize Base Brain
        
        Args:
            processing_mode: Brain processing mode
            reasoning_strategy: Reasoning strategy to use
            max_reasoning_steps: Maximum reasoning steps
            confidence_threshold: Minimum confidence for decisions
            enable_learning: Enable learning from interactions
            enable_optimization: Enable performance optimization
        """
        self.processing_mode = processing_mode
        self.reasoning_strategy = reasoning_strategy
        self.max_reasoning_steps = max_reasoning_steps
        self.confidence_threshold = confidence_threshold
        self.enable_learning = enable_learning
        self.enable_optimization = enable_optimization
        
        # Core components
        self.config = get_config()
        self.memory = get_unified_memory()
        self.vector_memory = get_unified_memory()  # Unified system provides both interfaces
        self.cache = get_cache()
        
        # Processing state
        self.is_processing = False
        self.processing_lock = threading.Lock()
        
        # Intent recognition patterns
        self.intent_patterns = self._initialize_intent_patterns()
        
        # Skill registry (will be populated by Skills System)
        self.skills: Dict[str, Any] = {}
        self.skill_categories: Dict[SkillCategory, List[str]] = {}
        
        # Performance tracking
        self.performance_metrics: List[PerformanceMetrics] = []
        self.total_processed_requests = 0
        
        # Learning data
        self.learned_patterns: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {}
        
        logger.info(f"Base Brain initialized: mode={processing_mode.value}, strategy={reasoning_strategy.value}")
    
    def _initialize_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Initialize intent recognition patterns"""
        return {
            IntentType.CODE: [
                "write code", "implement", "create function", "debug",
                "refactor", "test", "optimize code", "code review",
                "algorithm", "programming", "script", "class", "method"
            ],
            IntentType.DATA_ANALYSIS: [
                "analyze data", "statistics", "visualization", "chart",
                "trends", "patterns", "insights", "report", "metrics",
                "dashboard", "exploration", "correlation"
            ],
            IntentType.CONVERSATION: [
                "hello", "hi", "how are you", "tell me", "explain",
                "what is", "why", "how does", "describe", "conversation"
            ],
            IntentType.PLANNING: [
                "plan", "schedule", "roadmap", "strategy", "approach",
                "steps", "timeline", "milestone", "goals", "tasks"
            ],
            IntentType.DEBUGGING: [
                "error", "bug", "issue", "problem", "fix", "debug",
                "stack trace", "exception", "debugging", "troubleshoot"
            ],
            IntentType.LEARNING: [
                "learn", "tutorial", "guide", "how to", "teach",
                "explain concept", "understand", "study", "practice"
            ],
            IntentType.SYSTEM: [
                "system", "configuration", "setup", "install",
                "deploy", "environment", "performance", "monitor"
            ]
        }
    
    async def process_input(
        self,
        user_input: str,
        context: Optional[ConversationHistory] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, MiniMaxReasoningTrace]:
        """
        Process user input and generate response
        
        Args:
            user_input: User's input text
            context: Conversation context
            session_id: Session identifier
        
        Returns:
            Tuple of (response, reasoning_trace)
        """
        start_time = time.time()
        session_id = session_id or self.memory.session_id
        
        with self.processing_lock:
            self.is_processing = True
        
        try:
            # Initialize reasoning trace
            reasoning_trace = MiniMaxReasoningTrace()
            
            # Step 1: Intent Recognition
            intent_result = await self._recognize_intent(user_input, reasoning_trace)
            
            # Step 2: Context Retrieval
            relevant_context = await self._retrieve_context(user_input, intent_result, reasoning_trace)
            
            # Step 3: Skill Selection
            selected_skill = await self._select_skill(user_input, intent_result, reasoning_trace)
            
            # Step 4: Skill Execution
            skill_result = await self._execute_skill(
                selected_skill, user_input, relevant_context, intent_result, reasoning_trace
            )
            
            # Step 5: Response Generation
            response = await self._generate_response(
                skill_result, user_input, relevant_context, reasoning_trace
            )
            
            # Step 6: Learning and Memory Storage
            if self.enable_learning:
                await self._learn_from_interaction(
                    user_input, response, intent_result, skill_result
                )
            
            # Store in memory
            await self._store_in_memory(user_input, response, intent_result, skill_result)
            
            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(user_input, response, execution_time, True)
            
            self.total_processed_requests += 1
            
            logger.debug(f"Processed input in {execution_time:.3f}s: intent={intent_result.intent.value}")
            return response, reasoning_trace
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            error_response = "I apologize, but I encountered an error while processing your request. Please try again."
            
            # Store error in memory
            await self._store_in_memory(user_input, error_response, None, None)
            
            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(user_input, error_response, execution_time, False)
            
            return error_response, MiniMaxReasoningTrace()
        
        finally:
            with self.processing_lock:
                self.is_processing = False
    
    async def _recognize_intent(
        self,
        user_input: str,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> Any:
        """Recognize user intent from input"""
        input_lower = user_input.lower()
        intent_scores = {}
        
        # Pattern-based intent recognition
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            matched_patterns = []
            
            for pattern in patterns:
                if pattern in input_lower:
                    score += 1.0
                    matched_patterns.append(pattern)
            
            # Normalize score
            if patterns:
                score /= len(patterns)
            
            intent_scores[intent_type] = {
                "score": score,
                "matched_patterns": matched_patterns
            }
        
        # Find best intent
        best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k]["score"])
        confidence = intent_scores[best_intent]["score"]
        
        # Apply threshold
        if confidence < self.confidence_threshold:
            best_intent = IntentType.CONVERSATION  # Default fallback
            confidence = 0.5
        
        # Create intent result
        intent_result = type('IntentResult', (), {
            'intent': best_intent,
            'confidence': confidence,
            'scores': intent_scores,
            'matched_patterns': intent_scores[best_intent]["matched_patterns"]
        })()
        
        # Add to reasoning trace
        reasoning_trace.add_intent_analysis(
            intent=best_intent.value,
            confidence=confidence,
            categories=[best_intent.value],
            metadata={
                "matched_patterns": intent_scores[best_intent]["matched_patterns"],
                "all_scores": {k.value: v["score"] for k, v in intent_scores.items()}
            }
        )
        
        reasoning_trace.add_step(
            step_type="intent_recognition",
            description=f"Recognized intent: {best_intent.value}",
            input_data=user_input,
            output_data=intent_result.__dict__,
            confidence=confidence
        )
        
        return intent_result
    
    async def _retrieve_context(
        self,
        user_input: str,
        intent_result: Any,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> List[MemoryEntry]:
        """Retrieve relevant context from memory"""
        relevant_memories = []
        
        try:
            # Vector memory search for semantic similarity
            search_results = self.vector_memory.search(
                query=user_input,
                limit=5,
                threshold=0.6,
                memory_type=intent_result.intent
            )
            
            for result in search_results:
                memory_entry = MemoryEntry(
                    id=result.metadata.get("id", ""),
                    content=result.content,
                    memory_type=MemoryType(result.metadata.get("memory_type", "semantic")),
                    importance=result.metadata.get("importance", 0.5),
                    tags=result.metadata.get("tags", [])
                )
                relevant_memories.append(memory_entry)
            
            # Add reasoning step
            reasoning_trace.add_step(
                step_type="context_retrieval",
                description=f"Retrieved {len(relevant_memories)} relevant memories",
                input_data={"query": user_input, "intent": intent_result.intent.value},
                output_data=[m.content for m in relevant_memories],
                confidence=min(0.9, len(relevant_memories) * 0.2 + 0.3)
            )
            
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            reasoning_trace.add_step(
                step_type="context_retrieval",
                description="Context retrieval failed",
                input_data=user_input,
                output_data=[],
                confidence=0.0
            )
        
        return relevant_memories
    
    async def _select_skill(
        self,
        user_input: str,
        intent_result: Any,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> Optional[str]:
        """Select appropriate skill for the task"""
        intent = intent_result.intent
        
        # Map intents to skill categories
        intent_to_category = {
            IntentType.CODE: SkillCategory.CODE_GENERATION,
            IntentType.DATA_ANALYSIS: SkillCategory.DATA_ANALYSIS,
            IntentType.PLANNING: SkillCategory.PLANNING,
            IntentType.REASONING: SkillCategory.GENERAL,
            IntentType.DEBUGGING: SkillCategory.GENERAL,
            IntentType.SYSTEM: SkillCategory.GENERAL
        }
        
        target_category = intent_to_category.get(intent, SkillCategory.GENERAL)
        
        # Find suitable skills
        available_skills = self.skill_categories.get(target_category, [])
        
        if not available_skills:
            # Fallback to general skills
            available_skills = self.skill_categories.get(SkillCategory.GENERAL, [])
        
        # Select skill (simple selection for now)
        selected_skill = available_skills[0] if available_skills else None
        
        reasoning_trace.add_step(
            step_type="skill_selection",
            description=f"Selected skill: {selected_skill or 'none'}",
            input_data={"intent": intent.value, "target_category": target_category.value},
            output_data={"selected_skill": selected_skill, "available_skills": available_skills},
            confidence=0.8 if selected_skill else 0.3
        )
        
        return selected_skill
    
    async def _execute_skill(
        self,
        skill_name: Optional[str],
        user_input: str,
        context: List[MemoryEntry],
        intent_result: Any,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> SkillResult:
        """Execute selected skill"""
        start_time = time.time()
        
        if not skill_name:
            # No skill selected, return empty result
            result = SkillResult(
                success=True,
                output="No specific skill needed",
                skill_name="none",
                execution_time=time.time() - start_time
            )
            
            reasoning_trace.add_step(
                step_type="skill_execution",
                description="No skill execution needed",
                input_data=user_input,
                output_data=result.output,
                confidence=0.5
            )
            
            return result
        
        try:
            # Get skill implementation
            skill = self.skills.get(skill_name)
            
            if not skill:
                result = SkillResult(
                    success=False,
                    output=f"Skill {skill_name} not found",
                    skill_name=skill_name,
                    execution_time=time.time() - start_time,
                    error_message="Skill implementation not found"
                )
                
                reasoning_trace.add_step(
                    step_type="skill_execution",
                    description=f"Skill {skill_name} not found",
                    input_data=user_input,
                    output_data=result.output,
                    confidence=0.0
                )
                
                return result
            
            # Create skill context
            skill_context = SkillContext(
                user_input=user_input,
                intent=intent_result.intent,  # This would need to be passed
                conversation_history=[],  # Would be populated from context
                memory_context=context
            )
            
            # Execute skill (simplified for base implementation)
            # In real implementation, this would call the actual skill method
            result = SkillResult(
                success=True,
                output=f"Skill {skill_name} executed successfully",
                skill_name=skill_name,
                execution_time=time.time() - start_time
            )
            
            reasoning_trace.add_step(
                step_type="skill_execution",
                description=f"Executed skill: {skill_name}",
                input_data=skill_context.__dict__,
                output_data=result.output,
                confidence=0.9
            )
            
        except Exception as e:
            result = SkillResult(
                success=False,
                output=f"Error executing skill {skill_name}",
                skill_name=skill_name,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
            
            reasoning_trace.add_step(
                step_type="skill_execution",
                description=f"Skill execution failed: {skill_name}",
                input_data=user_input,
                output_data=str(e),
                confidence=0.0
            )
        
        return result
    
    async def _generate_response(
        self,
        skill_result: SkillResult,
        user_input: str,
        context: List[MemoryEntry],
        reasoning_trace: MiniMaxReasoningTrace
    ) -> str:
        """Generate final response"""
        if skill_result.success:
            response = str(skill_result.output)
            
            # Add context if relevant memories were found
            if context:
                context_summary = f" [Context: {len(context)} relevant memories considered]"
                response += context_summary
        else:
            response = f"I apologize, but I encountered an issue: {skill_result.error_message or 'Unknown error'}"
        
        reasoning_trace.add_step(
            step_type="response_generation",
            description="Generated final response",
            input_data={"skill_result": skill_result.success, "context_count": len(context)},
            output_data=response,
            confidence=0.8 if skill_result.success else 0.3
        )
        
        return response
    
    async def _learn_from_interaction(
        self,
        user_input: str,
        response: str,
        intent_result: Any,
        skill_result: SkillResult
    ) -> None:
        """Learn from the interaction to improve future responses"""
        try:
            # Extract patterns for learning
            learning_data = {
                "input_pattern": user_input.lower(),
                "intent": intent_result.intent.value if intent_result else "unknown",
                "confidence": getattr(intent_result, 'confidence', 0.0),
                "skill_used": skill_result.skill_name,
                "success": skill_result.success,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update learned patterns
            pattern_key = f"{intent_result.intent.value}_{skill_result.skill_name}"
            if pattern_key not in self.learned_patterns:
                self.learned_patterns[pattern_key] = []
            
            self.learned_patterns[pattern_key].append(learning_data)
            
            # Update user preferences based on successful interactions
            if skill_result.success:
                user_input_lower = user_input.lower()
                if user_input_lower not in self.user_preferences:
                    self.user_preferences[user_input_lower] = {
                        "count": 0,
                        "successful_skills": [],
                        "last_successful": None
                    }
                
                self.user_preferences[user_input_lower]["count"] += 1
                if skill_result.skill_name not in self.user_preferences[user_input_lower]["successful_skills"]:
                    self.user_preferences[user_input_lower]["successful_skills"].append(skill_result.skill_name)
                self.user_preferences[user_input_lower]["last_successful"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.warning(f"Learning failed: {e}")
    
    async def _store_in_memory(
        self,
        user_input: str,
        response: str,
        intent_result: Any,
        skill_result: Optional[SkillResult]
    ) -> None:
        """Store interaction in memory"""
        try:
            # Store in persistent memory
            conversation_id = self.memory.add_conversation(
                user_input=user_input,
                assistant_response=response,
                intent=getattr(intent_result, 'intent', {}).value if intent_result else None,
                skill_used=skill_result.skill_name if skill_result else None,
                metadata={
                    "confidence": getattr(intent_result, 'confidence', 0.0),
                    "success": skill_result.success if skill_result else False
                }
            )
            
            # Store relevant content in vector memory
            if intent_result and getattr(intent_result, 'confidence', 0.0) > 0.7:
                self.vector_memory.add_memory(
                    content=f"User: {user_input} | Assistant: {response}",
                    memory_type=MemoryType.EPISODIC,
                    importance=getattr(intent_result, 'confidence', 0.5),
                    metadata={
                        "conversation_id": conversation_id,
                        "intent": getattr(intent_result, 'intent', {}).value if intent_result else None,
                        "skill": skill_result.skill_name if skill_result else None
                    }
                )
            
        except Exception as e:
            logger.warning(f"Memory storage failed: {e}")
    
    def _update_performance_metrics(
        self,
        input_text: str,
        output_text: str,
        execution_time: float,
        success: bool
    ) -> None:
        """Update performance metrics"""
        metrics = PerformanceMetrics(
            operation_name="process_input",
            execution_time=execution_time,
            success=success,
            input_size=len(input_text),
            output_size=len(output_text),
            metadata={
                "processing_mode": self.processing_mode.value,
                "reasoning_strategy": self.reasoning_strategy.value,
                "total_requests": self.total_processed_requests
            }
        )
        
        self.performance_metrics.append(metrics)
        
        # Keep only recent metrics (last 1000)
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]
    
    def register_skill(self, skill_name: str, skill_instance: Any, category: SkillCategory) -> None:
        """Register a skill with the brain"""
        self.skills[skill_name] = skill_instance
        
        if category not in self.skill_categories:
            self.skill_categories[category] = []
        
        if skill_name not in self.skill_categories[category]:
            self.skill_categories[category].append(skill_name)
        
        logger.info(f"Registered skill: {skill_name} in category {category.value}")
    
    def unregister_skill(self, skill_name: str) -> None:
        """Unregister a skill from the brain"""
        if skill_name in self.skills:
            del self.skills[skill_name]
            
            # Remove from all categories
            for category_skills in self.skill_categories.values():
                if skill_name in category_skills:
                    category_skills.remove(skill_name)
            
            logger.info(f"Unregistered skill: {skill_name}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get brain status and statistics"""
        recent_metrics = [m for m in self.performance_metrics[-100:]] if self.performance_metrics else []
        
        avg_execution_time = (
            sum(m.execution_time for m in recent_metrics) / len(recent_metrics)
            if recent_metrics else 0.0
        )
        
        success_rate = (
            sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            if recent_metrics else 0.0
        )
        
        return {
            "processing_mode": self.processing_mode.value,
            "reasoning_strategy": self.reasoning_strategy.value,
            "is_processing": self.is_processing,
            "total_processed_requests": self.total_processed_requests,
            "registered_skills": len(self.skills),
            "skill_categories": {cat.value: len(skills) for cat, skills in self.skill_categories.items()},
            "learned_patterns": len(self.learned_patterns),
            "user_preferences": len(self.user_preferences),
            "recent_performance": {
                "average_execution_time": avg_execution_time,
                "success_rate": success_rate,
                "metrics_count": len(recent_metrics)
            },
            "memory_stats": {
                "conversations": len(self.memory.conversations),
                "vector_memories": len(self.vector_memory.vectors) if hasattr(self.vector_memory, 'vectors') else 0
            },
            "configuration": {
                "max_reasoning_steps": self.max_reasoning_steps,
                "confidence_threshold": self.confidence_threshold,
                "enable_learning": self.enable_learning,
                "enable_optimization": self.enable_optimization
            }
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Optimize brain performance based on usage patterns"""
        if not self.enable_optimization:
            return {"optimization_disabled": True}
        
        optimization_results = {}
        
        try:
            # Analyze performance patterns
            if self.performance_metrics:
                recent_metrics = self.performance_metrics[-50:]  # Last 50 requests
                
                # Identify slow operations
                slow_operations = [m for m in recent_metrics if m.execution_time > 2.0]
                if slow_operations:
                    optimization_results["slow_operations_detected"] = len(slow_operations)
                    
                    # Adjust reasoning strategy if needed
                    if len(slow_operations) > len(recent_metrics) * 0.3:
                        if self.reasoning_strategy == ReasoningStrategy.TREE_SEARCH:
                            self.reasoning_strategy = ReasoningStrategy.DIRECT
                            optimization_results["strategy_switched"] = "direct"
                        elif self.max_reasoning_steps > 5:
                            self.max_reasoning_steps = max(3, self.max_reasoning_steps - 2)
                            optimization_results["max_steps_reduced"] = self.max_reasoning_steps
                
                # Optimize confidence threshold based on success rate
                recent_success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
                if recent_success_rate < 0.7:
                    self.confidence_threshold = max(0.5, self.confidence_threshold - 0.1)
                    optimization_results["confidence_threshold_adjusted"] = self.confidence_threshold
                elif recent_success_rate > 0.9:
                    self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
                    optimization_results["confidence_threshold_adjusted"] = self.confidence_threshold
            
            # Clean up old metrics
            old_count = len(self.performance_metrics)
            if len(self.performance_metrics) > 500:
                self.performance_metrics = self.performance_metrics[-500:]
                optimization_results["metrics_cleaned"] = old_count - len(self.performance_metrics)
            
            logger.info(f"Performance optimization completed: {optimization_results}")
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            optimization_results["error"] = str(e)
        
        return optimization_results
    
    def shutdown(self) -> None:
        """Shutdown brain system"""
        logger.info("Shutting down Base Brain")
        
        # Perform final optimization
        if self.enable_optimization:
            self.optimize_performance()
        
        # Save learned patterns to persistent storage
        # (This would be implemented in a full system)
        
        logger.info("Base Brain shutdown complete")


# Singleton brain instance
_brain_instance: Optional[BaseBrain] = None
_brain_lock = threading.Lock()


def get_brain(
    processing_mode: ProcessingMode = ProcessingMode.STANDARD,
    reasoning_strategy: ReasoningStrategy = ReasoningStrategy.DIRECT
) -> BaseBrain:
    """
    Get singleton brain instance
    
    Args:
        processing_mode: Brain processing mode
        reasoning_strategy: Reasoning strategy
    
    Returns:
        BaseBrain singleton instance
    """
    global _brain_instance
    
    if _brain_instance is None:
        with _brain_lock:
            if _brain_instance is None:
                _brain_instance = BaseBrain(processing_mode, reasoning_strategy)
    
    return _brain_instance


def reset_brain() -> None:
    """Reset the brain instance"""
    global _brain_instance
    with _brain_lock:
        if _brain_instance:
            try:
                _brain_instance.shutdown()
            except Exception:
                pass
        _brain_instance = None
    logger.info("Brain instance reset")


def create_brain_instance(
    processing_mode: ProcessingMode = ProcessingMode.STANDARD,
    reasoning_strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
    max_reasoning_steps: int = 10,
    confidence_threshold: float = 0.7
) -> BaseBrain:
    """
    Create a new brain instance
    
    Args:
        processing_mode: Brain processing mode
        reasoning_strategy: Reasoning strategy
        max_reasoning_steps: Maximum reasoning steps
        confidence_threshold: Minimum confidence threshold
    
    Returns:
        New BaseBrain instance
    """
    return BaseBrain(
        processing_mode=processing_mode,
        reasoning_strategy=reasoning_strategy,
        max_reasoning_steps=max_reasoning_steps,
        confidence_threshold=confidence_threshold
    )