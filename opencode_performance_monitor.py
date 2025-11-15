#!/usr/bin/env python3
"""
OpenCode Performance Monitor
============================

Real-time performance monitoring dashboard for the unified OpenCode system.
Displays system metrics, skill execution statistics, and model performance.

Author: MiniMax Agent
Version: 3.0
"""

import time
import threading
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemMetric:
    """System performance metric"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    thread_count: int

@dataclass
class SkillMetric:
    """Skill execution metric"""
    timestamp: datetime
    skill_name: str
    duration: float
    success: bool
    error_message: Optional[str] = None
    retry_count: int = 0

@dataclass
class ModelMetric:
    """Model performance metric"""
    timestamp: datetime
    model_name: str
    provider: str
    response_time: float
    success: bool
    context_length: int
    tokens_used: int = 0

class PerformanceMonitor:
    """
    Real-time performance monitoring system
    """
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        
        # Metrics storage
        self.system_metrics: deque = deque(maxlen=max_history_size)
        self.skill_metrics: deque = deque(maxlen=max_history_size)
        self.model_metrics: deque = deque(maxlen=max_history_size)
        
        # Current monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitoring_interval = 1.0  # seconds
        
        # Network baseline for delta calculations
        self.last_network = None
        
        # Performance counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
    def start_monitoring(self):
        """Start the performance monitoring"""
        if self.is_monitoring:
            logger.warning("Performance monitoring already running")
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
        
    def stop_monitoring(self):
        """Stop the performance monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Performance monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                metric = self._collect_system_metric()
                with self._lock:
                    self.system_metrics.append(metric)
                    
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
                
    def _collect_system_metric(self) -> SystemMetric:
        """Collect current system metrics"""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv
        
        # Process info
        process = psutil.Process()
        process_count = len(psutil.pids())
        thread_count = process.num_threads()
        
        return SystemMetric(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_total_gb=memory.total / (1024**3),
            disk_percent=disk.percent,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            process_count=process_count,
            thread_count=thread_count
        )
        
    def record_skill_execution(self, skill_name: str, duration: float, success: bool, 
                              error_message: Optional[str] = None, retry_count: int = 0):
        """Record skill execution metrics"""
        with self._lock:
            self.skill_metrics.append(SkillMetric(
                timestamp=datetime.now(),
                skill_name=skill_name,
                duration=duration,
                success=success,
                error_message=error_message,
                retry_count=retry_count
            ))
            
            # Update counters
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
    def record_model_performance(self, model_name: str, provider: str, response_time: float,
                                success: bool, context_length: int, tokens_used: int = 0):
        """Record model performance metrics"""
        with self._lock:
            self.model_metrics.append(ModelMetric(
                timestamp=datetime.now(),
                model_name=model_name,
                provider=provider,
                response_time=response_time,
                success=success,
                context_length=context_length,
                tokens_used=tokens_used
            ))
            
    def get_current_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        with self._lock:
            if not self.system_metrics:
                return {"error": "No metrics available"}
                
            latest = self.system_metrics[-1]
            
            # Calculate trends if we have enough data
            trends = self._calculate_trends()
            
            return {
                "timestamp": latest.timestamp.isoformat(),
                "cpu": {
                    "percent": latest.cpu_percent,
                    "trend": trends.get("cpu_trend", 0)
                },
                "memory": {
                    "percent": latest.memory_percent,
                    "used_gb": latest.memory_used_gb,
                    "total_gb": latest.memory_total_gb,
                    "trend": trends.get("memory_trend", 0)
                },
                "disk": {
                    "percent": latest.disk_percent
                },
                "network": {
                    "bytes_sent": latest.network_bytes_sent,
                    "bytes_recv": latest.network_bytes_recv,
                    "trend_sent": trends.get("network_sent_trend", 0),
                    "trend_recv": trends.get("network_recv_trend", 0)
                },
                "processes": {
                    "count": latest.process_count,
                    "threads": latest.thread_count
                },
                "monitoring": {
                    "active": self.is_monitoring,
                    "total_metrics": len(self.system_metrics)
                }
            }
            
    def _calculate_trends(self) -> Dict[str, float]:
        """Calculate trends from recent metrics"""
        if len(self.system_metrics) < 10:
            return {}
            
        recent = list(self.system_metrics)[-10:]
        
        # Calculate trend slopes
        cpu_trend = self._calculate_slope([m.cpu_percent for m in recent])
        memory_trend = self._calculate_slope([m.memory_percent for m in recent])
        network_sent_trend = self._calculate_slope([m.network_bytes_sent for m in recent])
        network_recv_trend = self._calculate_slope([m.network_bytes_recv for m in recent])
        
        return {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "network_sent_trend": network_sent_trend,
            "network_recv_trend": network_recv_trend
        }
        
    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate simple slope of values over time"""
        if len(values) < 2:
            return 0.0
            
        n = len(values)
        x = list(range(n))
        
        # Simple linear regression slope
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(xi * yi for xi, yi in zip(x, values))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
            
        return (n * sum_xy - sum_x * sum_y) / denominator
        
    def get_skill_performance(self, time_window_minutes: int = 30) -> Dict[str, Any]:
        """Get skill performance statistics for recent time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            recent_skills = [m for m in self.skill_metrics if m.timestamp >= cutoff_time]
            
            if not recent_skills:
                return {"message": "No skill executions in the specified time window"}
                
            # Group by skill name
            skill_stats = defaultdict(lambda: {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "errors": []
            })
            
            for metric in recent_skills:
                stats = skill_stats[metric.skill_name]
                stats["executions"] += 1
                stats["total_duration"] += metric.duration
                
                if metric.success:
                    stats["successes"] += 1
                else:
                    stats["failures"] += 1
                    if metric.error_message:
                        stats["errors"].append(metric.error_message)
                        
            # Calculate averages
            for skill_name, stats in skill_stats.items():
                if stats["executions"] > 0:
                    stats["avg_duration"] = stats["total_duration"] / stats["executions"]
                    stats["success_rate"] = (stats["successes"] / stats["executions"]) * 100
                    
            return {
                "time_window_minutes": time_window_minutes,
                "total_executions": len(recent_skills),
                "unique_skills": len(skill_stats),
                "skills": dict(skill_stats)
            }
            
    def get_model_performance(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get model performance statistics"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            recent_models = [m for m in self.model_metrics if m.timestamp >= cutoff_time]
            
            if not recent_models:
                return {"message": "No model calls in the specified time window"}
                
            # Group by model
            model_stats = defaultdict(lambda: {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "total_tokens": 0,
                "providers": set()
            })
            
            for metric in recent_models:
                stats = model_stats[metric.model_name]
                stats["calls"] += 1
                stats["total_response_time"] += metric.response_time
                stats["total_tokens"] += metric.tokens_used
                stats["providers"].add(metric.provider)
                
                if metric.success:
                    stats["successes"] += 1
                else:
                    stats["failures"] += 1
                    
            # Calculate averages
            for model_name, stats in model_stats.items():
                if stats["calls"] > 0:
                    stats["avg_response_time"] = stats["total_response_time"] / stats["calls"]
                    stats["success_rate"] = (stats["successes"] / stats["calls"]) * 100
                    stats["provider_list"] = list(stats["providers"])
                    del stats["providers"]  # Remove set for JSON serialization
                    
            return {
                "time_window_minutes": time_window_minutes,
                "total_calls": len(recent_models),
                "unique_models": len(model_stats),
                "models": dict(model_stats)
            }
            
    def get_overall_performance(self) -> Dict[str, Any]:
        """Get overall system performance summary"""
        with self._lock:
            success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
            
            # Recent metrics (last 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            recent_metrics = [m for m in self.skill_metrics if m.timestamp >= cutoff_time]
            
            avg_response_time = 0.0
            if recent_metrics:
                avg_response_time = sum(m.duration for m in recent_metrics) / len(recent_metrics)
                
            # System health assessment
            if not self.system_metrics:
                health_status = "unknown"
            else:
                latest = self.system_metrics[-1]
                if latest.cpu_percent > 90 or latest.memory_percent > 90:
                    health_status = "critical"
                elif latest.cpu_percent > 70 or latest.memory_percent > 70:
                    health_status = "warning"
                else:
                    health_status = "healthy"
                    
            return {
                "timestamp": datetime.now().isoformat(),
                "request_statistics": {
                    "total_requests": self.total_requests,
                    "successful_requests": self.successful_requests,
                    "failed_requests": self.failed_requests,
                    "success_rate": success_rate
                },
                "recent_performance": {
                    "requests_last_5_min": len(recent_metrics),
                    "avg_response_time": avg_response_time
                },
                "system_health": health_status,
                "monitoring_status": {
                    "active": self.is_monitoring,
                    "uptime": datetime.now().isoformat(),
                    "metrics_collected": len(self.system_metrics)
                }
            }
            
    def export_metrics(self, filename: str, format: str = "json"):
        """Export metrics to file"""
        with self._lock:
            data = {
                "export_timestamp": datetime.now().isoformat(),
                "system_metrics": [asdict(m) for m in self.system_metrics],
                "skill_metrics": [asdict(m) for m in self.skill_metrics],
                "model_metrics": [asdict(m) for m in self.model_metrics],
                "summary": self.get_overall_performance()
            }
            
            # Convert datetime objects to strings for JSON
            for metric_list in [data["system_metrics"], data["skill_metrics"], data["model_metrics"]]:
                for metric in metric_list:
                    if "timestamp" in metric:
                        metric["timestamp"] = metric["timestamp"].isoformat()
                        
        if format.lower() == "json":
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            logger.warning(f"Export format '{format}' not supported, using JSON")
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
        logger.info(f"Metrics exported to {filename}")
        
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on thresholds"""
        alerts = []
        
        if not self.system_metrics:
            return alerts
            
        latest = self.system_metrics[-1]
        
        # CPU alert
        if latest.cpu_percent > 85:
            alerts.append({
                "type": "cpu_high",
                "message": f"CPU usage is high: {latest.cpu_percent:.1f}%",
                "severity": "warning" if latest.cpu_percent < 95 else "critical",
                "timestamp": latest.timestamp.isoformat()
            })
            
        # Memory alert
        if latest.memory_percent > 85:
            alerts.append({
                "type": "memory_high",
                "message": f"Memory usage is high: {latest.memory_percent:.1f}%",
                "severity": "warning" if latest.memory_percent < 95 else "critical",
                "timestamp": latest.timestamp.isoformat()
            })
            
        # Disk alert
        if latest.disk_percent > 90:
            alerts.append({
                "type": "disk_high",
                "message": f"Disk usage is high: {latest.disk_percent:.1f}%",
                "severity": "critical",
                "timestamp": latest.timestamp.isoformat()
            })
            
        # Skill error rate alert
        with self._lock:
            recent_skills = [m for m in self.skill_metrics if m.timestamp >= datetime.now() - timedelta(minutes=10)]
            if len(recent_skills) > 5:
                error_count = sum(1 for m in recent_skills if not m.success)
                error_rate = (error_count / len(recent_skills)) * 100
                if error_rate > 20:
                    alerts.append({
                        "type": "skill_error_rate",
                        "message": f"High skill error rate: {error_rate:.1f}%",
                        "severity": "warning" if error_rate < 50 else "critical",
                        "timestamp": datetime.now().isoformat()
                    })
                    
        return alerts

class PerformanceDashboard:
    """
    TUI-based performance dashboard
    """
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.running = False
        
    def start_dashboard(self):
        """Start the performance dashboard"""
        self.running = True
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        print("🚀 OpenCode Performance Dashboard v3.0")
        print("=" * 50)
        print("Real-time performance monitoring active")
        print("Commands: status, metrics, alerts, export, quit")
        print("=" * 50)
        
        try:
            while self.running:
                try:
                    command = input("\n> ").strip().lower()
                    
                    if command == 'quit':
                        break
                    elif command == 'status':
                        self._show_status()
                    elif command == 'metrics':
                        self._show_metrics()
                    elif command == 'alerts':
                        self._show_alerts()
                    elif command == 'export':
                        self._export_metrics()
                    elif command == 'help':
                        self._show_help()
                    elif command:
                        self._show_live_update()
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    
        finally:
            self.monitor.stop_monitoring()
            print("👋 Dashboard closed")
            
    def _show_status(self):
        """Show current system status"""
        status = self.monitor.get_current_system_status()
        perf = self.monitor.get_overall_performance()
        
        print("\n📊 SYSTEM STATUS")
        print("-" * 30)
        print(f"CPU: {status['cpu']['percent']:.1f}% (trend: {status['cpu']['trend']:+.2f})")
        print(f"Memory: {status['memory']['percent']:.1f}% ({status['memory']['used_gb']:.1f}GB / {status['memory']['total_gb']:.1f}GB)")
        print(f"Disk: {status['disk']['percent']:.1f}%")
        print(f"Processes: {status['processes']['count']} (threads: {status['processes']['threads']})")
        
        print(f"\n⚡ PERFORMANCE")
        print("-" * 30)
        print(f"Total Requests: {perf['request_statistics']['total_requests']}")
        print(f"Success Rate: {perf['request_statistics']['success_rate']:.1f}%")
        print(f"System Health: {perf['system_health'].upper()}")
        
    def _show_metrics(self):
        """Show detailed metrics"""
        skill_perf = self.monitor.get_skill_performance(30)
        model_perf = self.monitor.get_model_performance(60)
        
        print("\n🔧 SKILL PERFORMANCE (Last 30 min)")
        print("-" * 30)
        if "skills" in skill_perf:
            for skill_name, stats in list(skill_perf["skills"].items())[:5]:
                print(f"{skill_name}: {stats['executions']} executions, {stats['success_rate']:.1f}% success")
        else:
            print("No skill data available")
            
        print("\n🤖 MODEL PERFORMANCE (Last 60 min)")
        print("-" * 30)
        if "models" in model_perf:
            for model_name, stats in list(model_perf["models"].items())[:5]:
                print(f"{model_name}: {stats['calls']} calls, {stats['success_rate']:.1f}% success")
        else:
            print("No model data available")
            
    def _show_alerts(self):
        """Show performance alerts"""
        alerts = self.monitor.get_performance_alerts()
        
        print("\n🚨 PERFORMANCE ALERTS")
        print("-" * 30)
        if alerts:
            for alert in alerts:
                icon = "⚠️" if alert["severity"] == "warning" else "🛑"
                print(f"{icon} {alert['message']}")
        else:
            print("✅ No performance alerts")
            
    def _export_metrics(self):
        """Export metrics to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"opencode_metrics_{timestamp}.json"
        
        self.monitor.export_metrics(filename)
        print(f"✅ Metrics exported to {filename}")
        
    def _show_live_update(self):
        """Show live system update"""
        status = self.monitor.get_current_system_status()
        perf = self.monitor.get_overall_performance()
        
        print(f"\n🔄 LIVE UPDATE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"CPU: {status['cpu']['percent']:.1f}% | Memory: {status['memory']['percent']:.1f}%")
        print(f"Requests: {perf['request_statistics']['total_requests']} | Success: {perf['request_statistics']['success_rate']:.1f}%")
        
    def _show_help(self):
        """Show help information"""
        print("\n📚 HELP")
        print("-" * 30)
        print("Commands:")
        print("  status   - Show current system status")
        print("  metrics  - Show skill and model performance")
        print("  alerts   - Show performance alerts")
        print("  export   - Export metrics to file")
        print("  quit     - Exit dashboard")
        print("\nMonitoring features:")
        print("  • Real-time CPU, memory, disk monitoring")
        print("  • Skill execution tracking")
        print("  • Model performance analysis")
        print("  • Automated alerting")

# Integration with the unified brain system
class BrainPerformanceIntegration:
    """
    Integration layer between the unified brain and performance monitoring
    """
    
    def __init__(self, brain, monitor: PerformanceMonitor):
        self.brain = brain
        self.monitor = monitor
        
    def wrap_skill_execution(self, skill_name: str, skill_function, *args, **kwargs):
        """Wrap skill execution with performance monitoring"""
        start_time = time.time()
        
        try:
            result = skill_function(*args, **kwargs)
            duration = time.time() - start_time
            
            self.monitor.record_skill_execution(skill_name, duration, True)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.monitor.record_skill_execution(skill_name, duration, False, str(e))
            raise
            
    def wrap_model_call(self, model_name: str, provider: str, model_function, *args, **kwargs):
        """Wrap model call with performance monitoring"""
        start_time = time.time()
        
        try:
            result = model_function(*args, **kwargs)
            duration = time.time() - start_time
            
            # Extract context length if available
            context_length = kwargs.get('max_tokens', 1024)
            
            self.monitor.record_model_performance(
                model_name, provider, duration, True, context_length
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.monitor.record_model_performance(
                model_name, provider, duration, False, context_length
            )
            raise

# Main execution
if __name__ == "__main__":
    dashboard = PerformanceDashboard()
    dashboard.start_dashboard()