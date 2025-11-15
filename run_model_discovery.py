#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from enhanced_model_discovery import create_enhanced_model_discovery_module

async def main():
    print("Running Enhanced Model Discovery...")

    # Create and initialize module
    model_discovery = create_enhanced_model_discovery_module()
    await model_discovery.initialize()

    print("\n=== MODEL DISCOVERY RESULTS ===")
    stats = model_discovery.get_enhanced_stats()
    print(f"Total models discovered: {stats['total_models']}")
    print(f"Free models: {stats['free_models']}")
    print(f"Providers: {', '.join(stats['providers'])}")

    print("\n=== PROVIDER BREAKDOWN ===")
    for provider, provider_stats in stats['provider_stats'].items():
        print(f"{provider.upper()}: {provider_stats['total']} models ({provider_stats['free']} free)")

    print("\n=== TOP FREE MODELS ===")
    free_models = model_discovery.get_free_models()
    for i, model in enumerate(free_models[:15], 1):
        print(f"{i:2d}. {model.get_full_id()}")
        print(f"    Score: {model.integration_score:.1f}% | Context: {model.limits.context_tokens:,}")
        caps = [cap for cap, enabled in model.capabilities.to_dict().items() if enabled]
        print(f"    Capabilities: {', '.join(caps[:4])}")
        print()

    await model_discovery.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
