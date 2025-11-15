from functools import lru_cache
'\nAdvanced Analytics and Performance Monitoring Dashboard\n\nComprehensive analytics system with real-time monitoring, performance metrics,\ntrend analysis, and interactive dashboard capabilities.\n'
import json
import time
import logging
import threading
import statistics
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque, defaultdict
import sqlite3
import hashlib
logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    value: float
    tags: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Performance metrics for a component"""
    component_name: str
    response_times: List[float]
    success_rate: float
    error_rate: float
    throughput: float
    memory_usage: float
    cpu_usage: float
    last_updated: float

    def __post_init__(self):
        if not self.response_times:
            self.response_times = []

@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    metric_name: str
    condition: str
    threshold: float
    severity: str
    enabled: bool
    cooldown_period: float
    last_triggered: float = 0.0

class MetricsCollector:
    """Collects and stores metrics data"""

    def __init__(self, db_path: str='analytics.db'):
        self.db_path = Path(db_path)
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda : deque(maxlen=1000))
        self._lock = threading.RLock()
        self._init_database()
        self._start_flush_thread()

    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('\n                    CREATE TABLE IF NOT EXISTS metrics (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        metric_name TEXT,\n                        timestamp REAL,\n                        value REAL,\n                        tags TEXT,\n                        metadata TEXT\n                    )\n                ')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_metric_name ON metrics(metric_name)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_metric_timestamp ON metrics(metric_name, timestamp)')
                conn.execute('\n                    CREATE TABLE IF NOT EXISTS performance_metrics (\n                        id INTEGER PRIMARY KEY AUTOINCREMENT,\n                        component_name TEXT,\n                        timestamp REAL,\n                        response_times TEXT,\n                        success_rate REAL,\n                        error_rate REAL,\n                        throughput REAL,\n                        memory_usage REAL,\n                        cpu_usage REAL\n                    )\n                ')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_component_timestamp ON performance_metrics(component_name, timestamp)')
                conn.commit()
                logger.info('Analytics database initialized')
        except Exception as e:
            logger.error(f'Failed to initialize analytics database: {e}')

    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str]=None, metadata: Dict[str, Any]=None):
        """Record a metric value"""
        with self._lock:
            metric_point = MetricPoint(timestamp=time.time(), value=value, tags=tags or {}, metadata=metadata or {})
            self.metrics_buffer[metric_name].append(metric_point)

    def record_performance_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics for a component"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                response_times_json = json.dumps(metrics.response_times)
                conn.execute('\n                    INSERT INTO performance_metrics \n                    (component_name, timestamp, response_times, success_rate, \n                     error_rate, throughput, memory_usage, cpu_usage)\n                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n                ', (metrics.component_name, metrics.last_updated, response_times_json, metrics.success_rate, metrics.error_rate, metrics.throughput, metrics.memory_usage, metrics.cpu_usage))
                conn.commit()
        except Exception as e:
            logger.error(f'Failed to record performance metrics: {e}')

    @lru_cache(maxsize=128)
    def _flush_buffer(self):
        """Flush metrics buffer to database"""
        with self._lock:
            if not self.metrics_buffer:
                return
            try:
                with sqlite3.connect(self.db_path) as conn:
                    for (metric_name, points) in self.metrics_buffer.items():
                        for point in points:
                            tags_json = json.dumps(point.tags)
                            metadata_json = json.dumps(point.metadata)
                            conn.execute('\n                                INSERT INTO metrics \n                                (metric_name, timestamp, value, tags, metadata)\n                                VALUES (?, ?, ?, ?, ?)\n                            ', (metric_name, point.timestamp, point.value, tags_json, metadata_json))
                    conn.commit()
                    self.metrics_buffer.clear()
            except Exception as e:
                logger.error(f'Failed to flush metrics buffer: {e}')

    def _start_flush_thread(self):
        """Start background thread to flush metrics"""

        def flush_loop():
            while True:
                try:
                    self._flush_buffer()
                    time.sleep(30)
                except Exception as e:
                    logger.error(f'Error in flush thread: {e}')
                    time.sleep(10)
        thread = threading.Thread(target=flush_loop, daemon=True)
        thread.start()

    def get_metrics(self, metric_name: str, start_time: float=None, end_time: float=None, limit: int=1000) -> List[MetricPoint]:
        """Get metrics for a specific name"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = 'SELECT timestamp, value, tags, metadata FROM metrics WHERE metric_name = ?'
                params = [metric_name]
                if start_time:
                    query += ' AND timestamp >= ?'
                    params.append(start_time)
                if end_time:
                    query += ' AND timestamp <= ?'
                    params.append(end_time)
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                cursor = conn.execute(query, params)
                results = []
                for row in cursor:
                    (timestamp, value, tags_json, metadata_json) = row
                    tags = json.loads(tags_json) if tags_json else {}
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    results.append(MetricPoint(timestamp=timestamp, value=value, tags=tags, metadata=metadata))
                return results
        except Exception as e:
            logger.error(f'Failed to get metrics: {e}')
            return []

    def get_performance_metrics(self, component_name: str, start_time: float=None, end_time: float=None) -> List[PerformanceMetrics]:
        """Get performance metrics for a component"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = 'SELECT * FROM performance_metrics WHERE component_name = ?'
                params = [component_name]
                if start_time:
                    query += ' AND timestamp >= ?'
                    params.append(start_time)
                if end_time:
                    query += ' AND timestamp <= ?'
                    params.append(end_time)
                query += ' ORDER BY timestamp DESC'
                cursor = conn.execute(query, params)
                results = []
                for row in cursor:
                    (_, comp_name, timestamp, response_times_json, success_rate, error_rate, throughput, memory_usage, cpu_usage) = row
                    response_times = json.loads(response_times_json) if response_times_json else []
                    results.append(PerformanceMetrics(component_name=comp_name, response_times=response_times, success_rate=success_rate, error_rate=error_rate, throughput=throughput, memory_usage=memory_usage, cpu_usage=cpu_usage, last_updated=timestamp))
                return results
        except Exception as e:
            logger.error(f'Failed to get performance metrics: {e}')
            return []

class AlertManager:
    """Manages alert rules and notifications"""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict] = []
        self.notification_handlers: List[Callable] = []
        self._lock = threading.RLock()

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        with self._lock:
            self.alert_rules[rule.name] = rule
            logger.info(f'Added alert rule: {rule.name}')

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        with self._lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                logger.info(f'Removed alert rule: {rule_name}')

    def check_alerts(self, metric_name: str, value: float):
        """Check if any alerts should be triggered"""
        current_time = time.time()
        with self._lock:
            for rule in self.alert_rules.values():
                if not rule.enabled or rule.metric_name != metric_name:
                    continue
                if current_time - rule.last_triggered < rule.cooldown_period:
                    continue
                triggered = False
                if rule.condition == 'gt' and value > rule.threshold:
                    triggered = True
                elif rule.condition == 'lt' and value < rule.threshold:
                    triggered = True
                elif rule.condition == 'eq' and value == rule.threshold:
                    triggered = True
                elif rule.condition == 'gte' and value >= rule.threshold:
                    triggered = True
                elif rule.condition == 'lte' and value <= rule.threshold:
                    triggered = True
                if triggered:
                    self._trigger_alert(rule, value, current_time)

    def _trigger_alert(self, rule: AlertRule, value: float, timestamp: float):
        """Trigger an alert"""
        alert = {'rule_name': rule.name, 'metric_name': rule.metric_name, 'value': value, 'threshold': rule.threshold, 'condition': rule.condition, 'severity': rule.severity, 'timestamp': timestamp, 'message': f'Alert: {rule.name} - {rule.metric_name} is {value} (threshold: {rule.threshold})'}
        self.alert_history.append(alert)
        rule.last_triggered = timestamp
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f'Notification handler failed: {e}')
        logger.warning(alert['message'])

    def add_notification_handler(self, handler: Callable):
        """Add a notification handler"""
        self.notification_handlers.append(handler)

    def get_alert_history(self, limit: int=100) -> List[Dict]:
        """Get recent alert history"""
        with self._lock:
            return self.alert_history[-limit:]

class TrendAnalyzer:
    """Analyzes trends in metrics data"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    def calculate_trend(self, metric_name: str, window_hours: int=24) -> Dict[str, Any]:
        """Calculate trend for a metric over a time window"""
        end_time = time.time()
        start_time = end_time - window_hours * 3600
        metrics = self.metrics_collector.get_metrics(metric_name, start_time, end_time, limit=10000)
        if len(metrics) < 2:
            return {'trend': 'insufficient_data', 'slope': 0.0, 'correlation': 0.0, 'data_points': len(metrics)}
        metrics.sort(key=lambda x: x.timestamp)
        values = [m.value for m in metrics]
        timestamps = [m.timestamp for m in metrics]
        start_timestamp = timestamps[0]
        normalized_times = [(t - start_timestamp) / 3600 for t in timestamps]
        n = len(values)
        sum_x = sum(normalized_times)
        sum_y = sum(values)
        sum_xy = sum((x * y for (x, y) in zip(normalized_times, values)))
        sum_x2 = sum((x * x for x in normalized_times))
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        mean_x = sum_x / n
        mean_y = sum_y / n
        numerator = sum(((x - mean_x) * (y - mean_y) for (x, y) in zip(normalized_times, values)))
        sum_sq_x = sum(((x - mean_x) ** 2 for x in normalized_times))
        sum_sq_y = sum(((y - mean_y) ** 2 for y in values))
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        correlation = numerator / denominator if denominator != 0 else 0
        if abs(slope) < 0.01:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        return {'trend': trend, 'slope': slope, 'correlation': correlation, 'data_points': len(metrics), 'time_window_hours': window_hours, 'avg_value': statistics.mean(values), 'min_value': min(values), 'max_value': max(values), 'std_dev': statistics.stdev(values) if len(values) > 1 else 0}

    def detect_anomalies(self, metric_name: str, window_hours: int=24, threshold_std: float=2.0) -> List[Dict]:
        """Detect anomalies in metrics data"""
        end_time = time.time()
        start_time = end_time - window_hours * 3600
        metrics = self.metrics_collector.get_metrics(metric_name, start_time, end_time, limit=10000)
        if len(metrics) < 10:
            return []
        values = [m.value for m in metrics]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        anomalies = []
        for metric in metrics:
            z_score = abs((metric.value - mean_val) / std_val) if std_val > 0 else 0
            if z_score > threshold_std:
                anomalies.append({'timestamp': metric.timestamp, 'value': metric.value, 'z_score': z_score, 'deviation_from_mean': metric.value - mean_val, 'severity': 'high' if z_score > 3 else 'medium'})
        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)

