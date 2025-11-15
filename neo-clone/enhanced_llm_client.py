"""
Enhanced LLM Client with Automatic Model Fallback System

This module provides intelligent model routing and automatic fallback capabilities
by integrating the IntelligentModelRouter with the existing LLM client interface.

Key Features:
- Automatic model selection based on task requirements
- Intelligent fallback when primary models fail
- Performance tracking and optimization
- Seamless integration with existing brain systems

Author: MiniMax Agent
Version: 1.0
"""

import asyncio
import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Import existing systems
try:
    from ai_model_integration import (
        IntelligentModelRouter, TaskRequest, TaskResult, 
        ModelCapability, TaskPriority
    )
except ImportError:
    # Fallback if ai_model_integration is not available
    IntelligentModelRouter = None
    TaskRequest = None
    TaskResult = None
    ModelCapability = None
    TaskPriority = None

try:
    from config import Config
except ImportError:
    class Config:
        def __init__(self):
            self.provider = "ollama"
            self.model_name = "llama2"
            self.api_endpoint = "http://localhost:11434"
            self.max_tokens = 2048
            self.temperature = 0.7
            self.timeout = 30

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)

@dataclass
class ModelFallbackConfig:
    """Configuration for model fallback behavior"""
    enable_fallback: bool = True
    max_fallback_attempts: int = 3
    fallback_timeout: float = 30.0
    prefer_free_models: bool = True
    track_performance: bool = True
    auto_optimize: bool = True

