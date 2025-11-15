"""
Central reasoning engine (Neo-like) and LLM integration.

Implements:
- Single LLM client per process (provider abstraction via config)
- Conversation context/history (last N turns)
- Intent parser (keyword-based, extensible)
- Skill router (map intent to skill from registry)
- Structured response (explanation + skill output)
- Error handling/logging
- Phase 2 advanced capabilities integration
"""

import json
import logging
import os
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from config import Config, get_config
from skills import SkillsManager
from model_analytics import ModelAnalytics
from framework_integrator import FrameworkIntegrator
from self_optimization import SelfOptimizationEngine
from enhanced_llm_client import EnhancedLLMClient
from ai_model_integration import IntelligentModelRouter
import requests

logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str
    content: str

class ConversationHistory:
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._messages: List[Message] = []

    def add(self, role: str, content: str):
        self._messages.append(Message(role=role, content=content))
        # Limit the history size
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]

    def to_list(self) -> List[Dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self._messages]

    def clear(self):
        self._messages = []

class LLMClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session = requests.Session()

    def chat(self, messages: List[Dict[str, str]], timeout: int = 15) -> str:
        provider = self.cfg.provider.lower()
        if provider == "ollama":
            # Ollama local API: POST /api/chat
            url = self.cfg.api_endpoint.rstrip("/") + "/api/chat"
            payload = {
                "model": self.cfg.model_name,
                "messages": messages,
                "max_tokens": self.cfg.max_tokens,
                "temperature": self.cfg.temperature,
            }
            try:
                resp = self.session.post(url, json=payload, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "No response.")
            except Exception as e:
                logger.error(f"Ollama call failed: {e}")
                return "[Neo Error] LLM unavailable: " + str(e)
        # Add more providers here (Together.ai, HF) if needed
        return "[Neo Error] Provider not supported or missing integration."

