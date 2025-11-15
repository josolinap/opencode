#!/usr/bin/env python3
"""
Free models analysis for Neo-Clone - Simple version
"""

import sys
import os
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def analyze_free_models():
    """Analyze free models available in Neo-Clone"""
    print("FREE MODELS ANALYSIS - NEO-CLONE")
    print("=" * 50)

    # Load model configuration
    try:
        with open("opencode.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("ERROR: opencode.json not found")
        return
    except Exception as e:
        print(f"ERROR: Failed to load opencode.json: {e}")
        return

    if "models" not in config:
        print("ERROR: No models found in configuration")
        return

    models = config["models"]

    print(f"Total Models Available: {len(models)}")
    print("All Models are FREE")
    print()

    # Analyze by provider
    providers = {}
    for model_id, model_info in models.items():
        provider = model_info.get("provider", "unknown")
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model_info)

    print("PROVIDERS:")
    for provider, model_list in providers.items():
        print(f"{provider.upper()} ({len(model_list)} models):")

        # Calculate stats
        response_times = [m.get("response_time", 0) for m in model_list]
        avg_time = sum(response_times) / len(response_times) if response_times else 0

        # Count capabilities
        all_caps = []
        for model in model_list:
            all_caps.extend(model.get("capabilities", []))
        unique_caps = list(set(all_caps))

        print(f"  Average Response Time: {avg_time:.2f}s")
        print(f"  Capabilities: {unique_caps}")
        print(f"  Cost: FREE")

        # Show fastest model
        if model_list:
            fastest = min(
                model_list, key=lambda x: x.get("response_time", float("inf"))
            )
            print(
                f"  Fastest Model: {fastest.get('model', 'Unknown')} ({fastest.get('response_time', 0):.2f}s)"
            )
        print()

    # Show top 5 fastest models overall
    all_models = list(models.values())
    all_models.sort(key=lambda x: x.get("response_time", float("inf")))

    print("TOP 5 FASTEST MODELS:")
    for i, model in enumerate(all_models[:5], 1):
        print(
            f"{i}. {model.get('model', 'Unknown')} ({model.get('provider', 'Unknown')}) - {model.get('response_time', 0):.2f}s"
        )

    print()
    print("CAPABILITY BREAKDOWN:")

    # Count capabilities across all models
    capability_count = {}
    for model in models.values():
        for cap in model.get("capabilities", []):
            capability_count[cap] = capability_count.get(cap, 0) + 1

    for cap, count in sorted(
        capability_count.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"{cap}: {count} models")

    print()
    print("RECOMMENDATIONS:")
    print("For SPEED: HuggingFace models (DialoGPT-small fastest)")
    print("For QUALITY: Together.ai models (mistral-7b-instruct-v0.1)")
    print("For CONTEXT: Replicate models (4K-8K context)")
    print("For REASONING: HuggingFace FLAN-T5 models")
    print()

    print("HOW IT WORKS WITH NEO-CLONE:")
    print("1. All models are FREE - no API costs")
    print("2. Auto-failover between providers on failures")
    print("3. Automatic retry with exponential backoff")
    print("4. Response caching for speed")
    print("5. Performance monitoring and health checks")
    print("6. Circuit breaker protection")
    print()

    print("QUICK START:")
    print("1. Choose your use case:")
    print("   - General chat: Together.ai mistral-7b-instruct-v0.1")
    print("   - Fast responses: HuggingFace microsoft-DialoGPT-small")
    print("   - Long context: Replicate meta-llama-2-7b-chat")
    print("   - Reasoning tasks: HuggingFace google-flan-t5-base")
    print()
    print("2. Set API key in environment:")
    print("   - HuggingFace: HF_TOKEN")
    print("   - Together.ai: TOGETHER_API_KEY")
    print("   - Replicate: REPLICATE_API_TOKEN")
    print()
    print("3. Neo-Clone handles the rest automatically!")

    print("=" * 50)
    print("ANALYSIS COMPLETE!")
    print("=" * 50)


if __name__ == "__main__":
    analyze_free_models()
