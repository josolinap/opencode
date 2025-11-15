"""
Enhanced error handling and resilience utilities for Neo-Clone
Provides circuit breakers, retry mechanisms, and graceful degradation
"""

import time
import logging
import functools
from typing import Any, Callable, Dict, Optional, Type, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    error_type: str
    severity: ErrorSeverity
    retry_count: int = 0
    last_error_time: float = field(default_factory=time.time)
    recovery_suggestions: list = field(default_factory=list)


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception(
                        "Circuit breaker is OPEN - service temporarily unavailable"
                    )

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker returning to CLOSED state")
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(
                        f"Circuit breaker OPENED after {self.failure_count} failures"
                    )

                raise e

        return wrapper


class RetryManager:
    """Advanced retry manager with exponential backoff and jitter"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == self.max_retries:
                        logger.error(
                            f"All {self.max_retries} retries failed for {func.__name__}: {e}"
                        )
                        raise e

                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (self.backoff_factor**attempt), self.max_delay
                    )

                    # Add jitter to prevent thundering herd
                    if self.jitter:
                        import random

                        delay *= 0.5 + random.random() * 0.5

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)

            raise last_exception

        return wrapper


class GracefulDegradation:
    """Graceful degradation when services are unavailable"""

    def __init__(self, fallback_functions: Optional[Dict[str, Callable]] = None):
        self.fallback_functions = fallback_functions or {}
        self.service_status = {}

    def __call__(self, service_name: str, fallback_key: str = None):
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    self.service_status[service_name] = "healthy"
                    return result
                except Exception as e:
                    self.service_status[service_name] = f"degraded: {str(e)}"
                    logger.warning(
                        f"Service {service_name} degraded, using fallback: {e}"
                    )

                    # Try fallback function
                    if fallback_key and fallback_key in self.fallback_functions:
                        try:
                            fallback_result = self.fallback_functions[fallback_key](
                                *args, **kwargs
                            )
                            logger.info(
                                f"Fallback {fallback_key} succeeded for service {service_name}"
                            )
                            return fallback_result
                        except Exception as fallback_error:
                            logger.error(
                                f"Fallback {fallback_key} also failed: {fallback_error}"
                            )

                    # Return graceful degradation response
                    return self._get_degradation_response(service_name, e)

            return wrapper

        return decorator

    def _get_degradation_response(self, service_name: str, error: Exception) -> Any:
        """Get appropriate degradation response based on service"""
        degradation_responses = {
            "llm": f"[AI Service Temporarily Unavailable] I'm experiencing technical difficulties with my language model. Please try again in a few moments. Error: {str(error)}",
            "memory": "[Memory Service Unavailable] I can't access my memory right now, but I can still help with your current request.",
            "skills": "[Skills Service Limited] Some advanced features are unavailable, but I can still assist with basic tasks.",
            "plugins": "[Plugin Service Unavailable] Custom plugins are temporarily unavailable.",
            "web_search": "[Web Search Unavailable] I can't search the web right now, but I can help with other tasks.",
            "code_generation": "[Code Generation Limited] I'm having trouble with advanced code generation, but I can provide basic code examples.",
        }

        return degradation_responses.get(
            service_name,
            f"[Service Degraded] {service_name} is experiencing issues: {str(error)}",
        )

    def get_service_health(self) -> Dict[str, str]:
        """Get health status of all services"""
        return self.service_status.copy()


class ErrorAnalyzer:
    """Analyze errors and provide recovery suggestions"""

    def __init__(self):
        self.error_patterns = {
            "connection": {
                "keywords": ["connection", "network", "timeout", "unreachable"],
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Check internet connection",
                    "Verify service endpoint is accessible",
                    "Try again in a few moments",
                    "Consider switching to offline mode",
                ],
            },
            "authentication": {
                "keywords": ["unauthorized", "forbidden", "api key", "auth"],
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Verify API key is correct",
                    "Check API key permissions",
                    "Regenerate API key if needed",
                    "Ensure account is in good standing",
                ],
            },
            "rate_limit": {
                "keywords": ["rate limit", "too many requests", "quota", "429"],
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Wait before making more requests",
                    "Upgrade to higher tier plan",
                    "Implement request batching",
                    "Use caching to reduce requests",
                ],
            },
            "model_unavailable": {
                "keywords": ["model not found", "unavailable", "does not exist"],
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Check model name spelling",
                    "List available models",
                    "Try a different model",
                    "Update model repository",
                ],
            },
            "resource_exhausted": {
                "keywords": ["memory", "disk space", "cpu", "resources"],
                "severity": ErrorSeverity.CRITICAL,
                "suggestions": [
                    "Free up system resources",
                    "Restart the application",
                    "Increase resource limits",
                    "Check for memory leaks",
                ],
            },
        }

    def analyze_error(self, error_message: str) -> ErrorContext:
        """Analyze error and provide context"""
        error_lower = error_message.lower()

        for pattern_name, pattern_data in self.error_patterns.items():
            if any(keyword in error_lower for keyword in pattern_data["keywords"]):
                return ErrorContext(
                    error_type=pattern_name,
                    severity=pattern_data["severity"],
                    recovery_suggestions=pattern_data["suggestions"],
                )

        # Unknown error
        return ErrorContext(
            error_type="unknown",
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Try the operation again",
                "Check system logs for details",
                "Restart the application",
                "Contact support if issue persists",
            ],
        )


class ResilienceManager:
    """Central resilience management for Neo-Clone"""

    def __init__(self):
        self.circuit_breakers = {}
        self.retry_managers = {}
        self.degradation = GracefulDegradation()
        self.error_analyzer = ErrorAnalyzer()
        self.error_history = []

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(**kwargs)
        return self.circuit_breakers[name]

    def get_retry_manager(self, name: str, **kwargs) -> RetryManager:
        """Get or create retry manager for a service"""
        if name not in self.retry_managers:
            self.retry_managers[name] = RetryManager(**kwargs)
        return self.retry_managers[name]

    def handle_error(self, service_name: str, error: Exception, context: str = ""):
        """Handle error with appropriate resilience strategy"""
        error_context = self.error_analyzer.analyze_error(str(error))
        error_context.last_error_time = time.time()

        # Log error with context
        logger.error(
            f"Service {service_name} error in {context}: {error} (Type: {error_context.error_type}, Severity: {error_context.severity.value})"
        )

        # Add to history
        self.error_history.append(
            {
                "service": service_name,
                "error": str(error),
                "context": context,
                "error_context": error_context,
                "timestamp": time.time(),
            }
        )

        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

        return error_context

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        service_health = self.degradation.get_service_health()

        # Calculate error rates
        recent_errors = [
            e for e in self.error_history if time.time() - e["timestamp"] < 3600
        ]  # Last hour
        error_rate = len(recent_errors) / 60  # Errors per minute

        # Circuit breaker status
        circuit_status = {name: cb.state for name, cb in self.circuit_breakers.items()}

        return {
            "overall_health": "healthy"
            if error_rate < 1
            else "degraded"
            if error_rate < 5
            else "critical",
            "error_rate_per_minute": error_rate,
            "service_health": service_health,
            "circuit_breaker_status": circuit_status,
            "recent_errors": len(recent_errors),
            "total_errors": len(self.error_history),
        }


# Global resilience manager
resilience = ResilienceManager()


# Decorators for easy use
def with_circuit_breaker(service_name: str, **kwargs):
    """Decorator to add circuit breaker to function"""

    def decorator(func):
        circuit_breaker = resilience.get_circuit_breaker(service_name, **kwargs)
        return circuit_breaker(func)

    return decorator


def with_retry(service_name: str, **kwargs):
    """Decorator to add retry logic to function"""

    def decorator(func):
        retry_manager = resilience.get_retry_manager(service_name, **kwargs)
        return retry_manager(func)

    return decorator


def with_graceful_degradation(service_name: str, fallback_key: Optional[str] = None):
    """Decorator to add graceful degradation to function"""
    return resilience.degradation(service_name, fallback_key)