class Brain:
    def __init__(self, config: Config, skills: SkillsManager, llm_client: Optional[EnhancedLLMClient]=None):
        self.cfg = config
        self.skills = skills
        # Use Enhanced LLM Client with intelligent model routing
        self.llm = llm_client or EnhancedLLMClient(config)
        self.history = ConversationHistory(max_messages=20)
        self.analytics = ModelAnalytics()
        try:
            self.framework_integrator = FrameworkIntegrator(self)
        except TypeError:
            # FrameworkIntegrator may not be available or may require different parameters
            self.framework_integrator = None
        self.self_optimization = SelfOptimizationEngine(self)
        self.available_models = self._load_available_models()
        self.current_model = self._select_best_model()
        
        # Initialize intelligent model router for enhanced fallback
        try:
            self.model_router = IntelligentModelRouter()
            logger.info("[OK] Intelligent Model Router initialized for automatic fallback")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Intelligent Model Router: {e}")
            self.model_router = None
        
        # Initialize MiniMax Agent for enhanced skill activation
        try:
            from minimax_agent import get_minimax_agent
            self.minimax_agent = get_minimax_agent()
            logger.info("[OK] MiniMax Agent initialized for enhanced skill activation")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize MiniMax Agent: {e}")
            self.minimax_agent = None
        
        # Phase 2 Advanced Capabilities
        self._initialize_phase2_systems()

        # Initialize Autonomous Evolution Engine
        self._initialize_autonomous_evolution()

    def _initialize_phase2_systems(self):
        """Initialize Phase 2 advanced systems"""
        try:
            # Import Phase 2 systems
            from self_evolving_skills import GeneticSkillEvolver, SkillEvolutionManager
            from hierarchical_agents import MetaAgent, HierarchicalAgentManager
            from advanced_reasoning import TreeOfThoughtsReasoner, AdvancedReasoningManager
            
            # Initialize Self-Evolving Skills
            self.skill_evolver = GeneticSkillEvolver(population_size=20)
            self.skill_evolution_manager = SkillEvolutionManager()
            
            # Initialize Hierarchical Agents
            self.hierarchical_manager = HierarchicalAgentManager()
            agent_configs = [
                {"id": "exec_001", "name": "Executive Agent", "level": "executive"},
                {"id": "worker_001", "name": "Worker Agent", "level": "worker"}
            ]
            self.hierarchical_manager.initialize_hierarchy(agent_configs)
            
            # Initialize Advanced Reasoning
            self.advanced_reasoning_manager = AdvancedReasoningManager()
            
            logger.info("[OK] Phase 2 systems initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Phase 2 systems initialization failed: {e}")
            # Fallback to basic functionality
            self.skill_evolver = None
            self.skill_evolution_manager = None
            self.hierarchical_manager = None
            self.advanced_reasoning_manager = None

    def _initialize_autonomous_evolution(self):
        """Initialize the autonomous evolution engine functions (but don't start automatically)"""
        try:
            # Import functions instead of the full module to avoid global instance issues
            from autonomous_evolution_engine import start_evolution, get_evolution_status, stop_evolution, trigger_scan
            self.evolution_functions = {
                'start': start_evolution,
                'get_status': get_evolution_status,
                'stop': stop_evolution,
                'trigger_scan': trigger_scan
            }
            logger.info("[OK] Autonomous Evolution Engine functions initialized (start manually with evolution commands)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Autonomous Evolution Engine functions: {e}")
            self.evolution_functions = None

    def parse_intent(self, text: str) -> Dict[str, str]:
        lowered = text.lower()
        # Spec-Kit command detection (highest priority)
        if "/constitution" in lowered or "constitution" in lowered:
            return {"intent": "skill", "skill": "constitution"}
        if "/specify" in lowered or "/spec" in lowered or "specification" in lowered:
            return {"intent": "skill", "skill": "specification"}
        if "/plan" in lowered or "implementation plan" in lowered:
            return {"intent": "skill", "skill": "planning"}
        if "/tasks" in lowered or "task breakdown" in lowered:
            return {"intent": "skill", "skill": "task_breakdown"}
        if "/implement" in lowered or "implementation execution" in lowered:
            return {"intent": "skill", "skill": "implementation"}

        # Original skill routing
        if any(word in lowered for word in ["train", "model", "simulate", "recommend"]):
            return {"intent": "skill", "skill": "ml_training"}
        if any(word in lowered for word in ["sentiment", "analyze", "moderate", "toxic"]):
            return {"intent": "skill", "skill": "text_analysis"}
        if any(word in lowered for word in ["csv", "json", "data", "summary", "stats"]):
            return {"intent": "skill", "skill": "data_inspector"}
        if any(word in lowered for word in ["code", "python", "generate", "snippet", "explain"]):
            return {"intent": "skill", "skill": "code_generation"}
        if any(word in lowered for word in ["file", "read", "directory", "folder"]):
            return {"intent": "skill", "skill": "file_manager"}
        if any(word in lowered for word in ["search", "web", "find", "research"]):
            return {"intent": "skill", "skill": "web_search"}

        # Phase 2 Advanced Capabilities Detection
        if any(word in lowered for word in ["complex reasoning", "analyze deeply", "think through", "deep analysis"]):
            return {"intent": "advanced_reasoning"}
        
        if any(word in lowered for word in ["coordinate", "manage", "organize", "delegate", "team coordination"]):
            return {"intent": "hierarchical_coordination"}
        
        if any(word in lowered for word in ["evolve", "improve skills", "adapt", "optimize abilities", "skill evolution"]):
            return {"intent": "skill_evolution"}

        # Autonomous Evolution Engine commands
        if any(word in lowered for word in ["evolution", "autonomous", "scan codebase", "evolution status", "evolution report"]):
            return {"intent": "evolution_control"}

        return {"intent": "chat"}

    def route_to_skill(self, skill_name: str, text: str) -> Dict:
        try:
            skill = self.skills.get(skill_name)
            # Format params
            params = {"text": text}
            result = skill.execute(params)
            return {
                "chosen_skill": skill_name,
                "meta": {
                    "description": skill.description,
                    "example": skill.example_usage,
                },
                "output": result,
                "reasoning": f"Chose skill '{skill_name}' due to detected keywords."
            }
        except Exception as e:
            logger.error(f"Skill routing failed: {e}")
            return {"error": f"Skill routing failed: {e}"}

    def send_message(self, text: str) -> str:
        self.history.add("user", text)
        intent = self.parse_intent(text)
        
        # Debug: Log detected intent
        logger.info(f"Detected intent: {intent}")

        # Handle skill-based requests
        if intent["intent"] == "skill" and intent.get("skill"):
            skill_name = intent["skill"]
            start_time = time.time()
            result = self.route_to_skill(skill_name, text)
            response_time = time.time() - start_time

            # Record skill usage (always considered successful for now)
            self.record_model_usage(f"skill_{skill_name}", True, response_time)

            response = f"[Neo Reasoning] {result['reasoning']}\n[Skill Output]\n{result['output']}"
            self.history.add("assistant", f"[Skill:{skill_name}] {result}")
            return response

        # Handle Phase 2 Advanced Capabilities
        if intent["intent"] == "advanced_reasoning" and self.advanced_reasoning_manager:
            return self._handle_advanced_reasoning(text)
        
        if intent["intent"] == "hierarchical_coordination" and self.hierarchical_manager:
            return self._handle_hierarchical_coordination(text)
        
        if intent["intent"] == "skill_evolution" and self.skill_evolver:
            return self._handle_skill_evolution(text)

        # Handle Autonomous Evolution Engine commands
        if intent["intent"] == "evolution_control":
            return self._handle_evolution_control(text)

        # Enhanced skill execution with confidence scoring
        if hasattr(self, 'minimax_agent') and self.minimax_agent:
            try:
                # Get conversation context for enhanced analysis
                context_messages = [msg.content for msg in self.history._messages[-5:]]
                
                # Use enhanced MiniMax analysis
                intent_result = self.minimax_agent.analyze_user_input(text, context_messages)
                
                # Execute skills if confidence is high enough
                if intent_result["confidence"] > 0.7:
                    enhanced_response = self._execute_enhanced_skills(intent_result, text)
                    if enhanced_response:
                        self.history.add("assistant", enhanced_response)
                        return enhanced_response
            except Exception as e:
                logger.warning(f"Enhanced skill execution failed: {e}")
        
        # Handle chat requests with model fallback
        return self._send_chat_with_fallback(text)

    def _execute_enhanced_skills(self, intent_result: Dict, message: str) -> str:
        """Execute relevant skills based on enhanced intent analysis"""
        suggested_skills = intent_result.get("suggested_skills", [])
        responses = []
        skills_executed = []
        
        # Execute top 2 skills as per reference brain.py
        for skill_name in suggested_skills[:2]:
            if skill_name in self.skills.skills:
                try:
                    skill = self.skills.skills[skill_name]
                    start_time = time.time()
                    
                    # Execute skill with proper parameters
                    params = {"text": message, "confidence": intent_result.get("confidence", 0.5)}
                    result = skill.execute(params)
                    
                    execution_time = time.time() - start_time
                    
                    if result and result.strip():
                        # Format response with skill name labeling
                        formatted_response = f"**{skill_name}:** {result}"
                        responses.append(formatted_response)
                        skills_executed.append(skill_name)
                        
                        # Record skill usage
                        self.record_model_usage(f"enhanced_skill_{skill_name}", True, execution_time)
                        logger.info(f"✅ Executed enhanced skill: {skill_name} in {execution_time:.3f}s")
                    else:
                        logger.debug(f"Skill {skill_name} returned empty result")
                        
                except Exception as e:
                    logger.error(f"Error executing enhanced skill {skill_name}: {e}")
                    responses.append(f"**{skill_name}:** Error executing skill: {str(e)}")
        
        # Join multiple skill responses
        if responses:
            final_response = "\n\n".join(responses)
            
            # Add execution summary
            summary = f"[Enhanced Skill Execution] Skills used: {', '.join(skills_executed)} | Confidence: {intent_result.get('confidence', 0):.2f}"
            final_response = f"{summary}\n\n{final_response}"
            
            return final_response
        
        # Return None if no skills executed successfully
        return None

    def _handle_advanced_reasoning(self, text: str) -> str:
        """Handle advanced reasoning requests using Tree of Thoughts"""
        try:
            start_time = time.time()
            
            # Extract problem from text
            problem = text.replace("reasoning", "").replace("analyze deeply", "").replace("think through", "").strip()
            if not problem:
                problem = text
            
            # Use advanced reasoning
            result = self.advanced_reasoning_manager.reason(problem, {"request_type": "user_query"})
            response_time = time.time() - start_time
            
            # Record usage
            self.record_model_usage("advanced_reasoning", True, response_time)
            
            response = f"[🧠 Advanced Reasoning]\n"
            response += f"Confidence: {result.get('confidence', 0):.3f}\n"
            response += f"Thoughts Explored: {result.get('thoughts_count', 0)}\n\n"
            response += f"[Reasoning Result]\n{result.get('conclusion', 'No conclusion generated')}"
            
            self.history.add("assistant", f"[Advanced Reasoning] {result.get('conclusion', '')[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Advanced reasoning failed: {e}")
            return f"[❌ Advanced Reasoning Error] {str(e)}"

    def _handle_hierarchical_coordination(self, text: str) -> str:
        """Handle hierarchical coordination requests"""
        try:
            start_time = time.time()
            
            # Extract objectives from text
            objectives = [text]  # Simple extraction for now
            
            # Use hierarchical coordination
            result = self.hierarchical_manager.coordinate_system(objectives)
            response_time = time.time() - start_time
            
            # Record usage
            self.record_model_usage("hierarchical_coordination", True, response_time)
            
            response = f"[🏗️ Hierarchical Coordination]\n"
            response += f"Status: {result.get('status', 'unknown')}\n"
            response += f"Agents Involved: {len(result.get('agents_coordinated', []))}\n\n"
            response += f"[Coordination Result]\n{result.get('plan', 'No plan generated')}"
            
            self.history.add("assistant", f"[Hierarchical Coordination] {result.get('status', 'unknown')}")
            return response
            
        except Exception as e:
            logger.error(f"Hierarchical coordination failed: {e}")
            return f"[❌ Hierarchical Coordination Error] {str(e)}"

    def _handle_skill_evolution(self, text: str) -> str:
        """Handle skill evolution requests"""
        try:
            start_time = time.time()
            
            # Initialize skills if needed
            if not self.skill_evolution_manager.evolution_active:
                initial_skills = [
                    {"id": "adapt_001", "name": "Adaptive Analysis", "type": "analytical", "capabilities": ["data_analysis", "pattern_recognition"]},
                    {"id": "adapt_002", "name": "Creative Problem Solving", "type": "creative", "capabilities": ["innovation", "brainstorming"]}
                ]
                self.skill_evolution_manager.initialize_skills(initial_skills)
            
            # Trigger evolution
            self.skill_evolution_manager.trigger_evolution()
            response_time = time.time() - start_time
            
            # Record usage
            self.record_model_usage("skill_evolution", True, response_time)
            
            # Get evolution status
            evolution_status = self.skill_evolution_manager.get_evolution_status()
            
            response = f"[🧬 Skill Evolution]\n"
            response += f"Generation: {evolution_status.get('current_generation', 0)}\n"
            response += f"Population Size: {evolution_status.get('population_size', 0)}\n"
            response += f"Evolution Active: {evolution_status.get('evolution_active', False)}\n\n"
            response += f"[Evolution Status]\nEvolution cycle completed successfully"
            
            self.history.add("assistant", f"[Skill Evolution] Evolution completed")
            return response
            
        except Exception as e:
            logger.error(f"Skill evolution failed: {e}")
            return f"[❌ Skill Evolution Error] {str(e)}"

    def _handle_evolution_control(self, text: str) -> str:
        """Handle autonomous evolution engine control commands"""
        try:
            text_lower = text.lower()

            # Check for status/report commands
            if "status" in text_lower or "report" in text_lower:
                return self.get_evolution_report()

            # Check for start commands
            elif "start" in text_lower:
                success = self.start_evolution_engine()
                if success:
                    return "✅ Autonomous Evolution Engine started successfully"
                else:
                    return "❌ Failed to start Autonomous Evolution Engine"

            # Check for stop commands
            elif "stop" in text_lower:
                success = self.stop_evolution_engine()
                if success:
                    return "✅ Autonomous Evolution Engine stopped successfully"
                else:
                    return "❌ Failed to stop Autonomous Evolution Engine"

            # Check for scan commands
            elif "scan" in text_lower:
                result = self.trigger_evolution_scan()
                if result.get("success"):
                    opportunities = result.get("opportunities_found", 0)
                    return f"✅ Evolution scan completed. Found {opportunities} opportunities."
                else:
                    return f"❌ Evolution scan failed: {result.get('error', 'Unknown error')}"

            # Default to status report
            else:
                return self.get_evolution_report()

        except Exception as e:
            logger.error(f"Evolution control failed: {e}")
            return f"[❌ Evolution Control Error] {str(e)}"

    def _send_chat_with_fallback(self, user_message: str) -> str:
        """Send chat message with enhanced automatic model fallback"""
        try:
            # Use Enhanced LLM Client with intelligent routing if available
            if hasattr(self.llm, 'intelligent_router') and self.llm.intelligent_router:
                logger.info("🧠 Using intelligent model routing for automatic fallback")
                
                request_start_time = time.time()
                
                # Enhanced LLM Client will handle automatic fallback internally
                llm_response = self.llm.chat(self.history.to_list())
                response_duration = time.time() - request_start_time
                
                if not llm_response.startswith("[Neo Error]"):
                    self.history.add("assistant", llm_response)
                    # Record successful usage
                    self.record_model_usage("chat", True, response_duration)
                    return llm_response
                else:
                    # Record failed usage
                    self.record_model_usage("chat", False, response_duration, error_message=llm_response)
                    logger.warning(f"Intelligent routing failed: {llm_response}")
            
            # Fallback to manual model switching if intelligent routing fails
            logger.info("🔄 Using manual model fallback")
            return self._manual_model_fallback(user_message)
            
        except Exception as e:
            logger.error(f"Enhanced fallback failed: {e}")
            return self._manual_model_fallback(user_message)
    
    def _manual_model_fallback(self, user_message: str) -> str:
        """Manual model fallback as backup to intelligent routing"""
        max_retry_attempts = len(self.available_models) + 1  # Try all models plus original
        attempted_models = set()

        for retry_attempt in range(max_retry_attempts):
            try:
                # Try current model first
                active_model = self.current_model or f"{self.cfg.provider}/{self.cfg.model_name}"

                if active_model not in attempted_models:
                    attempted_models.add(active_model)
                    logger.info(f"Attempting to use model: {active_model}")

                    request_start_time = time.time()
                    llm_response = self.llm.chat(self.history.to_list())
                    response_duration = time.time() - request_start_time

                    if not llm_response.startswith("[Neo Error]"):
                        self.history.add("assistant", llm_response)
                        # Record successful usage
                        self.record_model_usage("chat", True, response_duration)
                        return llm_response

                    # Record failed usage
                    self.record_model_usage("chat", False, response_duration, error_message=llm_response)
                    logger.warning(f"Model {active_model} failed: {llm_response}")

                # Try switching to another available model
                available_models = [m for m in self.list_available_models() if m not in attempted_models]
                if available_models:
                    fallback_model = available_models[0]  # Try next available model
                    if self._switch_to_model_config(fallback_model):
                        attempted_models.add(fallback_model)
                        logger.info(f"Switched to fallback model: {fallback_model}")

                        fallback_start_time = time.time()
                        llm_response = self.llm.chat(self.history.to_list())
                        fallback_response_time = time.time() - fallback_start_time

                        if not llm_response.startswith("[Neo Error]"):
                            self.history.add("assistant", llm_response)
                            # Record successful usage
                            self.record_model_usage("chat", True, fallback_response_time)
                            return llm_response

                        # Record failed usage
                        self.record_model_usage("chat", False, fallback_response_time, error_message=llm_response)
                        logger.warning(f"Fallback model {fallback_model} also failed")

            except Exception as e:
                logger.error(f"Error in chat attempt {retry_attempt + 1}: {e}")

        # All models failed, use skills-only mode
        return self._fallback_skills_only_response()

    def _switch_to_model_config(self, model_id: str) -> bool:
        """Switch the LLM client to use a different model configuration"""
        try:
            model_info = self.get_model_info(model_id)
            if model_info:
                # Update config temporarily
                self.cfg.provider = model_info["provider"]
                self.cfg.model_name = model_info["model"]
                self.cfg.api_endpoint = model_info.get("endpoint", self.cfg.api_endpoint)
                self.cfg.max_tokens = model_info.get("context_length", self.cfg.max_tokens)

                # Recreate Enhanced LLM client with new config
                self.llm = EnhancedLLMClient(self.cfg)
                self.current_model = model_id
                logger.info(f"✅ Successfully switched to model: {model_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to switch to model {model_id}: {e}")

        return False

    def _fallback_skills_only_response(self) -> str:
        """Generate fallback response using skills when all models fail"""
        # Get the last user message to analyze for skill intent
        last_user_message = ""
        for msg in reversed(self.history._messages):
            if msg.role == "user":
                last_user_message = msg.content
                break
        
        if not last_user_message:
            # No user message found, provide generic help
            fallback = "I'm currently operating in skills-only mode since all language models are unavailable. "
            fallback += "I can still help with specialized tasks. Try asking me about:\n\n"
            
            skill_names = list(self.skills._skills.keys())
            for skill_name in sorted(skill_names)[:5]:  # Show top 5 skills
                skill = self.skills.get(skill_name)
                fallback += f"- **{skill_name}**: {skill.description}\n"
            
            fallback += "\nWhat would you like help with?"
            self.history.add("assistant", fallback)
            return fallback
        
        # Try to use appropriate skill based on the user's request
        intent = self.parse_intent(last_user_message)
        
        if intent["intent"] == "skill" and intent.get("skill"):
            # Direct skill request - use the skill
            skill_name = intent["skill"]
            try:
                skill = self.skills.get(skill_name)
                if skill:
                    start_time = time.time()
                    result = skill.execute({"text": last_user_message})
                    response_time = time.time() - start_time
                    
                    # Record skill usage
                    self.record_model_usage(f"skill_{skill_name}", True, response_time)
                    
                    response = f"[🛠️ Skills-Only Mode] Using {skill_name} skill\n\n"
                    response += f"[Skill Output]\n{result}"
                    
                    self.history.add("assistant", f"[Skills-Only:{skill_name}] {result[:100]}...")
                    return response
            except Exception as e:
                logger.error(f"Skill execution failed in fallback: {e}")
        
        # Check for code generation intent specifically
        if any(word in last_user_message.lower() for word in ["code", "python", "generate", "function", "class"]):
            try:
                skill = self.skills.get("code_generation")
                if skill:
                    start_time = time.time()
                    result = skill.execute({"text": last_user_message})
                    response_time = time.time() - start_time
                    
                    self.record_model_usage("skill_code_generation", True, response_time)
                    
                    response = f"[🛠️ Skills-Only Mode] Generated code using code generation skill\n\n"
                    response += f"[Code Output]\n{result}"
                    
                    self.history.add("assistant", f"[Skills-Only:Code] {result[:100]}...")
                    return response
            except Exception as e:
                logger.error(f"Code generation skill failed in fallback: {e}")
        
        # Check for data analysis intent
        if any(word in last_user_message.lower() for word in ["analyze", "data", "csv", "json", "stats"]):
            try:
                skill = self.skills.get("data_inspector")
                if skill:
                    start_time = time.time()
                    result = skill.execute({"text": last_user_message})
                    response_time = time.time() - start_time
                    
                    self.record_model_usage("skill_data_inspector", True, response_time)
                    
                    response = f"[🛠️ Skills-Only Mode] Analyzing data with data inspector skill\n\n"
                    response += f"[Analysis Output]\n{result}"
                    
                    self.history.add("assistant", f"[Skills-Only:Data] {result[:100]}...")
                    return response
            except Exception as e:
                logger.error(f"Data inspector skill failed in fallback: {e}")
        
        # Check for web search intent
        if any(word in last_user_message.lower() for word in ["search", "web", "find", "research"]):
            try:
                skill = self.skills.get("web_search")
                if skill:
                    start_time = time.time()
                    result = skill.execute({"text": last_user_message})
                    response_time = time.time() - start_time
                    
                    self.record_model_usage("skill_web_search", True, response_time)
                    
                    response = f"[🛠️ Skills-Only Mode] Searching with web research skill\n\n"
                    response += f"[Search Output]\n{result}"
                    
                    self.history.add("assistant", f"[Skills-Only:Web] {result[:100]}...")
                    return response
            except Exception as e:
                logger.error(f"Web search skill failed in fallback: {e}")
        
        # If no specific skill matched, provide intelligent help
        fallback = f"[🛠️ Skills-Only Mode] I'm operating without language models, but I can still help!\n\n"
        fallback += f"I detected you're asking about: '{last_user_message[:100]}{'...' if len(last_user_message) > 100 else ''}'\n\n"
        fallback += "Available skills I can use:\n"
        
        skill_names = list(self.skills._skills.keys())
        for skill_name in sorted(skill_names):
            skill = self.skills.get(skill_name)
            fallback += f"- **{skill_name}**: {skill.description}\n"
        
        fallback += "\nTry rephrasing your request with keywords like 'code', 'analyze', 'search', etc."
        
        # Add model status info
        if self.available_models:
            fallback += f"\n\nModel Status: {len(self.available_models)} models configured but currently unavailable."
        
        self.history.add("assistant", fallback)
        return fallback

    def clear_history(self):
        self.history.clear()

    def record_model_usage(self, task_type: str, success: bool, response_time: float,
                          token_count: Optional[int] = None, error_message: str = ""):
        """Record model usage for analytics"""
        if self.current_model:
            self.analytics.record_usage(
                model_id=self.current_model,
                task_type=task_type,
                success=success,
                response_time=response_time,
                token_count=token_count,
                error_message=error_message
            )

    def execute_framework_task(self, framework: str, task_type: str, parameters: Dict[str, Any],
                              models: Optional[List[str]] = None, parallel: bool = False) -> Dict[str, Any]:
        """Execute a task using an external framework"""
        try:
            # Initialize framework if not already done
            if framework not in self.framework_integrator.active_integrations:
                if not self.framework_integrator.initialize_framework(framework):
                    return {
                        "success": False,
                        "error": f"Failed to initialize framework {framework}",
                        "framework": framework,
                        "task_type": task_type
                    }

            # Create task request
            request = TaskRequest(
                framework=framework,
                task_type=task_type,
                parameters=parameters,
                models=models or [self.current_model] if self.current_model else [],
                parallel=parallel,
                timeout=30
            )

            # Execute task
            result = self.framework_integrator.execute_task(request)

            # Record usage for analytics
            self.record_model_usage(
                task_type=f"framework_{framework}_{task_type}",
                success=result.success,
                response_time=result.execution_time,
                error_message=result.error_message if not result.success else ""
            )

            return {
                "success": result.success,
                "output": result.output,
                "execution_time": result.execution_time,
                "error": result.error_message,
                "framework": framework,
                "task_type": task_type,
                "metadata": result.metadata
            }

        except Exception as e:
            logger.error(f"Framework task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "framework": framework,
                "task_type": task_type
            }

    def get_available_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Get status of available frameworks"""
        return self.framework_integrator.get_framework_status()

    def discover_framework_capabilities(self) -> Dict[str, List[str]]:
        """Discover all available framework capabilities"""
        return self.framework_integrator.discover_capabilities()

    def _load_available_models(self) -> Dict[str, Dict]:
        """Load available models from configuration, filtering by health status"""
        models = {}

        try:
            # Load from opencode.json
            config_path = self._find_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)

                models_config = config.get("models", {})
                health_status = config.get("model_health", {})

                for model_id, model_data in models_config.items():
                    # Check if model is validated and healthy
                    is_validated = model_data.get("status") == "validated"
                    is_healthy = health_status.get(model_id, {}).get("is_healthy", True)

                    if is_validated and is_healthy:
                        models[model_id] = model_data

        except Exception as e:
            logger.warning(f"Failed to load available models: {e}")

        return models

    def get_model_health_status(self) -> Dict[str, Dict]:
        """Get health status of all models"""
        try:
            config_path = self._find_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                return config.get("model_health", {})
        except Exception as e:
            logger.warning(f"Failed to load model health status: {e}")
        return {}

    def get_unhealthy_models(self) -> List[str]:
        """Get list of unhealthy model IDs"""
        health_status = self.get_model_health_status()
        return [model_id for model_id, status in health_status.items() if not status.get("is_healthy", True)]

    def get_healthy_models(self) -> List[str]:
        """Get list of healthy model IDs"""
        health_status = self.get_model_health_status()
        return [model_id for model_id, status in health_status.items() if status.get("is_healthy", True)]

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
        return "opencode.json"

    def _select_best_model(self, task_type: str = "general") -> Optional[str]:
        """Select the best available model based on analytics and performance"""
        if not self.available_models:
            return None

        available_model_ids = list(self.available_models.keys())

        # Use analytics to get optimal model for task type
        optimal_model = self.analytics.get_optimal_model(task_type, available_model_ids)

        if optimal_model:
            return optimal_model

        # Fallback: prefer fastest model with most capabilities
        best_model = None
        best_score = -1

        for model_id, model_data in self.available_models.items():
            capabilities = model_data.get("capabilities", [])
            response_time = model_data.get("response_time", 10.0)

            # Calculate score: capability count minus response time penalty
            score = len(capabilities) * 10 - response_time * 2

            if score > best_score:
                best_score = score
                best_model = model_id

        return best_model

    def switch_model(self, model_id: str) -> bool:
        """Switch to a different model if available"""
        if model_id in self.available_models:
            self.current_model = model_id
            logger.info(f"Switched to model: {model_id}")
            return True
        else:
            logger.warning(f"Model {model_id} not available")
            return False

    def get_model_info(self, model_id: Optional[str] = None) -> Optional[Dict]:
        """Get information about a specific model or current model"""
        target_model = model_id or self.current_model
        if target_model and target_model in self.available_models:
            return self.available_models[target_model]
        return None

    def list_available_models(self) -> List[str]:
        """List all available model IDs"""
        return list(self.available_models.keys())

    def auto_switch_model(self, required_capabilities: Optional[List[str]] = None) -> bool:
        """Automatically switch to the best model for required capabilities"""
        if required_capabilities is None:
            required_capabilities = ["reasoning"]

        best_model = None
        best_score = -1

        for model_id, model_data in self.available_models.items():
            capabilities = model_data.get("capabilities", [])
            response_time = model_data.get("response_time", 10.0)

            # Check if model has required capabilities
            if all(cap in capabilities for cap in required_capabilities):
                # Calculate score
                score = len(capabilities) * 10 - response_time * 2

                if score > best_score:
                    best_score = score
                    best_model = model_id

        if best_model and best_model != self.current_model:
            return self.switch_model(best_model)

        return False

    # Self-optimization methods
    def analyze_brain_health(self) -> str:
        """Perform comprehensive self-analysis and return report"""
        try:
            report = self.self_optimization.analyze_self()
            return self.self_optimization.get_self_analysis_report()
        except Exception as e:
            logger.error(f"Brain health analysis failed: {e}")
            return f"Brain health analysis failed: {e}"

    def run_self_tests(self) -> str:
        """Run comprehensive self-tests and return report"""
        try:
            results = self.self_optimization.run_self_tests()
            return self.self_optimization.get_self_test_report()
        except Exception as e:
            logger.error(f"Self-tests failed: {e}")
            return f"Self-tests failed: {e}"

    def optimize_brain(self) -> str:
        """Run self-optimization and return results"""
        try:
            actions = self.self_optimization.optimize_self()
            if actions:
                return f"Optimization completed. Executed {len(actions)} actions:\n" + "\n".join([
                    f"- {action.action_type} on {action.target}: {action.reasoning}"
                    for action in actions
                ])
            else:
                return "No optimization actions were needed or executed."
        except Exception as e:
            logger.error(f"Brain optimization failed: {e}")
            return f"Brain optimization failed: {e}"

    def get_optimization_status(self) -> str:
        """Get current optimization status"""
        try:
            status = "Active" if self.self_optimization.continuous_mode else "Inactive"
            last_analysis = "None"
            if self.self_optimization.analysis_history:
                last_analysis = self.self_optimization.analysis_history[-1].timestamp.strftime('%Y-%m-%d %H:%M:%S')

            return f"""Self-Optimization Status:
