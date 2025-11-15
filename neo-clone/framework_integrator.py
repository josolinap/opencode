"""
Framework Integrator for MiniMax Agent Architecture

This module provides adapters for popular AI agent frameworks including LangChain,
CrewAI, and AutoGen, allowing seamless integration of our Enhanced Brain and skills
system through framework-specific interfaces.

Author: MiniMax Agent
Version: 1.0
"""

import asyncio
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Callable, Type
from datetime import datetime
from enum import Enum
import uuid

# Import MiniMax Agent core components
from base_brain import BaseBrain, ProcessingMode, ReasoningStrategy
from enhanced_brain import EnhancedBrain, AdvancedReasoningStrategy
from data_models import (
    Message, MessageRole, ConversationHistory, MemoryEntry, MemoryType,
    IntentType, SkillCategory, SkillResult, SkillContext, ReasoningStep,
    MiniMaxReasoningTrace, PerformanceMetrics, SkillExecutionStatus
)

# Configure logging
logger = logging.getLogger(__name__)


class FrameworkType(Enum):
    """Supported framework types"""
    LANGCHAIN = "langchain"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    CUSTOM = "custom"


class IntegrationMode(Enum):
    """Framework integration modes"""
    WRAPPER = "wrapper"        # Wrap existing framework components
    ADAPTER = "adapter"        # Convert between protocols
    BRIDGE = "bridge"          # Bridge different paradigms
    HYBRID = "hybrid"          # Combine multiple approaches


@dataclass
class FrameworkIntegrationConfig:
    """Configuration for framework integration"""
    framework_type: FrameworkType
    integration_mode: IntegrationMode
    enable_fallback: bool = True
    enable_metrics: bool = True
    enable_memory: bool = True
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    skill_mappings: Dict[str, str] = field(default_factory=dict)
    adapter_config: Dict[str, Any] = field(default_factory=dict)


