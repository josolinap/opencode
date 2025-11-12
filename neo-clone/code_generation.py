"""
Code Generation Skill for Neo-Clone
Advanced code generation with OpenCode integration for creating complex AI systems.
"""

from skills import BaseSkill, SkillResult
from collections import OrderedDict
from functools import lru_cache
import hashlib
import logging
import re

logger = logging.getLogger(__name__)

class CodeGenerationSkill(BaseSkill):

    def __init__(self):
        super().__init__(
            name='code_generation',
            description='Advanced code generation with OpenCode integration for creating complex AI systems.',
            example='Generate an autonomous intelligence system with self-learning capabilities.'
        )
        self._cache = OrderedDict()
        self._max_cache_size = 100

    @property
    def parameters(self):
        return {
            'prompt': 'string - The code generation request',
            'language': 'string - Programming language (default: python). Supported: python, javascript, typescript',
            'style': 'string - Code style (default: professional)',
            'include_comments': 'boolean - Include comments (default: true)',
            'use_guidance': 'boolean - Use constrained generation with Guidance (default: true)'
        }

    def execute(self, params):
        """Execute code generation with given parameters"""
        try:
            prompt = params.get('prompt', 'Create a simple Python function')
            language = params.get('language', 'python')
            style = params.get('style', 'professional')
            include_comments = params.get('include_comments', True)
            use_guidance = params.get('use_guidance', True)

            # Generate cache key
            cache_key = hashlib.md5(f'{prompt}_{language}_{style}_{include_comments}_{use_guidance}'.encode()).hexdigest()
            
            # Check cache first
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                cached_result = self._cache[cache_key]
                cached_result['cached'] = True
                return SkillResult(True, cached_result.get('output', ''), cached_result)

            # Generate code
            generated_code = self._generate_code(prompt, language, style, include_comments)
            
            # Prepare result
            result = {
                'code': generated_code,
                'language': language,
                'style': style,
                'success': True,
                'cached': False
            }

            # Add to cache
            self._add_to_cache(cache_key, result)

            return SkillResult(True, f"Generated {language} code successfully", result)

        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            return SkillResult(False, f"Code generation failed: {str(e)}")

    def _generate_code(self, prompt, language='python', style='professional', include_comments=True):
        """Generate code based on prompt and language"""
        try:
            # Try to use enhanced OpenCode integration if available
            try:
                from enhanced_opencode_integration import EnhancedOpenCodeIntegration
                integration = EnhancedOpenCodeIntegration()
                
                full_prompt = f"""
Generate {style} {language} code for the following request:

Request: {prompt}

Requirements:
- Use modern {language} best practices
- Include proper error handling
- Add comprehensive comments
- Follow clean code principles
- Make it production-ready

Generate only the code with brief explanations.
"""
                
                result = integration.generate_response(prompt=full_prompt, model='opencode/big-pickle', max_tokens=1000)
                if result.get('success'):
                    return result.get('response', '')
            except ImportError:
                logger.warning("Enhanced OpenCode integration not available, using fallback")

            # Fallback to template-based generation
            return self._generate_template_code(prompt, language, style, include_comments)

        except Exception as e:
            logger.error(f"Code generation error: {str(e)}")
            return self._generate_fallback_code(prompt, language)

    def _generate_template_code(self, prompt, language='python', style='professional', include_comments=True):
        """Fallback template-based code generation"""
        prompt_lower = prompt.lower()
        
        if 'autonomous' in prompt_lower and 'intelligence' in prompt_lower:
            return self._generate_autonomous_intelligence_code(language)
        elif 'analytics' in prompt_lower or 'analysis' in prompt_lower:
            return self._generate_analytics_code(language)
        elif 'workflow' in prompt_lower:
            return self._generate_workflow_code(language)
        elif 'routing' in prompt_lower or 'router' in prompt_lower:
            return self._generate_routing_code(language)
        elif 'integration' in prompt_lower:
            return self._generate_integration_code(language)
        elif 'machine learning' in prompt_lower or 'ml' in prompt_lower:
            return self._generate_ml_code(language)
        else:
            return self._generate_general_code(prompt, language)

    def _generate_autonomous_intelligence_code(self, language='python'):
        """Generate autonomous intelligence system code"""
        if language == 'python':
            return '''
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LearningMetric:
    """Tracks learning metrics for continuous improvement"""
    timestamp: float
    task_type: str
    model_used: str
    success: bool
    response_time: float
    user_satisfaction: Optional[float] = None

class AutonomousIntelligence:
    """Self-learning AI system with continuous improvement"""

    def __init__(self):
        self.learning_metrics: List[LearningMetric] = []
        self.performance_patterns = {}
        self.context_memory = {}
        self.logger = logging.getLogger(__name__)

    def learn_from_interaction(self, task_type: str, model_used: str,
                              success: bool, response_time: float,
                              user_satisfaction: Optional[float] = None):
        """Learn from each interaction to improve performance"""
        metric = LearningMetric(
            timestamp=time.time(),
            task_type=task_type,
            model_used=model_used,
            success=success,
            response_time=response_time,
            user_satisfaction=user_satisfaction
        )
        self.learning_metrics.append(metric)
        self._update_performance_patterns()

    def _update_performance_patterns(self):
        """Update performance patterns based on accumulated metrics"""
        patterns = {}
        for metric in self.learning_metrics:
            key = f"{metric.task_type}_{metric.model_used}"
            if key not in patterns:
                patterns[key] = []
            patterns[key].append(metric)

        # Calculate optimal patterns
        for key, metrics in patterns.items():
            success_rate = sum(m.success for m in metrics) / len(metrics)
            avg_response_time = sum(m.response_time for m in metrics) / len(metrics)

            if success_rate > 0.8 and avg_response_time < 2.0:
                self.performance_patterns[key] = {
                    'success_rate': success_rate,
                    'avg_response_time': avg_response_time,
                    'confidence': min(len(metrics) / 10, 1.0)
                }

    def get_optimal_model(self, task_type: str) -> Optional[str]:
        """Get optimal model for a given task type"""
        candidates = []
        for pattern_key, pattern_data in self.performance_patterns.items():
            if task_type in pattern_key and pattern_data['confidence'] > 0.5:
                candidates.append((pattern_key, pattern_data))

        if candidates:
            best = max(candidates, key=lambda x: (x[1]['success_rate'], -x[1]['avg_response_time']))
            model = best[0].split('_')[-1]
            return model

        return None

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.learning_metrics:
            return {"status": "No data available"}

        total_interactions = len(self.learning_metrics)
        success_rate = sum(m.success for m in self.learning_metrics) / total_interactions
        avg_response_time = sum(m.response_time for m in self.learning_metrics) / total_interactions

        return {
            "total_interactions": total_interactions,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "performance_patterns": len(self.performance_patterns),
            "last_updated": datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    ai = AutonomousIntelligence()
    
    # Simulate learning from interactions
    ai.learn_from_interaction("code_generation", "gpt-4", True, 1.2, 0.9)
    ai.learn_from_interaction("text_analysis", "claude-3", True, 0.8, 0.85)
    
    # Get performance summary
    summary = ai.get_performance_summary()
    print(f"Performance summary: {summary}")
'''
        elif language == 'javascript':
            return '''
class LearningMetric {
    constructor(timestamp, taskType, modelUsed, success, responseTime, userSatisfaction = null) {
        this.timestamp = timestamp;
        this.taskType = taskType;
        this.modelUsed = modelUsed;
        this.success = success;
        this.responseTime = responseTime;
        this.userSatisfaction = userSatisfaction;
    }
}

class AutonomousIntelligence {
    constructor() {
        this.learningMetrics = [];
        this.performancePatterns = {};
        this.contextMemory = {};
    }

    learnFromInteraction(taskType, modelUsed, success, responseTime, userSatisfaction = null) {
        const metric = new LearningMetric(
            Date.now() / 1000,
            taskType,
            modelUsed,
            success,
            responseTime,
            userSatisfaction
        );
        this.learningMetrics.push(metric);
        this._updatePerformancePatterns();
    }

    _updatePerformancePatterns() {
        const patterns = {};
        for (const metric of this.learningMetrics) {
            const key = `${metric.taskType}_${metric.modelUsed}`;
            if (!patterns[key]) {
                patterns[key] = [];
            }
            patterns[key].push(metric);
        }

        for (const [key, metrics] of Object.entries(patterns)) {
            const successRate = metrics.filter(m => m.success).length / metrics.length;
            const avgResponseTime = metrics.reduce((sum, m) => sum + m.responseTime, 0) / metrics.length;

            if (successRate > 0.8 && avgResponseTime < 2.0) {
                this.performancePatterns[key] = {
                    successRate,
                    avgResponseTime,
                    confidence: Math.min(metrics.length / 10, 1.0)
                };
            }
        }
    }

    getOptimalModel(taskType) {
        const candidates = [];
        for (const [patternKey, patternData] of Object.entries(this.performancePatterns)) {
            if (patternKey.includes(taskType) && patternData.confidence > 0.5) {
                candidates.push([patternKey, patternData]);
            }
        }

        if (candidates.length > 0) {
            const best = candidates.reduce((a, b) => 
                (a[1].successRate > b[1].successRate || 
                (a[1].successRate === b[1].successRate && a[1].avgResponseTime < b[1].avgResponseTime)) ? a : b
            );
            return best[0].split('_').pop();
        }

        return null;
    }
}

// Example usage
const ai = new AutonomousIntelligence();
ai.learnFromInteraction("code_generation", "gpt-4", true, 1.2, 0.9);
console.log("Optimal model:", ai.getOptimalModel("code_generation"));
'''
        else:
            return self._generate_general_code("autonomous intelligence system", language)

    def _generate_analytics_code(self, language='python'):
        """Generate analytics system code"""
        if language == 'python':
            return '''
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    timestamp: float
    metric_name: str
    value: float
    tags: Dict[str, str]

class RealTimeAnalytics:
    """Real-time performance monitoring and analytics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.aggregates = defaultdict(list)
        self.alerts = []
        self.logger = logging.getLogger(__name__)
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_name=name,
            value=value,
            tags=tags or {}
        )
        self.metrics.append(metric)
        self.aggregates[name].append(metric)
        
        # Check for alerts
        self._check_alerts(name, value)
    
    def _check_alerts(self, name: str, value: float):
        """Check if metric triggers any alerts"""
        if name == "response_time" and value > 5.0:
            self.alerts.append({
                "timestamp": time.time(),
                "type": "high_response_time",
                "value": value,
                "severity": "warning"
            })
        
        if name == "error_rate" and value > 0.1:
            self.alerts.append({
                "timestamp": time.time(),
                "type": "high_error_rate", 
                "value": value,
                "severity": "critical"
            })
    
    def get_metrics_summary(self, time_window: Optional[float] = None) -> Dict[str, Any]:
        """Get summary of metrics within time window"""
        if time_window is None:
            time_window = 3600  # Default 1 hour
        
        cutoff_time = time.time() - time_window
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"status": "No recent metrics"}
        
        # Calculate statistics
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.metric_name].append(metric.value)
        
        summary = {}
        for name, values in metrics_by_name.items():
            summary[name] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1]
            }
        
        return {
            "time_window": time_window,
            "total_metrics": len(recent_metrics),
            "metrics_summary": summary,
            "active_alerts": len([a for a in self.alerts if a["timestamp"] > cutoff_time])
        }

# Example usage
if __name__ == "__main__":
    analytics = RealTimeAnalytics()
    
    # Record some metrics
    analytics.record_metric("response_time", 1.2, {"endpoint": "/api/generate"})
    analytics.record_metric("response_time", 0.8, {"endpoint": "/api/analyze"})
    analytics.record_metric("error_rate", 0.05, {"service": "auth"})
    
    # Get summary
    summary = analytics.get_metrics_summary()
    print(f"Analytics summary: {summary}")
'''
        else:
            return self._generate_general_code("analytics system", language)

    def _generate_workflow_code(self, language='python'):
        """Generate workflow system code"""
        return self._generate_general_code("workflow automation system", language)

    def _generate_routing_code(self, language='python'):
        """Generate routing system code"""
        return self._generate_general_code("intelligent routing system", language)

    def _generate_integration_code(self, language='python'):
        """Generate integration system code"""
        return self._generate_general_code("system integration layer", language)

    def _generate_ml_code(self, language='python'):
        """Generate machine learning code"""
        return self._generate_general_code("machine learning pipeline", language)

    def _generate_general_code(self, prompt, language='python'):
        """Generate general purpose code"""
        if language == 'python':
            return f'''
"""
Generated code for: {prompt}
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

class GeneratedSystem:
    """Auto-generated system for: {prompt}"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.created_at = datetime.now()

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute main functionality"""
        try:
            # Implementation placeholder
            result = {{
                "status": "success",
                "message": "Executed successfully",
                "timestamp": datetime.now().isoformat(),
                "params": params
            }}
            self.logger.info(f"Execution successful: {{result}}")
            return result

        except Exception as e:
            error_result = {{
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }}
            self.logger.error(f"Execution failed: {{error_result}}")
            return error_result

    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {{
            "system": "{prompt}",
            "status": "operational",
            "created_at": self.created_at.isoformat(),
            "uptime": str(datetime.now() - self.created_at)
        }}

# Example usage
if __name__ == "__main__":
    system = GeneratedSystem()

    # Test execution
    result = system.execute({{"test": True}})
    print(f"Result: {{result}}")

    # Check status
    status = system.get_status()
    print(f"Status: {{status}}")
'''
        elif language == 'javascript':
            return f'''
/**
 * Generated code for: {prompt}
 */

class GeneratedSystem {{
    constructor() {{
        this.logger = console;
        this.createdAt = new Date();
    }}

    execute(params) {{
        try {{
            // Implementation placeholder
            const result = {{
                status: "success",
                message: "Executed successfully",
                timestamp: new Date().toISOString(),
                params: params
            }};
            this.logger.log(`Execution successful: ${{JSON.stringify(result)}}`);
            return result;

        }} catch (e) {{
            const errorResult = {{
                status: "error",
                message: e.message,
                timestamp: new Date().toISOString()
            }};
            this.logger.error(`Execution failed: ${{JSON.stringify(errorResult)}}`);
            return errorResult;
        }}
    }}

    getStatus() {{
        return {{
            system: "{prompt}",
            status: "operational",
            createdAt: this.createdAt.toISOString(),
            uptime: Date.now() - this.createdAt.getTime()
        }};
    }}
}}

// Example usage
const system = new GeneratedSystem();
const result = system.execute({{ test: true }});
console.log(`Result: ${{JSON.stringify(result)}}`);
'''
        else:
            return f'// Generated code for: {prompt}\\n// Implementation for {language} would go here'

    def _generate_fallback_code(self, prompt, language='python'):
        """Generate fallback code when all else fails"""
        return f'''
# Fallback generated code for: {prompt}
# Language: {language}

def main():
    """Main function for {prompt}"""
    print("This is auto-generated fallback code for: {prompt}")
    # TODO: Implement actual functionality
    return {{"status": "placeholder", "message": "Implement actual functionality"}}

if __name__ == "__main__":
    main()
'''

    def _add_to_cache(self, key, value):
        """Add result to cache with LRU eviction"""
        if len(self._cache) >= self._max_cache_size:
            self._cache.popitem(last=False)
        self._cache[key] = value.copy()
        self._cache[key]['cached'] = False

# Test the skill
if __name__ == "__main__":
    skill = CodeGenerationSkill()
    
    # Test execution
    result = skill.execute({
        "prompt": "Create an autonomous intelligence system",
        "language": "python",
        "style": "professional"
    })
    
    print(f"Result: {result.success}")
    print(f"Output: {result.output}")
    if result.data:
        print(f"Data: {result.data}")