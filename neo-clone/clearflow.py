"""
clearflow.py - ClearFlow-inspired Type-Safe Workflow Orchestration

Inspired by ClearFlow's "correctness-first orchestration for emergent AI":
- Type-safe workflow definitions
- Deeply immutable data structures
- Message-driven architecture
- Mission-critical reliability
- 100% code coverage mindset
- Functional programming principles

Core Philosophy:
1. Correctness over performance
2. Immutability over mutability
3. Type safety over dynamic typing
4. Explicit over implicit
5. Testable over complex
"""

from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import logging
import asyncio
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)

# Type variables for generic typing
T = TypeVar('T')
R = TypeVar('R')

class WorkflowState(Enum):
    """Type-safe workflow states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskState(Enum):
    """Type-safe task states"""
    WAITING = "waiting"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass(frozen=True)
class WorkflowMessage:
    """Immutable workflow message"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    sender: str = ""
    receiver: str = ""
    correlation_id: Optional[str] = None
    
    def with_payload(self, **kwargs) -> 'WorkflowMessage':
        """Create new message with updated payload (immutable)"""
        new_payload = {**self.payload, **kwargs}
        return WorkflowMessage(
            id=self.id,
            type=self.type,
            payload=new_payload,
            timestamp=self.timestamp,
            sender=self.sender,
            receiver=self.receiver,
            correlation_id=self.correlation_id
        )