- Continuous Mode: {status}
- Last Analysis: {last_analysis}
- Total Analyses: {len(self.self_optimization.analysis_history)}
- Total Tests: {len(self.self_optimization.test_results)}
- Optimization Actions: {len(self.self_optimization.optimization_actions)}"""
        except Exception as e:
            logger.error(f"Failed to get optimization status: {e}")
            return f"Failed to get optimization status: {e}"

    # Autonomous Evolution Engine methods
    def get_evolution_status(self) -> Dict[str, Any]:
        """Get autonomous evolution engine status"""
        try:
            if self.evolution_functions:
                return self.evolution_functions['get_status']()
            else:
                return {"error": "Evolution engine not initialized"}
        except Exception as e:
            logger.error(f"Failed to get evolution status: {e}")
            return {"error": str(e)}

    def start_evolution_engine(self) -> bool:
        """Start the autonomous evolution engine"""
        try:
            if self.evolution_functions:
                self.evolution_functions['start']()
                logger.info("Evolution engine started")
                return True
            else:
                logger.error("Evolution engine not initialized")
                return False
        except Exception as e:
            logger.error(f"Failed to start evolution engine: {e}")
            return False

    def stop_evolution_engine(self) -> bool:
        """Stop the autonomous evolution engine"""
        try:
            if self.evolution_functions:
                self.evolution_functions['stop']()
                logger.info("Evolution engine stopped")
                return True
            else:
                logger.info("Evolution engine not initialized")
                return True
        except Exception as e:
            logger.error(f"Failed to stop evolution engine: {e}")
            return False

    def trigger_evolution_scan(self) -> Dict[str, Any]:
        """Manually trigger an evolution scan"""
        try:
            if self.evolution_functions:
                # Import the trigger function
                from autonomous_evolution_engine import trigger_scan
                opportunities = trigger_scan()
                return {
                    "success": True,
                    "opportunities_found": len(opportunities),
                    "opportunities": [opp.__dict__ for opp in opportunities[:5]]  # Return first 5
                }
            else:
                return {"error": "Evolution engine not initialized"}
        except Exception as e:
            logger.error(f"Failed to trigger evolution scan: {e}")
            return {"error": str(e)}

    def get_evolution_report(self) -> str:
        """Get a formatted evolution engine report"""
        try:
            if self.evolution_engine:
                status = self.evolution_engine.get_status()
                perf_report = self.evolution_engine.get_performance_report()

                report = f"""🤖 Autonomous Evolution Engine Report

