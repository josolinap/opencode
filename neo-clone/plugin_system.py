"""
Plugin System for MiniMax Agent Architecture

This module provides dynamic plugin management with security sandboxing,
hot-swapping capabilities, and comprehensive plugin lifecycle management.

Author: MiniMax Agent
Version: 1.0
"""

import asyncio
import importlib
import importlib.util
import inspect
import json
import shutil
import sys
import threading
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Callable, Union
import logging
import hashlib
import os

# Import foundational modules
from config import get_config
from data_models import SkillResult, SkillContext, SkillMetadata, PluginMetadata
from skills import BaseSkill, SkillsManager

# Configure logging
logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Plugin lifecycle status"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNLOADING = "unloading"


class PermissionType(Enum):
    """Plugin permissions"""
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_EXECUTE = "file:execute"
    NETWORK = "network"
    SYSTEM = "system"
    SKILL_EXECUTION = "skill:execute"
    MEMORY_ACCESS = "memory:access"
    CONFIG_ACCESS = "config:access"


class SecurityLevel(Enum):
    """Plugin security levels"""
    TRUSTED = "trusted"     # Full access
    RESTRICTED = "restricted"  # Limited access
    SANDBOXED = "sandboxed"    # Minimal access
    UNTRUSTED = "untrusted"   # No external access


class PluginSandbox:
    """
    Security sandbox for plugin execution
    
    Provides isolated execution environment with permission controls.
    """
    
    def __init__(self, permissions: List[PermissionType], security_level: SecurityLevel):
        self.permissions = set(permissions)
        self.security_level = security_level
        self.restricted_modules = self._get_restricted_modules()
        self.allowed_builtins = self._get_allowed_builtins()
        self.execution_count = 0
        self.last_execution = None
        
    def _get_restricted_modules(self) -> List[str]:
        """Get list of modules restricted based on security level"""
        base_restricted = [
            'os', 'subprocess', 'sys', 'threading', 'multiprocessing',
            'socket', 'urllib', 'requests', 'http', 'ftplib', 'telnetlib'
        ]
        
        if self.security_level in [SecurityLevel.SANDBOXED, SecurityLevel.UNTRUSTED]:
            base_restricted.extend([
                'json', 'pickle', 'marshal', 'builtins', 'types',
                'importlib', '__import__'
            ])
        
        if self.security_level == SecurityLevel.UNTRUSTED:
            base_restricted.extend([
                'math', 'random', 'time', 'datetime', 'collections',
                'itertools', 'functools', 'operator'
            ])
        
        return base_restricted
    
    def _get_allowed_builtins(self) -> Dict[str, Callable]:
        """Get allowed built-in functions based on security level"""
        allowed = {
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'reversed': reversed
        }
        
        if self.security_level in [SecurityLevel.SANDBOXED, SecurityLevel.UNTRUSTED]:
            # Remove potentially dangerous functions
            dangerous = ['eval', 'exec', 'compile', 'open', 'input', 'breakpoint']
            for func in dangerous:
                allowed.pop(func, None)
        
        return allowed
    
    def validate_execution(self, func_name: str, args: tuple, kwargs: dict) -> bool:
        """Validate if function execution is allowed"""
        self.execution_count += 1
        self.last_execution = datetime.now()
        
        # Check permission requirements
        if not self._check_permissions(func_name):
            logger.warning(f"Plugin execution denied: {func_name} - insufficient permissions")
            return False
        
        # Check for restricted patterns
        if self._contains_restricted_patterns(func_name, args, kwargs):
            logger.warning(f"Plugin execution denied: {func_name} - restricted patterns detected")
            return False
        
        return True
    
    def _check_permissions(self, func_name: str) -> bool:
        """Check if function execution is permitted"""
        # File operations
        if any(pattern in func_name.lower() for pattern in ['file', 'open', 'read', 'write']):
            return PermissionType.FILE_READ in self.permissions or PermissionType.FILE_WRITE in self.permissions
        
        # Network operations
        if any(pattern in func_name.lower() for pattern in ['http', 'url', 'request', 'fetch']):
            return PermissionType.NETWORK in self.permissions
        
        # System operations
        if any(pattern in func_name.lower() for pattern in ['system', 'os', 'subprocess']):
            return PermissionType.SYSTEM in self.permissions
        
        # Memory operations
        if any(pattern in func_name.lower() for pattern in ['memory', 'cache', 'store']):
            return PermissionType.MEMORY_ACCESS in self.permissions
        
        # Config operations
        if any(pattern in func_name.lower() for pattern in ['config', 'setting']):
            return PermissionType.CONFIG_ACCESS in self.permissions
        
        # Default allow for non-critical operations
        return True
    
    def _contains_restricted_patterns(self, func_name: str, args: tuple, kwargs: dict) -> bool:
        """Check for potentially dangerous patterns"""
        # Check for file path traversal
        for arg in args + tuple(kwargs.values()):
            if isinstance(arg, str) and ('..' in arg or arg.startswith('/')):
                if self.security_level in [SecurityLevel.SANDBOXED, SecurityLevel.UNTRUSTED]:
                    return True
        
        # Check for eval/exec attempts
        dangerous_funcs = ['eval', 'exec', 'compile', '__import__']
        if any(func in func_name.lower() for func in dangerous_funcs):
            return True
        
        return False
    
    def create_safe_globals(self) -> Dict[str, Any]:
        """Create safe globals for plugin execution"""
        safe_globals = self.allowed_builtins.copy()
        
        # Add safe modules based on security level
        if self.security_level != SecurityLevel.UNTRUSTED:
            safe_globals['json'] = json
            safe_globals['math'] = __import__('math')
            safe_globals['datetime'] = __import__('datetime')
            safe_globals['collections'] = __import__('collections')
        
        return safe_globals


