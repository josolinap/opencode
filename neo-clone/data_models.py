"""
Data Models for MiniMax Agent Architecture

This module provides comprehensive data structures and type definitions
for the entire MiniMax Agent system including messages, memory, skills,
reasoning traces, and performance metrics.

Author: MiniMax Agent
Version: 1.0
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
import json
import uuid


# ============================================================================
# Enums
# ============================================================================

class MessageRole(Enum):
    """Message role in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MemoryType(Enum):
    """Type of memory entry"""
    EPISODIC = "episodic"       # Specific events/conversations
    SEMANTIC = "semantic"       # General knowledge
    PROCEDURAL = "procedural"   # How-to knowledge
    WORKING = "working"         # Temporary context


class SkillCategory(Enum):
    """Skill category classification"""
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    RESEARCH = "research"
    WEB_SEARCH = "web_search"
    FILE_MANAGEMENT = "file_management"
    TEXT_ANALYSIS = "text_analysis"
    ML_TRAINING = "ml_training"
    PROJECT_MANAGEMENT = "project_management"
    PLANNING = "planning"
    GENERAL = "general"


class IntentType(Enum):
    """User intent classification"""
    CODE = "code"
    DATA_ANALYSIS = "data_analysis"
    CONVERSATION = "conversation"
    PLANNING = "planning"
    DEBUGGING = "debugging"
    LEARNING = "learning"
    SYSTEM = "system"
    REASONING = "reasoning"


class ProcessingMode(Enum):
    """Brain processing mode"""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    COLLABORATIVE = "collaborative"
    OPTIMIZED = "optimized"


class MemoryQueryType(Enum):
    """Type of memory query"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    EXACT = "exact"


class SkillExecutionStatus(Enum):
    """Skill execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProviderStatus(Enum):
    """Provider availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    UNKNOWN = "unknown"


# ============================================================================
# Message Models
# ============================================================================

@dataclass
class Message:
    """Single message in conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary (deserialization)"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now().isoformat())
            ),
            metadata=data.get("metadata", {})
        )
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))
    
    def __str__(self) -> str:
        """String representation"""
        return f"Message(role={self.role.value}, content='{self.content[:50]}...')"


@dataclass
class ConversationHistory:
    """Conversation history manager with automatic trimming"""
    messages: List[Message] = field(default_factory=list)
    max_history: int = 1000
    session_id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    
    def add(self, role: MessageRole, content: str, metadata: Optional[Dict] = None) -> None:
        """Add message to history with automatic trimming"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # Trim if exceeds max
        if len(self.messages) > self.max_history:
            # Keep the last max_history messages
            self.messages = self.messages[-self.max_history:]
    
    def get_recent(self, limit: int = 10) -> List[Message]:
        """Get recent messages"""
        return self.messages[-limit:] if limit > 0 else []
    
    def get_context(self, window_size: int = 10) -> List[Message]:
        """Get context window for current conversation"""
        return self.messages[-window_size:] if window_size > 0 else []
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries"""
        return [msg.to_dict() for msg in self.messages]
    
    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()
    
    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)
    
    def get_last_message(self) -> Optional[Message]:
        """Get the last message"""
        return self.messages[-1] if self.messages else None
    
    def find_messages_by_role(self, role: MessageRole) -> List[Message]:
        """Find all messages with specific role"""
        return [msg for msg in self.messages if msg.role == role]
    
    def search_content(self, query: str, case_sensitive: bool = False) -> List[Message]:
        """Search messages by content"""
        query_text = query if case_sensitive else query.lower()
        results = []
        
        for msg in self.messages:
            content = msg.content if case_sensitive else msg.content.lower()
            if query_text in content:
                results.append(msg)
        
        return results


# ============================================================================
# Memory Models
# ============================================================================

