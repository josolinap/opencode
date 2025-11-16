"""
Credibility Rollout Safeguards for Neo-Clone
Provides automatic monitoring and rollback mechanisms for safe credibility feature deployment.
"""

import os
import time
import threading
import statistics
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Configuration
MONITORING_ENABLED = os.getenv('CREDIBILITY_MONITORING_ENABLED', 'true').lower() == 'true'
LATENCY_SPIKE_THRESHOLD_MS = float(os.getenv('CREDIBILITY_LATENCY_SPIKE_THRESHOLD_MS', '5.0'))
ERROR_RATE_THRESHOLD = float(os.getenv('CREDIBILITY_ERROR_RATE_THRESHOLD', '0.05'))
MONITORING_WINDOW_MINUTES = int(os.getenv('CREDIBILITY_MONITORING_WINDOW_MINUTES', '5'))
ROLLBACK_ENABLED = os.getenv('CREDIBILITY_AUTO_ROLLBACK_ENABLED', 'true').lower() == 'true'

class RolloutMetrics:
    """Tracks rollout performance metrics for automatic safeguards."""

    def __init__(self, window_minutes: int = MONITORING_WINDOW_MINUTES):
        self.window_minutes = window_minutes
        self.metrics: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def record_metric(self, metric_type: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric."""
        with self.lock:
            metric = {
                'timestamp': datetime.now(),
                'type': metric_type,
                'value': value,
                'metadata': metadata or {}
            }
            self.metrics.append(metric)

            # Clean old metrics outside the window
            cutoff_time = datetime.now() - timedelta(minutes=self.window_minutes)
            self.metrics = [m for m in self.metrics if m['timestamp'] > cutoff_time]

    def get_recent_metrics(self, metric_type: str, minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent metrics of a specific type."""
        with self.lock:
            window_minutes = minutes or self.window_minutes
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
            return [m for m in self.metrics if m['type'] == metric_type and m['timestamp'] > cutoff_time]

    def calculate_average(self, metric_type: str, minutes: Optional[int] = None) -> Optional[float]:
        """Calculate average value for a metric type."""
        metrics = self.get_recent_metrics(metric_type, minutes)
        if not metrics:
            return None
        values = [m['value'] for m in metrics]
        return statistics.mean(values)

    def calculate_percentile(self, metric_type: str, percentile: float, minutes: Optional[int] = None) -> Optional[float]:
        """Calculate percentile value for a metric type."""
        metrics = self.get_recent_metrics(metric_type, minutes)
        if not metrics:
            return None
        values = [m['value'] for m in metrics]
        if len(values) < 2:
            return statistics.mean(values) if values else None
        return statistics.quantiles(values, n=100)[int(percentile) - 1]

    def get_error_rate(self, minutes: Optional[int] = None) -> float:
        """Calculate error rate from recent metrics."""
        total_metrics = len(self.get_recent_metrics('latency', minutes))
        error_metrics = len(self.get_recent_metrics('error', minutes))

        if total_metrics == 0:
            return 0.0

        return error_metrics / total_metrics


class RolloutSafeguards:
    """
    Automatic safeguards for credibility feature rollouts.

    Monitors performance metrics and triggers rollbacks if thresholds are exceeded.
    """

    def __init__(self):
        self.metrics = RolloutMetrics()
        self.monitoring_active = False
        self.rollback_callbacks: List[Callable] = []
        self.monitoring_thread: Optional[threading.Thread] = None

    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.monitoring_active or not MONITORING_ENABLED:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Credibility rollout monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        logger.info("Credibility rollout monitoring stopped")

    def record_latency(self, latency_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a latency measurement."""
        self.metrics.record_metric('latency', latency_ms, metadata)

    def record_error(self, error_type: str = 'general', metadata: Optional[Dict[str, Any]] = None):
        """Record an error occurrence."""
        self.metrics.record_metric('error', 1.0, {'error_type': error_type, **(metadata or {})})

    def add_rollback_callback(self, callback: Callable):
        """Add a callback to be executed on rollback."""
        self.rollback_callbacks.append(callback)

    def check_safeguards(self) -> Dict[str, Any]:
        """
        Check if any safeguards have been triggered.

        Returns:
            Dict with safeguard status and any triggered alerts
        """
        alerts = []

        # Check latency spike
        avg_latency = self.metrics.calculate_average('latency')
        if avg_latency and avg_latency > LATENCY_SPIKE_THRESHOLD_MS:
            alerts.append({
                'type': 'latency_spike',
                'message': f'Average latency {avg_latency:.2f}ms exceeds threshold {LATENCY_SPIKE_THRESHOLD_MS}ms',
                'severity': 'high',
                'metric': 'latency',
                'value': avg_latency,
                'threshold': LATENCY_SPIKE_THRESHOLD_MS
            })

        # Check error rate
        error_rate = self.metrics.get_error_rate()
        if error_rate > ERROR_RATE_THRESHOLD:
            alerts.append({
                'type': 'high_error_rate',
                'message': f'Error rate {error_rate:.3%} exceeds threshold {ERROR_RATE_THRESHOLD:.1%}',
                'severity': 'critical',
                'metric': 'error_rate',
                'value': error_rate,
                'threshold': ERROR_RATE_THRESHOLD
            })

        # Check 95th percentile latency
        p95_latency = self.metrics.calculate_percentile('latency', 95.0)
        if p95_latency and p95_latency > LATENCY_SPIKE_THRESHOLD_MS * 2:
            alerts.append({
                'type': 'latency_p95_spike',
                'message': f'95th percentile latency {p95_latency:.2f}ms is too high',
                'severity': 'medium',
                'metric': 'latency_p95',
                'value': p95_latency,
                'threshold': LATENCY_SPIKE_THRESHOLD_MS * 2
            })

        return {
            'alerts': alerts,
            'alert_count': len(alerts),
            'has_critical_alerts': any(a['severity'] == 'critical' for a in alerts),
            'has_high_alerts': any(a['severity'] in ['critical', 'high'] for a in alerts),
            'timestamp': datetime.now().isoformat()
        }

    def should_rollback(self) -> bool:
        """Determine if rollback should be triggered."""
        if not ROLLBACK_ENABLED:
            return False

        status = self.check_safeguards()
        return status['has_critical_alerts']

    def execute_rollback(self):
        """Execute rollback by calling all registered callbacks."""
        logger.warning("Executing credibility feature rollback due to safeguard triggers")

        for callback in self.rollback_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Rollback callback failed: {e}")

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        return {
            'monitoring_active': self.monitoring_active,
            'window_minutes': self.metrics.window_minutes,
            'total_metrics': len(self.metrics.metrics),
            'avg_latency_ms': self.metrics.calculate_average('latency'),
            'p95_latency_ms': self.metrics.calculate_percentile('latency', 95.0),
            'error_rate': self.metrics.get_error_rate(),
            'safeguard_status': self.check_safeguards(),
            'thresholds': {
                'latency_spike_threshold_ms': LATENCY_SPIKE_THRESHOLD_MS,
                'error_rate_threshold': ERROR_RATE_THRESHOLD
            }
        }

    def _monitoring_loop(self):
        """Main monitoring loop that runs in background thread."""
        check_interval = 30  # Check every 30 seconds

        while self.monitoring_active:
            try:
                # Check safeguards
                if self.should_rollback():
                    logger.warning("Safeguard thresholds exceeded, triggering rollback")
                    self.execute_rollback()
                    break  # Stop monitoring after rollback

                # Log status periodically (every 5 minutes)
                if int(time.time()) % 300 == 0:
                    stats = self.get_monitoring_stats()
                    safeguard_status = stats['safeguard_status']

                    if safeguard_status['alert_count'] > 0:
                        logger.warning(f"Safeguard alerts active: {safeguard_status['alert_count']}")
                        for alert in safeguard_status['alerts']:
                            logger.warning(f"  {alert['type']}: {alert['message']}")
                    else:
                        logger.info("Credibility monitoring: all safeguards green")

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

            time.sleep(check_interval)


# Global safeguards instance
_safeguards_instance: Optional[RolloutSafeguards] = None

def get_safeguards_instance() -> RolloutSafeguards:
    """Get or create global safeguards instance."""
    global _safeguards_instance
    if _safeguards_instance is None:
        _safeguards_instance = RolloutSafeguards()
    return _safeguards_instance

def record_credibility_latency(latency_ms: float, metadata: Optional[Dict[str, Any]] = None):
    """Record credibility computation latency for monitoring."""
    if MONITORING_ENABLED:
        safeguards = get_safeguards_instance()
        safeguards.record_latency(latency_ms, metadata)

def record_credibility_error(error_type: str = 'general', metadata: Optional[Dict[str, Any]] = None):
    """Record credibility computation error for monitoring."""
    if MONITORING_ENABLED:
        safeguards = get_safeguards_instance()
        safeguards.record_error(error_type, metadata)

def check_rollout_safeguards() -> Dict[str, Any]:
    """Check current rollout safeguard status."""
    safeguards = get_safeguards_instance()
    return safeguards.check_safeguards()

def get_rollout_monitoring_stats() -> Dict[str, Any]:
    """Get comprehensive rollout monitoring statistics."""
    safeguards = get_safeguards_instance()
    return safeguards.get_monitoring_stats()


# Example rollback callback
def default_rollback_callback():
    """Default rollback callback that disables credibility features."""
    logger.warning("Executing default credibility rollback")

    # Disable all credibility features
    os.environ['CREDIBILITY_POLICY_ENABLED'] = 'false'
    os.environ['WEBSEARCH_CREDIBILITY_ENABLED'] = 'false'
    os.environ['CREDIBILITY_POLICY_AB_TEST'] = 'false'

    logger.warning("All credibility features disabled due to safeguard triggers")


# Initialize safeguards with default rollback
def initialize_rollout_safeguards():
    """Initialize rollout safeguards with default configuration."""
    safeguards = get_safeguards_instance()
    safeguards.add_rollback_callback(default_rollback_callback)

    if MONITORING_ENABLED:
        safeguards.start_monitoring()
        logger.info("Credibility rollout safeguards initialized and monitoring started")
    else:
        logger.info("Credibility rollout safeguards initialized (monitoring disabled)")


# Test and example usage
if __name__ == "__main__":
    print("🛡️ Credibility Rollout Safeguards Test")
    print("=" * 50)

    # Initialize safeguards
    initialize_rollout_safeguards()

    # Test metrics recording
    print("\n1️⃣ Metrics Recording Test")
    record_credibility_latency(2.5, {'variant': 'control'})
    record_credibility_latency(3.1, {'variant': 'treatment_a'})
    record_credibility_latency(8.5, {'variant': 'treatment_a'})  # High latency
    record_credibility_error('timeout', {'url': 'example.com'})

    time.sleep(1)  # Allow metrics to be recorded

    # Check safeguards
    print("\n2️⃣ Safeguard Checking Test")
    status = check_rollout_safeguards()
    print(f"Alerts: {status['alert_count']}")
    print(f"Critical alerts: {status['has_critical_alerts']}")
    print(f"High alerts: {status['has_high_alerts']}")

    for alert in status['alerts']:
        print(f"  {alert['severity'].upper()}: {alert['message']}")

    # Get monitoring stats
    print("\n3️⃣ Monitoring Statistics Test")
    stats = get_rollout_monitoring_stats()
    print(f"Monitoring active: {stats['monitoring_active']}")
    print(f"Total metrics: {stats['total_metrics']}")
    print(".2f")
    print(".2f")
    print(".1%")

    # Test rollback trigger (if error rate is high)
    print("\n4️⃣ Rollback Trigger Test")
    for _ in range(10):  # Simulate high error rate
        record_credibility_error('test_error')

    time.sleep(1)

    should_rollback = get_safeguards_instance().should_rollback()
    print(f"Should rollback: {should_rollback}")

    if should_rollback:
        print("⚠️  Rollback would be triggered in production")
    else:
        print("✅ Safeguards are within acceptable limits")

    # Stop monitoring
    get_safeguards_instance().stop_monitoring()

    print("\n✅ Credibility Rollout Safeguards Test Complete")