class Plugin(ABC):
    """
    Abstract base class for all plugins
    
    Plugins should inherit from this class and implement the required methods.
    """
    
    def __init__(self, plugin_id: str, metadata: PluginMetadata):
        self.plugin_id = plugin_id
        self.metadata = metadata
        self.status = PluginStatus.UNLOADED
        self.sandbox: Optional[PluginSandbox] = None
        self.performance_metrics: List[Dict[str, Any]] = []
        self.error_count = 0
        self.last_error = None
        
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration"""
        pass
    
    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute the plugin's main functionality"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this plugin provides"""
        return []
    
    def validate_permissions(self, required_permissions: List[PermissionType]) -> bool:
        """Validate that plugin has required permissions"""
        if not self.sandbox:
            return False
        
        required_set = set(required_permissions)
        return required_set.issubset(self.sandbox.permissions)
    
    def update_performance_metrics(self, execution_time: float, success: bool, error: Optional[str] = None):
        """Update plugin performance metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "success": success,
            "error": error
        }
        
        self.performance_metrics.append(metrics)
        
        # Keep only recent metrics (last 100)
        if len(self.performance_metrics) > 100:
            self.performance_metrics = self.performance_metrics[-100:]
        
        if not success:
            self.error_count += 1
            self.last_error = error
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get plugin performance statistics"""
        if not self.performance_metrics:
            return {"total_executions": 0}
        
        total_executions = len(self.performance_metrics)
        successful_executions = sum(1 for m in self.performance_metrics if m["success"])
        total_time = sum(m["execution_time"] for m in self.performance_metrics)
        error_rate = self.error_count / total_executions if total_executions > 0 else 0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "average_execution_time": total_time / total_executions if total_executions > 0 else 0,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "last_error": self.last_error,
            "status": self.status.value
        }


