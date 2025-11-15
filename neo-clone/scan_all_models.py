#!/usr/bin/env python3
import asyncio
from enhanced_model_discovery import create_enhanced_model_discovery_module

async def main():
    print("Scanning for ALL available free models...")
    print("=" * 60)
    
    # Create and initialize module
    md = create_enhanced_model_discovery_module()
    await md.initialize()
    
    # Get comprehensive statistics
    stats = md.get_enhanced_stats()
    print(f"Total models discovered: {stats['total_models']}")
    print(f"Free models: {stats['free_models']}")
    print(f"Providers: {', '.join(stats['providers'])}")
    
    # Get all free models
    free_models = md.get_free_models()
    print(f"\nCOMPLETE FREE MODELS LIST ({len(free_models)} total):")
    print("-" * 60)
    
    for i, model in enumerate(free_models, 1):
        caps = [cap for cap, enabled in model.capabilities.to_dict().items() if enabled]
        print(f"{i:2d}. {model.get_full_id()}")
        print(f"    Score: {model.integration_score:.1f}% | Context: {model.limits.context_tokens:,}")
        print(f"    Capabilities: {', '.join(caps[:3])}{'...' if len(caps) > 3 else ''}")
        print(f"    Provider: {model.provider} | Status: {model.health.status.value}")
        print()
    
    # Provider breakdown
    print("\nPROVIDER BREAKDOWN:")
    print("-" * 60)
    for provider, provider_stats in stats['provider_stats'].items():
        if provider_stats['free'] > 0:
            print(f"{provider.upper()}: {provider_stats['free']} free models")
    
    # Cache efficiency
    cache_stats = stats['cache_stats']
    print(f"\nCACHE EFFICIENCY:")
    print(f"   Total cached: {cache_stats['total_models']} models")
    print(f"   Avoided rescans: {stats['cache_efficiency']['avoided_rescans']}")
    
    await md.shutdown()

if __name__ == "__main__":
    asyncio.run(main())