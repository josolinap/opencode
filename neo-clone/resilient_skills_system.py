"""
Resilient Skills System for Neo-Clone

Enhanced skills system with integrated error recovery, fallback mechanisms,
and intelligent tool switching when individual tools fail.
"""

import time
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import json
from pathlib import Path

# Import existing systems
from enhanced_error_recovery import EnhancedErrorRecovery, get_error_recovery, ErrorSeverity, ErrorCategory
from skills import BaseSkill, SkillResult, SkillRegistry

logger = logging.getLogger(__name__)

class SkillExecutionStatus(Enum):
    """Skill execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    RECOVERED = "recovered"
    FALLBACK_USED = "fallback_used"
    CIRCUIT_OPEN = "circuit_open"

@dataclass
class SkillExecutionResult:
    """Enhanced result for skill execution with resilience info"""
    status: SkillExecutionStatus
    result: SkillResult
    execution_time: float
    recovery_attempts: int = 0
    recovery_method: Optional[str] = None
    fallback_used: bool = False
    error_details: Optional[str] = None

@dataclass
class SkillFallbackConfig:
    """Configuration for skill fallback mechanisms"""
    primary_skill: str
    fallback_skills: List[str]
    fallback_conditions: List[str] = field(default_factory=list)
    max_fallback_attempts: int = 3
    timeout_seconds: float = 30.0

class ResilientSkillExecutor:
    """Enhanced skill executor with resilience and fallback capabilities"""
    
    def __init__(self, skill_registry: SkillRegistry = None):
        self.skill_registry = skill_registry or SkillRegistry()
        self.error_recovery = get_error_recovery()
        self.fallback_configs: Dict[str, SkillFallbackConfig] = {}
        self.execution_history: List[SkillExecutionResult] = []
        self.circuit_breakers: Dict[str, Any] = {}
        self._initialize_default_fallbacks()
        self._enable_auto_recovery()
    
    def _initialize_default_fallbacks(self):
        """Initialize default fallback configurations"""
        # Web search fallbacks
        self.fallback_configs["web_search"] = SkillFallbackConfig(
            primary_skill="web_search",
            fallback_skills=["file_manager", "data_inspector"],
            fallback_conditions=["network", "timeout", "rate_limit"]
        )
        
        # Data analysis fallbacks
        self.fallback_configs["data_inspector"] = SkillFallbackConfig(
            primary_skill="data_inspector",
            fallback_skills=["file_manager", "text_analysis"],
            fallback_conditions=["memory", "validation"]
        )
        
        # File operations fallbacks
        self.fallback_configs["file_manager"] = SkillFallbackConfig(
            primary_skill="file_manager",
            fallback_skills=["text_analysis", "web_search"],
            fallback_conditions=["system", "permission"]
        )
    
    def _enable_auto_recovery(self):
        """Enable automatic error recovery for skills"""
        self.error_recovery.enable_auto_healing()
        self.error_recovery.enable_learning()
    
    def register_fallback_config(self, config: SkillFallbackConfig):
        """Register a new fallback configuration"""
        self.fallback_configs[config.primary_skill] = config
        logger.info(f"Registered fallback config for {config.primary_skill}")
    
    def execute_skill_with_resilience(self, skill_name: str, params: Dict[str, Any]) -> SkillExecutionResult:
        """Execute a skill with full resilience and fallback support"""
        start_time = time.time()
        recovery_attempts = 0
        recovery_method = None
        fallback_used = False
        error_details = None
        
        try:
            # Get primary skill
            skill = self.skill_registry.get_skill(skill_name)
            if not skill:
                # Try to find alternative skill
                alternative = self._find_alternative_skill(skill_name, params)
                if alternative:
                    skill_name = alternative
                    skill = self.skill_registry.get_skill(skill_name)
                    fallback_used = True
                else:
                    return SkillExecutionResult(
                        status=SkillExecutionStatus.FAILED,
                        result=SkillResult(False, f"Skill '{skill_name}' not found and no alternatives available"),
                        execution_time=time.time() - start_time,
                        error_details="Skill not found"
                    )
            
            # Execute with circuit breaker protection
            try:
                result = self.error_recovery.protected_call(
                    f"skill_{skill_name}",
                    skill.execute,
                    params
                )
                
                return SkillExecutionResult(
                    status=SkillExecutionStatus.SUCCESS,
                    result=result,
                    execution_time=time.time() - start_time
                )
                
            except Exception as primary_error:
                error_details = str(primary_error)
                logger.warning(f"Primary skill {skill_name} failed: {primary_error}")
                
                # Attempt recovery
                context = {
                    'skill_name': skill_name,
                    'params': params,
                    'function': skill.execute,
                    'args': [params],
                    'kwargs': {}
                }
                
                recovered, method = self.error_recovery.attempt_recovery(primary_error, context)
                recovery_attempts += 1
                recovery_method = method
                
                if recovered:
                    # Try the skill again after recovery
                    try:
                        result = skill.execute(params)
                        return SkillExecutionResult(
                            status=SkillExecutionStatus.RECOVERED,
                            result=result,
                            execution_time=time.time() - start_time,
                            recovery_attempts=recovery_attempts,
                            recovery_method=recovery_method
                        )
                    except Exception as retry_error:
                        logger.warning(f"Retry after recovery failed: {retry_error}")
                
                # Try fallback skills
                fallback_result = self._try_fallback_skills(skill_name, params, primary_error)
                if fallback_result:
                    fallback_used = True
                    return SkillExecutionResult(
                        status=SkillExecutionStatus.FALLBACK_USED,
                        result=fallback_result,
                        execution_time=time.time() - start_time,
                        recovery_attempts=recovery_attempts,
                        fallback_used=fallback_used,
                        error_details=error_details
                    )
                
                # All attempts failed
                return SkillExecutionResult(
                    status=SkillExecutionStatus.FAILED,
                    result=SkillResult(False, f"Skill execution failed: {error_details}"),
                    execution_time=time.time() - start_time,
                    recovery_attempts=recovery_attempts,
                    recovery_method=recovery_method,
                    error_details=error_details
                )
                
        except Exception as system_error:
            logger.error(f"System error in skill execution: {system_error}")
            return SkillExecutionResult(
                status=SkillExecutionStatus.FAILED,
                result=SkillResult(False, f"System error: {system_error}"),
                execution_time=time.time() - start_time,
                error_details=str(system_error)
            )
        finally:
            # Record execution
            execution_result = SkillExecutionResult(
                status=SkillExecutionStatus.SUCCESS,  # Will be overwritten if failed
                result=SkillResult(True, ""),  # Will be overwritten
                execution_time=time.time() - start_time,
                recovery_attempts=recovery_attempts,
                recovery_method=recovery_method,
                fallback_used=fallback_used,
                error_details=error_details
            )
            self.execution_history.append(execution_result)
    
    def _find_alternative_skill(self, failed_skill: str, params: Dict[str, Any]) -> Optional[str]:
        """Find an alternative skill based on parameters and failed skill"""
        # Simple heuristic-based alternative finding
        text_content = params.get("text", "").lower()
        
        if "search" in text_content or "find" in text_content:
            return "web_search"
        elif "data" in text_content or "analyze" in text_content:
            return "data_inspector"
        elif "file" in text_content or "read" in text_content:
            return "file_manager"
        elif "sentiment" in text_content or "feeling" in text_content:
            return "text_analysis"
        
        return None
    
    def _try_fallback_skills(self, primary_skill: str, params: Dict[str, Any], original_error: Exception) -> Optional[SkillResult]:
        """Try fallback skills when primary skill fails"""
        fallback_config = self.fallback_configs.get(primary_skill)
        if not fallback_config:
            return None
        
        error_message = str(original_error).lower()
        
        # Check if fallback should be triggered
        should_fallback = (
            not fallback_config.fallback_conditions or
            any(condition in error_message for condition in fallback_config.fallback_conditions)
        )
        
        if not should_fallback:
            return None
        
        # Try each fallback skill
        for fallback_skill_name in fallback_config.fallback_skills:
            try:
                fallback_skill = self.skill_registry.get_skill(fallback_skill_name)
                if fallback_skill:
                    logger.info(f"Trying fallback skill: {fallback_skill_name}")
                    result = fallback_skill.execute(params)
                    if result.success:
                        logger.info(f"Fallback skill {fallback_skill_name} succeeded")
                        return result
            except Exception as fallback_error:
                logger.warning(f"Fallback skill {fallback_skill_name} failed: {fallback_error}")
                continue
        
        return None
    
    def get_resilience_statistics(self) -> Dict[str, Any]:
        """Get comprehensive resilience statistics"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "recovery_rate": 0.0,
                "fallback_rate": 0.0,
                "avg_execution_time": 0.0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e.status == SkillExecutionStatus.SUCCESS)
        recovered = sum(1 for e in self.execution_history if e.status == SkillExecutionStatus.RECOVERED)
        fallback_used = sum(1 for e in self.execution_history if e.status == SkillExecutionStatus.FALLBACK_USED)
        
        execution_times = [e.execution_time for e in self.execution_history]
        avg_execution_time = sum(execution_times) / len(execution_times)
        
        return {
            "total_executions": total,
            "success_rate": successful / total,
            "recovery_rate": recovered / total,
            "fallback_rate": fallback_used / total,
            "avg_execution_time": avg_execution_time,
            "error_recovery_stats": self.error_recovery.get_error_statistics(),
            "circuit_breaker_status": {
                name: cb.get_state() for name, cb in self.circuit_breakers.items()
            }
        }
    
    def create_resilient_skill_decorator(self, skill_name: str):
        """Create a decorator for making individual skills resilient"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                params = kwargs if kwargs else (args[0] if args else {})
                result = self.execute_skill_with_resilience(skill_name, params)
                return result.result
            return wrapper
        return decorator

class EnhancedSkillRegistry(SkillRegistry):
    """Enhanced skill registry with resilience features"""
    
    def __init__(self):
        super().__init__()
        self.resilient_executor = ResilientSkillExecutor(self)
    
    def execute_skill_resilient(self, skill_name: str, params: Dict[str, Any]) -> SkillExecutionResult:
        """Execute a skill with full resilience support"""
        return self.resilient_executor.execute_skill_with_resilience(skill_name, params)
    
    def register_resilient_skill(self, skill: BaseSkill, fallback_config: SkillFallbackConfig = None):
        """Register a skill with optional fallback configuration"""
        self.register_skill(skill)
        if fallback_config:
            self.resilient_executor.register_fallback_config(fallback_config)

# Global instance
_enhanced_registry = None

def get_enhanced_skill_registry() -> EnhancedSkillRegistry:
    """Get the global enhanced skill registry"""
    global _enhanced_registry
    if _enhanced_registry is None:
        _enhanced_registry = EnhancedSkillRegistry()
    return _enhanced_registry

def with_resilient_execution(skill_name: str):
    """Decorator for adding resilience to skill functions"""
    registry = get_enhanced_skill_registry()
    return registry.resilient_executor.create_resilient_skill_decorator(skill_name)

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the resilient skills system
    registry = get_enhanced_skill_registry()
    
    # Test successful execution
    print("Testing successful execution...")
    result = registry.execute_skill_resilient("text_analysis", {"text": "I love this amazing product!"})
    print(f"Result: {result.status} - {result.result.output}")
    
    # Test with non-existent skill (should trigger fallback)
    print("\nTesting fallback mechanism...")
    result = registry.execute_skill_resilient("non_existent_skill", {"text": "test"})
    print(f"Result: {result.status} - {result.result.output}")
    
    # Get statistics
    print("\nResilience Statistics:")
    stats = registry.resilient_executor.get_resilience_statistics()
    print(json.dumps(stats, indent=2, default=str))