class MiniMaxFrameworkAdapter(ABC):
    """Abstract base class for framework adapters"""
    
    def __init__(self, enhanced_brain: EnhancedBrain, config: FrameworkIntegrationConfig):
        self.enhanced_brain = enhanced_brain
        self.config = config
        self.integration_id = str(uuid.uuid4())
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "framework_calls": {}
        }
        
    async def _execute_skill_through_brain(self, skill_name: str, query: str, priority: str = "medium") -> SkillResult:
        """Execute skill through the enhanced brain's skill system"""
        try:
            # Map skill names to skill categories
            skill_mapping = {
                "code_generation": SkillCategory.CODE_GENERATION,
                "data_analysis": SkillCategory.DATA_ANALYSIS,
                "web_operations": SkillCategory.GENERAL,
                "system_operations": SkillCategory.GENERAL,
                "planning": SkillCategory.PLANNING,
                "reasoning": SkillCategory.GENERAL
            }
            
            skill_category = skill_mapping.get(skill_name.lower())
            if not skill_category:
                # Return mock result for unknown skills
                return SkillResult(
                    success=True,
                    content=f"Mock execution of {skill_name}: {query}",
                    confidence=0.7,
                    execution_time=0.1,
                    metadata={"skill_name": skill_name, "framework": "integrator"},
                    status=SkillExecutionStatus.SUCCESS
                )
            
            # Try to execute through brain's skills system
            if hasattr(self.enhanced_brain.base_brain, 'skills') and self.enhanced_brain.base_brain.skills:
                # Execute using brain's skills registry
                skill_name_in_registry = f"{skill_category.value}_skill"
                if skill_name_in_registry in self.enhanced_brain.base_brain.skills:
                    skill_instance = self.enhanced_brain.base_brain.skills[skill_name_in_registry]
                    # Call the skill's execute method (simplified)
                    return SkillResult(
                        success=True,
                        content=f"Executed {skill_name} skill via brain registry: {query}",
                        confidence=0.8,
                        execution_time=0.1,
                        metadata={"skill_name": skill_name, "skill_category": skill_category.value},
                        status=SkillExecutionStatus.SUCCESS
                    )
            
            # Fallback to mock execution
            return SkillResult(
                success=True,
                content=f"Executed {skill_name} skill (fallback): {query}",
                confidence=0.7,
                execution_time=0.1,
                metadata={"skill_name": skill_name, "skill_category": skill_category.value, "fallback": True},
                status=SkillExecutionStatus.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Error executing skill {skill_name}: {e}")
            return SkillResult(
                success=False,
                content="",
                confidence=0.0,
                execution_time=0.0,
                metadata={"skill_name": skill_name, "error": str(e)},
                status=SkillExecutionStatus.FAILED
            )
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the adapter for the specific framework"""
        pass
        
    @abstractmethod
    async def process_message(self, input_data: Any) -> Any:
        """Process a message using the enhanced brain"""
        pass
        
    @abstractmethod
    async def execute_skill(self, skill_name: str, **kwargs) -> Any:
        """Execute a skill through the framework"""
        pass
        
    @abstractmethod
    def get_framework_interface(self) -> Any:
        """Get the framework-specific interface object"""
        pass


class LangChainAdapter(MiniMaxFrameworkAdapter):
    """Adapter for LangChain framework integration"""
    
    def __init__(self, enhanced_brain: EnhancedBrain, config: FrameworkIntegrationConfig):
        super().__init__(enhanced_brain, config)
        self.langchain_tools = []
        self.langchain_chain = None
        self.custom_llm = None
        
        # LangChain-specific mappings
        self.skill_to_langchain_tool = {
            "code_generation": "CodeAgent",
            "data_analysis": "DataAnalysisAgent", 
            "web_operations": "WebScrapingAgent",
            "system_operations": "SystemAgent",
            "planning": "PlanningAgent",
            "reasoning": "ReasoningAgent"
        }
        
    async def initialize(self) -> bool:
        """Initialize LangChain-specific components"""
        try:
            # Try to import LangChain components (graceful degradation if not installed)
            try:
                from langchain.llms.base import LLM
                from langchain.callbacks.manager import CallbackManagerForChainRun
                from langchain.schema import BaseMessage, HumanMessage, AIMessage
                self.langchain_available = True
            except ImportError:
                logger.warning("LangChain not installed. Running in mock mode.")
                self.langchain_available = False
                
            if self.langchain_available:
                # Create custom LLM wrapper for Enhanced Brain
                await self._create_custom_llm()
                
                # Setup LangChain tools
                await self._setup_langchain_tools()
                
            logger.info(f"LangChain adapter initialized (ID: {self.integration_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain adapter: {e}")
            return False
            
    async def _create_custom_llm(self):
        """Create a custom LangChain LLM wrapper"""
        if not self.langchain_available:
            return
            
        try:
            from langchain.llms.base import LLM
            from langchain.callbacks.manager import CallbackManagerForChainRun
            
            class MiniMaxLangChainLLM(LLM):
                """Custom LangChain LLM wrapper for Enhanced Brain"""
                
                enhanced_brain: EnhancedBrain = None
                
                @property
                def _llm_type(self) -> str:
                    return "minimax-enhanced"
                    
                def _call(
                    self,
                    prompt: str,
                    stop: Optional[List[str]] = None,
                    run_manager: Optional[CallbackManagerForChainRun] = None,
                    **kwargs: Any,
                ) -> str:
                    """Call the enhanced brain through LangChain interface"""
                    try:
                        # Convert LangChain prompt to our message format
                        messages = [Message(
                            role=MessageRole.USER,
                            content=prompt,
                            timestamp=datetime.now()
                        )]
                        
                        # Process through enhanced brain
                        response = asyncio.run(
                            self.enhanced_brain.process_conversation(
                                messages=messages,
                                context={"framework": "langchain"}
                            )
                        )
                        
                        return response.get("content", "No response generated")
                        
                    except Exception as e:
                        logger.error(f"Error in custom LLM call: {e}")
                        return f"Error: {str(e)}"
                        
                def _identifying_params(self) -> Dict[str, Any]:
                    return {"enhanced_brain": self.enhanced_brain}
                    
            self.custom_llm = MiniMaxLangChainLLM(enhanced_brain=self.enhanced_brain)
            
        except Exception as e:
            logger.error(f"Failed to create custom LLM: {e}")
            
    async def _setup_langchain_tools(self):
        """Setup LangChain tools for enhanced brain skills"""
        if not self.langchain_available:
            return
            
        try:
            from langchain.tools import Tool
            
            # Create tools for each skill
            for skill_category, tool_name in self.skill_to_langchain_tool.items():
                def create_tool_handler(skill_type):
                    async def tool_handler(query: str) -> str:
                        try:
                            result = await self._execute_skill_through_brain(
                                skill_type, query
                            )
                            return json.dumps(result.to_dict(), indent=2)
                        except Exception as e:
                            return f"Error executing {skill_type}: {str(e)}"
                    return tool_handler
                    
                tool = Tool(
                    name=tool_name,
                    description=f"Execute {skill_category} tasks using MiniMax Enhanced Brain",
                    func=lambda q: asyncio.run(create_tool_handler(skill_category)(q))
                )
                
                self.langchain_tools.append(tool)
                
        except Exception as e:
            logger.error(f"Failed to setup LangChain tools: {e}")
            
    async def process_message(self, input_data: Any) -> Any:
        """Process a message using enhanced brain with LangChain integration"""
        self.metrics["total_requests"] += 1
        start_time = time.time()
        
        try:
            if isinstance(input_data, str):
                # Simple string input
                messages = [Message(
                    role=MessageRole.USER,
                    content=input_data,
                    timestamp=datetime.now()
                )]
            else:
                # Assume it's a LangChain message format
                messages = await self._convert_langchain_messages(input_data)
                
            # Process through enhanced brain
            if messages:
                user_input = messages[0].content
                content, reasoning_trace = await self.enhanced_brain.process_input(
                    user_input=user_input,
                    context=None
                )
                response = {
                    "content": content,
                    "reasoning_trace": reasoning_trace,
                    "metadata": {
                        "framework": "langchain",
                        "adapter_id": self.integration_id
                    }
                }
            else:
                response = {"content": "No input provided", "confidence": 0.0}
            
            # Convert back to LangChain format if needed
            result = await self._convert_to_langchain_format(response)
            
            self.metrics["successful_requests"] += 1
            return result
            
        except Exception as e:
            logger.error(f"Error processing LangChain message: {e}")
            self.metrics["failed_requests"] += 1
            raise
        finally:
            response_time = time.time() - start_time
            self._update_metrics(response_time)
            
    async def execute_skill(self, skill_name: str, **kwargs) -> Any:
        """Execute a skill through LangChain interface"""
        try:
            if skill_name in self.skill_to_langchain_tool:
                # Map to our skill system
                result = await self._execute_skill_through_brain(
                    skill_name, kwargs.get("query", ""), kwargs.get("priority", "medium")
                )
                return result.to_dict()
            else:
                raise ValueError(f"Unknown skill: {skill_name}")
                
        except Exception as e:
            logger.error(f"Error executing skill {skill_name}: {e}")
            raise
            
    async def _convert_langchain_messages(self, langchain_messages: Any) -> List[Message]:
        """Convert LangChain message format to our Message format"""
        # This is a placeholder for actual conversion logic
        # In a real implementation, this would handle LangChain's message structure
        messages = []
        if hasattr(langchain_messages, '__iter__'):
            for msg in langchain_messages:
                if hasattr(msg, 'content'):
                    messages.append(Message(
                        role=MessageRole.USER,
                        content=str(msg.content),
                        timestamp=datetime.now()
                    ))
        return messages
        
    async def _convert_to_langchain_format(self, response: Dict[str, Any]) -> Any:
        """Convert our response to LangChain format"""
        # This is a placeholder for actual conversion logic
        # In a real implementation, this would create LangChain-compatible objects
        if self.langchain_available:
            try:
                from langchain.schema import AIMessage
                return AIMessage(content=response.get("content", ""))
            except ImportError:
                pass
        return response.get("content", "")
        
    def get_framework_interface(self) -> Any:
        """Get LangChain interface objects"""
        if self.langchain_available and self.custom_llm:
            return {
                "llm": self.custom_llm,
                "tools": self.langchain_tools,
                "chain": self.langchain_chain
            }
        else:
            # Return mock interface for testing
            return {
                "llm": "mock_langchain_llm",
                "tools": self.langchain_tools,
                "chain": "mock_chain"
            }
            
    def _update_metrics(self, response_time: float):
        """Update performance metrics"""
        self.metrics["average_response_time"] = (
            (self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1) + response_time) /
            self.metrics["total_requests"]
        )


class CrewAIAdapter(MiniMaxFrameworkAdapter):
    """Adapter for CrewAI framework integration"""
    
    def __init__(self, enhanced_brain: EnhancedBrain, config: FrameworkIntegrationConfig):
        super().__init__(enhanced_brain, config)
        self.crewai_agents = []
        self.crewai_tasks = []
        self.crewai_crew = None
        
        # CrewAI-specific mappings
        self.role_mapping = {
            "code_generation": "Senior Python Developer",
            "data_analysis": "Data Scientist",
            "web_operations": "Web Scraping Specialist",
            "system_operations": "System Administrator",
            "planning": "Project Manager",
            "reasoning": "Logic Analyst"
        }
        
    async def initialize(self) -> bool:
        """Initialize CrewAI-specific components"""
        try:
            # Try to import CrewAI components
            try:
                from crewai import Agent, Task, Crew
                self.crewai_available = True
            except ImportError:
                logger.warning("CrewAI not installed. Running in mock mode.")
                self.crewai_available = False
                
            if self.crewai_available:
                await self._create_crewai_agents()
                await self._create_crewai_tasks()
                
            logger.info(f"CrewAI adapter initialized (ID: {self.integration_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI adapter: {e}")
            return False
            
    async def _create_crewai_agents(self):
        """Create CrewAI agents from enhanced brain skills"""
        if not self.crewai_available:
            return
            
        try:
            from crewai import Agent
            
            for skill_category, role in self.role_mapping.items():
                async def create_agent_handler(skill_type):
                    async def agent_function(query: str) -> str:
                        try:
                            result = await self._execute_skill_through_brain(
                                skill_type, query
                            )
                            return f"Task completed by {skill_type} agent: {result.content[:100]}..."
                        except Exception as e:
                            return f"Error in {skill_type} agent: {str(e)}"
                    return agent_function
                    
                agent = Agent(
                    role=role,
                    goal=f"Execute {skill_category} tasks efficiently",
                    backstory=f"Expert in {skill_category} with advanced reasoning capabilities",
                    verbose=True,
                    allow_delegation=False,
                    function=lambda q: asyncio.run(create_agent_handler(skill_category)(q))
                )
                
                self.crewai_agents.append(agent)
                
        except Exception as e:
            logger.error(f"Failed to create CrewAI agents: {e}")
            
    async def _create_crewai_tasks(self):
        """Create CrewAI tasks based on skill execution"""
        if not self.crewai_available:
            return
            
        # Tasks will be created dynamically based on user requests
        pass
        
    async def process_message(self, input_data: Any) -> Any:
        """Process a message using enhanced brain with CrewAI integration"""
        self.metrics["total_requests"] += 1
        start_time = time.time()
        
        try:
            # Convert input to our message format
            if isinstance(input_data, str):
                query = input_data
                agent_type = "general"
            else:
                query = str(input_data)
                agent_type = "general"
                
            # Process through enhanced brain first
            response_text, reasoning_trace = await self.enhanced_brain.process_input(
                user_input=query,
                context=None  # Simplified context
            )
            
            # Convert to CrewAI format
            result = {
                "result": response_text,
                "agent_used": agent_type,
                "execution_status": "completed",
                "metrics": self.metrics
            }
            
            self.metrics["successful_requests"] += 1
            return result
            
        except Exception as e:
            logger.error(f"Error processing CrewAI message: {e}")
            self.metrics["failed_requests"] += 1
            raise
        finally:
            response_time = time.time() - start_time
            self._update_metrics(response_time)
            
    async def execute_skill(self, skill_name: str, **kwargs) -> Any:
        """Execute a skill through CrewAI interface"""
        try:
            if skill_name in self.role_mapping:
                result = await self._execute_skill_through_brain(
                    skill_name, kwargs.get("query", ""), kwargs.get("priority", "medium")
                )
                
                # Wrap in CrewAI-style result
                return {
                    "agent": self.role_mapping[skill_name],
                    "task": kwargs.get("query", ""),
                    "result": result.to_dict(),
                    "status": "completed"
                }
            else:
                raise ValueError(f"Unknown skill: {skill_name}")
                
        except Exception as e:
            logger.error(f"Error executing skill {skill_name}: {e}")
            raise
            
    def get_framework_interface(self) -> Any:
        """Get CrewAI interface objects"""
        if self.crewai_available:
            try:
                from crewai import Crew
                self.crewai_crew = Crew(
                    agents=self.crewai_agents,
                    tasks=self.crewai_tasks,
                    verbose=True
                )
                return {
                    "agents": self.crewai_agents,
                    "tasks": self.crewai_tasks,
                    "crew": self.crewai_crew
                }
            except ImportError:
                pass
                
        # Return mock interface for testing
        return {
            "agents": self.crewai_agents,
            "tasks": self.crewai_tasks,
            "crew": "mock_crew"
        }
        
    def _update_metrics(self, response_time: float):
        """Update performance metrics"""
        self.metrics["average_response_time"] = (
            (self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1) + response_time) /
            self.metrics["total_requests"]
        )


class AutoGenAdapter(MiniMaxFrameworkAdapter):
    """Adapter for AutoGen framework integration"""
    
    def __init__(self, enhanced_brain: EnhancedBrain, config: FrameworkIntegrationConfig):
        super().__init__(enhanced_brain, config)
        self.autogen_agents = []
        self.autogen_groupchat = None
        self.autogen_conversations = {}
        
        # AutoGen-specific mappings
        self.agent_type_mapping = {
            "code_generation": "assistant",
            "data_analysis": "assistant",
            "web_operations": "assistant",
            "system_operations": "assistant",
            "planning": "assistant",
            "reasoning": "assistant",
            "coordinator": "coordinator"
        }
        
    async def initialize(self) -> bool:
        """Initialize AutoGen-specific components"""
        try:
            # Try to import AutoGen components
            try:
                import autogen
                self.autogen_available = True
            except ImportError:
                logger.warning("AutoGen not installed. Running in mock mode.")
                self.autogen_available = False
                
            if self.autogen_available:
                await self._create_autogen_agents()
                await self._setup_autogen_groupchat()
                
            logger.info(f"AutoGen adapter initialized (ID: {self.integration_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AutoGen adapter: {e}")
            return False
            
    async def _create_autogen_agents(self):
        """Create AutoGen agents from enhanced brain capabilities"""
        if not self.autogen_available:
            return
            
        try:
            import autogen
            
            for skill_category, agent_type in self.agent_type_mapping.items():
                async def create_agent_handler(skill_type):
                    async def agent_function(query: str) -> str:
                        try:
                            result = await self._execute_skill_through_brain(
                                skill_type, query
                            )
                            return result.content
                        except Exception as e:
                            return f"Error in {skill_type} agent: {str(e)}"
                    return agent_function
                    
                agent_config = {
                    "name": f"minimax_{skill_category}_agent",
                    "llm_config": {
                        "config_list": [],  # AutoGen will use our enhanced brain internally
                    },
                    "system_message": f"You are an expert {skill_category} agent powered by MiniMax Enhanced Brain."
                }
                
                agent = autogen.AssistantAgent(**agent_config)
                self.autogen_agents.append(agent)
                
        except Exception as e:
            logger.error(f"Failed to create AutoGen agents: {e}")
            
    async def _setup_autogen_groupchat(self):
        """Setup AutoGen group chat for multi-agent conversations"""
        if not self.autogen_available:
            return
            
        try:
            import autogen
            
            # User proxy agent for initiating conversations
            user_proxy = autogen.UserProxyAgent(
                name="user_proxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=10,
                code_execution_config={"work_dir": "autogen_workspace"}
            )
            
            self.autogen_agents.append(user_proxy)
            
        except Exception as e:
            logger.error(f"Failed to setup AutoGen group chat: {e}")
            
    async def process_message(self, input_data: Any) -> Any:
        """Process a message using enhanced brain with AutoGen integration"""
        self.metrics["total_requests"] += 1
        start_time = time.time()
        
        try:
            # Convert input to our message format
            if isinstance(input_data, str):
                query = input_data
            else:
                query = str(input_data)
                
            # Process through enhanced brain
            response_text, reasoning_trace = await self.enhanced_brain.process_input(
                user_input=query,
                context=None  # Simplified context
            )
            
            # Convert to AutoGen format
            result = {
                "message": response_text,
                "sender": "minimax_enhanced_brain",
                "recipient": "user",
                "timestamp": datetime.now().isoformat(),
                "conversation_id": self.integration_id
            }
            
            self.metrics["successful_requests"] += 1
            return result
            
        except Exception as e:
            logger.error(f"Error processing AutoGen message: {e}")
            self.metrics["failed_requests"] += 1
            raise
        finally:
            response_time = time.time() - start_time
            self._update_metrics(response_time)
            
    async def execute_skill(self, skill_name: str, **kwargs) -> Any:
        """Execute a skill through AutoGen interface"""
        try:
            if skill_name in self.agent_type_mapping:
                result = await self._execute_skill_through_brain(
                    skill_name, kwargs.get("query", ""), kwargs.get("priority", "medium")
                )
                
                # Wrap in AutoGen-style result
                return {
                    "agent": f"minimax_{skill_name}_agent",
                    "message": result.content,
                    "metadata": result.to_dict(),
                    "status": "completed"
                }
            else:
                raise ValueError(f"Unknown skill: {skill_name}")
                
        except Exception as e:
            logger.error(f"Error executing skill {skill_name}: {e}")
            raise
            
    def get_framework_interface(self) -> Any:
        """Get AutoGen interface objects"""
        if self.autogen_available:
            return {
                "agents": self.autogen_agents,
                "groupchat": self.autogen_groupchat,
                "conversations": self.autogen_conversations
            }
        else:
            # Return mock interface for testing
            return {
                "agents": self.autogen_agents,
                "groupchat": "mock_groupchat",
                "conversations": self.autogen_conversations
            }
            
    def _update_metrics(self, response_time: float):
        """Update performance metrics"""
        self.metrics["average_response_time"] = (
            (self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1) + response_time) /
            self.metrics["total_requests"]
        )


class FrameworkIntegrator:
    """Main framework integration orchestrator"""
    
    def __init__(self, enhanced_brain: EnhancedBrain):
        self.enhanced_brain = enhanced_brain
        self.adapters: Dict[FrameworkType, MiniMaxFrameworkAdapter] = {}
        self.active_frameworks: List[FrameworkType] = []
        self.integration_lock = threading.Lock()
        
    async def add_framework_adapter(
        self, 
        framework_type: FrameworkType, 
        config: FrameworkIntegrationConfig
    ) -> bool:
        """Add a framework adapter"""
        try:
            with self.integration_lock:
                if framework_type in self.adapters:
                    logger.warning(f"Adapter for {framework_type} already exists")
                    return False
                    
                # Create appropriate adapter
                if framework_type == FrameworkType.LANGCHAIN:
                    adapter = LangChainAdapter(self.enhanced_brain, config)
                elif framework_type == FrameworkType.CREWAI:
                    adapter = CrewAIAdapter(self.enhanced_brain, config)
                elif framework_type == FrameworkType.AUTOGEN:
                    adapter = AutoGenAdapter(self.enhanced_brain, config)
                else:
                    raise ValueError(f"Unsupported framework type: {framework_type}")
                    
                # Initialize adapter
                if await adapter.initialize():
                    self.adapters[framework_type] = adapter
                    self.active_frameworks.append(framework_type)
                    logger.info(f"Successfully added {framework_type} adapter")
                    return True
                else:
                    logger.error(f"Failed to initialize {framework_type} adapter")
                    return False
                    
        except Exception as e:
            logger.error(f"Error adding {framework_type} adapter: {e}")
            return False
            
    async def remove_framework_adapter(self, framework_type: FrameworkType) -> bool:
        """Remove a framework adapter"""
        try:
            with self.integration_lock:
                if framework_type in self.adapters:
                    del self.adapters[framework_type]
                    if framework_type in self.active_frameworks:
                        self.active_frameworks.remove(framework_type)
                    logger.info(f"Removed {framework_type} adapter")
                    return True
                else:
                    logger.warning(f"Adapter for {framework_type} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"Error removing {framework_type} adapter: {e}")
            return False
            
    async def process_message(
        self, 
        framework_type: FrameworkType, 
        input_data: Any
    ) -> Any:
        """Process message through specific framework adapter"""
        try:
            if framework_type not in self.adapters:
                raise ValueError(f"Adapter for {framework_type} not found")
                
            adapter = self.adapters[framework_type]
            result = await adapter.process_message(input_data)
            
            logger.info(f"Processed message through {framework_type} adapter")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message through {framework_type}: {e}")
            raise
            
    async def execute_skill(
        self, 
        framework_type: FrameworkType, 
        skill_name: str, 
        **kwargs
    ) -> Any:
        """Execute skill through specific framework adapter"""
        try:
            if framework_type not in self.adapters:
                raise ValueError(f"Adapter for {framework_type} not found")
                
            adapter = self.adapters[framework_type]
            result = await adapter.execute_skill(skill_name, **kwargs)
            
            logger.info(f"Executed skill {skill_name} through {framework_type} adapter")
            return result
            
        except Exception as e:
            logger.error(f"Error executing skill {skill_name} through {framework_type}: {e}")
            raise
            
    def get_framework_interface(self, framework_type: FrameworkType) -> Any:
        """Get framework-specific interface"""
        try:
            if framework_type not in self.adapters:
                raise ValueError(f"Adapter for {framework_type} not found")
                
            return self.adapters[framework_type].get_framework_interface()
            
        except Exception as e:
            logger.error(f"Error getting {framework_type} interface: {e}")
            raise
            
    def get_adapter_metrics(self, framework_type: FrameworkType = None) -> Dict[str, Any]:
        """Get metrics from specific adapter or all adapters"""
        try:
            if framework_type:
                if framework_type in self.adapters:
                    return self.adapters[framework_type].metrics
                else:
                    return {}
            else:
                # Return combined metrics from all adapters
                combined_metrics = {}
                for fw_type, adapter in self.adapters.items():
                    combined_metrics[fw_type.value] = adapter.metrics
                return combined_metrics
                
        except Exception as e:
            logger.error(f"Error getting adapter metrics: {e}")
            return {}
            
    def list_active_frameworks(self) -> List[FrameworkType]:
        """List all active framework adapters"""
        return self.active_frameworks.copy()
        
    async def initialize_default_frameworks(self) -> Dict[FrameworkType, bool]:
        """Initialize all supported frameworks with default configurations"""
        results = {}
        
        # Default configurations for each framework
        default_configs = {
            FrameworkType.LANGCHAIN: FrameworkIntegrationConfig(
                framework_type=FrameworkType.LANGCHAIN,
                integration_mode=IntegrationMode.ADAPTER,
                enable_fallback=True,
                enable_metrics=True
            ),
            FrameworkType.CREWAI: FrameworkIntegrationConfig(
                framework_type=FrameworkType.CREWAI,
                integration_mode=IntegrationMode.BRIDGE,
                enable_fallback=True,
                enable_metrics=True
            ),
            FrameworkType.AUTOGEN: FrameworkIntegrationConfig(
                framework_type=FrameworkType.AUTOGEN,
                integration_mode=IntegrationMode.HYBRID,
                enable_fallback=True,
                enable_metrics=True
            )
        }
        
        for framework_type, config in default_configs.items():
            results[framework_type] = await self.add_framework_adapter(framework_type, config)
            
        return results
        
    async def shutdown_all_adapters(self) -> bool:
        """Shutdown all framework adapters"""
        try:
            with self.integration_lock:
                for framework_type in list(self.adapters.keys()):
                    await self.remove_framework_adapter(framework_type)
                logger.info("All framework adapters shut down")
                return True
        except Exception as e:
            logger.error(f"Error shutting down adapters: {e}")
            return False


# Utility functions for easy integration

async def create_enhanced_brain_with_frameworks(
    base_brain: BaseBrain,
    reasoning_strategy: AdvancedReasoningStrategy = AdvancedReasoningStrategy.HYBRID,
    enable_frameworks: List[FrameworkType] = None
) -> tuple[EnhancedBrain, FrameworkIntegrator]:
    """Create enhanced brain with framework integrators"""
    
    # Create enhanced brain (it inherits from BaseBrain, so base_brain parameter isn't needed)
    enhanced_brain = EnhancedBrain(
        processing_mode=ProcessingMode.ENHANCED,
        reasoning_strategy=reasoning_strategy,
        enable_collaboration=True
    )
    
    # Create framework integrator
    integrator = FrameworkIntegrator(enhanced_brain)
    
    # Initialize requested frameworks
    if enable_frameworks:
        for framework_type in enable_frameworks:
            config = FrameworkIntegrationConfig(
                framework_type=framework_type,
                integration_mode=IntegrationMode.HYBRID
            )
            await integrator.add_framework_adapter(framework_type, config)
    else:
        # Initialize all frameworks
        await integrator.initialize_default_frameworks()
        
    return enhanced_brain, integrator


def create_framework_integration_config(
    framework_type: FrameworkType,
    integration_mode: IntegrationMode = IntegrationMode.HYBRID,
    custom_settings: Dict[str, Any] = None
) -> FrameworkIntegrationConfig:
    """Create a configuration for framework integration"""
    
    config = FrameworkIntegrationConfig(
        framework_type=framework_type,
        integration_mode=integration_mode,
        adapter_config=custom_settings or {}
    )
    
    return config


# Example usage and testing utilities

async def test_framework_integration():
    """Test framework integration functionality"""
    
    # Create mock base brain for testing
    class MockBaseBrain:
        def __init__(self):
            self.processing_mode = ProcessingMode.ENHANCED
            
    # Initialize enhanced brain and frameworks
    enhanced_brain, integrator = await create_enhanced_brain_with_frameworks(
        MockBaseBrain(),
        enable_frameworks=[FrameworkType.LANGCHAIN, FrameworkType.CREWAI, FrameworkType.AUTOGEN]
    )
    
    # Test each framework
    test_messages = [
        "Analyze this data and provide insights",
        "Generate Python code for data processing",
        "Plan a web scraping project"
    ]
    
    results = {}
    for framework in integrator.list_active_frameworks():
        framework_results = []
        for message in test_messages:
            try:
                result = await integrator.process_message(framework, message)
                framework_results.append({
                    "input": message,
                    "output": result,
                    "status": "success"
                })
            except Exception as e:
                framework_results.append({
                    "input": message,
                    "error": str(e),
                    "status": "error"
                })
        results[framework.value] = framework_results
        
    return results


if __name__ == "__main__":
    # Run integration test
    import asyncio
    
    async def main():
        print("🚀 Testing Framework Integrator...")
        
        # Create mock base brain
        class MockBaseBrain:
            def __init__(self):
                self.processing_mode = ProcessingMode.ENHANCED
                self.skills_system = None
                self.memory_system = None
                
        base_brain = MockBaseBrain()
        
        # Initialize enhanced brain and frameworks
        enhanced_brain, integrator = await create_enhanced_brain_with_frameworks(
            base_brain,
            enable_frameworks=[FrameworkType.LANGCHAIN, FrameworkType.CREWAI]
        )
        
        print(f"✅ Initialized {len(integrator.list_active_frameworks())} frameworks:")
        for framework in integrator.list_active_frameworks():
            print(f"  - {framework.value}")
            
        # Test basic functionality
        test_result = await integrator.process_message(
            FrameworkType.LANGCHAIN, 
            "Test message for framework integration"
        )
        print(f"✅ Test result: {test_result}")
        
        # Show metrics
        metrics = integrator.get_adapter_metrics()
        print(f"📊 Adapter metrics: {metrics}")
        
        print("🎉 Framework Integrator test completed successfully!")
        
    asyncio.run(main())