@dataclass(frozen=True)
class TaskResult(Generic[T]):
    """Immutable task result with type safety"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    
    def map(self, func: Callable[[T], R]) -> 'TaskResult[R]':
        """Map function over result data if successful"""
        if self.success and self.data is not None:
            try:
                new_data = func(self.data)
                return TaskResult[R](
                    success=True,
                    data=new_data,
                    metadata=self.metadata,
                    execution_time=self.execution_time
                )
            except Exception as e:
                return TaskResult[R](
                    success=False,
                    error=f"Map function failed: {str(e)}",
                    metadata=self.metadata,
                    execution_time=self.execution_time
                )
        return TaskResult[R](
            success=self.success,
            data=None,
            error=self.error,
            metadata=self.metadata,
            execution_time=self.execution_time
        )

@dataclass(frozen=True)
class WorkflowTask:
    """Immutable workflow task definition"""
    id: str
    name: str
    handler: Callable[[WorkflowMessage], TaskResult[Any]]
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 30.0
    retry_count: int = 3
    state: TaskState = TaskState.WAITING
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def with_state(self, state: TaskState) -> 'WorkflowTask':
        """Create new task with updated state"""
        return WorkflowTask(
            id=self.id,
            name=self.name,
            handler=self.handler,
            dependencies=self.dependencies,
            timeout=self.timeout,
            retry_count=self.retry_count,
            state=state,
            metadata=self.metadata
        )

@dataclass(frozen=True)
class WorkflowDefinition:
    """Immutable workflow definition"""
    id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def with_task(self, task: WorkflowTask) -> 'WorkflowDefinition':
        """Create new workflow with additional task"""
        new_tasks = self.tasks + [task]
        return WorkflowDefinition(
            id=self.id,
            name=self.name,
            description=self.description,
            tasks=new_tasks,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            metadata=self.metadata
        )

@dataclass(frozen=True)
class WorkflowExecution:
    """Immutable workflow execution state"""
    id: str
    workflow_id: str
    state: WorkflowState
    tasks: Dict[str, WorkflowTask]
    messages: List[WorkflowMessage]
    start_time: str
    end_time: Optional[str] = None
    result: Optional[TaskResult[Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def with_task_state(self, task_id: str, state: TaskState) -> 'WorkflowExecution':
        """Create new execution with updated task state"""
        if task_id in self.tasks:
            updated_task = self.tasks[task_id].with_state(state)
            new_tasks = {**self.tasks, task_id: updated_task}
            return WorkflowExecution(
                id=self.id,
                workflow_id=self.workflow_id,
                state=self.state,
                tasks=new_tasks,
                messages=self.messages,
                start_time=self.start_time,
                end_time=self.end_time,
                result=self.result,
                metadata=self.metadata
            )
        return self
    
    def with_message(self, message: WorkflowMessage) -> 'WorkflowExecution':
        """Create new execution with additional message"""
        new_messages = self.messages + [message]
        return WorkflowExecution(
            id=self.id,
            workflow_id=self.workflow_id,
            state=self.state,
            tasks=self.tasks,
            messages=new_messages,
            start_time=self.start_time,
            end_time=self.end_time,
            result=self.result,
            metadata=self.metadata
        )

def type_safe_task(func: Callable[[WorkflowMessage], TaskResult[T]]) -> Callable[[WorkflowMessage], TaskResult[T]]:
    """Decorator for type-safe task execution"""
    @wraps(func)
    def wrapper(message: WorkflowMessage) -> TaskResult[T]:
        try:
            # Validate message structure
            if not isinstance(message, WorkflowMessage):
                return TaskResult[T](
                    success=False,
                    error="Invalid message type"
                )
            
            # Execute task
            result = func(message)
            
            # Validate result
            if not isinstance(result, TaskResult):
                return TaskResult[T](
                    success=False,
                    error="Task must return TaskResult"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return TaskResult[T](
                success=False,
                error=f"Task execution error: {str(e)}"
            )
    
    return wrapper

class ClearFlow:
    """
    ClearFlow: Type-Safe Workflow Orchestration
    
    Mission-critical workflow engine with:
    - Type safety guarantees
    - Immutable data structures
    - Message-driven architecture
    - Comprehensive error handling
    - Testable components
    """
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.message_handlers: Dict[str, Callable[[WorkflowMessage], None]] = {}
        self.execution_history: List[WorkflowExecution] = []
        
        # Register default message handlers
        self._register_default_handlers()
        
        logger.info("ClearFlow initialized with type-safe workflow orchestration")
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers["task.completed"] = self._handle_task_completed
        self.message_handlers["task.failed"] = self._handle_task_failed
        self.message_handlers["workflow.started"] = self._handle_workflow_started
        self.message_handlers["workflow.completed"] = self._handle_workflow_completed
    
    def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a workflow definition with validation"""
        try:
            # Validate workflow
            self._validate_workflow(workflow)
            
            # Store workflow
            self.workflows[workflow.id] = workflow
            
            logger.info(f"Registered workflow: {workflow.name} ({workflow.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.id}: {e}")
            return False
    
    def _validate_workflow(self, workflow: WorkflowDefinition):
        """Validate workflow definition"""
        # Check for unique task IDs
        task_ids = [task.id for task in workflow.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Duplicate task IDs in workflow")
        
        # Check dependencies
        for task in workflow.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task {task.id} depends on non-existent task {dep}")
        
        # Check for circular dependencies
        self._check_circular_dependencies(workflow.tasks)
    
    def _check_circular_dependencies(self, tasks: List[WorkflowTask]):
        """Check for circular dependencies using DFS"""
        task_map = {task.id: task for task in tasks}
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            if task_id in task_map:
                for dep in task_map[task_id].dependencies:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    raise ValueError(f"Circular dependency detected involving task {task.id}")
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> str:
        """Execute a workflow with input validation"""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = self.workflows[workflow_id]
            
            # Validate input
            self._validate_input(workflow, input_data)
            
            # Create execution
            execution_id = str(uuid.uuid4())
            tasks = {task.id: task for task in workflow.tasks}
            
            execution = WorkflowExecution(
                id=execution_id,
                workflow_id=workflow_id,
                state=WorkflowState.RUNNING,
                tasks=tasks,
                messages=[],
                start_time=datetime.now().isoformat(),
                metadata={"input_data": input_data}
            )
            
            self.executions[execution_id] = execution
            
            # Send workflow started message
            start_message = WorkflowMessage(
                type="workflow.started",
                payload={"workflow_id": workflow_id, "execution_id": execution_id},
                sender="clearflow"
            )
            self._send_message(start_message)
            
            # Start task execution
            self._execute_tasks(execution_id)
            
            logger.info(f"Started workflow execution: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            return ""
    
    def _validate_input(self, workflow: WorkflowDefinition, input_data: Dict[str, Any]):
        """Validate workflow input against schema"""
        # Simplified validation - in production, use jsonschema
        if workflow.input_schema:
            required_fields = workflow.input_schema.get("required", [])
            for field in required_fields:
                if field not in input_data:
                    raise ValueError(f"Required input field missing: {field}")
    
    def _execute_tasks(self, execution_id: str):
        """Execute ready tasks in workflow"""
        execution = self.executions.get(execution_id)
        if not execution:
            return
        
        # Find ready tasks
        ready_tasks = []
        for task in execution.tasks.values():
            if task.state == TaskState.WAITING:
                # Check if dependencies are completed
                deps_completed = all(
                    execution.tasks[dep].state == TaskState.COMPLETED
                    for dep in task.dependencies
                )
                if deps_completed:
                    ready_tasks.append(task)
        
        # Execute ready tasks
        for task in ready_tasks:
            self._execute_task(execution_id, task)
    
    def _execute_task(self, execution_id: str, task: WorkflowTask):
        """Execute a single task"""
        try:
            # Update task state to running
            execution = self.executions[execution_id]
            execution = execution.with_task_state(task.id, TaskState.RUNNING)
            self.executions[execution_id] = execution
            
            # Create task message
            task_message = WorkflowMessage(
                type="task.execute",
                payload={"task_id": task.id, "execution_id": execution_id},
                sender="clearflow"
            )
            
            # Execute task handler
            start_time = datetime.now()
            result = task.handler(task_message)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update result with execution time
            if result.success:
                result = TaskResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata=result.metadata,
                    execution_time=execution_time
                )
                
                # Send completion message
                completion_message = WorkflowMessage(
                    type="task.completed",
                    payload={
                        "task_id": task.id,
                        "execution_id": execution_id,
                        "result": result
                    },
                    sender="task_executor"
                )
                self._send_message(completion_message)
            else:
                # Send failure message
                failure_message = WorkflowMessage(
                    type="task.failed",
                    payload={
                        "task_id": task.id,
                        "execution_id": execution_id,
                        "error": result.error
                    },
                    sender="task_executor"
                )
                self._send_message(failure_message)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            
            # Send failure message
            failure_message = WorkflowMessage(
                type="task.failed",
                payload={
                    "task_id": task.id,
                    "execution_id": execution_id,
                    "error": str(e)
                },
                sender="task_executor"
            )
            self._send_message(failure_message)
    
    def _send_message(self, message: WorkflowMessage):
        """Send message to appropriate handler"""
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Message handler failed for {message.type}: {e}")
    
    def _handle_task_completed(self, message: WorkflowMessage):
        """Handle task completion"""
        payload = message.payload
        execution_id = payload["execution_id"]
        task_id = payload["task_id"]
        
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution = execution.with_task_state(task_id, TaskState.COMPLETED)
            execution = execution.with_message(message)
            self.executions[execution_id] = execution
            
            # Continue executing tasks
            self._execute_tasks(execution_id)
            
            # Check if workflow is complete
            self._check_workflow_completion(execution_id)
    
    def _handle_task_failed(self, message: WorkflowMessage):
        """Handle task failure"""
        payload = message.payload
        execution_id = payload["execution_id"]
        task_id = payload["task_id"]
        
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution = execution.with_task_state(task_id, TaskState.FAILED)
            execution = execution.with_message(message)
            self.executions[execution_id] = execution
            
            # Mark workflow as failed
            execution = WorkflowExecution(
                id=execution.id,
                workflow_id=execution.workflow_id,
                state=WorkflowState.FAILED,
                tasks=execution.tasks,
                messages=execution.messages,
                start_time=execution.start_time,
                end_time=datetime.now().isoformat(),
                result=TaskResult(success=False, error=payload["error"]),
                metadata=execution.metadata
            )
            self.executions[execution_id] = execution
    
    def _handle_workflow_started(self, message: WorkflowMessage):
        """Handle workflow start"""
        logger.info(f"Workflow started: {message.payload}")
    
    def _handle_workflow_completed(self, message: WorkflowMessage):
        """Handle workflow completion"""
        logger.info(f"Workflow completed: {message.payload}")
    
    def _check_workflow_completion(self, execution_id: str):
        """Check if workflow execution is complete"""
        execution = self.executions.get(execution_id)
        if not execution:
            return
        
        # Check if all tasks are completed or failed
        all_done = all(
            task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.SKIPPED]
            for task in execution.tasks.values()
        )
        
        if all_done:
            # Determine workflow state
            failed_tasks = [
                task for task in execution.tasks.values()
                if task.state == TaskState.FAILED
            ]
            
            workflow_state = WorkflowState.COMPLETED if not failed_tasks else WorkflowState.FAILED
            
            # Create final result
            result_data = {
                "completed_tasks": [
                    task.id for task in execution.tasks.values()
                    if task.state == TaskState.COMPLETED
                ],
                "failed_tasks": [
                    task.id for task in execution.tasks.values()
                    if task.state == TaskState.FAILED
                ]
            }
            
            result = TaskResult(
                success=workflow_state == WorkflowState.COMPLETED,
                data=result_data,
                error=f"Failed tasks: {failed_tasks}" if failed_tasks else None
            )
            
            # Update execution
            final_execution = WorkflowExecution(
                id=execution.id,
                workflow_id=execution.workflow_id,
                state=workflow_state,
                tasks=execution.tasks,
                messages=execution.messages,
                start_time=execution.start_time,
                end_time=datetime.now().isoformat(),
                result=result,
                metadata=execution.metadata
            )
            
            self.executions[execution_id] = final_execution
            self.execution_history.append(final_execution)
            
            # Send completion message
            completion_message = WorkflowMessage(
                type="workflow.completed",
                payload={
                    "execution_id": execution_id,
                    "workflow_id": execution.workflow_id,
                    "state": workflow_state.value,
                    "result": result
                },
                sender="clearflow"
            )
            self._send_message(completion_message)
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "state": execution.state.value,
            "start_time": execution.start_time,
            "end_time": execution.end_time,
            "tasks": {
                task_id: {
                    "name": task.name,
                    "state": task.state.value,
                    "dependencies": task.dependencies
                }
                for task_id, task in execution.tasks.items()
            },
            "message_count": len(execution.messages),
            "result": execution.result.data if execution.result else None
        }
    
    def list_workflows(self) -> Dict[str, Dict[str, Any]]:
        """List all registered workflows"""
        return {
            workflow_id: {
                "name": workflow.name,
                "description": workflow.description,
                "task_count": len(workflow.tasks),
                "metadata": workflow.metadata
            }
            for workflow_id, workflow in self.workflows.items()
        }

# Global ClearFlow instance
_clearflow_instance = None

def get_clearflow() -> ClearFlow:
    """Get global ClearFlow instance"""
    global _clearflow_instance
    if _clearflow_instance is None:
        _clearflow_instance = ClearFlow()
    return _clearflow_instance