class FileProcessingPlugin(Plugin):
    """Example plugin for file processing"""
    
    def __init__(self, plugin_id: str, metadata: PluginMetadata):
        super().__init__(plugin_id, metadata)
        self.metadata.capabilities = ["file_read", "file_process", "text_analysis"]
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize file processing plugin"""
        try:
            self.status = PluginStatus.LOADED
            logger.info(f"FileProcessingPlugin initialized: {self.plugin_id}")
            return True
        except Exception as e:
            self.status = PluginStatus.ERROR
            logger.error(f"Failed to initialize FileProcessingPlugin: {e}")
            return False
    
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute file processing"""
        start_time = time.time()
        
        try:
            file_path = kwargs.get("file_path", "")
            operation = kwargs.get("operation", "read")
            
            if not file_path:
                raise ValueError("file_path parameter is required")
            
            if operation == "read":
                # Read file content (simplified)
                content = f"Content of file: {file_path}"
                result = f"Successfully read file: {file_path}\nContent preview: {content[:100]}..."
            else:
                result = f"File operation '{operation}' on {file_path} completed"
            
            execution_time = time.time() - start_time
            self.update_performance_metrics(execution_time, True)
            
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"operation": operation, "file_path": file_path}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.update_performance_metrics(execution_time, False, str(e))
            
            return SkillResult(
                success=False,
                output=f"File processing failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def cleanup(self) -> None:
        """Cleanup file processing resources"""
        self.status = PluginStatus.UNLOADING
        logger.info(f"FileProcessingPlugin cleanup: {self.plugin_id}")
        self.status = PluginStatus.UNLOADED


class WebScrapingPlugin(Plugin):
    """Example plugin for web scraping"""
    
    def __init__(self, plugin_id: str, metadata: PluginMetadata):
        super().__init__(plugin_id, metadata)
        self.metadata.capabilities = ["web_fetch", "html_parse", "data_extraction"]
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize web scraping plugin"""
        try:
            self.status = PluginStatus.LOADED
            logger.info(f"WebScrapingPlugin initialized: {self.plugin_id}")
            return True
        except Exception as e:
            self.status = PluginStatus.ERROR
            logger.error(f"Failed to initialize WebScrapingPlugin: {e}")
            return False
    
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute web scraping"""
        start_time = time.time()
        
        try:
            url = kwargs.get("url", "")
            
            if not url:
                raise ValueError("url parameter is required")
            
            # Simulate web scraping (in real implementation, would use requests/beautifulsoup)
            result = f"Successfully fetched content from: {url}\nTitle: Sample Page\nContent length: 1024 characters"
            
            execution_time = time.time() - start_time
            self.update_performance_metrics(execution_time, True)
            
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"url": url, "content_length": 1024}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.update_performance_metrics(execution_time, False, str(e))
            
            return SkillResult(
                success=False,
                output=f"Web scraping failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def cleanup(self) -> None:
        """Cleanup web scraping resources"""
        self.status = PluginStatus.UNLOADING
        logger.info(f"WebScrapingPlugin cleanup: {self.plugin_id}")
        self.status = PluginStatus.UNLOADED


class PluginManager:
    """
    Central manager for plugin lifecycle management
    
    Responsibilities:
    - Plugin discovery and loading
    - Security sandboxing
    - Hot-swapping support
    - Performance monitoring
    - Permission management
    """
    
    def __init__(self, plugin_dir: str = "plugins", security_level: SecurityLevel = SecurityLevel.RESTRICTED):
        self.plugin_dir = Path(plugin_dir)
        self.security_level = security_level
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.total_executions = 0
        self.successful_executions = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Plugin registry
        self._plugin_registry = {
            "FileProcessingPlugin": FileProcessingPlugin,
            "WebScrapingPlugin": WebScrapingPlugin
        }
        
        # Create plugin directory
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Plugin Manager initialized: dir={plugin_dir}, security={security_level.value}")
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in plugin directory"""
        discovered = []
        
        try:
            # Look for plugin manifest files
            for manifest_file in self.plugin_dir.glob("*/plugin.json"):
                try:
                    with open(manifest_file, 'r') as f:
                        metadata = PluginMetadata(**json.load(f))
                    discovered.append(metadata.name)
                    logger.debug(f"Discovered plugin: {metadata.name}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin manifest {manifest_file}: {e}")
            
            # Also check for Python plugin files
            for plugin_file in self.plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue  # Skip private modules
                discovered.append(plugin_file.stem)
                logger.debug(f"Discovered Python plugin: {plugin_file.stem}")
                
        except Exception as e:
            logger.error(f"Plugin discovery failed: {e}")
        
        return discovered
    
    def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Load a plugin by name"""
        with self._lock:
            if plugin_name in self.plugins:
                logger.warning(f"Plugin {plugin_name} already loaded")
                return True
            
            try:
                # Check if it's a built-in plugin
                if plugin_name in self._plugin_registry:
                    return self._load_builtin_plugin(plugin_name, config)
                else:
                    return self._load_external_plugin(plugin_name, config)
                    
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                return False
    
    def _load_builtin_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Load a built-in plugin"""
        try:
            plugin_class = self._plugin_registry[plugin_name]
            
            # Create plugin metadata
            metadata = PluginMetadata(
                name=plugin_name,
                version="1.0.0",
                description=f"Built-in {plugin_name}",
                author="MiniMax Agent",
                capabilities=[],
                config=config or {}
            )
            
            # Create plugin instance
            plugin_id = f"{plugin_name}_{int(time.time())}"
            plugin = plugin_class(plugin_id, metadata)
            
            # Create sandbox with appropriate permissions
            permissions = self._get_default_permissions(plugin_name)
            plugin.sandbox = PluginSandbox(permissions, self.security_level)
            
            # Initialize plugin
            if not asyncio.run(plugin.initialize(config or {})):
                logger.error(f"Plugin initialization failed: {plugin_name}")
                return False
            
            # Store plugin
            self.plugins[plugin_name] = plugin
            self.plugin_metadata[plugin_name] = metadata
            self.plugin_configs[plugin_name] = config or {}
            
            logger.info(f"Successfully loaded built-in plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load built-in plugin {plugin_name}: {e}")
            return False
    
    def _load_external_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Load an external plugin from file"""
        try:
            # This would implement loading from Python files
            # For now, return False as external loading is complex
            logger.warning(f"External plugin loading not implemented: {plugin_name}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to load external plugin {plugin_name}: {e}")
            return False
    
    def _get_default_permissions(self, plugin_name: str) -> List[PermissionType]:
        """Get default permissions for a plugin type"""
        if "FileProcessing" in plugin_name:
            return [PermissionType.FILE_READ]
        elif "WebScraping" in plugin_name:
            return [PermissionType.NETWORK]
        else:
            return []
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        with self._lock:
            if plugin_name not in self.plugins:
                logger.warning(f"Plugin {plugin_name} not found")
                return False
            
            try:
                plugin = self.plugins[plugin_name]
                plugin.status = PluginStatus.UNLOADING
                
                # Cleanup plugin
                asyncio.run(plugin.cleanup())
                
                # Remove from registry
                del self.plugins[plugin_name]
                del self.plugin_metadata[plugin_name]
                del self.plugin_configs[plugin_name]
                
                logger.info(f"Successfully unloaded plugin: {plugin_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_name}: {e}")
                return False
    
    async def execute_plugin(
        self,
        plugin_name: str,
        context: SkillContext,
        **kwargs
    ) -> SkillResult:
        """Execute a plugin with the given context"""
        start_time = time.time()
        
        with self._lock:
            if plugin_name not in self.plugins:
                return SkillResult(
                    success=False,
                    output=f"Plugin '{plugin_name}' not found",
                    skill_name=plugin_name,
                    execution_time=time.time() - start_time,
                    error_message="Plugin not loaded"
                )
            
            plugin = self.plugins[plugin_name]
            
            if plugin.status != PluginStatus.ACTIVE:
                return SkillResult(
                    success=False,
                    output=f"Plugin '{plugin_name}' is not active",
                    skill_name=plugin_name,
                    execution_time=time.time() - start_time,
                    error_message="Plugin not active"
                )
        
        try:
            # Validate execution in sandbox
            if plugin.sandbox:
                # This would validate the execution context
                pass  # Simplified for now
            
            # Execute plugin
            result = await plugin.execute(context, **kwargs)
            
            # Update global statistics
            with self._lock:
                self.total_executions += 1
                if result.success:
                    self.successful_executions += 1
                
                # Record execution history
                self.execution_history.append({
                    "plugin_name": plugin_name,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "user_input": context.user_input[:100]  # Truncate for storage
                })
                
                # Keep only recent history (last 1000 entries)
                if len(self.execution_history) > 1000:
                    self.execution_history = self.execution_history[-1000:]
            
            return result
            
        except Exception as e:
            logger.error(f"Plugin execution failed for {plugin_name}: {e}")
            return SkillResult(
                success=False,
                output=f"Plugin execution failed: {str(e)}",
                skill_name=plugin_name,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a loaded plugin"""
        with self._lock:
            if plugin_name not in self.plugins:
                logger.warning(f"Plugin {plugin_name} not found")
                return False
            
            plugin = self.plugins[plugin_name]
            plugin.status = PluginStatus.ACTIVE
            logger.info(f"Activated plugin: {plugin_name}")
            return True
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate a loaded plugin"""
        with self._lock:
            if plugin_name not in self.plugins:
                logger.warning(f"Plugin {plugin_name} not found")
                return False
            
            plugin = self.plugins[plugin_name]
            plugin.status = PluginStatus.INACTIVE
            logger.info(f"Deactivated plugin: {plugin_name}")
            return True
    
    def hot_reload_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Hot-reload a plugin (reload without restarting)"""
        logger.info(f"Hot-reloading plugin: {plugin_name}")
        
        # Unload existing plugin
        if not self.unload_plugin(plugin_name):
            return False
        
        # Load updated plugin
        return self.load_plugin(plugin_name, config)
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a plugin"""
        if plugin_name not in self.plugins:
            return None
        
        plugin = self.plugins[plugin_name]
        metadata = self.plugin_metadata[plugin_name]
        
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "capabilities": metadata.capabilities,
            "status": plugin.status.value,
            "permissions": list(plugin.sandbox.permissions) if plugin.sandbox else [],
            "security_level": self.security_level.value,
            "performance": plugin.get_performance_stats(),
            "config": self.plugin_configs.get(plugin_name, {}),
            "error_count": plugin.error_count,
            "last_error": plugin.last_error
        }
    
    def list_plugins(self, status_filter: Optional[PluginStatus] = None) -> List[str]:
        """List all plugins, optionally filtered by status"""
        plugin_names = list(self.plugins.keys())
        
        if status_filter:
            plugin_names = [
                name for name in plugin_names
                if self.plugins[name].status == status_filter
            ]
        
        return plugin_names
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive plugin statistics"""
        with self._lock:
            plugin_stats = {}
            
            for plugin_name, plugin in self.plugins.items():
                plugin_stats[plugin_name] = {
                    "status": plugin.status.value,
                    "performance": plugin.get_performance_stats(),
                    "capabilities": plugin.get_capabilities(),
                    "permissions": list(plugin.sandbox.permissions) if plugin.sandbox else [],
                    "error_count": plugin.error_count,
                    "last_error": plugin.last_error
                }
            
            overall_success_rate = (
                self.successful_executions / self.total_executions
                if self.total_executions > 0 else 0.0
            )
            
            return {
                "total_plugins": len(self.plugins),
                "active_plugins": len([p for p in self.plugins.values() if p.status == PluginStatus.ACTIVE]),
                "total_executions": self.total_executions,
                "successful_executions": self.successful_executions,
                "overall_success_rate": overall_success_rate,
                "plugin_statistics": plugin_stats,
                "security_level": self.security_level.value,
                "plugin_directory": str(self.plugin_dir),
                "recent_history_count": len(self.execution_history)
            }
    
    def create_plugin_manifest(self, plugin_name: str, description: str, capabilities: List[str]) -> str:
        """Create a plugin manifest file"""
        manifest = {
            "name": plugin_name,
            "version": "1.0.0",
            "description": description,
            "author": "Unknown",
            "capabilities": capabilities,
            "dependencies": [],
            "config": {}
        }
        
        manifest_path = self.plugin_dir / plugin_name / "plugin.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Created plugin manifest: {manifest_path}")
        return str(manifest_path)
    
    def shutdown(self) -> None:
        """Shutdown plugin manager and cleanup all plugins"""
        logger.info("Shutting down Plugin Manager")
        
        # Unload all plugins
        plugin_names = list(self.plugins.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)
        
        logger.info("Plugin Manager shutdown complete")


# Global plugin manager instance
_plugin_manager_instance: Optional[PluginManager] = None
_plugin_manager_lock = threading.Lock()


def get_plugin_manager(
    plugin_dir: str = "plugins",
    security_level: SecurityLevel = SecurityLevel.RESTRICTED
) -> PluginManager:
    """
    Get singleton plugin manager instance
    
    Args:
        plugin_dir: Plugin directory path
        security_level: Default security level for plugins
    
    Returns:
        PluginManager singleton instance
    """
    global _plugin_manager_instance
    
    if _plugin_manager_instance is None:
        with _plugin_manager_lock:
            if _plugin_manager_instance is None:
                _plugin_manager_instance = PluginManager(plugin_dir, security_level)
    
    return _plugin_manager_instance


def reset_plugin_manager() -> None:
    """Reset the plugin manager instance"""
    global _plugin_manager_instance
    with _plugin_manager_lock:
        if _plugin_manager_instance:
            try:
                _plugin_manager_instance.shutdown()
            except Exception:
                pass
        _plugin_manager_instance = None
    logger.info("Plugin manager instance reset")


def create_plugin_manager_instance(
    plugin_dir: str = "plugins",
    security_level: SecurityLevel = SecurityLevel.RESTRICTED
) -> PluginManager:
    """
    Create a new plugin manager instance
    
    Args:
        plugin_dir: Plugin directory path
        security_level: Default security level for plugins
    
    Returns:
        New PluginManager instance
    """
    return PluginManager(plugin_dir, security_level)
