#!/usr/bin/env python3
"""
Free Model Scanner - Neo-Clone Skill
Automatically discovers, analyzes, and manages free AI models for OpenCode integration
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

class FreeModelScanner:
    """
    Specialized Neo-Clone skill for scanning and managing free AI models
    """
    
    def __init__(self):
        self.name = "free_model_scanner"
        self.description = "Scans for and manages free AI models for OpenCode integration"
        self.version = "1.0.0"
        
        # Cache for storing discovered models
        self.cache_file = "free_models_cache.json"
        self.cache_ttl = 3600  # 1 hour
        
        # OpenCode models command path
        self.opencode_path = os.path.abspath("../packages/opencode/src")
    
    def _find_bun(self) -> Optional[str]:
        """Find bun executable in PATH"""
        try:
            # Try full path from npm first
            npm_bun = r"C:\Users\JO\AppData\Roaming\npm\bun.cmd"
            if os.path.exists(npm_bun):
                return npm_bun
            
            # Try common bun commands
            candidates = ["bun", "bun.cmd", "bun.exe"]
            for candidate in candidates:
                result = subprocess.run([candidate, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return candidate
                
            return None
        except Exception:
            return None
        
    def scan_free_models(self, force_refresh: bool = False) -> Dict:
        """
        Scan for all free models in the OpenCode database
        
        Args:
            force_refresh: Force refresh of model cache
            
        Returns:
            Dict containing free models information
        """
        try:
            # Change to OpenCode directory
            original_cwd = os.getcwd()
            os.chdir(self.opencode_path)
            
            # Find bun executable
            bun_cmd = self._find_bun()
            if not bun_cmd:
                return {
                    "success": False,
                    "error": "Bun executable not found in PATH",
                    "models": []
                }
            
            # Refresh cache if requested
            if force_refresh:
                print("[INFO] Refreshing model cache...")
                subprocess.run([bun_cmd, "run", "index.ts", "models", "--cache"], 
                             capture_output=True, text=True, cwd=self.opencode_path)
            
            # Get free models in JSON format
            result = subprocess.run([
                bun_cmd, "run", "index.ts", 
                "models", "list", 
                "--cost", "free", 
                "--format", "json",
                "--limit", "100"
            ], capture_output=True, text=True, cwd=self.opencode_path)
            
            os.chdir(original_cwd)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to scan models: {result.stderr}",
                    "models": []
                }
            
            # Parse JSON response
            models = json.loads(result.stdout)
            
            # Analyze each model for integration potential
            analyzed_models = []
            for model in models:
                analysis = self._analyze_model_integration(model)
                analyzed_models.append(analysis)
            
            # Sort by integration score
            analyzed_models.sort(key=lambda x: x["integration_score"], reverse=True)
            
            # Cache results
            self._cache_results(analyzed_models)
            
            return {
                "success": True,
                "models": analyzed_models,
                "total_found": len(analyzed_models),
                "scan_time": datetime.now().isoformat(),
                "recommendations": self._generate_recommendations(analyzed_models)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Scan failed: {str(e)}",
                "models": []
            }
    
    def _analyze_model_integration(self, model: Dict) -> Dict:
        """
        Analyze a model for OpenCode integration potential
        
        Args:
            model: Model information from OpenCode
            
        Returns:
            Enhanced model information with integration analysis
        """
        base_score = 50
        
        # Capability scoring
        capabilities = model.get("capabilities", {})
        if capabilities.get("reasoning", False):
            base_score += 20
        if capabilities.get("tool_call", False):
            base_score += 15
        if capabilities.get("temperature", False):
            base_score += 10
        if capabilities.get("attachment", False):
            base_score += 10
        
        # Context length scoring
        context_limit = model.get("limits", {}).get("context", 0)
        if context_limit >= 200000:
            base_score += 15
        elif context_limit >= 100000:
            base_score += 10
        elif context_limit >= 32000:
            base_score += 5
        
        # Provider scoring (OpenCode provider gets bonus)
        if model.get("provider") == "opencode":
            base_score += 25
        
        # Integration readiness
        integration_ready = all([
            capabilities.get("tool_call", False),
            capabilities.get("reasoning", False),
            context_limit >= 32000
        ])
        
        if integration_ready:
            base_score += 10
        
        return {
            **model,
            "integration_score": min(100, base_score),
            "integration_ready": integration_ready,
            "recommended_uses": self._get_recommended_uses(model),
            "integration_complexity": self._assess_integration_complexity(model)
        }
    
    def _get_recommended_uses(self, model: Dict) -> List[str]:
        """
        Get recommended use cases for a model based on its capabilities
        """
        uses = []
        capabilities = model.get("capabilities", {})
        
        if capabilities.get("reasoning", False):
            uses.extend(["Complex problem solving", "Code analysis", "Logical reasoning"])
        
        if capabilities.get("tool_call", False):
            uses.extend(["API integration", "File operations", "External tool usage"])
        
        if capabilities.get("attachment", False):
            uses.extend(["Image analysis", "Document processing", "Multi-modal tasks"])
        
        if capabilities.get("temperature", False):
            uses.extend(["Creative writing", "Content generation", "Brainstorming"])
        
        context = model.get("limits", {}).get("context", 0)
        if context >= 200000:
            uses.append("Large document processing")
        
        return uses
    
    def _assess_integration_complexity(self, model: Dict) -> str:
        """
        Assess how complex it would be to integrate this model
        """
        if model.get("provider") == "opencode":
            return "low"
        
        capabilities = model.get("capabilities", {})
        if all(capabilities.get(k, False) for k in ["tool_call", "reasoning"]):
            return "medium"
        
        return "high"
    
    def _generate_recommendations(self, models: List[Dict]) -> Dict:
        """
        Generate recommendations based on available free models
        """
        if not models:
            return {
                "primary_recommendation": None,
                "alternative_options": [],
                "integration_suggestions": []
            }
        
        # Best model for general use
        best_model = models[0]
        
        # Models for specific use cases
        reasoning_models = [m for m in models if m.get("capabilities", {}).get("reasoning", False)]
        tool_models = [m for m in models if m.get("capabilities", {}).get("tool_call", False)]
        attachment_models = [m for m in models if m.get("capabilities", {}).get("attachment", False)]
        
        return {
            "primary_recommendation": {
                "model": f"{best_model['provider']}/{best_model['model']}",
                "reason": f"Highest integration score ({best_model['integration_score']}%) with excellent capabilities",
                "best_for": best_model.get("recommended_uses", [])[:3]
            },
            "alternative_options": [
                {
                    "model": f"{m['provider']}/{m['model']}",
                    "strength": m.get("recommended_uses", ["General use"])[0]
                }
                for m in models[1:4]  # Top 3 alternatives
            ],
            "integration_suggestions": [
                "Use opencode/big-pickle for general reasoning and tool calling",
                "Use opencode/grok-code for attachment support and larger context",
                "Consider implementing model switching based on task requirements"
            ]
        }
    
    def _cache_results(self, models: List[Dict]):
        """Cache scan results"""
        try:
            cache_data = {
                "models": models,
                "timestamp": datetime.now().timestamp(),
                "version": self.version
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to cache results: {e}")
    
    def get_cached_results(self) -> Optional[Dict]:
        """Get cached scan results if still valid"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            timestamp = cache_data.get("timestamp", 0)
            if datetime.now().timestamp() - timestamp > self.cache_ttl:
                return None
            
            return cache_data
        except Exception:
            return None
    
    def monitor_for_new_models(self) -> Dict:
        """
        Monitor for new free models since last scan
        """
        cached = self.get_cached_results()
        if not cached:
            return self.scan_free_models()
        
        # Current scan
        current = self.scan_free_models()
        
        if not current.get("success"):
            return current
        
        # Compare with cached results
        cached_models = {f"{m['provider']}/{m['model']}" for m in cached.get("models", [])}
        current_models = {f"{m['provider']}/{m['model']}" for m in current.get("models", [])}
        
        new_models = current_models - cached_models
        removed_models = cached_models - current_models
        
        return {
            **current,
            "new_models": [m for m in current.get("models", []) 
                          if f"{m['provider']}/{m['model']}" in new_models],
            "removed_models": list(removed_models),
            "has_changes": len(new_models) > 0 or len(removed_models) > 0
        }
    
    def generate_integration_code(self, model: Dict) -> str:
        """
        Generate code snippets for integrating a specific model
        """
        provider = model.get("provider")
        model_id = model.get("model")
        capabilities = model.get("capabilities", {})
        
        code = f"""
// Integration code for {provider}/{model_id}
// Generated by Free Model Scanner

// Model Configuration
const modelConfig = {{
  provider: "{provider}",
  model: "{model_id}",
  capabilities: {{
    reasoning: {capabilities.get("reasoning", False)},
    tool_call: {capabilities.get("tool_call", False)},
    temperature: {capabilities.get("temperature", False)},
    attachment: {capabilities.get("attachment", False)}
  }},
  limits: {{
    context: {model.get("limits", {}).get("context", 0)},
    output: {model.get("limits", {}).get("output", 0)}
  }}
}}

// Usage Example
async function useModel(prompt) {{
  const response = await opencode.run(prompt, {{
    model: "{provider}/{model_id}",
    // Add any additional options based on capabilities
    {', temperature: 0.7' if capabilities.get("temperature") else ''}
    {', tools: ["file_manager", "web_search"]' if capabilities.get("tool_call") else ''}
  }})
  
  return response
}}

// Recommended for: {', '.join(model.get("recommended_uses", ["General use"]))}
"""
        return code.strip()