@dataclass
class MemoryEntry:
    """Single memory entry with metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.EPISODIC
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5  # 0.0 to 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now().isoformat())
            ),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
    
    def update_importance(self, new_importance: float) -> None:
        """Update importance score with bounds checking"""
        self.importance = max(0.0, min(1.0, new_importance))
    
    def add_tag(self, tag: str) -> None:
        """Add tag if not already present"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove tag if present"""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if memory has specific tag"""
        return tag in self.tags
    
    def __str__(self) -> str:
        """String representation"""
        return f"MemoryEntry(id={self.id[:8]}, type={self.memory_type.value}, importance={self.importance})"


@dataclass
class MemoryVector:
    """Vector memory entry with embeddings"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    embedding: List[float] = field(default_factory=list)
    memory_type: MemoryType = MemoryType.SEMANTIC
    importance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def similarity(self, other: "MemoryVector") -> float:
        """Calculate cosine similarity with another vector"""
        if not self.embedding or not other.embedding:
            return 0.0
        
        if len(self.embedding) != len(other.embedding):
            # Pad shorter vector with zeros
            max_len = max(len(self.embedding), len(other.embedding))
            embedding_a = self.embedding + [0.0] * (max_len - len(self.embedding))
            embedding_b = other.embedding + [0.0] * (max_len - len(other.embedding))
        else:
            embedding_a = self.embedding
            embedding_b = other.embedding
        
        # Cosine similarity implementation
        dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
        magnitude_a = sum(a * a for a in embedding_a) ** 0.5
        magnitude_b = sum(b * b for b in embedding_b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        similarity = dot_product / (magnitude_a * magnitude_b)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    def distance(self, other: "MemoryVector") -> float:
        """Calculate Euclidean distance to another vector"""
        if not self.embedding or not other.embedding:
            return 1.0
        
        if len(self.embedding) != len(other.embedding):
            max_len = max(len(self.embedding), len(other.embedding))
            embedding_a = self.embedding + [0.0] * (max_len - len(self.embedding))
            embedding_b = other.embedding + [0.0] * (max_len - len(other.embedding))
        else:
            embedding_a = self.embedding
            embedding_b = other.embedding
        
        distance = sum((a - b) ** 2 for a, b in zip(embedding_a, embedding_b)) ** 0.5
        return min(1.0, distance)  # Normalize to [0, 1]


# ============================================================================
# Skill Models
# ============================================================================

@dataclass
class SkillResult:
    """Result from skill execution"""
    success: bool
    output: Any
    skill_name: str
    execution_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result_dict = asdict(self)
        result_dict["success"] = self.success
        return result_dict
    
    def __str__(self) -> str:
        """String representation"""
        status = "SUCCESS" if self.success else "FAILED"
        return f"SkillResult({status}, skill={self.skill_name}, time={self.execution_time:.2f}s)"


@dataclass
class SkillContext:
    """Context for skill execution"""
    user_input: str
    intent: IntentType
    conversation_history: List[Message]
    memory_context: List[MemoryEntry] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_relevant_context(self, limit: int = 5) -> List[Message]:
        """Get relevant context messages"""
        return self.conversation_history[-limit:] if limit > 0 else []
    
    def add_preference(self, key: str, value: Any) -> None:
        """Add user preference"""
        self.user_preferences[key] = value


@dataclass
class SkillMetadata:
    """Skill metadata and capabilities"""
    name: str
    category: SkillCategory
    description: str
    version: str = "1.0.0"
    author: str = "Unknown"
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "dependencies": self.dependencies,
            "parameters": self.parameters,
            "examples": self.examples
        }


# ============================================================================
# Reasoning Models
# ============================================================================

@dataclass
class ReasoningStep:
    """Single step in reasoning chain"""
    step_number: int
    step_type: str  # "analysis", "retrieval", "generation", etc.
    description: str
    input_data: Any
    output_data: Any
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type,
            "description": self.description,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MiniMaxReasoningTrace:
    """Complete reasoning trace for MiniMax agent"""
    steps: List[ReasoningStep] = field(default_factory=list)
    intent_analysis: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    final_confidence: float = 0.0
    
    def add_step(
        self,
        step_type: str,
        description: str,
        input_data: Any,
        output_data: Any,
        confidence: float = 1.0
    ) -> None:
        """Add reasoning step"""
        step = ReasoningStep(
            step_number=len(self.steps) + 1,
            step_type=step_type,
            description=description,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence
        )
        self.steps.append(step)
    
    def add_intent_analysis(
        self,
        intent: str,
        confidence: float,
        categories: List[str],
        metadata: Optional[Dict] = None
    ) -> None:
        """Add intent analysis"""
        self.intent_analysis = {
            "intent": intent,
            "confidence": confidence,
            "categories": categories,
            "metadata": metadata or {}
        }
        self.confidence_score = confidence
    
    def get_step_by_type(self, step_type: str) -> Optional[ReasoningStep]:
        """Get first step matching the given type"""
        for step in self.steps:
            if step.step_type == step_type:
                return step
        return None
    
    def get_steps_by_type(self, step_type: str) -> List[ReasoningStep]:
        """Get all steps matching the given type"""
        return [step for step in self.steps if step.step_type == step_type]
    
    def get_average_confidence(self) -> float:
        """Calculate average confidence across all steps"""
        if not self.steps:
            return 0.0
        return sum(step.confidence for step in self.steps) / len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "steps": [step.to_dict() for step in self.steps],
            "intent_analysis": self.intent_analysis,
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "final_confidence": self.final_confidence
        }


