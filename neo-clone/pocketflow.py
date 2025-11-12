"""
pocketflow.py - PocketFlow-inspired Minimalist Agent Orchestration System

Inspired by PocketFlow's "100-line LLM framework" philosophy:
- Ultra-minimalist agent orchestration
- Let Agents build Agents
- Flow-based programming for AI workflows
- Zero-dependency, maximum functionality

Core Principles:
1. Simplicity over complexity
2. Agents as first-class citizens
3. Composable workflows
4. Self-organizing systems
"""

import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FlowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class FlowContext:
    """Minimal context for flow execution"""
    session_id: str
    user_input: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    confidence: float = 1.0
    
@dataclass
class Agent:
    """Ultra-minimalist agent definition"""
    id: str
    name: str
    capabilities: List[AgentCapability]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    priority: int = 0
    max_retries: int = 3
    timeout: int = 30

@dataclass
class FlowStep:
    """Single step in a flow"""
    agent_id: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    state: FlowState = FlowState.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class PocketFlow:
    """
    PocketFlow: 100-line LLM framework philosophy
    Let Agents build Agents!
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.flows: Dict[str, List[FlowStep]] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self._initialize_core_agents()
        
    def _initialize_core_agents(self):
        """Initialize core Neo-Clone agents as PocketFlow agents"""
        
        # Reasoning Agent
        reasoner = Agent(
            id="reasoner",
            name="Advanced Reasoner",
            capabilities=[
                AgentCapability(
                    name="complex_reasoning",
                    description="Handles complex multi-step reasoning",
                    input_types=["text", "query", "problem"],
                    output_types=["analysis", "solution", "plan"]
                )
            ],
            handler=self._reasoner_handler,
            priority=10
        )
        self.register_agent(reasoner)
        
        # Code Generation Agent
        coder = Agent(
            id="coder", 
            name="Code Generator",
            capabilities=[
                AgentCapability(
                    name="code_generation",
                    description="Generates and explains code",
                    input_types=["request", "specification"],
                    output_types=["code", "explanation", "documentation"]
                )
            ],
            handler=self._coder_handler,
            priority=8
        )
        self.register_agent(coder)
        
        # Data Analysis Agent
        analyst = Agent(
            id="analyst",
            name="Data Analyst", 
            capabilities=[
                AgentCapability(
                    name="data_analysis",
                    description="Analyzes data and provides insights",
                    input_types=["data", "query", "file"],
                    output_types=["insights", "summary", "visualization"]
                )
            ],
            handler=self._analyst_handler,
            priority=7
        )
        self.register_agent(analyst)
        
        # Orchestrator Agent (meta-agent that builds other agents)
        orchestrator = Agent(
            id="orchestrator",
            name="Agent Orchestrator",
            capabilities=[
                AgentCapability(
                    name="agent_building",
                    description="Creates and configures other agents",
                    input_types=["requirement", "specification"],
                    output_types=["agent", "workflow", "plan"]
                )
            ],
            handler=self._orchestrator_handler,
            priority=9
        )
        self.register_agent(orchestrator)
    
    def register_agent(self, agent: Agent) -> bool:
        """Register a new agent"""
        try:
            self.agents[agent.id] = agent
            logger.info(f"Registered agent: {agent.name} ({agent.id})")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent {agent.id}: {e}")
            return False
    
    def create_flow(self, session_id: str, user_input: str, agent_ids: Optional[List[str]] = None) -> str:
        """Create a new flow based on user input"""
        try:
            context = FlowContext(session_id=session_id, user_input=user_input)
            
            # Auto-select agents if not specified
            if agent_ids is None:
                agent_ids = self._select_agents_for_input(user_input)
            
            # Create flow steps
            flow_steps = []
            for i, agent_id in enumerate(agent_ids):
                if agent_id in self.agents:
                    step = FlowStep(
                        agent_id=agent_id,
                        input_data={"context": context, "step": i},
                        dependencies=flow_steps[-1:1] if i > 0 else []
                    )
                    flow_steps.append(step)
            
            self.flows[session_id] = flow_steps
            self.active_sessions[session_id] = {
                "context": context,
                "created_at": time.time(),
                "state": "created"
            }
            
            logger.info(f"Created flow for session {session_id} with {len(flow_steps)} steps")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create flow: {e}")
            return ""
    
    def execute_flow(self, session_id: str) -> Dict[str, Any]:
        """Execute a flow with all its steps"""
        if session_id not in self.flows:
            return {"success": False, "error": "Flow not found"}
        
        flow_steps = self.flows[session_id]
        results = []
        
        try:
            for step in flow_steps:
                if step.agent_id not in self.agents:
                    step.state = FlowState.FAILED
                    step.error = f"Agent {step.agent_id} not found"
                    continue
                
                agent = self.agents[step.agent_id]
                step.state = FlowState.RUNNING
                step.start_time = time.time()
                
                try:
                    # Execute agent handler
                    result = agent.handler(step.input_data)
                    step.result = result
                    step.state = FlowState.COMPLETED
                    results.append(result)
                    
                except Exception as e:
                    step.error = str(e)
                    step.state = FlowState.FAILED
                    logger.error(f"Agent {step.agent_id} failed: {e}")
                
                finally:
                    step.end_time = time.time()
            
            # Update session state
            self.active_sessions[session_id]["state"] = "completed"
            self.active_sessions[session_id]["completed_at"] = time.time()
            
            return {
                "success": True,
                "session_id": session_id,
                "results": results,
                "execution_time": sum(
                    (step.end_time or 0) - (step.start_time or 0) 
                    for step in flow_steps
                )
            }
            
        except Exception as e:
            logger.error(f"Flow execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _select_agents_for_input(self, user_input: str) -> List[str]:
        """Intelligently select agents based on user input"""
        input_lower = user_input.lower()
        selected_agents = []
        
        # Simple keyword-based selection (can be enhanced with ML)
        if any(word in input_lower for word in ["code", "python", "generate", "implement"]):
            selected_agents.append("coder")
        
        if any(word in input_lower for word in ["analyze", "data", "stats", "summary"]):
            selected_agents.append("analyst")
        
        if any(word in input_lower for word in ["reason", "complex", "solve", "plan"]):
            selected_agents.append("reasoner")
        
        # Always include orchestrator for complex tasks
        if len(selected_agents) > 1 or any(word in input_lower for word in ["build", "create", "design"]):
            selected_agents.insert(0, "orchestrator")
        
        # Default to reasoner if nothing selected
        if not selected_agents:
            selected_agents.append("reasoner")
        
        return selected_agents
    
    # Agent handlers
    def _reasoner_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reasoning tasks"""
        context = input_data.get("context")
        if not context:
            return {"error": "No context provided"}
        
        # This would integrate with Neo-Clone's minimax_agent skill
        return {
            "agent": "reasoner",
            "analysis": f"Analyzing: {context.user_input}",
            "reasoning_type": "complex",
            "confidence": 0.9
        }
    
    def _coder_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code generation tasks"""
        context = input_data.get("context")
        if not context:
            return {"error": "No context provided"}
        
        # This would integrate with Neo-Clone's code_generation skill
        return {
            "agent": "coder",
            "code_type": "python",
            "generated": f"# Code for: {context.user_input}\nprint('Hello, Neo-Clone!')",
            "explanation": "Generated Python code based on request"
        }
    
    def _analyst_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data analysis tasks"""
        context = input_data.get("context")
        if not context:
            return {"error": "No context provided"}
        
        # This would integrate with Neo-Clone's data_inspector skill
        return {
            "agent": "analyst",
            "analysis_type": "data_inspection",
            "insights": f"Data insights for: {context.user_input}",
            "summary": "Analysis completed successfully"
        }
    
    def _orchestrator_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent orchestration and building"""
        context = input_data.get("context")
        if not context:
            return {"error": "No context provided"}
        
        # Dynamic agent creation based on requirements
        return {
            "agent": "orchestrator",
            "action": "agent_coordination",
            "plan": f"Orchestrated plan for: {context.user_input}",
            "created_agents": ["dynamic_agent_1"],
            "workflow": "sequential"
        }
    
    def get_flow_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a flow"""
        if session_id not in self.flows:
            return {"error": "Flow not found"}
        
        flow_steps = self.flows[session_id]
        session_info = self.active_sessions.get(session_id, {})
        
        return {
            "session_id": session_id,
            "state": session_info.get("state", "unknown"),
            "steps": [
                {
                    "agent_id": step.agent_id,
                    "state": step.state.value,
                    "duration": (step.end_time or 0) - (step.start_time or 0) if step.end_time and step.start_time else None,
                    "has_result": step.result is not None,
                    "error": step.error
                }
                for step in flow_steps
            ]
        }
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all registered agents"""
        return {
            agent_id: {
                "name": agent.name,
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "input_types": cap.input_types,
                        "output_types": cap.output_types,
                        "confidence": cap.confidence
                    }
                    for cap in agent.capabilities
                ],
                "priority": agent.priority
            }
            for agent_id, agent in self.agents.items()
        }
    
    def create_dynamic_agent(self, requirement: str, session_id: str) -> Optional[str]:
        """Create a dynamic agent based on requirements (Let Agents build Agents!)"""
        try:
            # Generate agent ID
            agent_id = f"dynamic_{int(time.time())}"
            
            # Create capabilities based on requirement
            capabilities = [
                AgentCapability(
                    name="dynamic_task",
                    description=f"Handles: {requirement}",
                    input_types=["text", "requirement"],
                    output_types=["result", "analysis"]
                )
            ]
            
            # Create dynamic handler
            def dynamic_handler(input_data: Dict[str, Any]) -> Dict[str, Any]:
                context = input_data.get("context")
                return {
                    "agent": agent_id,
                    "type": "dynamic",
                    "requirement": requirement,
                    "result": f"Dynamic execution for: {context.user_input if context else requirement}",
                    "confidence": 0.8
                }
            
            # Register the new agent
            agent = Agent(
                id=agent_id,
                name=f"Dynamic Agent - {requirement[:30]}",
                capabilities=capabilities,
                handler=dynamic_handler,
                priority=5
            )
            
            if self.register_agent(agent):
                logger.info(f"Created dynamic agent: {agent_id} for requirement: {requirement}")
                return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create dynamic agent: {e}")
        
        return None
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up a completed session"""
        try:
            if session_id in self.flows:
                del self.flows[session_id]
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            logger.info(f"Cleaned up session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
            return False

# Global PocketFlow instance
_pocketflow_instance = None

def get_pocketflow() -> PocketFlow:
    """Get global PocketFlow instance"""
    global _pocketflow_instance
    if _pocketflow_instance is None:
        _pocketflow_instance = PocketFlow()
    return _pocketflow_instance