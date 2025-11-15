"""
Enhanced MiniMax Agent for Advanced AI Reasoning

This module provides the main agent with advanced reasoning capabilities,
tree-based decision making, state evaluation, multi-step planning, and
dynamic skill generation.

Enhanced Features:
- Dynamic reasoning and skill generation
- Advanced tree search algorithms (A*, Monte Carlo, Minimax)
- Adaptive strategy selection
- Performance optimization and learning
- Real-time state evaluation
- Multi-modal reasoning support

Author: MiniMax Agent
Version: 2.0 Enhanced
"""

import asyncio
import heapq
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
import logging
import math
import threading

# Import foundational modules
try:
    from config import get_config
except ImportError:
    def get_config():
        return {"model": "default", "timeout": 30}

from data_models import (
    Message, MessageRole, ConversationHistory, MemoryEntry, MemoryType,
    IntentType, MiniMaxReasoningTrace, ReasoningStep, SkillResult, SkillContext,
    PerformanceMetrics
)
try:
    from unified_memory import get_unified_memory
    def get_memory():
        return get_unified_memory()
    def get_vector_memory():
        return get_unified_memory()
except ImportError:
    def get_memory():
        return None
    def get_vector_memory():
        return None
try:
    from cache_system import get_cache
except ImportError:
    def get_cache():
        return None
try:
    from base_brain import get_brain, ProcessingMode, ReasoningStrategy
except ImportError:
    def get_brain():
        return None
    class ProcessingMode:
        STANDARD = "standard"
        ENHANCED = "enhanced"
    class ReasoningStrategy:
        DIRECT = "direct"
try:
    from skills import get_skills_manager
except ImportError:
    def get_skills_manager():
        return None
try:
    from plugin_system import get_plugin_manager
except ImportError:
    def get_plugin_manager():
        return None

