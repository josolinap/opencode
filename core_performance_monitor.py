# Core Performance Monitor - Essential performance tracking
# Author: MiniMax Agent
# Created: 2025-11-14

import psutil
import time
import json
from datetime import datetime
from typing import Dict, Any

class CorePerformanceMonitor:
    def __init__(self):
        self.metrics = []
        
    def get_current_metrics(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent
        }
        
    def record_model_performance(self, model_name: str, response_time: float, success: bool):
        self.metrics.append({
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "response_time": response_time,
            "success": success
        })
        
    def get_performance_summary(self) -> Dict[str, Any]:
        current = self.get_current_metrics()
        
        model_metrics = self.metrics
        avg_response_time = 0
        success_rate = 100
        
        if model_metrics:
            avg_response_time = sum(m["response_time"] for m in model_metrics) / len(model_metrics)
            success_count = sum(1 for m in model_metrics if m["success"])
            success_rate = (success_count / len(model_metrics)) * 100
            
        health_score = 100
        if current["cpu_percent"] > 80: health_score -= 20
        if current["memory_percent"] > 85: health_score -= 20
        if avg_response_time > 3.0: health_score -= 15
        
        return {
            "system": current,
            "models": {
                "avg_response_time": avg_response_time,
                "success_rate": success_rate,
                "total_requests": len(model_metrics)
            },
            "health_score": max(0, health_score)
        }

_monitor = CorePerformanceMonitor()
def get_monitor():
    return _monitor
