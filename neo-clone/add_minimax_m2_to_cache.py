#!/usr/bin/env python3
"""
Add MiniMax M2 to Free Models Cache

This script adds MiniMax M2 to the free_models_cache.json file
so it appears in the model selection interface.
"""

import json

def add_minimax_m2_to_cache():
    """Add MiniMax M2 model to the free models cache"""
    
    # Load existing cache
    with open('free_models_cache.json', 'r') as f:
        cache_data = json.load(f)
    
    # Create MiniMax M2 model entry
    minimax_m2_model = {
        "provider": "minimax",
        "model": "m2",
        "name": "MiniMax M2",
        "cost": {
            "input": 0,
            "output": 0,
            "cache_read": 0,
            "cache_write": 0,
            "is_free": True,
            "tier": "free"
        },
        "capabilities": {
            "reasoning": True,
            "tool_call": True,
            "temperature": True,
            "attachment": False
        },
        "limits": {
            "context": 128000,
            "output": 64000
        },
        "release_date": "2024-01-01",
        "integration_score": 90.0,
        "integration_ready": True,
        "recommended_uses": [
            "Complex reasoning",
            "Large document analysis", 
            "Advanced problem solving",
            "Code generation",
            "Content creation"
        ],
        "integration_complexity": "low",
        "model_size": "Large"
    }
    
    # Add MiniMax M2 to models list
    cache_data["models"].append(minimax_m2_model)
    
    # Update total model count
    cache_data["total_models"] = len(cache_data["models"])
    
    # Update timestamp
    from datetime import datetime
    cache_data["timestamp"] = datetime.now().timestamp()
    
    # Save updated cache
    with open('free_models_cache.json', 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    print("✅ MiniMax M2 successfully added to free models cache!")
    print(f"📊 Total models now: {cache_data['total_models']}")
    print("🎯 Model will now appear in model selection interface")

if __name__ == "__main__":
    add_minimax_m2_to_cache()
