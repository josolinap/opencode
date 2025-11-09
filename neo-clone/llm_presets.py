"""
llm_presets.py - LLM Parameter Presets for Neo-Clone

Implements:
- Preset configurations for different use cases
- Dynamic preset switching
- Custom preset creation and management
- Temperature, max_tokens, and other parameter presets
- Usage analytics and optimization suggestions
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class LLMParameters:
    """LLM parameters configuration"""
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.9
    top_k: int = 50
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = None
    system_prompt: Optional[str] = None
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []

@dataclass
class LLMProfile:
    """Complete LLM profile with metadata"""
    name: str
    description: str
    category: str  # creative, technical, analytical, conversational
    parameters: LLMParameters
    use_cases: List[str]
    keywords: List[str]
    recommended_models: List[str]
    created_at: str
    updated_at: str
    author: str = "Neo-Clone"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMProfile':
        params_data = data.pop('parameters', {})
        parameters = LLMParameters(**params_data)
        return cls(parameters=parameters, **data)

class LLMPresetManager:
    """Manages LLM parameter presets"""
    
    def __init__(self, presets_dir: str = "data/presets"):
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        self.presets_file = self.presets_dir / "presets.json"
        self.custom_presets_file = self.presets_dir / "custom_presets.json"
        self.usage_file = self.presets_dir / "usage_stats.json"
        
        # Load presets
        self.built_in_presets = self._load_builtin_presets()
        self.custom_presets = self._load_custom_presets()
        self.usage_stats = self._load_usage_stats()
        
        # Validate presets
        self._validate_presets()
    
    def _load_builtin_presets(self) -> Dict[str, LLMProfile]:
        """Load built-in presets"""
        presets = {
            # Creative Presets
            "creative_writing": LLMProfile(
                name="creative_writing",
                description="Optimized for creative writing, storytelling, and brainstorming",
                category="creative",
                parameters=LLMParameters(
                    temperature=0.8,
                    max_tokens=1500,
                    top_p=0.95,
                    top_k=60,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    system_prompt="You are a creative writing assistant. Generate engaging, imaginative content with rich details and compelling narratives."
                ),
                use_cases=["creative writing", "storytelling", "brainstorming", "content creation"],
                keywords=["creative", "write", "story", "brainstorm", "imagine", "invent"],
                recommended_models=["ggml-neural-chat", "llama2", "mistral"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            "poetry_mode": LLMProfile(
                name="poetry_mode",
                description="Specialized for poetry, rhyming, and artistic expression",
                category="creative",
                parameters=LLMParameters(
                    temperature=0.9,
                    max_tokens=800,
                    top_p=0.98,
                    top_k=70,
                    frequency_penalty=0.2,
                    presence_penalty=0.15,
                    system_prompt="You are a poetry expert. Create beautiful, rhythmically pleasing poems with proper structure and emotional depth."
                ),
                use_cases=["poetry", "rhyme", "lyrics", "artistic expression"],
                keywords=["poem", "poetry", "rhyme", "verse", "lyric"],
                recommended_models=["ggml-neural-chat", "llama2"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            # Technical Presets
            "code_generation": LLMProfile(
                name="code_generation",
                description="Optimized for programming, code generation, and technical explanations",
                category="technical",
                parameters=LLMParameters(
                    temperature=0.1,
                    max_tokens=2000,
                    top_p=0.8,
                    top_k=30,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    system_prompt="You are a senior software engineer. Generate clean, efficient, well-documented code with proper error handling and best practices."
                ),
                use_cases=["code generation", "debugging", "technical explanations", "architecture"],
                keywords=["code", "program", "function", "debug", "algorithm", "technical"],
                recommended_models=["ggml-neural-chat", "codellama", "starcoder"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            "data_analysis": LLMProfile(
                name="data_analysis",
                description="Focused on data analysis, statistics, and analytical reasoning",
                category="technical",
                parameters=LLMParameters(
                    temperature=0.3,
                    max_tokens=1200,
                    top_p=0.85,
                    top_k=40,
                    frequency_penalty=0.05,
                    presence_penalty=0.05,
                    system_prompt="You are a data scientist. Provide accurate statistical analysis, clear data interpretation, and evidence-based conclusions."
                ),
                use_cases=["data analysis", "statistics", "research", "insights"],
                keywords=["data", "analyze", "statistics", "trends", "insights", "research"],
                recommended_models=["ggml-neural-chat", "llama2"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            # Analytical Presets
            "fact_checking": LLMProfile(
                name="fact_checking",
                description="Designed for fact verification and accurate information retrieval",
                category="analytical",
                parameters=LLMParameters(
                    temperature=0.1,
                    max_tokens=1000,
                    top_p=0.7,
                    top_k=20,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    system_prompt="You are a fact-checking expert. Provide accurate, verifiable information with clear sources and confidence levels."
                ),
                use_cases=["fact checking", "verification", "research", "accuracy"],
                keywords=["fact", "verify", "check", "confirm", "accurate", "true"],
                recommended_models=["ggml-neural-chat", "llama2"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            "analytical_reasoning": LLMProfile(
                name="analytical_reasoning",
                description="Optimized for logical reasoning and problem-solving",
                category="analytical",
                parameters=LLMParameters(
                    temperature=0.2,
                    max_tokens=1500,
                    top_p=0.8,
                    top_k=35,
                    frequency_penalty=0.05,
                    presence_penalty=0.05,
                    system_prompt="You are a logical reasoning expert. Break down complex problems into step-by-step solutions with clear explanations."
                ),
                use_cases=["reasoning", "problem solving", "logical thinking", "analysis"],
                keywords=["reason", "solve", "logic", "analyze", "think", "problem"],
                recommended_models=["ggml-neural-chat", "llama2"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            # Conversational Presets
            "conversational": LLMProfile(
                name="conversational",
                description="Natural conversation with friendly, helpful responses",
                category="conversational",
                parameters=LLMParameters(
                    temperature=0.6,
                    max_tokens=800,
                    top_p=0.9,
                    top_k=50,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    system_prompt="You are a friendly, helpful AI assistant. Engage in natural conversation while being informative and supportive."
                ),
                use_cases=["casual conversation", "help", "chat", "assistance"],
                keywords=["chat", "talk", "hello", "help", "conversation", "friendly"],
                recommended_models=["ggml-neural-chat", "llama2", "mistral"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            "tutorial_mode": LLMProfile(
                name="tutorial_mode",
                description="Patient, educational responses perfect for learning",
                category="conversational",
                parameters=LLMParameters(
                    temperature=0.4,
                    max_tokens=1000,
                    top_p=0.85,
                    top_k=45,
                    frequency_penalty=0.05,
                    presence_penalty=0.05,
                    system_prompt="You are a patient teacher. Provide clear, step-by-step explanations suitable for learners at all levels."
                ),
                use_cases=["tutorials", "education", "learning", "teaching"],
                keywords=["teach", "learn", "explain", "tutorial", "guide", "step"],
                recommended_models=["ggml-neural-chat", "llama2"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            # Specialized Presets
            "research_mode": LLMProfile(
                name="research_mode",
                description="Academic and research-focused responses with citations",
                category="analytical",
                parameters=LLMParameters(
                    temperature=0.3,
                    max_tokens=2000,
                    top_p=0.8,
                    top_k=30,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    system_prompt="You are a research assistant. Provide detailed, well-sourced information with proper academic tone and structure."
                ),
                use_cases=["research", "academic writing", "citations", "scholarly work"],
                keywords=["research", "academic", "study", "cite", "scholarly", "source"],
                recommended_models=["ggml-neural-chat", "llama2"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            
            "quick_responses": LLMProfile(
                name="quick_responses",
                description="Fast, concise responses for quick interactions",
                category="conversational",
                parameters=LLMParameters(
                    temperature=0.4,
                    max_tokens=400,
                    top_p=0.8,
                    top_k=30,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    system_prompt="You provide quick, concise answers. Get straight to the point while being helpful."
                ),
                use_cases=["quick answers", "brief responses", "efficiency"],
                keywords=["quick", "brief", "short", "fast", "concise", "summary"],
                recommended_models=["ggml-neural-chat", "mistral"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        }
        
        return presets
    
    def _load_custom_presets(self) -> Dict[str, LLMProfile]:
        """Load custom presets from file"""
        try:
            if self.custom_presets_file.exists():
                with open(self.custom_presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {name: LLMProfile.from_dict(profile_data) for name, profile_data in data.items()}
        except Exception as e:
            logger.warning(f"Failed to load custom presets: {e}")
        return {}
    
    def _load_usage_stats(self) -> Dict[str, Any]:
        """Load preset usage statistics"""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load usage stats: {e}")
        return {
            "total_uses": {},
            "last_used": {},
            "user_feedback": {},
            "success_rates": {}
        }
    
    def _validate_presets(self):
        """Validate preset parameters"""
        for preset_name, preset in self.built_in_presets.items():
            self._validate_profile(preset, f"built-in preset {preset_name}")
        
        for preset_name, preset in self.custom_presets.items():
            self._validate_profile(preset, f"custom preset {preset_name}")
    
    def _validate_profile(self, profile: LLMProfile, name: str):
        """Validate LLM profile parameters"""
        params = profile.parameters
        
        if not (0.0 <= params.temperature <= 2.0):
            logger.warning(f"Invalid temperature in {name}: {params.temperature}")
        
        if params.max_tokens <= 0:
            logger.warning(f"Invalid max_tokens in {name}: {params.max_tokens}")
        
        if not (0.0 <= params.top_p <= 1.0):
            logger.warning(f"Invalid top_p in {name}: {params.top_p}")
        
        if params.top_k < 0:
            logger.warning(f"Invalid top_k in {name}: {params.top_k}")
    
    def get_preset(self, name: str) -> Optional[LLMProfile]:
        """Get a preset by name"""
        # Check custom presets first
        if name in self.custom_presets:
            self._update_usage_stats(name)
            return self.custom_presets[name]
        
        # Check built-in presets
        if name in self.built_in_presets:
            self._update_usage_stats(name)
            return self.built_in_presets[name]
        
        return None
    
    def list_presets(self, category: Optional[str] = None) -> Dict[str, LLMProfile]:
        """List all presets, optionally filtered by category"""
        all_presets = {**self.built_in_presets, **self.custom_presets}
        
        if category:
            return {name: preset for name, preset in all_presets.items() 
                   if preset.category == category}
        
        return all_presets
    
    def find_presets_by_keywords(self, keywords: List[str]) -> Dict[str, float]:
        """Find presets matching keywords with relevance scores"""
        all_presets = {**self.built_in_presets, **self.custom_presets}
        results = {}
        
        for name, preset in all_presets.items():
            score = 0.0
            
            # Check keywords
            for keyword in keywords:
                if keyword.lower() in preset.name.lower():
                    score += 2.0
                if any(keyword.lower() in kw.lower() for kw in preset.keywords):
                    score += 1.0
                if any(keyword.lower() in uc.lower() for uc in preset.use_cases):
                    score += 1.5
                if keyword.lower() in preset.description.lower():
                    score += 0.5
            
            if score > 0:
                results[name] = score
        
        # Sort by score
        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))
    
    def auto_select_preset(self, user_input: str) -> Optional[str]:
        """Automatically select appropriate preset based on user input"""
        # Extract keywords from user input
        words = user_input.lower().split()
        
        # Find matching presets
        matches = self.find_presets_by_keywords(words)
        
        if matches:
            # Return the highest scoring preset
            best_match = max(matches.items(), key=lambda x: x[1])
            logger.info(f"Auto-selected preset '{best_match[0]}' for input: {user_input[:50]}...")
            return best_match[0]
        
        # Default to conversational if no match found
        return "conversational"
    
    def create_custom_preset(self, name: str, description: str, category: str, 
                           parameters: LLMParameters, use_cases: List[str],
                           keywords: List[str], author: str = "User") -> bool:
        """Create a new custom preset"""
        if name in self.built_in_presets or name in self.custom_presets:
            logger.warning(f"Preset '{name}' already exists")
            return False
        
        try:
            profile = LLMProfile(
                name=name,
                description=description,
                category=category,
                parameters=parameters,
                use_cases=use_cases,
                keywords=keywords,
                recommended_models=["ggml-neural-chat"],  # Default
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                author=author
            )
            
            self.custom_presets[name] = profile
            self._save_custom_presets()
            
            logger.info(f"Created custom preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom preset: {e}")
            return False
    
    def update_preset(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing custom preset"""
        if name not in self.custom_presets:
            logger.warning(f"Custom preset '{name}' not found")
            return False
        
        try:
            preset = self.custom_presets[name]
            
            # Update fields
            for field, value in updates.items():
                if field == "parameters":
                    # Merge parameter updates
                    current_params = preset.parameters
                    new_params = {**asdict(current_params), **value}
                    preset.parameters = LLMParameters(**new_params)
                elif hasattr(preset, field):
                    setattr(preset, field, value)
            
            preset.updated_at = datetime.now().isoformat()
            
            self._save_custom_presets()
            logger.info(f"Updated custom preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update preset: {e}")
            return False
    
    def delete_custom_preset(self, name: str) -> bool:
        """Delete a custom preset"""
        if name not in self.custom_presets:
            logger.warning(f"Custom preset '{name}' not found")
            return False
        
        try:
            del self.custom_presets[name]
            self._save_custom_presets()
            logger.info(f"Deleted custom preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete preset: {e}")
            return False
    
    def get_preset_suggestions(self, user_input: str) -> List[Dict[str, Any]]:
        """Get preset suggestions for user input"""
        auto_preset = self.auto_select_preset(user_input)
        keyword_matches = self.find_presets_by_keywords(user_input.lower().split())
        
        suggestions = []
        
        # Add auto-selected preset
        if auto_preset:
            suggestions.append({
                "preset": auto_preset,
                "reason": "Auto-selected based on input",
                "confidence": "high"
            })
        
        # Add other relevant presets
        for preset_name, score in list(keyword_matches.items())[:3]:
            if preset_name != auto_preset:
                suggestions.append({
                    "preset": preset_name,
                    "reason": f"Matched keywords (score: {score:.1f})",
                    "confidence": "medium" if score > 1.0 else "low"
                })
        
        return suggestions
    
    def _update_usage_stats(self, preset_name: str):
        """Update usage statistics for a preset"""
        try:
            if preset_name not in self.usage_stats["total_uses"]:
                self.usage_stats["total_uses"][preset_name] = 0
            self.usage_stats["total_uses"][preset_name] += 1
            
            self.usage_stats["last_used"][preset_name] = datetime.now().isoformat()
            
            self._save_usage_stats()
        except Exception as e:
            logger.warning(f"Failed to update usage stats: {e}")
    
    def _save_custom_presets(self):
        """Save custom presets to file"""
        try:
            data = {name: preset.to_dict() for name, preset in self.custom_presets.items()}
            with open(self.custom_presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save custom presets: {e}")
    
    def _save_usage_stats(self):
        """Save usage statistics to file"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage stats: {e}")
    
    def export_presets(self, output_file: str, include_stats: bool = True) -> bool:
        """Export presets to JSON file"""
        try:
            data = {
                "built_in_presets": {name: preset.to_dict() for name, preset in self.built_in_presets.items()},
                "custom_presets": {name: preset.to_dict() for name, preset in self.custom_presets.items()}
            }
            
            if include_stats:
                data["usage_stats"] = self.usage_stats
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported presets to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export presets: {e}")
            return False
    
    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get analytics on preset usage"""
        total_uses = self.usage_stats["total_uses"]
        last_used = self.usage_stats["last_used"]
        
        # Most used presets
        most_used = sorted(total_uses.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Recently used
        recent = sorted(last_used.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Category usage
        all_presets = {**self.built_in_presets, **self.custom_presets}
        category_usage = {}
        
        for preset_name, uses in total_uses.items():
            if preset_name in all_presets:
                category = all_presets[preset_name].category
                if category not in category_usage:
                    category_usage[category] = 0
                category_usage[category] += uses
        
        return {
            "most_used_presets": most_used,
            "recently_used": recent,
            "category_usage": category_usage,
            "total_interactions": sum(total_uses.values()),
            "unique_presets_used": len(total_uses)
        }

# Global preset manager instance
_preset_manager_instance = None

def get_preset_manager() -> LLMPresetManager:
    """Get global preset manager instance (singleton pattern)"""
    global _preset_manager_instance
    if _preset_manager_instance is None:
        _preset_manager_instance = LLMPresetManager()
    return _preset_manager_instance