📊 Current Status:
- Running: {'✅ Yes' if status.get('is_running', False) else '❌ No'}
- Opportunities Discovered: {status.get('metrics', {}).get('opportunities_discovered', 0)}
- Opportunities Implemented: {status.get('metrics', {}).get('opportunities_implemented', 0)}
- Performance Gains: {status.get('metrics', {}).get('performance_gains', 0.0)}
- Features Added: {status.get('metrics', {}).get('features_added', 0)}
- Improvements Made: {status.get('metrics', {}).get('improvements_made', 0)}

🔧 LLM Independence:
- Core Functions LLM-Free: {'✅ Yes' if status.get('llm_independence', {}).get('core_functionality_llm_free', False) else '❌ No'}
- LLM Enhancements Available: {'✅ Yes' if status.get('llm_independence', {}).get('llm_enhancements_available', False) else '❌ No'}

🌐 Internet Scanning:
- Enabled: {'✅ Yes' if status.get('internet_scanning', {}).get('enabled', False) else '❌ No'}
- Last Scan: {status.get('internet_scanning', {}).get('last_scan', 'Never') or 'Never'}

⚡ Performance Metrics:
- Average Scan Time: {perf_report.get('summary', {}).get('average_scan_time', 0):.2f}s
- Opportunities Per Scan: {perf_report.get('summary', {}).get('opportunities_per_scan', 0):.1f}
- Implementation Success Rate: {perf_report.get('summary', {}).get('implementation_success_rate', 0)*100:.1f}%

🔍 Active Capabilities:
"""
                for capability in status.get('capabilities_llm_independent', []):
                    report += f"- {capability}\n"

                return report
            else:
                return "❌ Evolution engine not initialized"
        except Exception as e:
            logger.error(f"Failed to generate evolution report: {e}")
            return f"❌ Failed to generate evolution report: {e}"
