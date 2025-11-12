from functools import lru_cache
'\nautomated_workflows.py - Advanced Automated Workflow System\n\nProvides intelligent automation for complex multi-step tasks with workflow orchestration,\nconditional logic, error handling, and adaptive execution based on real-time feedback.\n'
import time
import threading
import logging
import json
import asyncio
import queue
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import uuid
import re
logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PAUSED = 'paused'
    CANCELLED = 'cancelled'

class StepStatus(Enum):
    """Individual step status"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'

class StepType(Enum):
    """Types of workflow steps"""
    TASK = 'task'
    CONDITION = 'condition'
    PARALLEL = 'parallel'
    DELAY = 'delay'
    LOOP = 'loop'
    SUBWORKFLOW = 'subworkflow'

@dataclass
class WorkflowStep:
    """Individual workflow step definition"""
    step_id: str
    name: str
    step_type: StepType
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    on_failure: str = 'fail'
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

@dataclass
class WorkflowDefinition:
    """Workflow definition"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    triggers: List[str] = field(default_factory=list)
    schedule: Optional[str] = None
    max_concurrent: int = 1
    timeout: Optional[float] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    start_time: float
    end_time: Optional[float] = None
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    progress: float = 0.0

class WorkflowEngine:
    """Advanced workflow execution engine"""

    def __init__(self, storage_path: str='workflows.json'):
        self.storage_path = Path(storage_path)
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.execution_queue = queue.Queue()
        self.active_executions: Dict[str, threading.Thread] = {}
        self.is_running = False
        self.executor_thread: Optional[threading.Thread] = None
        self.action_handlers: Dict[str, Callable] = {}
        self.condition_evaluators: Dict[str, Callable] = {}
        self._load_workflows()
        self._register_default_handlers()

    def _load_workflows(self):
        """Load workflow definitions from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for workflow_data in data.get('workflows', []):
                    steps = [WorkflowStep(**step_data) for step_data in workflow_data['steps']]
                    workflow = WorkflowDefinition(workflow_id=workflow_data['workflow_id'], name=workflow_data['name'], description=workflow_data['description'], steps=steps, triggers=workflow_data.get('triggers', []), schedule=workflow_data.get('schedule'), max_concurrent=workflow_data.get('max_concurrent', 1), timeout=workflow_data.get('timeout'), retry_policy=workflow_data.get('retry_policy', {}), metadata=workflow_data.get('metadata', {}))
                    self.workflows[workflow.workflow_id] = workflow
                logger.info(f'Loaded {len(self.workflows)} workflow definitions')
        except Exception as e:
            logger.warning(f'Failed to load workflows: {e}')

    def _save_workflows(self):
        """Save workflow definitions to storage"""
        try:
            data = {'workflows': [{'workflow_id': w.workflow_id, 'name': w.name, 'description': w.description, 'steps': [asdict(step) for step in w.steps], 'triggers': w.triggers, 'schedule': w.schedule, 'max_concurrent': w.max_concurrent, 'timeout': w.timeout, 'retry_policy': w.retry_policy, 'metadata': w.metadata} for w in self.workflows.values()], 'last_updated': time.time()}
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f'Failed to save workflows: {e}')

    def _register_default_handlers(self):
        """Register default action and condition handlers"""
        self.register_action_handler('delay', self._handle_delay)
        self.register_action_handler('log', self._handle_log)
        self.register_action_handler('set_variable', self._handle_set_variable)
        self.register_action_handler('execute_skill', self._handle_execute_skill)
        self.register_action_handler('http_request', self._handle_http_request)
        self.register_action_handler('file_operation', self._handle_file_operation)
        self.register_condition_evaluator('equals', self._eval_equals)
        self.register_condition_evaluator('contains', self._eval_contains)
        self.register_condition_evaluator('greater_than', self._eval_greater_than)
        self.register_condition_evaluator('less_than', self._eval_less_than)
        self.register_condition_evaluator('regex', self._eval_regex)

    def register_action_handler(self, action_name: str, handler: Callable):
        """Register an action handler"""
        self.action_handlers[action_name] = handler
        logger.debug(f'Registered action handler: {action_name}')

    def register_condition_evaluator(self, condition_name: str, evaluator: Callable):
        """Register a condition evaluator"""
        self.condition_evaluators[condition_name] = evaluator
        logger.debug(f'Registered condition evaluator: {condition_name}')

    def create_workflow(self, name: str, description: str, steps: List[Dict[str, Any]], triggers: List[str]=None, schedule: str=None) -> str:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        workflow_steps = []
        for (i, step_data) in enumerate(steps):
            step = WorkflowStep(step_id=step_data.get('step_id', f'step_{i}'), name=step_data.get('name', f'Step {i + 1}'), step_type=StepType(step_data.get('step_type', 'task')), action=step_data.get('action', ''), parameters=step_data.get('parameters', {}), conditions=step_data.get('conditions', []), dependencies=step_data.get('dependencies', []), retry_config=step_data.get('retry_config', {}), timeout=step_data.get('timeout'), on_failure=step_data.get('on_failure', 'fail'))
            workflow_steps.append(step)
        workflow = WorkflowDefinition(workflow_id=workflow_id, name=name, description=description, steps=workflow_steps, triggers=triggers or [], schedule=schedule, max_concurrent=1, timeout=None, retry_policy={}, metadata={})
        self.workflows[workflow_id] = workflow
        self._save_workflows()
        logger.info(f'Created workflow: {name} ({workflow_id})')
        return workflow_id

    def execute_workflow(self, workflow_id: str, context: Dict[str, Any]=None) -> str:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f'Workflow not found: {workflow_id}')
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(execution_id=execution_id, workflow_id=workflow_id, status=WorkflowStatus.PENDING, start_time=time.time(), context=context or {})
        self.executions[execution_id] = execution
        self.execution_queue.put(execution_id)
        if not self.is_running:
            self.start()
        logger.info(f'Queued workflow execution: {execution_id}')
        return execution_id

    def start(self):
        """Start the workflow engine"""
        if self.is_running:
            logger.warning('Workflow engine already running')
            return
        self.is_running = True
        self.executor_thread = threading.Thread(target=self._execution_loop, daemon=True)
        self.executor_thread.start()
        logger.info('Workflow engine started')

    def stop(self):
        """Stop the workflow engine"""
        self.is_running = False
        for (execution_id, thread) in self.active_executions.items():
            try:
                thread.join(timeout=10)
            except:
                pass
        if self.executor_thread:
            self.executor_thread.join(timeout=5)
        logger.info('Workflow engine stopped')

    def _execution_loop(self):
        """Main execution loop"""
        while self.is_running:
            try:
                try:
                    execution_id = self.execution_queue.get(timeout=1)
                except queue.Empty:
                    continue
                execution_thread = threading.Thread(target=self._execute_workflow, args=(execution_id,), daemon=True)
                self.active_executions[execution_id] = execution_thread
                execution_thread.start()
            except Exception as e:
                logger.error(f'Error in execution loop: {e}')
                time.sleep(1)

    @lru_cache(maxsize=128)
    def _execute_workflow(self, execution_id: str):
        """Execute a specific workflow"""
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        try:
            execution.status = WorkflowStatus.RUNNING
            step_graph = self._build_step_graph(workflow.steps)
            completed_steps = set()
            total_steps = len(workflow.steps)
            while len(completed_steps) < total_steps:
                ready_steps = [step for step in workflow.steps if step.step_id not in completed_steps and all((dep in completed_steps for dep in step.dependencies)) and self._evaluate_conditions(step, execution)]
                if not ready_steps:
                    pending_steps = [step for step in workflow.steps if step.step_id not in completed_steps]
                    if not pending_steps:
                        break
                    else:
                        can_proceed = False
                        for step in pending_steps:
                            if self._evaluate_conditions(step, execution):
                                can_proceed = True
                                break
                        if not can_proceed:
                            logger.warning(f'Workflow {execution_id} stuck - unmet conditions')
                            break
                        else:
                            time.sleep(0.1)
                            continue
                parallel_steps = [s for s in ready_steps if s.step_type == StepType.PARALLEL]
                sequential_steps = [s for s in ready_steps if s.step_type != StepType.PARALLEL]
                if parallel_steps:
                    self._execute_parallel_steps(parallel_steps, execution)
                for step in sequential_steps:
                    if self._execute_step(step, execution):
                        completed_steps.add(step.step_id)
                        execution.completed_steps.append(step.step_id)
                    else:
                        execution.failed_steps.append(step.step_id)
                        if step.on_failure == 'fail':
                            execution.status = WorkflowStatus.FAILED
                            execution.error = f'Step failed: {step.name}'
                            break
                        elif step.on_failure == 'skip':
                            completed_steps.add(step.step_id)
                execution.progress = len(completed_steps) / total_steps
                if workflow.timeout and time.time() - execution.start_time > workflow.timeout:
                    execution.status = WorkflowStatus.FAILED
                    execution.error = 'Workflow timeout'
                    break
            if execution.status == WorkflowStatus.RUNNING:
                if len(execution.failed_steps) == 0:
                    execution.status = WorkflowStatus.COMPLETED
                else:
                    execution.status = WorkflowStatus.FAILED
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            logger.error(f'Workflow execution {execution_id} failed: {e}')
        finally:
            execution.end_time = time.time()
            self.active_executions.pop(execution_id, None)

    def _execute_step(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Execute a single workflow step"""
        step.status = StepStatus.RUNNING
        step.start_time = time.time()
        execution.current_step = step.step_id
        try:
            logger.debug(f'Executing step: {step.name}')
            if step.step_type == StepType.DELAY:
                result = self._handle_delay(step.parameters.get('duration', 1))
            elif step.step_type == StepType.CONDITION:
                result = self._evaluate_conditions(step, execution)
            elif step.step_type == StepType.LOOP:
                result = self._handle_loop(step, execution)
            elif step.step_type == StepType.SUBWORKFLOW:
                result = self._handle_subworkflow(step, execution)
            else:
                result = self._execute_action(step.action, step.parameters, execution)
            step.result = result
            step.status = StepStatus.COMPLETED
            execution.results[step.step_id] = result
            return True
        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED
            logger.error(f'Step {step.name} failed: {e}')
            if step.retry_config:
                return self._handle_retry(step, execution)
            else:
                return False
        finally:
            step.end_time = time.time()

    def _execute_action(self, action: str, parameters: Dict[str, Any], execution: WorkflowExecution) -> Any:
        """Execute an action with parameters"""
        if action not in self.action_handlers:
            raise ValueError(f'Unknown action: {action}')
        handler = self.action_handlers[action]
        substituted_params = self._substitute_variables(parameters, execution.context)
        return handler(substituted_params, execution)

    def _substitute_variables(self, data: Any, context: Dict[str, Any]) -> Any:
        """Substitute variables in data using context"""
        if isinstance(data, str):
            pattern = '\\$\\{([^}]+)\\}'

            def replace_var(match):
                var_path = match.group(1)
                return str(self._get_nested_value(context, var_path, match.group(0)))
            return re.sub(pattern, replace_var, data)
        elif isinstance(data, dict):
            return {k: self._substitute_variables(v, context) for (k, v) in data.items()}
        elif isinstance(data, list):
            return [self._substitute_variables(item, context) for item in data]
        else:
            return data

    def _get_nested_value(self, data: Dict[str, Any], path: str, default: Any=None) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def _evaluate_conditions(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Evaluate step conditions"""
        if not step.conditions:
            return True
        for condition in step.conditions:
            if not self._evaluate_condition(condition, execution):
                return False
        return True

    def _evaluate_condition(self, condition: str, execution: WorkflowExecution) -> bool:
        """Evaluate a single condition"""
        parts = condition.split(':', 2)
        if len(parts) < 2:
            logger.warning(f'Invalid condition format: {condition}')
            return False
        evaluator_name = parts[0]
        if evaluator_name not in self.condition_evaluators:
            logger.warning(f'Unknown condition evaluator: {evaluator_name}')
            return False
        evaluator = self.condition_evaluators[evaluator_name]
        try:
            if len(parts) == 2:
                return evaluator(parts[1], execution)
            else:
                return evaluator(parts[1], parts[2], execution)
        except Exception as e:
            logger.error(f'Condition evaluation failed: {e}')
            return False

    def _build_step_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph from steps"""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.dependencies
        return graph

    def _execute_parallel_steps(self, steps: List[WorkflowStep], execution: WorkflowExecution):
        """Execute multiple steps in parallel"""
        threads = []

        def execute_step_thread(step):
            self._execute_step(step, execution)
        for step in steps:
            thread = threading.Thread(target=execute_step_thread, args=(step,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    def _handle_delay(self, params: Dict[str, Any], execution: WorkflowExecution=None) -> str:
        """Handle delay action"""
        duration = params.get('duration', 1)
        time.sleep(duration)
        return f'Delayed for {duration} seconds'

    def _handle_log(self, params: Dict[str, Any], execution: WorkflowExecution) -> str:
        """Handle log action"""
        message = params.get('message', '')
        level = params.get('level', 'info')
        if level == 'debug':
            logger.debug(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
        else:
            logger.info(message)
        return f'Logged: {message}'

    def _handle_set_variable(self, params: Dict[str, Any], execution: WorkflowExecution) -> str:
        """Handle set_variable action"""
        name = params.get('name', '')
        value = params.get('value', '')
        execution.context[name] = value
        return f'Set variable {name} = {value}'

    def _handle_execute_skill(self, params: Dict[str, Any], execution: WorkflowExecution) -> Any:
        """Handle execute_skill action"""
        skill_name = params.get('skill_name', '')
        skill_params = params.get('parameters', {})
        return f'Executed skill: {skill_name} with params: {skill_params}'

    def _handle_http_request(self, params: Dict[str, Any], execution: WorkflowExecution) -> Any:
        """Handle http_request action"""
        url = params.get('url', '')
        method = params.get('method', 'GET')
        return f'HTTP {method} to {url}'

    def _handle_file_operation(self, params: Dict[str, Any], execution: WorkflowExecution) -> Any:
        """Handle file_operation action"""
        operation = params.get('operation', '')
        path = params.get('path', '')
        return f'File operation: {operation} on {path}'

    def _handle_loop(self, step: WorkflowStep, execution: WorkflowExecution) -> List[Any]:
        """Handle loop step"""
        iterations = step.parameters.get('iterations', 1)
        loop_action = step.parameters.get('action', '')
        results = []
        for i in range(iterations):
            loop_context = execution.context.copy()
            loop_context['loop_index'] = i
            loop_context['loop_iteration'] = i + 1
            if loop_action in self.action_handlers:
                result = self.action_handlers[loop_action](step.parameters, execution)
                results.append(result)
        return results

    def _handle_subworkflow(self, step: WorkflowStep, execution: WorkflowExecution) -> Any:
        """Handle subworkflow step"""
        subworkflow_id = step.parameters.get('workflow_id', '')
        sub_context = execution.context.copy()
        sub_context.update(step.parameters.get('context', {}))
        sub_execution_id = self.execute_workflow(subworkflow_id, sub_context)
        while sub_execution_id in self.executions:
            sub_execution = self.executions[sub_execution_id]
            if sub_execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                return sub_execution.results
            time.sleep(0.1)
        return None

    def _handle_retry(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Handle step retry logic"""
        max_retries = step.retry_config.get('max_retries', 3)
        retry_delay = step.retry_config.get('delay', 1)
        retry_count = getattr(step, '_retry_count', 0)
        if retry_count >= max_retries:
            return False
        step._retry_count = retry_count + 1
        time.sleep(retry_delay)
        return self._execute_step(step, execution)

    def _eval_equals(self, value1: str, value2: str, execution: WorkflowExecution=None) -> bool:
        """Evaluate equals condition"""
        return str(value1) == str(value2)

    def _eval_contains(self, text: str, substring: str, execution: WorkflowExecution=None) -> bool:
        """Evaluate contains condition"""
        return substring in text

    def _eval_greater_than(self, value1: str, value2: str, execution: WorkflowExecution=None) -> bool:
        """Evaluate greater than condition"""
        try:
            return float(value1) > float(value2)
        except ValueError:
            return str(value1) > str(value2)

    def _eval_less_than(self, value1: str, value2: str, execution: WorkflowExecution=None) -> bool:
        """Evaluate less than condition"""
        try:
            return float(value1) < float(value2)
        except ValueError:
            return str(value1) < str(value2)

    def _eval_regex(self, pattern: str, text: str, execution: WorkflowExecution=None) -> bool:
        """Evaluate regex condition"""
        try:
            return bool(re.search(pattern, text))
        except re.error:
            return False

    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""
        if execution_id not in self.executions:
            return {'error': 'Execution not found'}
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        return {'execution_id': execution_id, 'workflow_id': execution.workflow_id, 'workflow_name': workflow.name, 'status': execution.status.value, 'progress': execution.progress, 'current_step': execution.current_step, 'completed_steps': execution.completed_steps, 'failed_steps': execution.failed_steps, 'start_time': execution.start_time, 'end_time': execution.end_time, 'duration': (execution.end_time or time.time()) - execution.start_time, 'results': execution.results, 'context': execution.context, 'error': execution.error}

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows"""
        return [{'workflow_id': w.workflow_id, 'name': w.name, 'description': w.description, 'steps_count': len(w.steps), 'triggers': w.triggers, 'schedule': w.schedule} for w in self.workflows.values()]

    def list_executions(self, workflow_id: str=None) -> List[Dict[str, Any]]:
        """List workflow executions"""
        executions = self.executions.values()
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        return [{'execution_id': e.execution_id, 'workflow_id': e.workflow_id, 'status': e.status.value, 'progress': e.progress, 'start_time': e.start_time, 'end_time': e.end_time, 'duration': (e.end_time or time.time()) - e.start_time} for e in executions]
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    engine = WorkflowEngine()
    engine.start()
    try:
        sample_workflow = [{'name': 'Start Processing', 'action': 'log', 'parameters': {'message': 'Starting automated processing', 'level': 'info'}}, {'name': 'Set Initial Variables', 'action': 'set_variable', 'parameters': {'name': 'processing_count', 'value': 0}}, {'name': 'Process Data', 'action': 'execute_skill', 'parameters': {'skill_name': 'data_processor', 'batch_size': 100}, 'conditions': ['equals:${processing_count},0']}, {'name': 'Wait for Completion', 'action': 'delay', 'parameters': {'duration': 2}}, {'name': 'Log Completion', 'action': 'log', 'parameters': {'message': 'Processing completed successfully'}}]
        workflow_id = engine.create_workflow(name='Sample Data Processing', description='Automated data processing workflow', steps=sample_workflow)
        execution_id = engine.execute_workflow(workflow_id)
        while True:
            status = engine.get_workflow_status(execution_id)
            print(f"Status: {status['status']}, Progress: {status['progress']:.1%}")
            if status['status'] in ['completed', 'failed']:
                break
            time.sleep(1)
        print(f'Final status: {status}')
        print('\nAvailable workflows:')
        for workflow in engine.list_workflows():
            print(f"- {workflow['name']}: {workflow['description']}")
    finally:
        engine.stop()