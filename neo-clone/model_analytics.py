#!/usr/bin/env python3
"""
Model Analytics and Optimization System for NEO-CLONE
Tracks model usage patterns and optimizes model selection automatically
"""

import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
import os

logger = logging.getLogger(__name__)

@dataclass
class ModelUsage:
    """Record of a model usage instance"""
    model_id: str
    task_type: str
    success: bool
    response_time: float
    token_count: Optional[int]
    error_message: str = ""
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class TaskPattern:
    """Pattern analysis for a task type"""
    task_type: str
    total_usages: int
    success_rate: float
    avg_response_time: float
    best_model: str
    model_performance: Dict[str, Dict[str, float]]  # model -> {success_rate, avg_time}
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

class ModelAnalytics:
    """Analytics system for model usage and optimization"""

    def __init__(self, config_path: str = "../opencode.json", history_file: str = "model_usage_history.json"):
        self.config_path = config_path
        self.history_file = os.path.join(os.path.dirname(config_path), history_file)
        self.usage_history: List[ModelUsage] = []
        self.task_patterns: Dict[str, TaskPattern] = {}
        self.model_stats: Dict[str, Dict[str, Any]] = {}

        # Load existing data
        self._load_history()
        self._analyze_patterns()

    def record_usage(self, model_id: str, task_type: str, success: bool,
                    response_time: float, token_count: Optional[int] = None,
                    error_message: str = ""):
        """Record a model usage instance"""
        usage = ModelUsage(
            model_id=model_id,
            task_type=task_type,
            success=success,
            response_time=response_time,
            token_count=token_count,
            error_message=error_message
        )

        self.usage_history.append(usage)
        self._update_patterns(usage)
        self._save_history()

        logger.debug(f"Recorded usage: {model_id} for {task_type} - {'success' if success else 'failed'}")

    def get_optimal_model(self, task_type: str, available_models: List[str]) -> Optional[str]:
        """Get the optimal model for a task type based on historical performance"""
        if task_type not in self.task_patterns:
            # No historical data, return fastest available model
            return self._get_fastest_model(available_models)

        pattern = self.task_patterns[task_type]

        # Filter to available models
        available_performance = {
            model: pattern.model_performance.get(model, {})
            for model in available_models
            if model in pattern.model_performance
        }

        if not available_performance:
            # No historical data for available models
            return self._get_fastest_model(available_models)

        # Score models based on success rate and response time
        model_scores = {}
        for model, perf in available_performance.items():
            success_rate = perf.get('success_rate', 0.5)
            avg_time = perf.get('avg_time', 10.0)

            # Score = success_rate * 100 - (response_time penalty)
            score = (success_rate * 100) - (avg_time * 2)
            model_scores[model] = score

        # Return model with highest score
        if model_scores:
            return max(model_scores, key=lambda m: model_scores[m])

        return self._get_fastest_model(available_models)

    def _get_fastest_model(self, available_models: List[str]) -> Optional[str]:
        """Get the fastest model from available options"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            models_config = config.get("models", {})
            fastest_model = None
            fastest_time = float('inf')

            for model_id in available_models:
                if model_id in models_config:
                    response_time = models_config[model_id].get("response_time", 10.0)
                    if response_time < fastest_time:
                        fastest_time = response_time
                        fastest_model = model_id

            return fastest_model

        except Exception as e:
            logger.warning(f"Failed to get fastest model: {e}")
            return available_models[0] if available_models else None

    def _update_patterns(self, usage: ModelUsage):
        """Update task patterns with new usage data"""
        task_type = usage.task_type

        if task_type not in self.task_patterns:
            self.task_patterns[task_type] = TaskPattern(
                task_type=task_type,
                total_usages=0,
                success_rate=0.0,
                avg_response_time=0.0,
                best_model="",
                model_performance={}
            )

        pattern = self.task_patterns[task_type]
        pattern.total_usages += 1
        pattern.last_updated = datetime.now()

        # Update model performance
        model = usage.model_id
        if model not in pattern.model_performance:
            pattern.model_performance[model] = {
                'success_count': 0,
                'total_count': 0,
                'total_time': 0.0,
                'success_rate': 0.0,
                'avg_time': 0.0
            }

        perf = pattern.model_performance[model]
        perf['total_count'] += 1
        perf['total_time'] += usage.response_time

        if usage.success:
            perf['success_count'] += 1

        # Recalculate stats
        perf['success_rate'] = perf['success_count'] / perf['total_count']
        perf['avg_time'] = perf['total_time'] / perf['total_count']

        # Update overall pattern stats
        all_usages = [u for u in self.usage_history if u.task_type == task_type]
        pattern.success_rate = sum(1 for u in all_usages if u.success) / len(all_usages)
        pattern.avg_response_time = sum(u.response_time for u in all_usages) / len(all_usages)

        # Find best model
        best_model = None
        best_score = -1

        for m, p in pattern.model_performance.items():
            score = p['success_rate'] * 100 - p['avg_time'] * 2
            if score > best_score:
                best_score = score
                best_model = m

        pattern.best_model = best_model or ""

    def _analyze_patterns(self):
        """Analyze all usage history to build patterns"""
        if not self.usage_history:
            return

        # Group by task type
        task_groups = defaultdict(list)
        for usage in self.usage_history:
            task_groups[usage.task_type].append(usage)

        # Build patterns
        for task_type, usages in task_groups.items():
            self._update_patterns(usages[-1])  # Use last usage to trigger pattern update

    def get_analytics_report(self) -> str:
        """Generate a comprehensive analytics report"""
        report = "# Model Analytics Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if not self.usage_history:
            report += "No usage data available yet.\n"
            return report

        # Summary stats
        total_usages = len(self.usage_history)
        successful_usages = sum(1 for u in self.usage_history if u.success)
        overall_success_rate = successful_usages / total_usages * 100

        report += "## Summary\n\n"
        report += f"- Total model usages: {total_usages}\n"
        report += f"- Overall success rate: {overall_success_rate:.1f}%\n"
        report += f"- Task types analyzed: {len(self.task_patterns)}\n"
        report += f"- Models used: {len(set(u.model_id for u in self.usage_history))}\n\n"

        # Task patterns
        if self.task_patterns:
            report += "## Task Performance\n\n"
            report += "| Task Type | Usages | Success Rate | Avg Time | Best Model |\n"
            report += "|-----------|--------|--------------|----------|------------|\n"

            for pattern in sorted(self.task_patterns.values(), key=lambda p: p.total_usages, reverse=True):
                report += f"| {pattern.task_type} | {pattern.total_usages} | {pattern.success_rate:.1f}% | {pattern.avg_response_time:.2f}s | {pattern.best_model} |\n"

            report += "\n"

        # Model performance
        model_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'time': 0.0})
        for usage in self.usage_history:
            model_stats[usage.model_id]['total'] += 1
            model_stats[usage.model_id]['time'] += usage.response_time
            if usage.success:
                model_stats[usage.model_id]['success'] += 1

        if model_stats:
            report += "## Model Performance\n\n"
            report += "| Model | Usages | Success Rate | Avg Time |\n"
            report += "|-------|--------|--------------|----------|\n"

            for model, stats in sorted(model_stats.items(), key=lambda x: x[1]['total'], reverse=True):
                success_rate = stats['success'] / stats['total'] * 100
                avg_time = stats['time'] / stats['total']
                report += f"| {model} | {stats['total']} | {success_rate:.1f}% | {avg_time:.2f}s |\n"

        return report

    def _load_history(self):
        """Load usage history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)

                self.usage_history = []
                for item in data.get('usage_history', []):
                    # Convert timestamp string back to datetime
                    timestamp_str = item.get('timestamp')
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str)
                    else:
                        timestamp = datetime.now()

                    usage = ModelUsage(
                        model_id=item['model_id'],
                        task_type=item['task_type'],
                        success=item['success'],
                        response_time=item['response_time'],
                        token_count=item.get('token_count'),
                        error_message=item.get('error_message', ''),
                        timestamp=timestamp
                    )
                    self.usage_history.append(usage)

                logger.info(f"Loaded {len(self.usage_history)} usage records")

        except Exception as e:
            logger.warning(f"Failed to load usage history: {e}")

    def _save_history(self):
        """Save usage history to file"""
        try:
            data = {
                'usage_history': [asdict(u) for u in self.usage_history[-1000:]],  # Keep last 1000 records
                'last_updated': datetime.now().isoformat()
            }

            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save usage history: {e}")

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove usage data older than specified days"""
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        original_count = len(self.usage_history)

        self.usage_history = [u for u in self.usage_history if u.timestamp and u.timestamp > cutoff]

        removed_count = original_count - len(self.usage_history)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old usage records")
            self._save_history()
            self._analyze_patterns()  # Re-analyze with cleaned data