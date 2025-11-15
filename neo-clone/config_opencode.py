"""
Configuration System for MiniMax Agent Architecture

This module provides provider-agnostic configuration management with
multi-source loading capabilities and comprehensive validation.

Author: MiniMax Agent
Version: 1.0
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from pathlib import Path
import os
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Config(BaseModel):
    """
    Provider-agnostic configuration with validation and auto-loading.
    
    Features:
    - Environment variable resolution
    - File-based configuration loading
    - Directory creation and validation
    - Comprehensive parameter validation
    """
    
    # Provider Configuration
    provider: str = Field(
        default="ollama",
        description="LLM provider name"
    )
    model_name: str = Field(
        default="llama2",
        description="Model identifier"
    )
    api_endpoint: str = Field(
        default="http://localhost:11434",
        description="Provider API endpoint"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authenticated providers"
    )
    
    # Model Parameters
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=128000,
        description="Maximum tokens for generation"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    system_prompt: str = Field(
        default="You are a helpful AI assistant.",
        description="System prompt for LLM"
    )
    
    # Memory Configuration
    memory_enabled: bool = Field(
        default=True,
        description="Enable persistent memory"
    )
    memory_dir: str = Field(
        default="data/memory",
        description="Memory storage directory"
    )
    max_history: int = Field(
        default=1000,
        ge=10,
        description="Maximum conversation history entries"
    )
    
    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable response caching"
    )
    cache_size: int = Field(
        default=1000,
        ge=10,
        description="Maximum cache entries"
    )
    cache_ttl: int = Field(
        default=300,
        ge=60,
        description="Cache TTL in seconds"
    )
    
    # Plugin Configuration
    plugin_dir: str = Field(
        default="plugins",
        description="Plugin directory"
    )
    enable_plugins: bool = Field(
        default=True,
        description="Enable plugin system"
    )
    
    # Performance Configuration
    max_concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max concurrent requests"
    )
    request_timeout: int = Field(
        default=30,
        ge=1,
        description="Request timeout in seconds"
    )
    
    # Feature Flags
    enable_analytics: bool = Field(
        default=True,
        description="Enable analytics tracking"
    )
    enable_optimization: bool = Field(
        default=True,
        description="Enable self-optimization"
    )
    enable_vector_memory: bool = Field(
        default=True,
        description="Enable vector memory search"
    )
    
    @field_validator('api_key')
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and resolve API key from environment variables.
        
        Supports environment variable interpolation in format: ${VAR_NAME}
        """
        if v and v.startswith('${') and v.endswith('}'):
            env_var = v[2:-1]
            resolved_key = os.getenv(env_var)
            if not resolved_key:
                logger.warning(f"Environment variable {env_var} not found for API key")
            return resolved_key
        return v
    
    @field_validator('memory_dir', 'plugin_dir')
    def validate_directories(cls, v: str) -> str:
        """
        Ensure directories exist and are writable.
        
        Creates directories if they don't exist.
        """
        try:
            Path(v).mkdir(parents=True, exist_ok=True)
            # Verify write permissions
            test_file = Path(v) / ".write_test"
            test_file.touch(exist_ok=True)
            test_file.unlink()
            return v
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot create directory {v}: {e}")
            # Fall back to a default writable location
            fallback_dir = Path.home() / ".minimax_agent" / v
            fallback_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback directory: {fallback_dir}")
            return str(fallback_dir)
    
    @field_validator('api_endpoint')
    def validate_api_endpoint(cls, v: str) -> str:
        """
        Validate API endpoint format.
        
        Ensures the endpoint is a valid URL format.
        """
        if not v.startswith(('http://', 'https://')):
            logger.warning(f"API endpoint {v} doesn't include protocol (http/https)")
        return v
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from file with fallback chain:
        
        1. Provided config_path parameter
        2. opencode.json in current/parent directories (up to 10 levels)
        3. Environment variable overrides
        4. Default values
        
        Args:
            config_path: Optional explicit path to configuration file
            
        Returns:
            Config instance with loaded settings
        """
        config_data = {}
        
        # Step 1: Try explicit config path
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load config file {config_path}: {e}")
        
        # Step 2: Search for opencode.json
        elif not config_path:
            current = Path.cwd()
            for _ in range(10):  # Search up to 10 directory levels
                config_file = current / "opencode.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                        logger.info(f"Found configuration file: {config_file}")
                        break
                    except (json.JSONDecodeError, IOError) as e:
                        logger.warning(f"Failed to load {config_file}: {e}")
                parent = current.parent
                if parent == current:
                    break  # Reached filesystem root
                current = parent
        
        # Step 3: Override with environment variables
        env_overrides = {
            'provider': os.getenv('OPENCODE_PROVIDER'),
            'model_name': os.getenv('OPENCODE_MODEL'),
            'api_key': os.getenv('OPENCODE_API_KEY'),
            'api_endpoint': os.getenv('OPENCODE_ENDPOINT'),
            'memory_dir': os.getenv('OPENCODE_MEMORY_DIR'),
            'plugin_dir': os.getenv('OPENCODE_PLUGIN_DIR'),
            'max_concurrent_requests': os.getenv('OPENCODE_MAX_REQUESTS'),
        }
        
        for key, value in env_overrides.items():
            if value is not None:
                try:
                    # Convert string values to appropriate types
                    if key in ['max_concurrent_requests']:
                        config_data[key] = int(value)
                    elif key in ['memory_enabled', 'cache_enabled', 'enable_plugins', 
                                 'enable_analytics', 'enable_optimization', 'enable_vector_memory']:
                        config_data[key] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        config_data[key] = value
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert environment variable {key}={value}: {e}")
        
        # Step 4: Create config instance (uses defaults for missing values)
        try:
            config = cls(**config_data)
            logger.debug("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to create config instance: {e}")
            # Return default config as last resort
            logger.warning("Using default configuration")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return self.model_dump()
    
    def save_to_file(self, config_path: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Path where to save the configuration file
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            config_dict = self.to_dict()
            
            # Ensure parent directory exists
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {config_path}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            raise
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration and return validation results.
        
        Returns:
            Dictionary with validation results and any warnings
        """
        results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Validate API endpoint accessibility (basic check)
        if self.api_endpoint.startswith(('http://', 'https://')):
            # Basic URL format validation
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.api_endpoint)
                if not parsed.netloc:
                    results["warnings"].append("API endpoint appears to be malformed")
            except Exception:
                results["warnings"].append("Cannot parse API endpoint")
        
        # Validate resource limits
        if self.max_concurrent_requests > 50:
            results["warnings"].append(f"High concurrent requests ({self.max_concurrent_requests}) may impact performance")
        
        # Validate cache settings
        if self.cache_size > 10000:
            results["warnings"].append(f"Large cache size ({self.cache_size}) may consume significant memory")
        
        # Check for required directories
        try:
            Path(self.memory_dir).exists()
            Path(self.plugin_dir).exists()
        except Exception as e:
            results["errors"].append(f"Directory validation failed: {e}")
            results["valid"] = False
        
        return results
    
    def get_provider_config(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration subset.
        
        Returns:
            Dictionary containing only provider-related settings
        """
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "api_endpoint": self.api_endpoint,
            "api_key": self.api_key,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "system_prompt": self.system_prompt
        }
    
    def get_memory_config(self) -> Dict[str, Any]:
        """
        Get memory-related configuration subset.
        
        Returns:
            Dictionary containing only memory-related settings
        """
        return {
            "memory_enabled": self.memory_enabled,
            "memory_dir": self.memory_dir,
            "max_history": self.max_history,
            "enable_vector_memory": self.enable_vector_memory
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"Config(provider={self.provider}, model={self.model_name}, endpoint={self.api_endpoint})"


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the global configuration instance (singleton pattern).
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Global Config instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config.load_from_file(config_path)
    
    return _config_instance


def reload_config(config_path: Optional[str] = None) -> Config:
    """
    Reload the global configuration instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        New Config instance
    """
    global _config_instance
    
    _config_instance = Config.load_from_file(config_path)
    return _config_instance


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config_instance
    _config_instance = None
    logger.info("Configuration instance reset")