def main():
    """Main function for CLI usage"""
    scanner = FreeModelScanner()
    
    if len(sys.argv) < 2:
        print("Usage: python free_model_scanner.py [scan|monitor|generate <provider/model>]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "scan":
        force_refresh = "--refresh" in sys.argv
        result = scanner.scan_free_models(force_refresh)
        
        if result.get("success"):
            print(f"[SUCCESS] Found {result['total_found']} free models")
            print(f"[INFO] Scan time: {result['scan_time']}")
            print("\n[TOP MODELS]:")
            for i, model in enumerate(result["models"][:5], 1):
                print(f"{i}. {model['provider']}/{model['model']} - Score: {model['integration_score']}%")
            
            print(f"\n[RECOMMENDATIONS]:")
            recs = result.get("recommendations", {})
            if recs.get("primary_recommendation"):
                primary = recs["primary_recommendation"]
                print(f"Primary: {primary['model']}")
                print(f"Reason: {primary['reason']}")
        else:
            print(f"[ERROR] Scan failed: {result.get('error')}")
    
    elif command == "monitor":
        result = scanner.monitor_for_new_models()
        
        if result.get("has_changes"):
            print(f"[NEW] {len(result.get('new_models', []))} new models found!")
            for model in result.get("new_models", []):
                print(f"  + {model['provider']}/{model['model']}")
        else:
            print("[INFO] No new free models found")
    
    elif command == "generate" and len(sys.argv) >= 3:
        model_spec = sys.argv[2]
        # First scan to get model info
        scan_result = scanner.scan_free_models()
        
        if scan_result.get("success"):
            target_model = None
            for model in scan_result["models"]:
                if f"{model['provider']}/{model['model']}" == model_spec:
                    target_model = model
                    break
            
            if target_model:
                code = scanner.generate_integration_code(target_model)
                print(code)
            else:
                print(f"[ERROR] Model {model_spec} not found in free models")
        else:
            print(f"[ERROR] Failed to scan models: {scan_result.get('error')}")
    
    else:
        print("[ERROR] Invalid command")
        print("Usage: python free_model_scanner.py [scan|monitor|generate <provider/model>]")

if __name__ == "__main__":
    main()