class AdvancedAnalyticsDashboard:
    """Main analytics dashboard system"""

    def __init__(self, config_path: str='analytics_config.json'):
        self.config_path = Path(config_path)
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.trend_analyzer = TrendAnalyzer(self.metrics_collector)
        self.component_metrics: Dict[str, PerformanceMetrics] = {}
        self.dashboard_enabled = True
        self.auto_alerts_enabled = True
        self._lock = threading.RLock()
        self._load_config()
        self._start_monitoring()
        self._initialize_default_alerts()

    def _load_config(self):
        """Load analytics configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.dashboard_enabled = config.get('dashboard_enabled', True)
                    self.auto_alerts_enabled = config.get('auto_alerts_enabled', True)
                    for rule_data in config.get('alert_rules', []):
                        rule = AlertRule(**rule_data)
                        self.alert_manager.add_alert_rule(rule)
                logger.info('Analytics configuration loaded')
        except Exception as e:
            logger.warning(f'Could not load analytics config: {e}')

    def _save_config(self):
        """Save analytics configuration"""
        try:
            config = {'dashboard_enabled': self.dashboard_enabled, 'auto_alerts_enabled': self.auto_alerts_enabled, 'alert_rules': [asdict(rule) for rule in self.alert_manager.alert_rules.values()]}
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f'Could not save analytics config: {e}')

    def _initialize_default_alerts(self):
        """Initialize default alert rules"""
        default_rules = [AlertRule(name='High Error Rate', metric_name='error_rate', condition='gt', threshold=0.1, severity='high', enabled=True, cooldown_period=300), AlertRule(name='Low Success Rate', metric_name='success_rate', condition='lt', threshold=0.8, severity='medium', enabled=True, cooldown_period=300), AlertRule(name='High Response Time', metric_name='avg_response_time', condition='gt', threshold=10.0, severity='medium', enabled=True, cooldown_period=300), AlertRule(name='High Memory Usage', metric_name='memory_usage', condition='gt', threshold=1000, severity='high', enabled=True, cooldown_period=600)]
        for rule in default_rules:
            if rule.name not in self.alert_manager.alert_rules:
                self.alert_manager.add_alert_rule(rule)

    def record_component_metrics(self, component_name: str, response_time: float, success: bool, memory_usage: float=0, cpu_usage: float=0):
        """Record metrics for a component"""
        with self._lock:
            if component_name not in self.component_metrics:
                self.component_metrics[component_name] = PerformanceMetrics(component_name=component_name, response_times=[], success_rate=1.0, error_rate=0.0, throughput=0.0, memory_usage=memory_usage, cpu_usage=cpu_usage, last_updated=time.time())
            metrics = self.component_metrics[component_name]
            metrics.response_times.append(response_time)
            if len(metrics.response_times) > 100:
                metrics.response_times = metrics.response_times[-100:]
            total_requests = len(metrics.response_times)
            successful_requests = sum((1 for rt in metrics.response_times if rt > 0))
            metrics.success_rate = successful_requests / total_requests
            metrics.error_rate = 1.0 - metrics.success_rate
            metrics.memory_usage = memory_usage
            metrics.cpu_usage = cpu_usage
            metrics.last_updated = time.time()
            one_minute_ago = time.time() - 60
            recent_requests = len([rt for rt in metrics.response_times if rt > 0])
            metrics.throughput = recent_requests / 60.0
            self.metrics_collector.record_metric(f'{component_name}_response_time', response_time)
            self.metrics_collector.record_metric(f'{component_name}_success_rate', metrics.success_rate)
            self.metrics_collector.record_metric(f'{component_name}_error_rate', metrics.error_rate)
            self.metrics_collector.record_metric(f'{component_name}_throughput', metrics.throughput)
            self.metrics_collector.record_metric(f'{component_name}_memory_usage', memory_usage)
            self.metrics_collector.record_metric(f'{component_name}_cpu_usage', cpu_usage)
            if self.auto_alerts_enabled:
                self.alert_manager.check_alerts(f'{component_name}_success_rate', metrics.success_rate)
                self.alert_manager.check_alerts(f'{component_name}_error_rate', metrics.error_rate)
                self.alert_manager.check_alerts(f'{component_name}_response_time', response_time)
                self.alert_manager.check_alerts(f'{component_name}_memory_usage', memory_usage)
            if total_requests % 10 == 0:
                self.metrics_collector.record_performance_metrics(metrics)

    def _start_monitoring(self):
        """Start background monitoring"""

        def monitoring_loop():
            while True:
                try:
                    current_time = time.time()
                    components_to_remove = []
                    for (name, metrics) in self.component_metrics.items():
                        if current_time - metrics.last_updated > 3600:
                            components_to_remove.append(name)
                    for name in components_to_remove:
                        del self.component_metrics[name]
                    time.sleep(60)
                except Exception as e:
                    logger.error(f'Error in monitoring loop: {e}')
                    time.sleep(30)
        thread = threading.Thread(target=monitoring_loop, daemon=True)
        thread.start()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        with self._lock:
            component_overview = {}
            for (name, metrics) in self.component_metrics.items():
                component_overview[name] = {'success_rate': metrics.success_rate, 'error_rate': metrics.error_rate, 'avg_response_time': statistics.mean(metrics.response_times) if metrics.response_times else 0, 'throughput': metrics.throughput, 'memory_usage': metrics.memory_usage, 'cpu_usage': metrics.cpu_usage, 'last_updated': metrics.last_updated}
            recent_alerts = self.alert_manager.get_alert_history(20)
            if self.component_metrics:
                avg_success_rate = statistics.mean([m.success_rate for m in self.component_metrics.values()])
                avg_response_time = statistics.mean([statistics.mean(m.response_times) if m.response_times else 0 for m in self.component_metrics.values()])
                health_score = avg_success_rate * 0.6 + min(1.0, 5.0 / max(0.1, avg_response_time)) * 0.4
            else:
                health_score = 1.0
            return {'timestamp': time.time(), 'health_score': health_score, 'component_overview': component_overview, 'recent_alerts': recent_alerts, 'total_components': len(self.component_metrics), 'dashboard_enabled': self.dashboard_enabled, 'auto_alerts_enabled': self.auto_alerts_enabled}

    def get_component_trends(self, component_name: str) -> Dict[str, Any]:
        """Get trend analysis for a component"""
        trends = {}
        for metric_type in ['response_time', 'success_rate', 'error_rate', 'throughput']:
            metric_name = f'{component_name}_{metric_type}'
            trend = self.trend_analyzer.calculate_trend(metric_name)
            trends[metric_type] = trend
        return trends

    def get_component_anomalies(self, component_name: str) -> Dict[str, List[Dict]]:
        """Get anomaly detection for a component"""
        anomalies = {}
        for metric_type in ['response_time', 'success_rate', 'error_rate', 'throughput']:
            metric_name = f'{component_name}_{metric_type}'
            metric_anomalies = self.trend_analyzer.detect_anomalies(metric_name)
            anomalies[metric_type] = metric_anomalies
        return anomalies

    def get_system_summary(self) -> Dict[str, Any]:
        """Get system-wide summary"""
        with self._lock:
            if not self.component_metrics:
                return {'total_components': 0, 'avg_success_rate': 0, 'avg_response_time': 0, 'total_throughput': 0, 'total_memory_usage': 0, 'avg_cpu_usage': 0, 'health_score': 1.0}
            success_rates = [m.success_rate for m in self.component_metrics.values()]
            response_times = [statistics.mean(m.response_times) if m.response_times else 0 for m in self.component_metrics.values()]
            throughputs = [m.throughput for m in self.component_metrics.values()]
            memory_usages = [m.memory_usage for m in self.component_metrics.values()]
            cpu_usages = [m.cpu_usage for m in self.component_metrics.values()]
            avg_success_rate = statistics.mean(success_rates)
            avg_response_time = statistics.mean(response_times)
            total_throughput = sum(throughputs)
            total_memory_usage = sum(memory_usages)
            avg_cpu_usage = statistics.mean(cpu_usages)
            health_score = avg_success_rate * 0.6 + min(1.0, 5.0 / max(0.1, avg_response_time)) * 0.4
            return {'total_components': len(self.component_metrics), 'avg_success_rate': avg_success_rate, 'avg_response_time': avg_response_time, 'total_throughput': total_throughput, 'total_memory_usage': total_memory_usage, 'avg_cpu_usage': avg_cpu_usage, 'health_score': health_score, 'timestamp': time.time()}

    def enable_dashboard(self):
        """Enable the dashboard"""
        self.dashboard_enabled = True
        logger.info('Analytics dashboard enabled')

    def disable_dashboard(self):
        """Disable the dashboard"""
        self.dashboard_enabled = False
        logger.info('Analytics dashboard disabled')

    def enable_auto_alerts(self):
        """Enable automatic alerts"""
        self.auto_alerts_enabled = True
        logger.info('Auto alerts enabled')

    def disable_auto_alerts(self):
        """Disable automatic alerts"""
        self.auto_alerts_enabled = False
        logger.info('Auto alerts disabled')
_analytics_dashboard = None

def get_analytics_dashboard() -> AdvancedAnalyticsDashboard:
    """Get the global analytics dashboard instance"""
    global _analytics_dashboard
    if _analytics_dashboard is None:
        _analytics_dashboard = AdvancedAnalyticsDashboard()
    return _analytics_dashboard