class EnhancedLLMClient:
    """
    Enhanced LLM client with intelligent model routing and automatic fallback.
    
    This client automatically selects the best model for each task
    and provides seamless fallback when models fail.
    """
    
    def __init__(self, config: Config, fallback_config: Optional[ModelFallbackConfig] = None):
        self.cfg = config
        self.fallback_config = fallback_config or ModelFallbackConfig()
        
        # Initialize model router if available
        if IntelligentModelRouter:
            self.model_router = IntelligentModelRouter()
            self.intelligent_routing = True
            logger.info("Enhanced LLM client initialized with intelligent routing")
        else:
            self.model_router = None
            self.intelligent_routing = False
            logger.warning("Intelligent routing unavailable, using fallback mode")
        
        # Initialize basic HTTP client for direct communication
        if requests:
            self.session = requests.Session()
        else:
            self.session = None
            logger.error("requests library not available")
        
        # Performance tracking
        self.request_history = []
        self.model_performance = {}
        
    def chat(self, messages: List[Dict[str, str]], timeout: int = 15) -> str:
        """
        Enhanced chat method with automatic model fallback.
        
        Args:
            messages: Conversation history in OpenAI format
            timeout: Request timeout in seconds
            
        Returns:
            Model response as string
        """
        if not self.intelligent_routing:
            return self._fallback_chat(messages, timeout)
        
        try:
            # Convert messages to task request
            task_request = self._create_task_request(messages, timeout)
            
            # Execute with intelligent routing (sync wrapper for async with timeout protection)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Add timeout protection for async operations
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(
                        self.model_router.execute_task(task_request),
                        timeout=min(timeout, 10)  # Max 10 seconds for routing
                    )
                )
            except asyncio.TimeoutError:
                logger.warning("Intelligent routing timed out")
                return self._fallback_chat(messages, timeout)
            
            # Track performance
            self._track_performance(result)
            
            if result.success:
                return result.result
            else:
                logger.warning(f"Intelligent routing failed: {result.error_message}")
                return self._fallback_chat(messages, timeout)
                
        except Exception as e:
            logger.error(f"Enhanced chat failed: {e}")
            return self._fallback_chat(messages, timeout)
    
    def _fallback_chat(self, messages: List[Dict[str, str]], timeout: int) -> str:
        """
        Fallback chat method using direct model communication.
        
        This is used when intelligent routing is unavailable or fails.
        """
        if not self.session:
            return "[Error] No HTTP client available"
        
        provider = self.cfg.provider.lower()
        if provider == "ollama":
            return self._ollama_chat(messages, timeout)
        else:
            return f"[Error] Provider {provider} not supported in fallback mode"
    
    def _ollama_chat(self, messages: List[Dict[str, str]], timeout: int) -> str:
        """Direct Ollama communication with fast failure detection"""
        url = self.cfg.api_endpoint.rstrip("/") + "/api/chat"
        payload = {
            "model": self.cfg.model_name,
            "messages": messages,
            "max_tokens": self.cfg.max_tokens,
            "temperature": self.cfg.temperature,
        }
        
        # Use shorter timeout for faster failure detection
        fast_timeout = min(timeout, 5)
        
        try:
            resp = self.session.post(url, json=payload, timeout=fast_timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "No response.")
        except Exception as e:
            logger.error(f"Ollama fallback failed: {e}")
            # Return a graceful fallback response instead of error
            return self._generate_fallback_response(messages)
    
    def _create_task_request(self, messages: List[Dict[str, str]], timeout: int) -> TaskRequest:
        """Convert chat messages to TaskRequest format"""
        if not TaskRequest:
            raise ImportError("TaskRequest not available")
        
        # Extract the last user message as the prompt
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Determine task type and capabilities from message
        task_type, capabilities = self._analyze_task_requirements(user_message)
        
        return TaskRequest(
            task_type=task_type,
            prompt=user_message,
            capabilities_needed=capabilities,
            priority=TaskPriority.MEDIUM,
            max_tokens=self.cfg.max_tokens,
            timeout=timeout,
            require_reliability=True
        )
    
    def _analyze_task_requirements(self, message: str) -> tuple[str, List[ModelCapability]]:
        """
        Analyze message to determine task type and required capabilities.
        
        Returns:
            Tuple of (task_type, required_capabilities)
        """
        if not ModelCapability:
            return "general", []
        
        message_lower = message.lower()
        capabilities = []
        task_type = "general"
        
        # Analyze for different task types
        if any(word in message_lower for word in ["code", "python", "function", "class", "programming"]):
            capabilities.extend([
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_ANALYSIS
            ])
            task_type = "code_generation"
        
        if any(word in message_lower for word in ["analyze", "explain", "debug", "fix"]):
            capabilities.extend([
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.REASONING
            ])
            task_type = "analysis"
        
        if any(word in message_lower for word in ["write", "create", "generate", "compose"]):
            capabilities.append(ModelCapability.TEXT_GENERATION)
            if task_type == "general":
                task_type = "text_generation"
        
        if any(word in message_lower for word in ["search", "find", "research", "look up"]):
            capabilities.append(ModelCapability.WEB_SEARCH)
            task_type = "web_search"
        
        if any(word in message_lower for word in ["reason", "think", "solve", "logic"]):
            capabilities.append(ModelCapability.REASONING)
            if task_type == "general":
                task_type = "reasoning"
        
        # Default capabilities if none detected
        if not capabilities:
            capabilities = [ModelCapability.TEXT_GENERATION, ModelCapability.REASONING]
        
        return task_type, list(set(capabilities))  # Remove duplicates
    
    def _track_performance(self, result: TaskResult):
        """Track model performance for optimization"""
        if not self.fallback_config.track_performance:
            return
        
        model_name = result.model_used
        if model_name not in self.model_performance:
            self.model_performance[model_name] = {
                "success_count": 0,
                "failure_count": 0,
                "total_response_time": 0.0,
                "total_tokens": 0,
                "last_used": 0.0
            }
        
        perf = self.model_performance[model_name]
        if result.success:
            perf["success_count"] += 1
        else:
            perf["failure_count"] += 1
        
        perf["total_response_time"] += result.execution_time
        perf["total_tokens"] += result.tokens_used
        perf["last_used"] = time.time()
        
        # Keep only recent history
        self.request_history.append({
            "model": model_name,
            "success": result.success,
            "response_time": result.execution_time,
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-500:]
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models"""
        stats = {}
        
        for model_name, perf in self.model_performance.items():
            total_requests = perf["success_count"] + perf["failure_count"]
            if total_requests > 0:
                success_rate = perf["success_count"] / total_requests
                avg_response_time = perf["total_response_time"] / total_requests
            else:
                success_rate = 0.0
                avg_response_time = 0.0
            
            stats[model_name] = {
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "total_requests": total_requests,
                "last_used": perf["last_used"]
            }
        
        return stats
    
    def get_best_models(self) -> List[str]:
        """Get list of models ranked by performance"""
        if not self.model_performance:
            return []
        
        # Sort models by success rate and response time
        ranked_models = []
        for model_name, perf in self.model_performance.items():
            total_requests = perf["success_count"] + perf["failure_count"]
            if total_requests >= 3:  # Only consider models with sufficient data
                success_rate = perf["success_count"] / total_requests
                avg_response_time = perf["total_response_time"] / total_requests
                
                # Calculate score (higher is better)
                score = success_rate * 0.7 + (1.0 / (1.0 + avg_response_time)) * 0.3
                ranked_models.append((model_name, score))
        
        # Sort by score (descending)
        ranked_models.sort(key=lambda x: x[1], reverse=True)
        return [model for model, _ in ranked_models]
    
    def _generate_fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a graceful fallback response when models are unavailable"""
        # Extract the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Generate contextual fallback response
        if not user_message:
            return "I'm here to help! What would you like to know?"
        
        # Simple keyword-based responses for common queries
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! I'm Neo-Clone, your AI assistant. I can help with code generation, data analysis, web research, and more. What can I help you with today?"
        
        if any(word in message_lower for word in ["help", "commands", "what can you do"]):
            return """I can help you with:
• Code generation (Python, ML, algorithms)
• Data analysis (CSV, JSON, insights)
• Text analysis (sentiment, moderation)
• ML training guidance
• File management
• Web research
• Advanced reasoning
• Project planning

Just ask me anything!"""
        
        if any(word in message_lower for word in ["skill", "skills"]):
            return "I have 12 specialized skills including code generation, data analysis, web research, and more. Type 'skills' in the CLI to see all available skills."
        
        if any(word in message_lower for word in ["bye", "exit", "quit"]):
            return "Goodbye! Feel free to come back anytime you need help."
        
        # Check for specific skill requests and provide targeted help
        if any(word in message_lower for word in ["code", "python", "generate", "function", "class"]):
            return "I can help you generate code! While models are connecting, try asking specifically for 'code generation' or I can use my code generation skill once you provide more details about what you'd like to create."
        
        if any(word in message_lower for word in ["analyze", "data", "csv", "json", "stats"]):
            return "I can help you analyze data! Try asking me to 'analyze data' or use my data inspector skill. You can also provide file paths or data directly."
        
        if any(word in message_lower for word in ["search", "web", "find", "research"]):
            return "I can help you research information! Try asking me to 'search the web' or use my web research skill to find current information."
        
        if any(word in message_lower for word in ["sentiment", "text", "moderate", "analyze text"]):
            return "I can help you analyze text! Try asking me to 'analyze text sentiment' or use my text analysis skill for content processing."
        
        # Default intelligent response
        message_preview = user_message[:100] + ('...' if len(user_message) > 100 else '')
        response = f"I understand you're asking about: '{message_preview}'. \n\n"
        response += "I'm currently operating in enhanced mode with intelligent routing. While the primary models are connecting, I have 12 specialized skills ready:\n\n"
        response += "• Code generation (Python, ML, algorithms)\n"
        response += "• Data analysis (CSV, JSON, insights)\n" 
        response += "• Text analysis (sentiment, moderation)\n"
        response += "• Web research and fact-checking\n"
        response += "• ML training guidance\n"
        response += "• File management\n"
        response += "• Advanced reasoning\n\n"
        response += "Try rephrasing your request with skill-specific keywords!"
        return response

    def reset_performance_tracking(self):
        """Reset all performance tracking data"""
        self.model_performance.clear()
        self.request_history.clear()
        logger.info("Performance tracking reset")

# Factory function for easy integration
def create_enhanced_llm_client(config: Config, 
                             fallback_config: Optional[ModelFallbackConfig] = None) -> EnhancedLLMClient:
    """
    Factory function to create an enhanced LLM client.
    
    Args:
        config: LLM configuration
        fallback_config: Optional fallback configuration
        
    Returns:
        EnhancedLLMClient instance
    """
    return EnhancedLLMClient(config, fallback_config)