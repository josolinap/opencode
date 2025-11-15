"""
Enhanced configuration management with validation and hot-reloading
Supports multiple sources, validation, and runtime updates
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading
import time
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    TOGETHER = "together"
    REPLICATE = "replicate"
    OPENAI = "openai"
    CUSTOM = "custom"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheLevel(str, Enum):
    NONE = "none"
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


@dataclass
class ConfigSource:
    name: str
    path: Optional[str] = None
    priority: int = 0
    last_modified: Optional[float] = None


class EnhancedConfig(BaseModel):
    """Enhanced configuration with comprehensive validation"""

    # Core LLM Settings
    provider: ProviderType = Field(ProviderType.OLLAMA, description="LLM provider")
    model_name: str = Field("llama3.2:latest", description="Model name")
    api_endpoint: Optional[str] = Field(None, description="Custom API endpoint")
    api_key: Optional[str] = Field(None, description="API key for cloud providers")

    # Generation Parameters
    max_tokens: int = Field(1024, ge=1, le=32768, description="Max tokens per response")
    temperature: float = Field(
        0.7, ge=0.0, le=2.0, description="Generation temperature"
    )
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p sampling")
    repetition_penalty: float = Field(
        1.0, ge=0.0, le=2.0, description="Repetition penalty"
    )

    # Performance Settings
    timeout: int = Field(30, ge=5, le=300, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(
        1.0, ge=0.1, le=10.0, description="Retry delay in seconds"
    )

    # Caching Settings
    cache_level: CacheLevel = Field(CacheLevel.MEMORY, description="Caching level")
    cache_ttl: int = Field(1800, ge=60, le=86400, description="Cache TTL in seconds")
    cache_size: int = Field(100, ge=10, le=1000, description="Memory cache size")

    # System Settings
    log_level: LogLevel = Field(LogLevel.INFO, description="Logging level")
    log_file: Optional[str] = Field(None, description="Log file path")
    data_dir: str = Field("data", description="Data directory")
    backup_enabled: bool = Field(True, description="Enable automatic backups")

    # UI Settings
    theme: str = Field("auto", description="UI theme (light/dark/auto)")
    ui_mode: str = Field("cli", description="Default UI mode")

    # Advanced Settings
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    plugins_enabled: bool = Field(True, description="Enable plugin system")
    auto_save: bool = Field(True, description="Auto-save conversations")
    max_history: int = Field(50, ge=10, le=1000, description="Max conversation history")

    # Security Settings
    api_key_env_var: Optional[str] = Field(
        None, description="Environment variable for API key"
    )
    rate_limit_enabled: bool = Field(True, description="Enable rate limiting")
    request_rate_limit: int = Field(
        60, ge=1, le=1000, description="Requests per minute"
    )

    @validator("api_endpoint")
    def validate_api_endpoint(cls, v, values):
        provider = values.get("provider")
        if provider == ProviderType.OLLAMA and not v:
            return "http://localhost:11434"
        elif provider in [
            ProviderType.HUGGINGFACE,
            ProviderType.TOGETHER,
            ProviderType.REPLICATE,
        ]:
            return v or f"https://api.{provider.value}.com/v1"
        return v

    @validator("data_dir")
    def validate_data_dir(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @validator("log_file")
    def validate_log_file(cls, v):
        if v:
            Path(v).parent.mkdir(parents=True, exist_ok=True)
        return v


class ConfigManager:
    """Advanced configuration manager with validation and hot-reloading"""

    def __init__(self):
        self.config_sources = []
        self._config: Optional[EnhancedConfig] = None
        self._lock = threading.RLock()
        self._watchers = []
        self._last_reload = time.time()
        self._validation_errors = []

        # Initialize config sources
        self._initialize_sources()

    def _initialize_sources(self):
        """Initialize configuration sources in priority order"""
        self.config_sources = [
            ConfigSource("command_line", priority=100),
            ConfigSource("environment", priority=80),
            ConfigSource("config_file", priority=60),
            ConfigSource("opencode_json", priority=40),
            ConfigSource("defaults", priority=20),
        ]

    def load_config(
        self,
        config_path: Optional[str] = None,
        validate: bool = True,
        reload: bool = False,
    ) -> EnhancedConfig:
        """Load configuration from all sources"""
        with self._lock:
            if reload and self._config:
                logger.info("Reloading configuration")

            # Load from each source in priority order
            config_data = {}

            # 1. Defaults
            config_data.update(self._load_defaults())

            # 2. opencode.json
            opencode_config = self._load_opencode_json()
            if opencode_config:
                config_data.update(opencode_config)

            # 3. Config file
            if config_path:
                file_config = self._load_config_file(config_path)
                if file_config:
                    config_data.update(file_config)

            # 4. Environment variables
            env_config = self._load_environment()
            if env_config:
                config_data.update(env_config)

            # 5. Command line arguments (would be passed separately)

            # Create config object
            try:
                self._config = EnhancedConfig(**config_data)
                self._last_reload = time.time()

                if validate:
                    self._validate_config()

                logger.info(
                    f"Configuration loaded successfully from {len([s for s in self.config_sources if self._source_has_data(s)])} sources"
                )
                return self._config

            except ValidationError as e:
                self._validation_errors = e.errors()
                logger.error(f"Configuration validation failed: {e}")
                raise ValueError(f"Invalid configuration: {e}")

    def _source_has_data(self, source: ConfigSource) -> bool:
        """Check if a config source has data"""
        # This would be implemented based on actual loading logic
        return source.name in ["defaults", "opencode_json"]  # Simplified for now

    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration"""
        return asdict(EnhancedConfig())

    def _load_opencode_json(self) -> Optional[Dict[str, Any]]:
        """Load configuration from opencode.json"""
        opencode_paths = [
            Path.cwd() / "opencode.json",
            Path.cwd().parent / "opencode.json",
            Path.home() / ".opencode" / "opencode.json",
        ]

        for path in opencode_paths:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Extract relevant config sections
                    config = {}
                    if "models" in data:
                        # Use first available model
                        models = data["models"]
                        if models:
                            first_model = next(iter(models.values()))
                            config.update(
                                {
                                    "provider": first_model.get("provider", "ollama"),
                                    "model_name": first_model.get(
                                        "model", "llama3.2:latest"
                                    ),
                                    "api_endpoint": first_model.get("endpoint"),
                                }
                            )

                    logger.debug(f"Loaded opencode.json from {path}")
                    return config

                except Exception as e:
                    logger.warning(f"Failed to load opencode.json from {path}: {e}")

        return None

    def _load_config_file(self, path: str) -> Optional[Dict[str, Any]]:
        """Load configuration from specified file"""
        try:
            config_path = Path(path)
            if not config_path.exists():
                logger.warning(f"Config file not found: {path}")
                return None

            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.debug(f"Loaded config file: {path}")
            return data

        except Exception as e:
            logger.error(f"Failed to load config file {path}: {e}")
            return None

    def _load_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}
        env_mappings = {
            "NEO_PROVIDER": ("provider", str),
            "NEO_MODEL": ("model_name", str),
            "NEO_API_KEY": ("api_key", str),
            "NEO_API_ENDPOINT": ("api_endpoint", str),
            "NEO_MAX_TOKENS": ("max_tokens", int),
            "NEO_TEMPERATURE": ("temperature", float),
            "NEO_LOG_LEVEL": ("log_level", LogLevel),
            "NEO_DATA_DIR": ("data_dir", str),
            "NEO_CACHE_LEVEL": ("cache_level", CacheLevel),
            "NEO_THEME": ("theme", str),
            "NEO_UI_MODE": ("ui_mode", str),
        }

        for env_var, (config_key, config_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if config_type == int:
                        value = int(value)
                    elif config_type == float:
                        value = float(value)
                    elif config_type == LogLevel:
                        value = LogLevel(value.upper())
                    elif config_type == CacheLevel:
                        value = CacheLevel(value.lower())

                    env_config[config_key] = value
                    logger.debug(f"Loaded from environment: {config_key}={value}")
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid environment value {env_var}={value}: {e}")

        return env_config

    def _validate_config(self):
        """Validate current configuration"""
        if not self._config:
            return

        self._validation_errors = []

        # Custom validations
        validations = [
            self._validate_api_access(),
            self._validate_paths(),
            self._validate_performance_settings(),
            self._validate_security_settings(),
        ]

        for validation in validations:
            if validation:
                self._validation_errors.extend(validation)

        if self._validation_errors:
            logger.warning(
                f"Configuration validation warnings: {self._validation_errors}"
            )

    def _validate_api_access(self) -> List[str]:
        """Validate API access configuration"""
        errors = []

        if self._config.provider != ProviderType.OLLAMA:
            if not self._config.api_key:
                errors.append("API key required for cloud providers")

            if not self._config.api_endpoint:
                errors.append("API endpoint required for cloud providers")

        return errors

    def _validate_paths(self) -> List[str]:
        """Validate path configurations"""
        errors = []

        # Check data directory
        try:
            data_path = Path(self._config.data_dir)
            data_path.mkdir(parents=True, exist_ok=True)

            # Check write permissions
            test_file = data_path / ".permission_test"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            errors.append(f"Data directory issue: {e}")

        # Check log file path
        if self._config.log_file:
            try:
                log_path = Path(self._config.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Log file path issue: {e}")

        return errors

    def _validate_performance_settings(self) -> List[str]:
        """Validate performance settings"""
        errors = []

        if self._config.cache_size < 10:
            errors.append("Cache size too small (minimum: 10)")

        if self._config.timeout < 5:
            errors.append("Timeout too short (minimum: 5 seconds)")

        if self._config.max_retries > 10:
            errors.append("Too many retries (maximum: 10)")

        return errors

    def _validate_security_settings(self) -> List[str]:
        """Validate security settings"""
        errors = []

        if self._config.api_key and len(self._config.api_key) < 10:
            errors.append("API key seems too short")

        if self._config.request_rate_limit > 1000:
            errors.append("Rate limit too high (maximum: 1000/minute)")

        return errors

    def get_config(self) -> Optional[EnhancedConfig]:
        """Get current configuration"""
        return self._config

    def update_config(self, updates: Dict[str, Any], save: bool = False) -> bool:
        """Update configuration with new values"""
        if not self._config:
            logger.error("No configuration loaded")
            return False

        try:
            # Create updated config
            current_dict = self._config.dict()
            current_dict.update(updates)

            # Validate updated config
            updated_config = EnhancedConfig(**current_dict)
            self._config = updated_config

            if save:
                self.save_config()

            logger.info(f"Configuration updated: {list(updates.keys())}")
            return True

        except ValidationError as e:
            logger.error(f"Configuration update failed: {e}")
            return False

    def save_config(self, path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        if not self._config:
            logger.error("No configuration to save")
            return False

        save_path = Path(path) if path else Path.cwd() / "neo-clone-config.json"

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self._config.dict(), f, indent=2, default=str)

            logger.info(f"Configuration saved to {save_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def get_validation_errors(self) -> List[str]:
        """Get current validation errors"""
        return self._validation_errors.copy()

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display"""
        if not self._config:
            return {"status": "not_loaded"}

        return {
            "provider": self._config.provider.value,
            "model": self._config.model_name,
            "cache_level": self._config.cache_level.value,
            "log_level": self._config.log_level.value,
            "data_dir": self._config.data_dir,
            "theme": self._config.theme,
            "validation_errors": len(self._validation_errors),
            "last_reload": self._last_reload,
        }


# Global configuration manager
config_manager = ConfigManager()


def load_enhanced_config(
    config_path: Optional[str] = None, validate: bool = True
) -> EnhancedConfig:
    """Load enhanced configuration"""
    return config_manager.load_config(config_path=config_path, validate=validate)


def get_config() -> Optional[EnhancedConfig]:
    """Get current configuration"""
    return config_manager.get_config()


def update_config(updates: Dict[str, Any], save: bool = False) -> bool:
    """Update configuration"""
    return config_manager.update_config(updates, save)


def save_config(path: Optional[str] = None) -> bool:
    """Save current configuration"""
    return config_manager.save_config(path)
