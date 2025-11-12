#!/usr/bin/env python3
"""
Model Health Monitoring System for NEO-CLONE
Periodically checks AI model availability and updates health status
"""

import json
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import os

from model_validator import ModelValidator, ValidationResult

logger = logging.getLogger(__name__)

@dataclass
class ModelHealth:
    """Health status of a model"""
    model_id: str
    last_checked: datetime
    is_healthy: bool
    response_time: float
    consecutive_failures: int
    last_error: str = ""

class ModelMonitor:
    """Periodic health monitoring for AI models"""

    def __init__(self, config_path: str = "../opencode.json", health_check_interval: int = 3600):
        """
        Initialize model monitor

        Args:
            config_path: Path to opencode.json config file
            health_check_interval: Seconds between health checks (default 1 hour)
        """
        self.config_path = config_path
        self.health_check_interval = health_check_interval
        self.validator = ModelValidator()
        self.health_status: Dict[str, ModelHealth] = {}
        self.max_consecutive_failures = 3  # Mark unhealthy after 3 failures

    def load_config(self) -> Dict:
        """Load current opencode.json configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Load health status from config
                self._load_health_status_from_config(config)
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {"models": {}}

    def save_config(self, config: Dict):
        """Save updated configuration to opencode.json"""
        try:
            # Save health status to config
            self._save_health_status_to_config(config)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _load_health_status_from_config(self, config: Dict):
        """Load health status from config file"""
        health_data = config.get("model_health", {})
        for model_id, health_dict in health_data.items():
            self.health_status[model_id] = ModelHealth(
                model_id=model_id,
                last_checked=datetime.fromisoformat(health_dict.get("last_checked", datetime.min.isoformat())),
                is_healthy=health_dict.get("is_healthy", True),
                response_time=health_dict.get("response_time", 0.0),
                consecutive_failures=health_dict.get("consecutive_failures", 0),
                last_error=health_dict.get("last_error", "")
            )

    def _save_health_status_to_config(self, config: Dict):
        """Save health status to config file"""
        health_data = {}
        for model_id, health in self.health_status.items():
            health_data[model_id] = {
                "last_checked": health.last_checked.isoformat(),
                "is_healthy": health.is_healthy,
                "response_time": health.response_time,
                "consecutive_failures": health.consecutive_failures,
                "last_error": health.last_error
            }
        config["model_health"] = health_data

    def create_model_info(self, model_id: str, model_config: Dict):
        """Create a model info object for validation"""
        class ModelInfo:
            def __init__(self, provider, model_name, api_endpoint):
                self.provider = provider
                self.model_name = model_name
                self.api_endpoint = api_endpoint

        provider, model_name = model_id.split('/', 1)
        endpoint = model_config.get('endpoint', '')

        return ModelInfo(provider, model_name, endpoint)

    def check_model_health(self, model_id: str, model_config: Dict) -> ModelHealth:
        """Check health of a single model"""
        logger.info(f"Checking health of {model_id}")

        model_info = self.create_model_info(model_id, model_config)

        # Test basic connectivity
        is_connected, response_time, error_msg = self.validator.test_basic_connectivity(model_info)

        # Update health status
        current_health = self.health_status.get(model_id, ModelHealth(
            model_id=model_id,
            last_checked=datetime.min,
            is_healthy=True,
            response_time=0.0,
            consecutive_failures=0
        ))

        current_health.last_checked = datetime.now()

        if is_connected:
            current_health.is_healthy = True
            current_health.response_time = response_time
            current_health.consecutive_failures = 0
            current_health.last_error = ""
            logger.info(f"[HEALTHY] {model_id} is healthy (response time: {response_time:.2f}s)")
        else:
            current_health.consecutive_failures += 1
            current_health.last_error = error_msg

            if current_health.consecutive_failures >= self.max_consecutive_failures:
                current_health.is_healthy = False
                logger.warning(f"[UNHEALTHY] {model_id} marked unhealthy after {current_health.consecutive_failures} failures: {error_msg}")
            else:
                logger.warning(f"[WARNING] {model_id} failed health check ({current_health.consecutive_failures}/{self.max_consecutive_failures}): {error_msg}")

        self.health_status[model_id] = current_health
        return current_health

    def update_config_with_health(self, config: Dict):
        """Update config with latest health information"""
        for model_id, model_config in config.get("models", {}).items():
            if model_id in self.health_status:
                health = self.health_status[model_id]

                # Update response time
                if health.is_healthy:
                    model_config["response_time"] = health.response_time
                    model_config["last_health_check"] = health.last_checked.isoformat()
                else:
                    # Mark unhealthy models
                    model_config["healthy"] = False
                    model_config["last_error"] = health.last_error
                    model_config["last_health_check"] = health.last_checked.isoformat()

    def run_health_check(self, force: bool = False) -> Dict[str, ModelHealth]:
        """
        Run health check on all models

        Args:
            force: Force check even if recently checked
        """
        config = self.load_config()
        models = config.get("models", {})

        logger.info(f"Starting health check for {len(models)} models")

        checked_models = {}

        for model_id, model_config in models.items():
            # Skip if recently checked and not forcing
            if not force and model_id in self.health_status:
                last_check = self.health_status[model_id].last_checked
                if datetime.now() - last_check < timedelta(seconds=self.health_check_interval):
                    logger.debug(f"Skipping {model_id} - recently checked")
                    continue

            health = self.check_model_health(model_id, model_config)
            checked_models[model_id] = health

        # Update config with health information
        self.update_config_with_health(config)
        self.save_config(config)

        logger.info(f"Health check completed. Checked {len(checked_models)} models")
        return checked_models

    def get_health_report(self) -> str:
        """Generate a health report"""
        # Ensure health status is loaded
        if not self.health_status:
            self.load_config()

        report = "# Model Health Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if not self.health_status:
            report += "No health checks have been performed yet.\n"
            return report

        healthy_count = sum(1 for h in self.health_status.values() if h.is_healthy)
        total_count = len(self.health_status)

        report += f"## Summary\n\n"
        report += f"- Total models: {total_count}\n"
        report += f"- Healthy models: {healthy_count}\n"
        report += f"- Unhealthy models: {total_count - healthy_count}\n\n"

        report += "## Model Status\n\n"
        report += "| Model | Status | Response Time | Last Check | Failures |\n"
        report += "|-------|--------|---------------|------------|----------|\n"

        for model_id, health in sorted(self.health_status.items(),
                                      key=lambda x: (not x[1].is_healthy, x[1].response_time)):
            status = "Healthy" if health.is_healthy else "Unhealthy"
            response_time = f"{health.response_time:.2f}s" if health.response_time > 0 else "N/A"
            last_check = health.last_checked.strftime('%H:%M:%S')
            failures = health.consecutive_failures

            report += f"| {model_id} | {status} | {response_time} | {last_check} | {failures} |\n"

        # Show unhealthy models details
        unhealthy = [h for h in self.health_status.values() if not h.is_healthy]
        if unhealthy:
            report += "\n## Unhealthy Models Details\n\n"
            for health in unhealthy:
                report += f"### {health.model_id}\n"
                report += f"- Last error: {health.last_error}\n"
                report += f"- Consecutive failures: {health.consecutive_failures}\n"
                report += f"- Last checked: {health.last_checked.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return report

    def list_models(self):
        """List all models with their current status"""
        config = self.load_config()
        models = config.get("models", {})

        print("Model Inventory")
        print("=" * 80)
        print("<15")
        print("-" * 80)

        for model_id, model_config in models.items():
            health = self.health_status.get(model_id)
            if health:
                status = "Healthy" if health.is_healthy else "Unhealthy"
                response_time = f"{health.response_time:.2f}s" if health.response_time > 0 else "N/A"
                failures = health.consecutive_failures
            else:
                status = "Unknown"
                response_time = "N/A"
                failures = 0

            provider = model_config.get("provider", "unknown")
            print(f"{model_id:<40} {provider:<15} {status:<10} {response_time:<12} {failures:<8}")

        print(f"\nTotal models: {len(models)}")

    def show_model_details(self, model_id: str):
        """Show detailed information for a specific model"""
        config = self.load_config()
        models = config.get("models", {})

        if model_id not in models:
            print(f"❌ Model '{model_id}' not found")
            return

        model_config = models[model_id]
        health = self.health_status.get(model_id)

        print(f"Model Details: {model_id}")
        print("=" * 50)
        print(f"Provider: {model_config.get('provider', 'unknown')}")
        print(f"Model: {model_config.get('model', 'unknown')}")
        print(f"Endpoint: {model_config.get('endpoint', 'unknown')}")
        print(f"Context Length: {model_config.get('context_length', 'unknown')}")
        print(f"Cost: {model_config.get('cost', 'unknown')}")

        if health:
            status = "Healthy" if health.is_healthy else "Unhealthy"
            print(f"Status: {status}")
            print(f"Response Time: {health.response_time:.2f}s" if health.response_time > 0 else "Response Time: N/A")
            print(f"Consecutive Failures: {health.consecutive_failures}")
            print(f"Last Error: {health.last_error or 'None'}")
            print(f"Last Checked: {health.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("Status: Never checked")

        capabilities = model_config.get("capabilities", [])
        if capabilities:
            print(f"Capabilities: {', '.join(capabilities)}")

    def test_single_model(self, model_id: str):
        """Test a specific model manually"""
        config = self.load_config()
        models = config.get("models", {})

        if model_id not in models:
            print(f"Model '{model_id}' not found")
            return

        print(f"Testing model: {model_id}")
        health = self.check_model_health(model_id, models[model_id])

        if health.is_healthy:
            print(f"Test passed - Response time: {health.response_time:.2f}s")
        else:
            print(f"Test failed - Error: {health.last_error}")

    def show_analytics(self):
        """Show model usage analytics"""
        try:
            from model_analytics import ModelAnalytics
            analytics = ModelAnalytics(self.config_path, self.config_path.replace('opencode.json', 'model_usage_history.json'))
            report = analytics.get_analytics_report()
            print(report)
        except ImportError:
            print("Analytics module not available")
        except Exception as e:
            print(f"Error loading analytics: {e}")

    def clean_unhealthy_models(self):
        """Remove models that have been persistently unhealthy"""
        config = self.load_config()
        models = config.get("models", {})
        health_status = config.get("model_health", {})

        to_remove = []
        for model_id, health_dict in health_status.items():
            if not health_dict.get("is_healthy", True) and health_dict.get("consecutive_failures", 0) >= self.max_consecutive_failures:
                to_remove.append(model_id)

        if not to_remove:
            print("No persistently unhealthy models to remove")
            return

        print(f"Removing {len(to_remove)} persistently unhealthy models:")
        for model_id in to_remove:
            print(f"  - {model_id}")
            if model_id in models:
                del models[model_id]

        self.save_config(config)
        print("Cleanup completed")

    def get_healthy_models(self) -> List[str]:
        """Get list of currently healthy model IDs"""
        return [model_id for model_id, health in self.health_status.items() if health.is_healthy]

def main():
    """CLI interface for model monitoring"""
    import argparse

    parser = argparse.ArgumentParser(description="Model Health Monitor for NEO-CLONE")
    parser.add_argument("--config", default="../opencode.json", help="Path to config file")
    parser.add_argument("--force", action="store_true", help="Force health check even if recently done")
    parser.add_argument("--report", action="store_true", help="Generate and print health report")
    parser.add_argument("--interval", type=int, default=3600, help="Health check interval in seconds")
    parser.add_argument("--list", action="store_true", help="List all models with status")
    parser.add_argument("--details", type=str, help="Show detailed information for a specific model")
    parser.add_argument("--test", type=str, help="Test a specific model manually")
    parser.add_argument("--analytics", action="store_true", help="Show model usage analytics")
    parser.add_argument("--clean", action="store_true", help="Remove persistently unhealthy models")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    monitor = ModelMonitor(args.config, args.interval)

    if args.list:
        monitor.list_models()
    elif args.details:
        monitor.show_model_details(args.details)
    elif args.test:
        monitor.test_single_model(args.test)
    elif args.analytics:
        monitor.show_analytics()
    elif args.clean:
        monitor.clean_unhealthy_models()
    elif args.report:
        print(monitor.get_health_report())
    else:
        results = monitor.run_health_check(force=args.force)
        print(f"Health check completed for {len(results)} models")

        # Print summary
        healthy = sum(1 for h in results.values() if h.is_healthy)
        print(f"Healthy: {healthy}/{len(results)} models")

if __name__ == "__main__":
    main()