#!/usr/bin/env python3
"""
Model Integration System for NEO-CLONE
Dynamically adds validated models to the system and updates configurations
"""

import json
import os
from typing import Dict, List, Optional
from model_discovery import ModelDiscovery, ModelInfo
from model_validator import ModelValidator, ValidationResult
import logging

logger = logging.getLogger(__name__)

class ModelIntegrator:
    """Integrates discovered and validated models into NEO-CLONE"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self.discovery = ModelDiscovery(self.config_path)
        self.validator = ModelValidator()

    def _find_config_path(self) -> str:
        """Find the opencode.json config file"""
        current_dir = os.getcwd()
        for _ in range(10):
            config_path = os.path.join(current_dir, "opencode.json")
            if os.path.exists(config_path):
                return config_path
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir
        return "opencode.json"

    def discover_and_integrate_models(self) -> Dict[str, ModelInfo]:
        """Complete workflow: discover, validate, and integrate models"""
        logger.info("Starting model discovery and integration...")

        # 1. Discover available models
        discovered = self.discovery.scan_all_sources()
        logger.info(f"Discovered {len(discovered)} potential models")

        # 2. Validate models
        validated = self.discovery.validate_models(discovered)
        logger.info(f"Validated {len(validated)} models successfully")

        # 3. Add to configuration
        if validated:
            success = self.discovery.add_to_config(validated)
            if success:
                logger.info("Successfully updated configuration")
            else:
                logger.error("Failed to update configuration")

        # 4. Update brain awareness
        self._update_brain_config(validated)

        return validated

    def _update_brain_config(self, validated_models: Dict[str, ModelInfo]) -> bool:
        """Update brain configuration to be aware of new models"""
        try:
            # Load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

            # Ensure models section exists
            if "models" not in config:
                config["models"] = {}

            # Add brain awareness section
            if "brain" not in config:
                config["brain"] = {}

            if "model_awareness" not in config["brain"]:
                config["brain"]["model_awareness"] = {}

            # Update model awareness
            awareness = config["brain"]["model_awareness"]
            awareness["last_updated"] = self._get_timestamp()
            awareness["total_models"] = len(validated_models)
            awareness["providers"] = list(set(m.provider for m in validated_models.values()))

            # Add model rankings
            awareness["best_models"] = self._rank_models(validated_models)

            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info("Updated brain model awareness")
            return True

        except Exception as e:
            logger.error(f"Failed to update brain config: {e}")
            return False

    def _rank_models(self, models: Dict[str, ModelInfo]) -> Dict[str, List[str]]:
        """Rank models by different criteria"""
        rankings = {
            "fastest": [],
            "most_capable": [],
            "best_overall": []
        }

        if not models:
            return rankings

        # Sort by response time (fastest first)
        fastest = sorted(models.values(), key=lambda m: m.response_time)[:3]
        rankings["fastest"] = [f"{m.provider}/{m.model_name}" for m in fastest]

        # Sort by capability count
        most_capable = sorted(models.values(),
                            key=lambda m: len(m.capabilities) if m.capabilities else 0,
                            reverse=True)[:3]
        rankings["most_capable"] = [f"{m.provider}/{m.model_name}" for m in most_capable]

        # Best overall (simple scoring)
        scored = []
        for model_id, model in models.items():
            score = 0
            if model.capabilities:
                score += len(model.capabilities) * 10
            score -= model.response_time * 2  # Penalize slow response
            scored.append((model_id, score))

        best_overall = sorted(scored, key=lambda x: x[1], reverse=True)[:3]
        rankings["best_overall"] = [model_id for model_id, _ in best_overall]

        return rankings

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_model_recommendation(self, task_type: str = "general") -> Optional[ModelInfo]:
        """Get the best model recommendation for a specific task type"""
        if not self.discovery.validated_models:
            # Try to load from config
            self._load_models_from_config()

        if not self.discovery.validated_models:
            return None

        # Task-specific recommendations
        task_requirements = {
            "general": ["reasoning"],
            "coding": ["reasoning", "code_generation"],
            "creative": ["reasoning", "creativity"],
            "analysis": ["reasoning", "analysis"],
            "math": ["reasoning", "math"],
            "fast": ["reasoning"]  # Prioritize speed
        }

        required_caps = task_requirements.get(task_type, ["reasoning"])
        return self.discovery.get_best_model(required_caps)

    def _load_models_from_config(self):
        """Load validated models from existing configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)

                models_config = config.get("models", {})
                for model_id, model_data in models_config.items():
                    if model_data.get("status") == "validated":
                        model_info = ModelInfo(
                            provider=model_data["provider"],
                            model_name=model_data["model"],
                            api_endpoint=model_data["endpoint"],
                            context_length=model_data.get("context_length", 4096),
                            capabilities=model_data.get("capabilities", ["reasoning"]),
                            cost=model_data.get("cost", "free"),
                            status="validated",
                            response_time=model_data.get("response_time", 1.0)
                        )
                        self.discovery.validated_models[model_id] = model_info

        except Exception as e:
            logger.warning(f"Failed to load models from config: {e}")

    def generate_model_report(self) -> str:
        """Generate a comprehensive report of all available models"""
        report = "# NEO-CLONE Model Integration Report\n\n"

        # Load current state
        self._load_models_from_config()

        total_discovered = len(self.discovery.discovered_models)
        total_validated = len(self.discovery.validated_models)

        report += f"## Model Statistics\n\n"
        report += f"- **Discovered Models**: {total_discovered}\n"
        report += f"- **Validated Models**: {total_validated}\n"
        report += f"- **Validation Rate**: {(total_validated/total_discovered*100):.1f}%\\n" if total_discovered > 0 else "- **Validation Rate**: 0%\n\n"

        if self.discovery.validated_models:
            report += "## Available Models\n\n"
            report += "| Model ID | Provider | Capabilities | Response Time | Cost |\n"
            report += "|----------|----------|--------------|---------------|------|\n"

            for model_id, model in self.discovery.validated_models.items():
                caps = ", ".join(model.capabilities) if model.capabilities else "unknown"
                report += f"| {model_id} | {model.provider} | {caps} | {model.response_time:.2f}s | {model.cost} |\n"

            report += "\n## Recommendations\n\n"

            # Get best models for different tasks
            tasks = ["general", "coding", "creative", "analysis", "fast"]
            for task in tasks:
                best_model = self.get_model_recommendation(task)
                if best_model:
                    report += f"- **{task.title()} Tasks**: {best_model.provider}/{best_model.model_name} ({best_model.response_time:.2f}s)\\n"

        report += "\n## Integration Status\n\n"
        report += "- ✅ Model Discovery: Active\n"
        report += "- ✅ Model Validation: Active\n"
        report += "- ✅ Configuration Updates: Active\n"
        report += "- ✅ Brain Awareness: Active\n"
        report += "- ✅ Automatic Fallbacks: Active\n\n"

        report += "## Next Steps\n\n"
        report += "1. Run periodic model discovery to find new models\n"
        report += "2. Monitor model performance and update rankings\n"
        report += "3. Add support for new model providers as they become available\n"
        report += "4. Implement model health monitoring and automatic switching\n"

        return report

    def run_health_check(self) -> Dict[str, bool]:
        """Run health check on all integrated models"""
        health_status = {}

        for model_id, model_info in self.discovery.validated_models.items():
            try:
                is_healthy, response_time, error = self.validator.test_basic_connectivity(model_info)
                health_status[model_id] = is_healthy

                if not is_healthy:
                    logger.warning(f"Model {model_id} health check failed: {error}")
                    # Mark as needing re-validation
                    model_info.status = "needs_check"
                else:
                    logger.info(f"Model {model_id} is healthy ({response_time:.2f}s)")

            except Exception as e:
                health_status[model_id] = False
                logger.error(f"Health check error for {model_id}: {e}")

        return health_status

    def auto_recover(self) -> bool:
        """Automatically recover from model failures by rediscovering and revalidating"""
        logger.info("Starting automatic model recovery...")

        try:
            # Re-run discovery and integration
            validated = self.discover_and_integrate_models()

            if validated:
                logger.info(f"Successfully recovered {len(validated)} models")
                return True
            else:
                logger.warning("No models could be recovered")
                return False

        except Exception as e:
            logger.error(f"Auto-recovery failed: {e}")
            return False