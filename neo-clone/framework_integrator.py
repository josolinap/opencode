#!/usr/bin/env python3
"""
Framework Integration System for NEO-CLONE
Integrates external frameworks (LangChain, CrewAI, AutoGen, etc.) with Neo-Clone's brain
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib
import subprocess
import sys

logger = logging.getLogger(__name__)

@dataclass
class FrameworkInfo:
    """Information about an integrated framework"""
    name: str
    version: str
    description: str
    capabilities: List[str]
    installed: bool = False
    compatible: bool = False
    config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}

@dataclass
class TaskRequest:
    """Request to execute a task using a framework"""
    framework: str
    task_type: str
    parameters: Dict[str, Any]
    models: Optional[List[str]] = None
    parallel: bool = False
    timeout: int = 30

    def __post_init__(self):
        if self.models is None:
            self.models = []

@dataclass
class TaskResult:
    """Result from framework task execution"""
    framework: str
    task_type: str
    success: bool
    output: Any
    execution_time: float
    error_message: str = ""
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class FrameworkIntegrator:
    """Integrates external AI frameworks with Neo-Clone"""

    def __init__(self, config_path: str = "../opencode.json"):
        self.config_path = config_path
        self.frameworks: Dict[str, FrameworkInfo] = {}
        self.active_integrations: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Initialize supported frameworks
        self._initialize_frameworks()

    def _initialize_frameworks(self):
        """Initialize supported frameworks"""
        frameworks_config = {
            "langchain": {
                "description": "LangChain for LLM orchestration and agent building",
                "capabilities": ["agent_orchestration", "tool_calling", "chain_building", "memory_management"],
                "required_packages": ["langchain", "langchain-core"],
                "min_version": "0.1.0"
            },
            "crewai": {
                "description": "CrewAI for multi-agent collaborative systems",
                "capabilities": ["multi_agent", "crew_orchestration", "task_decomposition", "role_assignment"],
                "required_packages": ["crewai"],
                "min_version": "0.1.0"
            },
            "autogen": {
                "description": "AutoGen for multi-agent conversations and tool use",
                "capabilities": ["multi_agent_chat", "tool_execution", "code_execution", "human_loop"],
                "required_packages": ["autogen-agentchat"],
                "min_version": "0.2.0"
            },
            "ray": {
                "description": "Ray for distributed computing and parallel execution",
                "capabilities": ["parallel_execution", "distributed_computing", "task_scheduling"],
                "required_packages": ["ray"],
                "min_version": "2.0.0"
            },
            "celery": {
                "description": "Celery for distributed task queuing",
                "capabilities": ["task_queueing", "distributed_tasks", "async_execution"],
                "required_packages": ["celery"],
                "min_version": "5.0.0"
            }
        }

        for name, config in frameworks_config.items():
            self.frameworks[name] = FrameworkInfo(
                name=name,
                version="unknown",
                description=config["description"],
                capabilities=config["capabilities"],
                config=config
            )

        # Check which frameworks are installed
        self._check_installed_frameworks()

    def _check_installed_frameworks(self):
        """Check which frameworks are installed and compatible"""
        for name, framework in self.frameworks.items():
            try:
                # Check if required packages are installed
                required_packages = framework.config.get("required_packages", [])
                packages_installed = True

                for package in required_packages:
                    try:
                        importlib.import_module(package.replace("-", "_"))
                    except ImportError:
                        packages_installed = False
                        break

                if packages_installed:
                    framework.installed = True
                    # Try to get version
                    try:
                        if name == "langchain":
                            import langchain
                            framework.version = langchain.__version__
                        elif name == "crewai":
                            import crewai
                            framework.version = crewai.__version__
                        elif name == "autogen":
                            import autogen
                            framework.version = autogen.__version__
                        elif name == "ray":
                            import ray
                            framework.version = ray.__version__
                        elif name == "celery":
                            import celery
                            framework.version = celery.__version__
                    except:
                        pass

                    # Check compatibility
                    framework.compatible = self._check_framework_compatibility(name, framework.version)

            except Exception as e:
                logger.warning(f"Error checking framework {name}: {e}")

    def _check_framework_compatibility(self, name: str, version: str) -> bool:
        """Check if framework version is compatible"""
        if version == "unknown":
            return False

        try:
            min_version = self.frameworks[name].config.get("min_version", "0.0.0")
            # Simple version comparison (could be enhanced)
            return version >= min_version
        except:
            return False

    def install_framework(self, name: str) -> bool:
        """Install a framework if not already installed"""
        if name not in self.frameworks:
            logger.error(f"Unknown framework: {name}")
            return False

        framework = self.frameworks[name]
        if framework.installed:
            logger.info(f"Framework {name} is already installed")
            return True

        try:
            required_packages = framework.config.get("required_packages", [])
            for package in required_packages:
                logger.info(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])

            # Re-check installation
            self._check_installed_frameworks()
            return framework.installed

        except Exception as e:
            logger.error(f"Failed to install framework {name}: {e}")
            return False

    def initialize_framework(self, name: str, config: Dict[str, Any] = None) -> bool:
        """Initialize a framework for use"""
        if name not in self.frameworks:
            logger.error(f"Unknown framework: {name}")
            return False

        framework = self.frameworks[name]
        if not framework.installed or not framework.compatible:
            logger.error(f"Framework {name} is not installed or compatible")
            return False

        try:
            if name == "langchain":
                return self._initialize_langchain(config or {})
            elif name == "crewai":
                return self._initialize_crewai(config or {})
            elif name == "autogen":
                return self._initialize_autogen(config or {})
            elif name == "ray":
                return self._initialize_ray(config or {})
            elif name == "celery":
                return self._initialize_celery(config or {})
            else:
                logger.error(f"No initialization method for framework {name}")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize framework {name}: {e}")
            return False

    def execute_task(self, request: TaskRequest) -> TaskResult:
        """Execute a task using the specified framework"""
        start_time = time.time()

        try:
            if request.framework not in self.active_integrations:
                logger.error(f"Framework {request.framework} is not initialized")
                return TaskResult(
                    framework=request.framework,
                    task_type=request.task_type,
                    success=False,
                    output=None,
                    execution_time=time.time() - start_time,
                    error_message=f"Framework {request.framework} not initialized"
                )

            if request.parallel and len(request.models) > 1:
                return self._execute_parallel_task(request, start_time)
            else:
                return self._execute_single_task(request, start_time)

        except Exception as e:
            return TaskResult(
                framework=request.framework,
                task_type=request.task_type,
                success=False,
                output=None,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    def _execute_single_task(self, request: TaskRequest, start_time: float) -> TaskResult:
        """Execute a single task"""
        try:
            framework_instance = self.active_integrations[request.framework]

            if request.framework == "langchain":
                result = self._execute_langchain_task(framework_instance, request)
            elif request.framework == "crewai":
                result = self._execute_crewai_task(framework_instance, request)
            elif request.framework == "autogen":
                result = self._execute_autogen_task(framework_instance, request)
            else:
                result = self._execute_generic_task(framework_instance, request)

            result.execution_time = time.time() - start_time
            return result

        except Exception as e:
            return TaskResult(
                framework=request.framework,
                task_type=request.task_type,
                success=False,
                output=None,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    def _execute_parallel_task(self, request: TaskRequest, start_time: float) -> TaskResult:
        """Execute a task in parallel across multiple models"""
        try:
            results = []

            # Submit parallel tasks
            futures = []
            for model in request.models:
                single_request = TaskRequest(
                    framework=request.framework,
                    task_type=request.task_type,
                    parameters={**request.parameters, "model": model},
                    models=[model],
                    parallel=False,
                    timeout=request.timeout
                )

                future = self.executor.submit(self._execute_single_task, single_request, time.time())
                futures.append(future)

            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel task failed: {e}")

            return TaskResult(
                framework=request.framework,
                task_type=request.task_type,
                success=True,
                output=results,
                execution_time=time.time() - start_time,
                metadata={"parallel_results": len(results)}
            )

        except Exception as e:
            return TaskResult(
                framework=request.framework,
                task_type=request.task_type,
                success=False,
                output=None,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

    # Framework-specific initialization methods
    def _initialize_langchain(self, config: Dict[str, Any]) -> bool:
        """Initialize LangChain integration"""
        try:
            # Try different import paths for different LangChain versions
            try:
                from langchain_core.language_models import BaseLanguageModel
            except ImportError:
                try:
                    from langchain.schema import BaseLanguageModel
                except ImportError:
                    # LangChain might not have BaseLanguageModel in this version
                    pass

            # Store LangChain components for later use
            self.active_integrations["langchain"] = {
                "initialized": True,
                "config": config
            }
            return True
        except Exception as e:
            logger.error(f"LangChain initialization failed: {e}")
            return False

    def _initialize_crewai(self, config: Dict[str, Any]) -> bool:
        """Initialize CrewAI integration"""
        try:
            import crewai
            self.active_integrations["crewai"] = {
                "initialized": True,
                "config": config
            }
            return True
        except Exception as e:
            logger.error(f"CrewAI initialization failed: {e}")
            return False

    def _initialize_autogen(self, config: Dict[str, Any]) -> bool:
        """Initialize AutoGen integration"""
        try:
            import autogen
            self.active_integrations["autogen"] = {
                "initialized": True,
                "config": config
            }
            return True
        except Exception as e:
            logger.error(f"AutoGen initialization failed: {e}")
            return False

    def _initialize_ray(self, config: Dict[str, Any]) -> bool:
        """Initialize Ray integration"""
        try:
            import ray
            if not ray.is_initialized():
                ray.init(**config)
            self.active_integrations["ray"] = {
                "initialized": True,
                "config": config
            }
            return True
        except Exception as e:
            logger.error(f"Ray initialization failed: {e}")
            return False

    def _initialize_celery(self, config: Dict[str, Any]) -> bool:
        """Initialize Celery integration"""
        try:
            from celery import Celery
            # This would need proper Celery configuration
            self.active_integrations["celery"] = {
                "initialized": True,
                "config": config
            }
            return True
        except Exception as e:
            logger.error(f"Celery initialization failed: {e}")
            return False

    # Framework-specific task execution methods
    def _execute_langchain_task(self, instance: Any, request: TaskRequest) -> TaskResult:
        """Execute task using LangChain"""
        try:
            # This is a simplified example - would need specific implementation
            # based on the actual LangChain use case
            return TaskResult(
                framework="langchain",
                task_type=request.task_type,
                success=True,
                output={"message": f"LangChain task executed: {request.task_type}"},
                execution_time=0.0
            )
        except Exception as e:
            return TaskResult(
                framework="langchain",
                task_type=request.task_type,
                success=False,
                output=None,
                execution_time=0.0,
                error_message=str(e)
            )

    def _execute_crewai_task(self, instance: Any, request: TaskRequest) -> TaskResult:
        """Execute task using CrewAI"""
        try:
            # Simplified CrewAI execution
            return TaskResult(
                framework="crewai",
                task_type=request.task_type,
                success=True,
                output={"message": f"CrewAI task executed: {request.task_type}"},
                execution_time=0.0
            )
        except Exception as e:
            return TaskResult(
                framework="crewai",
                task_type=request.task_type,
                success=False,
                output=None,
                execution_time=0.0,
                error_message=str(e)
            )

    def _execute_autogen_task(self, instance: Any, request: TaskRequest) -> TaskResult:
        """Execute task using AutoGen"""
        try:
            # Simplified AutoGen execution
            return TaskResult(
                framework="autogen",
                task_type=request.task_type,
                success=True,
                output={"message": f"AutoGen task executed: {request.task_type}"},
                execution_time=0.0
            )
        except Exception as e:
            return TaskResult(
                framework="autogen",
                task_type=request.task_type,
                success=False,
                output=None,
                execution_time=0.0,
                error_message=str(e)
            )

    def _execute_generic_task(self, instance: Any, request: TaskRequest) -> TaskResult:
        """Execute generic task"""
        return TaskResult(
            framework=request.framework,
            task_type=request.task_type,
            success=True,
            output={"message": f"Generic task executed: {request.task_type}"},
            execution_time=0.0
        )

    def get_framework_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all frameworks"""
        status = {}
        for name, framework in self.frameworks.items():
            status[name] = {
                "installed": framework.installed,
                "compatible": framework.compatible,
                "version": framework.version,
                "description": framework.description,
                "capabilities": framework.capabilities,
                "active": name in self.active_integrations
            }
        return status

    def discover_capabilities(self) -> Dict[str, List[str]]:
        """Discover all available capabilities across frameworks"""
        capabilities = {}
        for name, framework in self.frameworks.items():
            if framework.installed and framework.compatible:
                for capability in framework.capabilities:
                    if capability not in capabilities:
                        capabilities[capability] = []
                    capabilities[capability].append(name)
        return capabilities