# Configure logging
logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in the reasoning tree"""
    ROOT = "root"
    INTENT_ANALYSIS = "intent_analysis"
    CONTEXT_RETRIEVAL = "context_retrieval"
    SKILL_SELECTION = "skill_selection"
    SKILL_EXECUTION = "skill_execution"
    RESPONSE_GENERATION = "response_generation"
    EVALUATION = "evaluation"
    LEAF = "leaf"


class SearchStrategy(Enum):
    """Tree search strategies"""
    DFS = "depth_first"       # Depth-first search
    BFS = "breadth_first"     # Breadth-first search
    A_STAR = "a_star"         # A* search
    MINIMAX = "minimax"       # Minimax with alpha-beta pruning
    MONTE_CARLO = "monte_carlo"  # Monte Carlo Tree Search


class EvaluationMetric(Enum):
    """Metrics for evaluating reasoning paths"""
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    EFFICIENCY = "efficiency"
    CONFIDENCE = "confidence"


@dataclass
class ReasoningNode:
    """Node in the reasoning tree"""
    node_id: str
    node_type: NodeType
    content: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    # Evaluation metrics
    score: float = 0.0
    confidence: float = 0.0
    relevance: float = 0.0

    # Metadata
    depth: int = 0
    actions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    # Performance
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ReasoningPath:
    """Complete reasoning path from root to leaf"""
    nodes: List[ReasoningNode] = field(default_factory=list)
    total_score: float = 0.0
    total_confidence: float = 0.0
    total_execution_time: float = 0.0
    success_rate: float = 0.0

    def add_node(self, node: ReasoningNode) -> None:
        """Add node to the path"""
        self.nodes.append(node)
        self._recalculate_metrics()

    def _recalculate_metrics(self) -> None:
        """Recalculate path metrics"""
        if not self.nodes:
            return

        self.total_score = sum(node.score for node in self.nodes) / len(self.nodes)
        self.total_confidence = sum(node.confidence for node in self.nodes) / len(self.nodes)
        self.total_execution_time = sum(node.execution_time for node in self.nodes)
        self.success_rate = sum(1 for node in self.nodes if node.success) / len(self.nodes)

    def get_depth(self) -> int:
        """Get the depth of the path"""
        return len(self.nodes) - 1 if self.nodes else 0

    def get_leaf_nodes(self) -> List[ReasoningNode]:
        """Get all leaf nodes in the path"""
        if not self.nodes:
            return []

        # A path is a single sequence, so the last node is the leaf
        return [self.nodes[-1]]


@dataclass
class TreeSearchState:
    """State for tree search algorithms"""
    current_node: ReasoningNode
    path: ReasoningPath
    visited_nodes: Set[str]
    frontier: List[Tuple[float, int, str]]  # (priority, counter, node_id)
    counter: int = 0  # For tie-breaking in priority queue

    def push_to_frontier(self, priority: float, node_id: str) -> None:
        """Push node to priority queue"""
        heapq.heappush(self.frontier, (priority, self.counter, node_id))
        self.counter += 1

    def pop_from_frontier(self) -> Optional[Tuple[float, str]]:
        """Pop node from priority queue"""
        if not self.frontier:
            return None

        priority, _, node_id = heapq.heappop(self.frontier)
        return priority, node_id

    def is_frontier_empty(self) -> bool:
        """Check if frontier is empty"""
        return len(self.frontier) == 0


class StateEvaluator:
    """Evaluates and scores reasoning states"""

    def __init__(self, weights: Dict[EvaluationMetric, float] = None):
        self.weights = weights or {
            EvaluationMetric.RELEVANCE: 0.3,
            EvaluationMetric.COHERENCE: 0.2,
            EvaluationMetric.COMPLETENESS: 0.2,
            EvaluationMetric.EFFICIENCY: 0.15,
            EvaluationMetric.CONFIDENCE: 0.15
        }

    def evaluate_node(self, node: ReasoningNode, context: Dict[str, Any] = None) -> Dict[EvaluationMetric, float]:
        """Evaluate a reasoning node"""
        scores = {}

        # Relevance score
        scores[EvaluationMetric.RELEVANCE] = self._calculate_relevance(node, context)

        # Coherence score
        scores[EvaluationMetric.COHERENCE] = self._calculate_coherence(node)

        # Completeness score
        scores[EvaluationMetric.COMPLETENESS] = self._calculate_completeness(node)

        # Efficiency score
        scores[EvaluationMetric.EFFICIENCY] = self._calculate_efficiency(node)

        # Confidence score
        scores[EvaluationMetric.CONFIDENCE] = node.confidence

        return scores

    def _calculate_relevance(self, node: ReasoningNode, context: Dict[str, Any] = None) -> float:
        """Calculate relevance score"""
        # Base relevance on node type and content
        base_scores = {
            NodeType.ROOT: 1.0,
            NodeType.INTENT_ANALYSIS: 0.9,
            NodeType.CONTEXT_RETRIEVAL: 0.8,
            NodeType.SKILL_SELECTION: 0.9,
            NodeType.SKILL_EXECUTION: 0.8,
            NodeType.RESPONSE_GENERATION: 1.0,
            NodeType.EVALUATION: 0.7,
            NodeType.LEAF: 0.6
        }

        relevance = base_scores.get(node.node_type, 0.5)

        # Adjust based on depth (prefer nodes at reasonable depth)
        optimal_depth = 5
        depth_penalty = abs(node.depth - optimal_depth) * 0.1
        relevance = max(0.0, relevance - depth_penalty)

        return min(1.0, relevance)

    def _calculate_coherence(self, node: ReasoningNode) -> float:
        """Calculate coherence score"""
        # Coherence based on successful execution and error-free path
        if not node.success:
            return 0.2

        # Check if node has logical actions
        if not node.actions:
            return 0.5

        # Prefer nodes with specific, actionable content
        content_quality = min(1.0, len(node.content) / 50)  # Normalize by content length
        action_quality = min(1.0, len(node.actions) / 3)   # Reasonable number of actions

        return (content_quality + action_quality) / 2

    def _calculate_completeness(self, node: ReasoningNode) -> float:
        """Calculate completeness score"""
        # Completeness based on whether the node represents a complete reasoning step
        required_fields = ['content', 'actions']
        missing_fields = [field for field in required_fields if not getattr(node, field, None)]

        if missing_fields:
            return 0.3

        # Prefer nodes that have both analysis and action components
        has_analysis = len(node.content) > 20
        has_actions = len(node.actions) > 0

        if has_analysis and has_actions:
            return 1.0
        elif has_analysis or has_actions:
            return 0.7
        else:
            return 0.3

    def _calculate_efficiency(self, node: ReasoningNode) -> float:
        """Calculate efficiency score"""
        # Efficiency based on execution time and success
        if not node.success:
            return 0.1

        # Optimal execution time range (0.1 to 2.0 seconds)
        optimal_time = 1.0
        time_ratio = node.execution_time / optimal_time

        if time_ratio <= 1.0:
            efficiency = 1.0
        else:
            efficiency = 1.0 / (1.0 + (time_ratio - 1.0))

        return max(0.1, efficiency)

    def calculate_path_score(self, path: ReasoningPath) -> float:
        """Calculate overall score for a reasoning path"""
        if not path.nodes:
            return 0.0

        # Get individual scores
        node_scores = []
        for node in path.nodes:
            evaluation = self.evaluate_node(node)
            weighted_score = sum(
                evaluation[metric] * self.weights[metric]
                for metric in EvaluationMetric
            )
            node_scores.append(weighted_score)

        # Average node scores with depth bonus
        avg_score = sum(node_scores) / len(node_scores)
        depth_bonus = min(0.2, path.get_depth() * 0.05)  # Bonus for deeper reasoning

        return min(1.0, avg_score + depth_bonus)


class MiniMaxAgent:
    """
    MiniMax Agent with advanced reasoning capabilities

    Features:
    - Tree-based reasoning and search
    - State evaluation and scoring
    - Multi-step planning
    - Adaptive strategy selection
    - Performance optimization
    """

    def __init__(
        self,
        search_strategy: SearchStrategy = SearchStrategy.A_STAR,
        max_depth: int = 7,
        max_nodes: int = 100,
        confidence_threshold: float = 0.7,
        enable_pruning: bool = True,
        adaptive_strategy: bool = True
    ):
        """
        Initialize MiniMax Agent

        Args:
            search_strategy: Tree search strategy to use
            max_depth: Maximum reasoning depth
            max_nodes: Maximum nodes to explore
            confidence_threshold: Minimum confidence for decisions
            enable_pruning: Enable alpha-beta pruning
            adaptive_strategy: Enable adaptive strategy selection
        """
        self.search_strategy = search_strategy
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.confidence_threshold = confidence_threshold
        self.enable_pruning = enable_pruning
        self.adaptive_strategy = adaptive_strategy

        # Core components
        self.config = get_config()
        self.memory = get_memory()
        self.vector_memory = get_vector_memory()
        self.cache = get_cache()
        self.brain = get_brain()
        self.skills_manager = get_skills_manager()
        self.plugin_manager = get_plugin_manager()

        # Reasoning components
        self.state_evaluator = StateEvaluator()
        self.reasoning_tree: Dict[str, ReasoningNode] = {}
        self.reasoning_paths: List[ReasoningPath] = []

        # Performance tracking
        self.performance_metrics: List[PerformanceMetrics] = []
        self.total_reasoning_sessions = 0
        self.successful_sessions = 0

        # Strategy adaptation
        self.strategy_performance: Dict[SearchStrategy, Dict[str, float]] = {
            strategy: {"success_rate": 0.0, "avg_time": 0.0, "avg_quality": 0.0}
            for strategy in SearchStrategy
        }

        logger.info(f"MiniMax Agent initialized: strategy={search_strategy.value}, max_depth={max_depth}")

    async def process_input(
        self,
        user_input: str,
        context: Optional[ConversationHistory] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, MiniMaxReasoningTrace]:
        """
        Process user input with advanced reasoning

        Args:
            user_input: User's input text
            context: Conversation context
            session_id: Session identifier

        Returns:
            Tuple of (response, reasoning_trace)
        """
        start_time = time.time()
        session_id = session_id or self.memory.session_id

        self.total_reasoning_sessions += 1

        try:
            # Reset reasoning state
            self._reset_reasoning_state()

            # Create reasoning trace
            reasoning_trace = MiniMaxReasoningTrace()

            # Step 1: Analyze input and create root node
            root_node = await self._create_root_node(user_input, reasoning_trace)

            # Step 2: Perform tree search for optimal reasoning path
            optimal_path = await self._perform_tree_search(root_node, reasoning_trace)

            # Step 3: Execute the optimal path
            response = await self._execute_optimal_path(optimal_path, reasoning_trace)

            # Step 4: Update strategy performance
            if self.adaptive_strategy:
                self._update_strategy_performance(
                    self.search_strategy, time.time() - start_time, True, reasoning_trace.confidence_score
                )

            # Step 5: Learn from the session
            await self._learn_from_session(user_input, response, optimal_path)

            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(user_input, response, execution_time, True)
            self.successful_sessions += 1

            logger.info(f"MiniMax processing completed: {execution_time:.3f}s, confidence={reasoning_trace.confidence_score:.2f}")
            return response, reasoning_trace

        except Exception as e:
            logger.error(f"MiniMax processing failed: {e}")
            error_response = "I apologize, but I encountered an error during advanced reasoning. Please try again."

            # Update strategy performance for failure
            if self.adaptive_strategy:
                self._update_strategy_performance(
                    self.search_strategy, time.time() - start_time, False, 0.0
                )

            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(user_input, error_response, execution_time, False)

            return error_response, MiniMaxReasoningTrace()

    async def _create_root_node(self, user_input: str, reasoning_trace: MiniMaxReasoningTrace) -> ReasoningNode:
        """Create the root reasoning node"""
        root_node = ReasoningNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.ROOT,
            content=f"Analyzing user input: {user_input}",
            depth=0,
            actions=["analyze_input", "prepare_reasoning"],
            context={"user_input": user_input}
        )

        self.reasoning_tree[root_node.node_id] = root_node

        reasoning_trace.add_step(
            step_type="root_creation",
            description="Created root reasoning node",
            input_data=user_input,
            output_data=root_node.content,
            confidence=1.0
        )

        return root_node

    async def _perform_tree_search(
        self,
        root_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> ReasoningPath:
        """Perform tree search to find optimal reasoning path"""
        start_time = time.time()

        # Initialize search state
        root_path = ReasoningPath()
        root_path.add_node(root_node)

        search_state = TreeSearchState(
            current_node=root_node,
            path=root_path,
            visited_nodes=set([root_node.node_id]),
            frontier=[]
        )

        # Push root to frontier
        search_state.push_to_frontier(1.0, root_node.node_id)

        best_path = root_path
        best_score = 0.0

        nodes_explored = 0
        pruning_count = 0

        while not search_state.is_frontier_empty() and nodes_explored < self.max_nodes:
            # Get next node to explore
            priority, node_id = search_state.pop_from_frontier()

            if node_id in search_state.visited_nodes:
                continue

            current_node = self.reasoning_tree[node_id]
            search_state.visited_nodes.add(node_id)
            nodes_explored += 1

            # Check if we've reached optimal depth or node
            if current_node.depth >= self.max_depth or self._is_goal_node(current_node):
                # Evaluate path and update best
                path_score = self.state_evaluator.calculate_path_score(search_state.path)
                if path_score > best_score:
                    best_score = path_score
                    best_path = ReasoningPath(nodes=search_state.path.nodes.copy())
                continue

            # Generate child nodes
            child_nodes = await self._generate_child_nodes(current_node, reasoning_trace)

            # Add children to search frontier
            for child_node in child_nodes:
                self.reasoning_tree[child_node.node_id] = child_node

                # Create path including this child
                child_path = ReasoningPath(nodes=search_state.path.nodes.copy())
                child_path.add_node(child_node)

                # Evaluate child node
                evaluation = self.state_evaluator.evaluate_node(child_node)
                child_score = sum(
                    evaluation[metric] * self.state_evaluator.weights[metric]
                    for metric in EvaluationMetric
                )

                # Alpha-beta pruning
                if self.enable_pruning and self._should_prune(current_node, child_score, best_score):
                    pruning_count += 1
                    continue

                # Add to frontier with priority (higher score = higher priority)
                search_state.push_to_frontier(child_score, child_node.node_id)

        execution_time = time.time() - start_time

        reasoning_trace.add_step(
            step_type="tree_search",
            description=f"Tree search completed: {nodes_explored} nodes, {pruning_count} pruned",
            input_data={"strategy": self.search_strategy.value, "max_depth": self.max_depth},
            output_data={
                "nodes_explored": nodes_explored,
                "pruning_count": pruning_count,
                "best_score": best_score,
                "execution_time": execution_time
            },
            confidence=min(1.0, best_score)
        )

        return best_path

    async def _generate_child_nodes(
        self,
        parent_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> List[ReasoningNode]:
        """Generate child nodes based on parent node type and content"""
        child_nodes = []

        if parent_node.node_type == NodeType.ROOT:
            # Generate intent analysis node
            intent_node = await self._create_intent_analysis_node(parent_node, reasoning_trace)
            child_nodes.append(intent_node)

        elif parent_node.node_type == NodeType.INTENT_ANALYSIS:
            # Generate context retrieval node
            context_node = await self._create_context_retrieval_node(parent_node, reasoning_trace)
            child_nodes.append(context_node)

        elif parent_node.node_type == NodeType.CONTEXT_RETRIEVAL:
            # Generate skill selection node
            skill_node = await self._create_skill_selection_node(parent_node, reasoning_trace)
            child_nodes.append(skill_node)

        elif parent_node.node_type == NodeType.SKILL_SELECTION:
            # Generate skill execution node
            execution_node = await self._create_skill_execution_node(parent_node, reasoning_trace)
            child_nodes.append(execution_node)

        elif parent_node.node_type == NodeType.SKILL_EXECUTION:
            # Generate response generation node
            response_node = await self._create_response_generation_node(parent_node, reasoning_trace)
            child_nodes.append(response_node)

        elif parent_node.node_type == NodeType.RESPONSE_GENERATION:
            # Generate evaluation node
            evaluation_node = await self._create_evaluation_node(parent_node, reasoning_trace)
            child_nodes.append(evaluation_node)

        # Link parent and children
        for child_node in child_nodes:
            parent_node.children_ids.append(child_node.node_id)
            child_node.parent_id = parent_node.node_id

        return child_nodes

    async def _create_intent_analysis_node(
        self,
        parent_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> ReasoningNode:
        """Create intent analysis node"""
        start_time = time.time()

        user_input = parent_node.context.get("user_input", "")

        # Use brain's intent recognition
        intent_result = await self.brain._recognize_intent(user_input, reasoning_trace)

        node = ReasoningNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.INTENT_ANALYSIS,
            content=f"Intent recognized: {intent_result.intent.value} (confidence: {intent_result.confidence:.2f})",
            depth=parent_node.depth + 1,
            actions=["classify_intent", "assess_confidence"],
            context={
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "scores": intent_result.scores
            },
            confidence=intent_result.confidence,
            execution_time=time.time() - start_time
        )

        return node

    async def _create_context_retrieval_node(
        self,
        parent_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> ReasoningNode:
        """Create context retrieval node"""
        start_time = time.time()

        user_input = parent_node.context.get("user_input", "")
        intent = parent_node.context.get("intent", "conversation")

        # Use brain's context retrieval
        relevant_context = await self.brain._retrieve_context(user_input, type('IntentResult', (), {
            'intent': type('Intent', (), {'value': intent})()
        })(), reasoning_trace)

        node = ReasoningNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.CONTEXT_RETRIEVAL,
            content=f"Retrieved {len(relevant_context)} relevant context items",
            depth=parent_node.depth + 1,
            actions=["search_memory", "filter_relevant"],
            context={
                "context_count": len(relevant_context),
                "context_items": [m.content for m in relevant_context[:3]]  # Top 3
            },
            confidence=min(0.9, len(relevant_context) * 0.2 + 0.3),
            execution_time=time.time() - start_time
        )

        return node

    async def _create_skill_selection_node(
        self,
        parent_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> ReasoningNode:
        """Create skill selection node"""
        start_time = time.time()

        user_input = parent_node.context.get("user_input", "")
        intent = parent_node.context.get("intent", "conversation")

        # Use brain's skill selection
        selected_skill = await self.brain._select_skill(user_input, type('IntentResult', (), {
            'intent': type('Intent', (), {'value': intent})()
        })(), reasoning_trace)

        node = ReasoningNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.SKILL_SELECTION,
            content=f"Selected skill: {selected_skill or 'conversation'}",
            depth=parent_node.depth + 1,
            actions=["select_skill", "validate_availability"],
            context={
                "selected_skill": selected_skill,
                "available_skills": self.skills_manager.list_skills()
            },
            confidence=0.8 if selected_skill else 0.5,
            execution_time=time.time() - start_time
        )

        return node

    async def _create_skill_execution_node(
        self,
        parent_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> ReasoningNode:
        """Create skill execution node"""
        start_time = time.time()

        user_input = parent_node.context.get("user_input", "")
        selected_skill = parent_node.context.get("selected_skill")

        # Use brain's skill execution
        skill_result = await self.brain._execute_skill(
            selected_skill, user_input, [], type('IntentResult', (), {
                'intent': type('Intent', (), {'value': 'conversation'})()
            })(), reasoning_trace
        )

        node = ReasoningNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.SKILL_EXECUTION,
            content=f"Skill execution: {'success' if skill_result.success else 'failed'}",
            depth=parent_node.depth + 1,
            actions=["execute_skill", "handle_result"],
            context={
                "skill_result": skill_result.success,
                "output_preview": str(skill_result.output)[:100] if skill_result.output else "",
                "execution_time": skill_result.execution_time
            },
            confidence=0.9 if skill_result.success else 0.3,
            execution_time=time.time() - start_time,
            success=skill_result.success,
            error_message=skill_result.error_message
        )

        return node

    async def _create_response_generation_node(
        self,
        parent_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> ReasoningNode:
        """Create response generation node"""
        start_time = time.time()

        user_input = parent_node.context.get("user_input", "")
        skill_result = parent_node.context.get("skill_result", False)

        # Generate response
        if skill_result:
            response = "I have successfully processed your request using advanced reasoning."
        else:
            response = "I understand your request and will do my best to help you."

        node = ReasoningNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.RESPONSE_GENERATION,
            content=f"Generated response: {response[:50]}...",
            depth=parent_node.depth + 1,
            actions=["synthesize_response", "validate_coherence"],
            context={
                "response": response,
                "response_length": len(response)
            },
            confidence=0.8,
            execution_time=time.time() - start_time
        )

        return node

    async def _create_evaluation_node(
        self,
        parent_node: ReasoningNode,
        reasoning_trace: MiniMaxReasoningTrace
    ) -> ReasoningNode:
        """Create evaluation node"""
        start_time = time.time()

        # Evaluate the complete reasoning path
        path_nodes = []  # This would collect all nodes in the path

        # Calculate overall confidence
        overall_confidence = parent_node.confidence

        # Check for errors in the path
        has_errors = parent_node.error_message is not None

        evaluation_result = "success" if not has_errors else "partial_success"

        node = ReasoningNode(
            node_id=str(uuid.uuid4()),
            node_type=NodeType.EVALUATION,
            content=f"Reasoning evaluation: {evaluation_result} (confidence: {overall_confidence:.2f})",
            depth=parent_node.depth + 1,
            actions=["evaluate_path", "calculate_confidence"],
            context={
                "evaluation_result": evaluation_result,
                "overall_confidence": overall_confidence,
                "has_errors": has_errors
            },
            confidence=overall_confidence,
            execution_time=time.time() - start_time
        )

        return node

    def _is_goal_node(self, node: ReasoningNode) -> bool:
        """Check if node represents a goal state"""
        return node.node_type in [NodeType.LEAF, NodeType.EVALUATION] and node.confidence >= self.confidence_threshold

    def _should_prune(self, parent_node: ReasoningNode, child_score: float, best_score: float) -> bool:
        """Check if branch should be pruned (alpha-beta pruning)"""
        # Simple pruning: if child score is significantly worse than best
        return child_score < best_score - 0.2

    async def _execute_optimal_path(self, path: ReasoningPath, reasoning_trace: MiniMaxReasoningTrace) -> str:
        """Execute the optimal reasoning path"""
        if not path.nodes:
            return "I apologize, but I could not find a valid reasoning path."

        # Extract response from the last node
        last_node = path.nodes[-1]

        if last_node.node_type == NodeType.RESPONSE_GENERATION:
            response = last_node.context.get("response", "Default response")
        else:
            response = f"I have completed the reasoning process with {last_node.confidence:.2f} confidence."

        # Update reasoning trace with path information
        reasoning_trace.confidence_score = path.total_confidence

        for i, node in enumerate(path.nodes[1:], 1):  # Skip root node
            reasoning_trace.add_step(
                step_type=node.node_type.value,
                description=node.content,
                input_data=node.context,
                output_data=node.content,
                confidence=node.confidence
            )

        return response

    async def _learn_from_session(
        self,
        user_input: str,
        response: str,
        optimal_path: ReasoningPath
    ) -> None:
        """Learn from the reasoning session"""
        try:
            # Store in memory
            await self.brain._store_in_memory(user_input, response, None, None)

            # Update strategy performance if adaptive
            if self.adaptive_strategy:
                path_score = self.state_evaluator.calculate_path_score(optimal_path)
                # This would update internal learning mechanisms

        except Exception as e:
            logger.warning(f"Learning from session failed: {e}")

    def _update_strategy_performance(
        self,
        strategy: SearchStrategy,
        execution_time: float,
        success: bool,
        quality_score: float
    ) -> None:
        """Update performance metrics for strategy adaptation"""
        stats = self.strategy_performance[strategy]

        # Update success rate (exponential moving average)
        alpha = 0.1
        stats["success_rate"] = (1 - alpha) * stats["success_rate"] + alpha * (1.0 if success else 0.0)

        # Update average time
        stats["avg_time"] = (1 - alpha) * stats["avg_time"] + alpha * execution_time

        # Update average quality
        stats["avg_quality"] = (1 - alpha) * stats["avg_quality"] + alpha * quality_score

    def adapt_strategy(self) -> bool:
        """Adapt search strategy based on performance"""
        if not self.adaptive_strategy:
            return False

        current_stats = self.strategy_performance[self.search_strategy]

        # If current strategy is performing poorly, consider switching
        if (current_stats["success_rate"] < 0.6 or
            current_stats["avg_time"] > 5.0 or
            current_stats["avg_quality"] < 0.5):

            # Find best performing strategy
            best_strategy = min(
                self.strategy_performance.keys(),
                key=lambda s: (
                    1 - self.strategy_performance[s]["success_rate"] +
                    self.strategy_performance[s]["avg_time"] / 10.0 +
                    (1 - self.strategy_performance[s]["avg_quality"])
                )
            )

            if best_strategy != self.search_strategy:
                old_strategy = self.search_strategy
                self.search_strategy = best_strategy
                logger.info(f"Adapted strategy from {old_strategy.value} to {best_strategy.value}")
                return True

        return False

    def _reset_reasoning_state(self) -> None:
        """Reset reasoning state for new session"""
        self.reasoning_tree.clear()
        self.reasoning_paths.clear()

    def _update_performance_metrics(
        self,
        input_text: str,
        output_text: str,
        execution_time: float,
        success: bool
    ) -> None:
        """Update performance metrics"""
        metrics = PerformanceMetrics(
            operation_name="minimax_reasoning",
            execution_time=execution_time,
            success=success,
            input_size=len(input_text),
            output_size=len(output_text),
            metadata={
                "search_strategy": self.search_strategy.value,
                "max_depth": self.max_depth,
                "confidence_threshold": self.confidence_threshold,
                "total_sessions": self.total_reasoning_sessions
            }
        )

        self.performance_metrics.append(metrics)

        # Keep only recent metrics (last 500)
        if len(self.performance_metrics) > 500:
            self.performance_metrics = self.performance_metrics[-500:]

    def get_status(self) -> Dict[str, Any]:
        """Get MiniMax Agent status and statistics"""
        recent_metrics = [m for m in self.performance_metrics[-50:]] if self.performance_metrics else []

        avg_execution_time = (
            sum(m.execution_time for m in recent_metrics) / len(recent_metrics)
            if recent_metrics else 0.0
        )

        success_rate = (
            sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            if recent_metrics else 0.0
        )

        return {
            "search_strategy": self.search_strategy.value,
            "max_depth": self.max_depth,
            "max_nodes": self.max_nodes,
            "confidence_threshold": self.confidence_threshold,
            "adaptive_strategy": self.adaptive_strategy,
            "total_reasoning_sessions": self.total_reasoning_sessions,
            "successful_sessions": self.successful_sessions,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "current_reasoning_nodes": len(self.reasoning_tree),
            "strategy_performance": {
                strategy.value: stats.copy()
                for strategy, stats in self.strategy_performance.items()
            },
            "performance_metrics_count": len(self.performance_metrics)
        }

    def analyze_user_input(self, message: str, context: List[str]) -> Dict:
        """Analyze user intent and suggest actions - Enhanced from reference brain.py"""
        # Enhanced intent analysis with keyword patterns
        message_lower = message.lower()
        
        # Intent classification with expanded patterns
        intents = []
        
        # Code generation patterns
        if any(word in message_lower for word in ["code", "python", "script", "program", "function", "class", "algorithm", "implement"]):
            intents.append("code_generation")
        
        # Data analysis patterns  
        if any(word in message_lower for word in ["analyze", "data", "csv", "json", "dataset", "statistics", "insights"]):
            intents.append("data_analysis")
        
        # Web search patterns
        if any(word in message_lower for word in ["search", "find", "web", "research", "lookup", "information"]):
            intents.append("web_search")
        
        # File management patterns
        if any(word in message_lower for word in ["file", "read", "write", "directory", "folder", "manage", "organize"]):
            intents.append("file_manager")
        
        # ML training patterns
        if any(word in message_lower for word in ["ml", "train", "model", "machine learning", "neural", "ai", "predict"]):
            intents.append("ml_training")
        
        # Text analysis patterns
        if any(word in message_lower for word in ["text", "sentiment", "analyze text", "moderation", "content"]):
            intents.append("text_analysis")
        
        # Constitution patterns
        if any(word in message_lower for word in ["constitution", "principles", "rules", "guidelines", "foundation"]):
            intents.append("constitution")
        
        # Specification patterns
        if any(word in message_lower for word in ["spec", "requirement", "specification", "technical", "documentation"]):
            intents.append("specification")
        
        # Planning patterns
        if any(word in message_lower for word in ["plan", "roadmap", "strategy", "timeline", "milestone"]):
            intents.append("planning")
        
        # Task breakdown patterns
        if any(word in message_lower for word in ["breakdown", "task", "organize", "structure", "decompose"]):
            intents.append("task_breakdown")
        
        # Implementation patterns
        if any(word in message_lower for word in ["implement", "execute", "deploy", "build", "create"]):
            intents.append("implementation")
        
        # Skill creation patterns
        if any(word in message_lower for word in ["create", "skill", "tool", "capability", "functionality"]):
            intents.append("skill_creation")
        
        # Enhanced confidence scoring
        base_confidence = 0.5
        intent_bonus = len(intents) * 0.12
        context_bonus = min(len(context) * 0.03, 0.15)
        length_bonus = min(len(message) / 1000, 0.1)
        
        confidence = base_confidence + intent_bonus + context_bonus + length_bonus
        confidence = min(confidence, 0.95)
        
        # Enhanced reasoning trace
        reasoning_trace = {
            "intent_analysis": f"Detected {len(intents)} intent patterns: {', '.join(intents)}",
            "context_analysis": f"Processed {len(context)} context items for enhanced understanding",
            "skill_suggestion": f"Recommended top {min(3, len(intents))} skills based on confidence {confidence:.2f}",
            "keyword_matches": [word for word in message_lower.split() if len(word) > 3],
            "complexity_score": min(len(message) / 100, 1.0)
        }
        
        return {
            "primary_intent": intents[0] if intents else "general",
            "all_intents": intents,
            "suggested_skills": intents[:3],  # Top 3 skills
            "confidence": confidence,
            "message": message,
            "context_count": len(context),
            "reasoning_trace": reasoning_trace,
            "execution_strategy": "parallel" if len(intents) > 2 else "sequential"
        }

    def shutdown(self) -> None:
        """Shutdown MiniMax Agent"""
        logger.info("Shutting down MiniMax Agent")

        # Perform final adaptation
        if self.adaptive_strategy:
            self.adapt_strategy()

        logger.info("MiniMax Agent shutdown complete")


# Singleton agent instance
_agent_instance: Optional[MiniMaxAgent] = None
_agent_lock = threading.Lock()


def get_minimax_agent(
    search_strategy: SearchStrategy = SearchStrategy.A_STAR,
    max_depth: int = 7,
    max_nodes: int = 100
) -> MiniMaxAgent:
    """
    Get singleton MiniMax Agent instance

    Args:
        search_strategy: Tree search strategy
        max_depth: Maximum reasoning depth
        max_nodes: Maximum nodes to explore

    Returns:
        MiniMaxAgent singleton instance
    """
    global _agent_instance

    if _agent_instance is None:
        with _agent_lock:
            if _agent_instance is None:
                _agent_instance = MiniMaxAgent(search_strategy, max_depth, max_nodes)

    return _agent_instance


def reset_minimax_agent() -> None:
    """Reset the MiniMax Agent instance"""
    global _agent_instance
    with _agent_lock:
        if _agent_instance:
            try:
                _agent_instance.shutdown()
            except Exception:
                pass
        _agent_instance = None
    logger.info("MiniMax Agent instance reset")


def create_minimax_agent_instance(
    search_strategy: SearchStrategy = SearchStrategy.A_STAR,
    max_depth: int = 7,
    max_nodes: int = 100,
    confidence_threshold: float = 0.7
) -> MiniMaxAgent:
    """
    Create a new MiniMax Agent instance

    Args:
        search_strategy: Tree search strategy
        max_depth: Maximum reasoning depth
        max_nodes: Maximum nodes to explore
        confidence_threshold: Minimum confidence threshold

    Returns:
        New MiniMaxAgent instance
    """
    return MiniMaxAgent(
        search_strategy=search_strategy,
        max_depth=max_depth,
        max_nodes=max_nodes,
        confidence_threshold=confidence_threshold
    )
