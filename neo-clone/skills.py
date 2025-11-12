"""
Skill registry and base skill classes for neo-clone brain system.

Provides a dynamic skill system with automatic discovery and execution.
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Import SystemHealerSkill
try:
    from system_healer import SystemHealerSkill
except ImportError:
    # Fallback if system_healer is not available
    class SystemHealerSkill:
        def __init__(self):
            self.name = "system_healer"
            self.description = "System healer (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "System healer skill not available")

# Import FreeModelScannerSkill
try:
    from free_model_scanner import FreeModelScanner
except ImportError:
    # Fallback if free_model_scanner is not available
    class FreeModelScanner:
        def __init__(self):
            self.name = "free_model_scanner"
            self.description = "Free model scanner (unavailable)"
            self.example = ""
        
        def scan_free_models(self, force_refresh=False):
            return {"success": False, "error": "Free model scanner not available", "models": []}

# Import integrated backup skills
try:
    from advanced_pentesting_reverse_engineering import AdvancedPentestingReverseEngineeringSkill
except ImportError:
    class AdvancedPentestingReverseEngineeringSkill:
        def __init__(self):
            self.name = "advanced_pentesting_reverse_engineering"
            self.description = "Advanced pentesting and reverse engineering (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "Advanced pentesting skill not available")

try:
    from security_evolution_engine import SecurityEvolutionEngineSkill
except ImportError:
    class SecurityEvolutionEngineSkill:
        def __init__(self):
            self.name = "security_evolution_engine"
            self.description = "Security evolution engine (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "Security evolution engine skill not available")

try:
    from autonomous_reasoning_skill import AutonomousReasoningSkill, SkillRoutingOptimizer, CrossSkillDependencyAnalyzer
except ImportError:
    class AutonomousReasoningSkill:
        def __init__(self):
            self.name = "autonomous_reasoning"
            self.description = "Autonomous reasoning (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "Autonomous reasoning skill not available")
    
    class SkillRoutingOptimizer:
        def __init__(self):
            self.name = "skill_routing_optimizer"
            self.description = "Skill routing optimizer (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "Skill routing optimizer not available")
    
    class CrossSkillDependencyAnalyzer:
        def __init__(self):
            self.name = "cross_skill_dependency_analyzer"
            self.description = "Cross-skill dependency analyzer (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "Cross-skill dependency analyzer not available")

try:
    from federated_learning import FederatedLearningSkill
except ImportError:
    class FederatedLearningSkill:
        def __init__(self):
            self.name = "federated_learning"
            self.description = "Federated learning (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "Federated learning skill not available")

try:
    from ml_workflow_generator import MLWorkflowGenerator
except ImportError:
    class MLWorkflowGenerator:
        def __init__(self):
            self.name = "ml_workflow_generator"
            self.description = "ML workflow generator (unavailable)"
            self.example = ""
        
        def execute(self, params):
            from skills_fixed import SkillResult
            return SkillResult(False, "ML workflow generator not available")


@dataclass
class SkillResult:
    """Result of skill execution."""
    success: bool
    output: str
    data: Optional[Dict[str, Any]] = None


class BaseSkill(ABC):
    """Base class for all skills in the neo-clone system."""
    
    def __init__(self, name: str, description: str, example: str = ""):
        self.name = name
        self.description = description
        self.example = example
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> SkillResult:
        """Execute the skill with given parameters."""
        pass


class SkillRegistry:
    """Registry for managing available skills."""
    
    def __init__(self):
        self.skills = {}
        self._register_default_skills()
    
    def register_skill(self, skill: BaseSkill):
        """Register a new skill."""
        self.skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self.skills.get(name)
    
    def list_skills(self) -> List[str]:
        """List all available skill names."""
        return list(self.skills.keys())
    
    def _register_default_skills(self):
        """Register default skills."""
        default_skills = [
            TextAnalysisSkill(),
            DataInspectorSkill(),
            MLTrainingSkill(),
            FileManagerSkill(),
            WebSearchSkill(),
            MiniMaxAgentSkill(),
            ConstitutionSkill(),
            SpecificationSkill(),
            PlanningSkill(),
            TaskBreakdownSkill(),
            ImplementationSkill(),
            SystemHealerSkill(),
            # Integrated backup skills
            AdvancedPentestingReverseEngineeringSkill(),
            SecurityEvolutionEngineSkill(),
            AutonomousReasoningSkill(),
            SkillRoutingOptimizer(),
            CrossSkillDependencyAnalyzer(),
            FederatedLearningSkill(),
            MLWorkflowGenerator()
        ]
        
        for skill in default_skills:
            self.register_skill(skill)


class TextAnalysisSkill(BaseSkill):
    """Skill for sentiment analysis and text moderation."""

    def __init__(self):
        super().__init__(
            "text_analysis",
            "Performs sentiment analysis and text moderation",
            "Analyze the sentiment of this text: 'I love this product!'"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        text = params.get("text", "")
        # Simple sentiment analysis
        positive_words = ["good", "great", "excellent", "amazing", "love", "like", "best"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "dislike", "poor"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = "Positive"
        elif negative_count > positive_count:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        output = f"Sentiment Analysis Result: {sentiment}\n"
        output += f"Positive indicators: {positive_count}\n"
        output += f"Negative indicators: {negative_count}\n"
        output += f"Text length: {len(text)} characters"

        return SkillResult(success=True, output=output)


class DataInspectorSkill(BaseSkill):
    """Skill for analyzing CSV/JSON data."""

    def __init__(self):
        super().__init__(
            "data_inspector",
            "Analyzes CSV/JSON data and provides summaries",
            "Analyze this CSV data and provide summary statistics"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        text = params.get("text", "")
        # Simple data analysis response
        output = "Data Inspector Skill activated.\n"
        output += "I can analyze CSV and JSON data files.\n"
        output += "Please provide a file path or data content to analyze.\n"
        output += f"Input text length: {len(text)} characters"

        return SkillResult(success=True, output=output)


class MLTrainingSkill(BaseSkill):
    """Skill for ML model training guidance."""

    def __init__(self):
        super().__init__(
            "ml_training",
            "Provides ML model training guidance and recommendations",
            "Guide me through training a classification model"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "ML Training Skill activated.\n"
        output += "I can provide guidance on:\n"
        output += "- Model selection and architecture\n"
        output += "- Data preprocessing and feature engineering\n"
        output += "- Training strategies and hyperparameter tuning\n"
        output += "- Evaluation metrics and validation\n"
        output += "- Deployment considerations"

        return SkillResult(success=True, output=output)


class FileManagerSkill(BaseSkill):
    """Skill for file management operations."""

    def __init__(self):
        super().__init__(
            "file_manager",
            "Manages file operations and directory navigation",
            "Read the contents of a file and analyze it"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "File Manager Skill activated.\n"
        output += "I can help with:\n"
        output += "- Reading and writing files\n"
        output += "- Directory navigation and listing\n"
        output += "- File search and filtering\n"
        output += "- Content analysis and extraction"

        return SkillResult(success=True, output=output)


class WebSearchSkill(BaseSkill):
    """Skill for web search and information retrieval."""

    def __init__(self):
        super().__init__(
            "web_search",
            "Performs web searches and retrieves information",
            "Search for information about machine learning best practices"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        query = params.get("query", "")
        output = f"Web Search Skill activated.\n"
        output += f"Search query: {query}\n"
        output += "I can search the web for current information,\n"
        output += "fact-check claims, and find relevant resources."

        return SkillResult(success=True, output=output)


class MiniMaxAgentSkill(BaseSkill):
    """Skill for advanced reasoning with MiniMax agent."""

    def __init__(self):
        super().__init__(
            "minimax_agent",
            "Advanced reasoning and decision-making with MiniMax algorithm",
            "Analyze this complex decision problem using minimax reasoning"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "MiniMax Agent Skill activated.\n"
        output += "I can perform:\n"
        output += "- Complex decision analysis\n"
        output += "- Game theory applications\n"
        output += "- Strategic planning and optimization\n"
        output += "- Risk assessment and mitigation"

        return SkillResult(success=True, output=output)


class ConstitutionSkill(BaseSkill):
    """Skill for constitutional AI and ethical reasoning."""

    def __init__(self):
        super().__init__(
            "constitution",
            "Applies constitutional principles for ethical AI behavior",
            "Evaluate this response for ethical considerations"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "Constitution Skill activated.\n"
        output += "I can provide:\n"
        output += "- Ethical analysis and guidance\n"
        output += "- Constitutional AI principles\n"
        output += "- Harm prevention and safety measures\n"
        output += "- Fairness and bias evaluation"

        return SkillResult(success=True, output=output)


class SpecificationSkill(BaseSkill):
    """Skill for creating detailed specifications."""

    def __init__(self):
        super().__init__(
            "specification",
            "Creates detailed technical specifications and requirements",
            "Create a specification for a web application"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "Specification Skill activated.\n"
        output += "I can create:\n"
        output += "- Technical specifications\n"
        output += "- Requirements documents\n"
        output += "- API documentation\n"
        output += "- System architecture designs"

        return SkillResult(success=True, output=output)


class PlanningSkill(BaseSkill):
    """Skill for strategic planning and project management."""

    def __init__(self):
        super().__init__(
            "planning",
            "Creates strategic plans and project roadmaps",
            "Create a project plan for developing a mobile app"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "Planning Skill activated.\n"
        output += "I can help with:\n"
        output += "- Project planning and roadmapping\n"
        output += "- Task breakdown and scheduling\n"
        output += "- Resource allocation and management\n"
        output += "- Risk assessment and mitigation"

        return SkillResult(success=True, output=output)


class TaskBreakdownSkill(BaseSkill):
    """Skill for breaking down complex tasks."""

    def __init__(self):
        super().__init__(
            "task_breakdown",
            "Breaks down complex tasks into manageable steps",
            "Break down the process of building a machine learning pipeline"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "Task Breakdown Skill activated.\n"
        output += "I can:\n"
        output += "- Decompose complex problems\n"
        output += "- Create step-by-step workflows\n"
        output += "- Identify dependencies and prerequisites\n"
        output += "- Estimate effort and timeline"

        return SkillResult(success=True, output=output)


class ImplementationSkill(BaseSkill):
    """Skill for code implementation and development."""

    def __init__(self):
        super().__init__(
            "implementation",
            "Implements code solutions and development tasks",
            "Implement a REST API for user management"
        )

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        output = "Implementation Skill activated.\n"
        output += "I can help with:\n"
        output += "- Code implementation and development\n"
        output += "- Algorithm design and optimization\n"
        output += "- Debugging and troubleshooting\n"
        output += "- Code review and refactoring"

        return SkillResult(success=True, output=output)


class FreeModelScannerSkill(BaseSkill):
    """Skill for scanning and managing free AI models."""

    def __init__(self):
        super().__init__(
            "free_model_scanner",
            "Scans for and manages free AI models for OpenCode integration",
            "Scan for available free models and their capabilities"
        )
        self.scanner = FreeModelScanner()

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        try:
            action = params.get("action", "scan")
            force_refresh = params.get("force_refresh", False)
            
            if action == "scan":
                result = self.scanner.scan_free_models(force_refresh)
                
                if result.get("success"):
                    output = "[FREE MODEL SCANNER] Results:\n"
                    output += f"Found {result['total_found']} free models\n"
                    output += f"Scan time: {result['scan_time']}\n\n"
                    
                    output += "Top Models:\n"
                    for i, model in enumerate(result["models"][:5], 1):
                        output += f"{i}. {model['provider']}/{model['model']} - Score: {model['integration_score']}%\n"
                        output += f"   Capabilities: {', '.join(model.get('recommended_uses', [])[:3])}\n"
                    
                    recs = result.get("recommendations", {})
                    if recs.get("primary_recommendation"):
                        primary = recs["primary_recommendation"]
                        output += f"\nPrimary Recommendation: {primary['model']}\n"
                        output += f"Reason: {primary['reason']}\n"
                    
                    return SkillResult(success=True, output=output)
                else:
                    return SkillResult(success=False, output=f"Scan failed: {result.get('error')}")
            
            elif action == "monitor":
                result = self.scanner.monitor_for_new_models()
                
                if result.get("has_changes"):
                    output = f"[NEW] {len(result.get('new_models', []))} new models found!\n"
                    for model in result.get("new_models", []):
                        output += f"  + {model['provider']}/{model['model']}\n"
                else:
                    output = "[INFO] No new free models found\n"
                
                return SkillResult(success=True, output=output)
            
            else:
                return SkillResult(success=False, output="Unknown action. Use 'scan' or 'monitor'")
                
        except Exception as e:
            return SkillResult(success=False, output=f"Free model scanner error: {str(e)}")


# Skill Registry
AVAILABLE_SKILLS = {
    "code_generation": CodeGenerationSkill(),
    "text_analysis": TextAnalysisSkill(),
    "data_inspector": DataInspectorSkill(),
    "ml_training": MLTrainingSkill(),
    "file_manager": FileManagerSkill(),
    "web_search": WebSearchSkill(),
    "minimax_agent": MiniMaxAgentSkill(),
    "constitution": ConstitutionSkill(),
    "task_breakdown": TaskBreakdownSkill(),
    "implementation": ImplementationSkill(),
    "free_model_scanner": FreeModelScannerSkill(),
}