# ============================================================================
# Performance Models
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation_name: str
    execution_time: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    input_size: int = 0
    output_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @property
    def throughput(self) -> float:
        """Calculate throughput (output_size / execution_time)"""
        return self.output_size / self.execution_time if self.execution_time > 0 else 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: float = 300.0  # 5 minutes
    hit_count: int = 0
    similarity_score: float = 1.0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl
    
    def access(self) -> None:
        """Record cache hit"""
        self.hit_count += 1
    
    def update_ttl(self, new_ttl: float) -> None:
        """Update TTL"""
        self.ttl = max(0.0, new_ttl)


# ============================================================================
# Integration Models
# ============================================================================

@dataclass
class ModelInfo:
    """AI model information"""
    provider: str
    model_name: str
    api_endpoint: str
    api_key_required: bool = False
    context_length: int = 4096
    capabilities: List[str] = field(default_factory=list)
    cost: str = "free"
    status: ProviderStatus = ProviderStatus.UNKNOWN
    response_time: float = 0.0
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result_dict = asdict(self)
        result_dict["status"] = self.status.value
        return result_dict
    
    def is_available(self) -> bool:
        """Check if model is available"""
        return self.status == ProviderStatus.AVAILABLE


@dataclass
class FrameworkInfo:
    """External framework information"""
    name: str
    version: str
    description: str
    capabilities: List[str]
    installed: bool = False
    compatible: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SystemInfo:
    """System information and status"""
    version: str = "1.0.0"
    platform: str = ""
    python_version: str = ""
    uptime: float = 0.0
    memory_usage: Dict[str, float] = field(default_factory=dict)
    active_sessions: int = 0
    total_requests: int = 0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SearchResult:
    """Search result with metadata"""
    content: str
    relevance_score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result_dict = asdict(self)
        result_dict["timestamp"] = self.timestamp.isoformat()
        return result_dict


# ============================================================================
# Utility Functions
# ============================================================================

def create_message(role: str, content: str, **kwargs) -> Message:
    """Helper function to create a message with validation"""
    try:
        role_enum = MessageRole(role)
    except ValueError:
        raise ValueError(f"Invalid message role: {role}")
    
    return Message(role=role_enum, content=content, **kwargs)


def create_memory_entry(
    content: str,
    memory_type: str = "episodic",
    importance: float = 0.5,
    **kwargs
) -> MemoryEntry:
    """Helper function to create a memory entry with validation"""
    try:
        type_enum = MemoryType(memory_type)
    except ValueError:
        raise ValueError(f"Invalid memory type: {memory_type}")
    
    if not 0.0 <= importance <= 1.0:
        raise ValueError("Importance must be between 0.0 and 1.0")
    
    return MemoryEntry(
        content=content,
        memory_type=type_enum,
        importance=importance,
        **kwargs
    )


def validate_embedding(embedding: List[float]) -> bool:
    """Validate embedding format"""
    return (
        isinstance(embedding, list) and
        len(embedding) > 0 and
        all(isinstance(x, (int, float)) for x in embedding)
    )


def normalize_vector(vector: List[float]) -> List[float]:
    """Normalize vector to unit length"""
    import math
    
    magnitude = math.sqrt(sum(x * x for x in vector))
    if magnitude == 0:
        return vector
    
    return [x / magnitude for x in vector]