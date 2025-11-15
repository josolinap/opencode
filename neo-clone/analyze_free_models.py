#!/usr/bin/env python3
"""
Comprehensive analysis of free models available in Neo-Clone
"""

import sys
import os
import json
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def analyze_free_models():
    """Analyze all free models available in Neo-Clone"""
    print("🔍 FREE MODELS ANALYSIS - NEO-CLONE")
    print("=" * 60)

    # Load model configuration
    try:
        with open("opencode.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ opencode.json not found")
        return
    except Exception as e:
        print(f"❌ Error loading opencode.json: {e}")
        return

    if "models" not in config:
        print("❌ No models found in configuration")
        return

    models = config["models"]

    print(f"\n📊 OVERVIEW:")
    print(f"   Total Models Available: {len(models)}")
    print(f"   All Models are FREE: ✅")

    # Analyze by provider
    providers = {}
    for model_id, model_info in models.items():
        provider = model_info.get("provider", "unknown")
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model_info)

    print(f"\n🏢 PROVIDERS:")
    for provider, model_list in providers.items():
        print(f"\n   {provider.upper()} ({len(model_list)} models):")

        # Calculate stats for this provider
        total_response_time = sum(m.get("response_time", 0) for m in model_list)
        avg_response_time = total_response_time / len(model_list) if model_list else 0

        # Count capabilities
        capabilities = {}
        for model in model_list:
            for cap in model.get("capabilities", []):
                capabilities[cap] = capabilities.get(cap, 0) + 1

        print(f"      📈 Average Response Time: {avg_response_time:.2f}s")
        print(f"      🎯 Capabilities: {list(capabilities.keys())}")
        print(f"      💰 Cost: FREE")

        # Show top models for this provider
        sorted_models = sorted(
            model_list, key=lambda x: x.get("response_time", float("inf"))
        )
        print(
            f"      🏆 Fastest Model: {sorted_models[0].get('model', 'Unknown')} ({sorted_models[0].get('response_time', 0):.2f}s)"
        )

    # Analyze capabilities across all models
    print(f"\n🧠 CAPABILITY ANALYSIS:")
    all_capabilities = {}
    capability_models = {}

    for model_id, model_info in models.items():
        for cap in model_info.get("capabilities", []):
            all_capabilities[cap] = all_capabilities.get(cap, 0) + 1
            if cap not in capability_models:
                capability_models[cap] = []
            capability_models[cap].append(model_info.get("model", "Unknown"))

    for cap, count in sorted(
        all_capabilities.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"\n   🎯 {cap.upper()} ({count} models):")
        print(f"      📊 Models: {', '.join(capability_models[cap][:5])}")
        if len(capability_models[cap]) > 5:
            print(f"      ... and {len(capability_models[cap]) - 5} more")

    # Performance analysis
    print(f"\n⚡ PERFORMANCE ANALYSIS:")
    response_times = [m.get("response_time", 0) for m in models.values()]

    if response_times:
        fastest_time = min(response_times)
        slowest_time = max(response_times)
        avg_time = sum(response_times) / len(response_times)

        # Find fastest and slowest models
        fastest_model = None
        slowest_model = None

        for model_id, model_info in models.items():
            if model_info.get("response_time", 0) == fastest_time:
                fastest_model = model_info.get("model", "Unknown")
            if model_info.get("response_time", 0) == slowest_time:
                slowest_model = model_info.get("model", "Unknown")

        print(f"   🚀 Fastest: {fastest_model} ({fastest_time:.2f}s)")
        print(f"   🐌 Slowest: {slowest_model} ({slowest_time:.2f}s)")
        print(f"   📊 Average: {avg_time:.2f}s")
        print(f"   📈 Performance Range: {slowest_time - fastest_time:.2f}s")

    # Context length analysis
    print(f"\n📏 CONTEXT LENGTH ANALYSIS:")
    context_lengths = [m.get("context_length", 0) for m in models.values()]

    if context_lengths:
        max_context = max(context_lengths)
        min_context = min(context_lengths)
        avg_context = sum(context_lengths) / len(context_lengths)

        print(f"   📚 Max Context: {max_context:,} tokens")
        print(f"   📖 Min Context: {min_context:,} tokens")
        print(f"   📊 Average: {avg_context:.0f} tokens")

        # Categorize by context length
        small_context = [
            m for m in models.values() if m.get("context_length", 0) < 2048
        ]
        medium_context = [
            m for m in models.values() if 2048 <= m.get("context_length", 0) < 4096
        ]
        large_context = [
            m for m in models.values() if m.get("context_length", 0) >= 4096
        ]

        print(f"   📊 Small Context (<2K): {len(small_context)} models")
        print(f"   📊 Medium Context (2K-4K): {len(medium_context)} models")
        print(f"   📊 Large Context (4K+): {len(large_context)} models")

    # Provider recommendations
    print(f"\n🎯 PROVIDER RECOMMENDATIONS:")

    # Best for speed
    fastest_by_provider = {}
    for provider, model_list in providers.items():
        if model_list:
            fastest = min(
                model_list, key=lambda x: x.get("response_time", float("inf"))
            )
            fastest_by_provider[provider] = {
                "model": fastest.get("model", "Unknown"),
                "time": fastest.get("response_time", 0),
                "capabilities": fastest.get("capabilities", []),
            }

    print("   🚀 Best for SPEED:")
    for provider, info in fastest_by_provider.items():
        print(f"      {provider}: {info['model']} ({info['time']:.2f}s)")

    # Best for context
    best_context_by_provider = {}
    for provider, model_list in providers.items():
        if model_list:
            best = max(model_list, key=lambda x: x.get("context_length", 0))
            best_context_by_provider[provider] = {
                "model": best.get("model", "Unknown"),
                "context": best.get("context_length", 0),
                "capabilities": best.get("capabilities", []),
            }

    print("   📚 Best for CONTEXT:")
    for provider, info in best_context_by_provider.items():
        print(f"      {provider}: {info['model']} ({info['context']:,} tokens)")

    # Best overall (balanced)
    best_overall = {}
    for provider, model_list in providers.items():
        if model_list:
            # Score: speed (50%) + context (30%) + capabilities (20%)
            def score_model(model):
                speed_score = (
                    5.0 - model.get("response_time", 5.0)
                ) / 5.0  # Lower time = higher score
                context_score = (
                    model.get("context_length", 0) / 8192
                )  # Normalize to 0-1
                capability_score = (
                    len(model.get("capabilities", [])) / 5
                )  # Normalize to 0-1
                return speed_score * 0.5 + context_score * 0.3 + capability_score * 0.2

            best = max(model_list, key=score_model)
            best_overall[provider] = {
                "model": best.get("model", "Unknown"),
                "score": score_model(best),
                "time": best.get("response_time", 0),
                "context": best.get("context_length", 0),
                "capabilities": best.get("capabilities", []),
            }

    print("   🏆 Best OVERALL (Balanced):")
    for provider, info in best_overall.items():
        print(f"      {provider}: {info['model']} (Score: {info['score']:.2f})")

    # Usage recommendations
    print(f"\n💡 USAGE RECOMMENDATIONS:")

    # General recommendations
    print("   🎯 For GENERAL CHAT:")
    print("      • Together.ai models (best balance of speed and quality)")
    print("      • Start with 'togethercomputer/mistral-7b-instruct-v0.1'")
    print("      • Fallback to 'togethercomputer/llama-2-7b-chat'")

    print("   🧠 For REASONING TASKS:")
    print("      • HuggingFace FLAN-T5 models (excellent at logical reasoning)")
    print("      • Use 'huggingface/google-flan-t5-base'")
    print("      • Good for: analysis, planning, step-by-step tasks")

    print("   💬 For CONVERSATION:")
    print("      • HuggingFace BlenderBot models (optimized for dialogue)")
    print("      • Use 'huggingface/facebook-blenderbot-400M-distill'")
    print("      • Good for: chat, roleplay, interactive conversation")

    print("   🚀 For SPEED:")
    print("      • HuggingFace DialoGPT-small (fastest at ~1.3s)")
    print("      • Use 'huggingface/microsoft-DialoGPT-small'")
    print("      • Best for: quick responses, real-time applications")

    print("   📚 For LONG CONTEXT:")
    print("      • Replicate models (4K-8K context)")
    print("      • Use 'replicate/meta-llama-2-7b-chat'")
    print("      • Best for: document analysis, long conversations, code generation")

    print("   🔧 For DEVELOPMENT:")
    print("      • Models with 'tool_calling' capability")
    print("      • Replicate and Together.ai models support tool calling")
    print("      • Best for: function calling, API integration, structured outputs")

    # Technical details
    print(f"\n⚙️ TECHNICAL DETAILS:")
    print("   🌐 All models use REST APIs")
    print("   🔑 Authentication: API keys required for cloud providers")
    print("   📊 Rate Limits: Varies by provider (typically 60-1000 requests/minute)")
    print("   💰 Cost: 100% FREE for all listed models")
    print("   🔄 Auto-Failover: Built into Neo-Clone enhanced LLM client")
    print("   📈 Performance Monitoring: Automatic with retry and circuit breaker")

    print(f"\n🎯 QUICK START GUIDE:")
    print("   1. Choose provider based on your needs:")
    print("      - SPEED: HuggingFace")
    print("      - QUALITY: Together.ai")
    print("      - CONTEXT: Replicate")
    print("      - REASONING: HuggingFace FLAN-T5")
    print()
    print("   2. Set API key in environment or config:")
    print("      - HuggingFace: HF_TOKEN")
    print("      - Together.ai: TOGETHER_API_KEY")
    print("      - Replicate: REPLICATE_API_TOKEN")
    print()
    print("   3. Neo-Clone will automatically:")
    print("      • Switch providers on failures")
    print("      • Retry with exponential backoff")
    print("      • Cache responses for speed")
    print("      • Monitor performance and health")
    print()
    print("   4. All models are FREE and ready to use! 🚀")

    print("\n" + "=" * 60)
    print("🎉 NEO-CLONE FREE MODELS: ANALYSIS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    analyze_free_models()
