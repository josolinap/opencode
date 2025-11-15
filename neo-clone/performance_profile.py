#!/usr/bin/env python3
"""
Performance Profiling Script for Neo-Clone Components

Identifies bottlenecks and optimization opportunities.
"""

import asyncio
import time
import sys
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce log noise

class PerformanceProfiler:
    def __init__(self):
        self.results = {}

    async def profile_model_discovery(self) -> Dict[str, Any]:
        """Profile model discovery initialization"""
        print("Profiling Enhanced Model Discovery...")

        start_total = time.time()
        results = {}

        try:
            sys.path.append('.')
            from enhanced_model_discovery import create_enhanced_model_discovery_module

            # Time individual discovery sources
            discovery = create_enhanced_model_discovery_module()

            # Profile cache loading
            start = time.time()
            # Cache is loaded in __init__, so we can't easily separate this

            # Profile discovery initialization
            start_discovery = time.time()
            await discovery.initialize()
            discovery_time = time.time() - start_discovery

            total_time = time.time() - start_total

            stats = discovery.get_enhanced_stats()

            results = {
                'total_time': total_time,
                'discovery_time': discovery_time,
                'models_loaded': stats['total_models'],
                'free_models': stats['free_models'],
                'cache_stats': stats['cache_stats'],
                'providers': list(stats['provider_stats'].keys())
            }

        except Exception as e:
            results = {'error': str(e), 'total_time': time.time() - start_total}

        return results

    def profile_memory_system(self) -> Dict[str, Any]:
        """Profile memory system initialization"""
        print("Profiling Memory System...")

        start = time.time()
        results = {}

        try:
            sys.path.append('.')
            from memory import get_memory

            memory = get_memory()
            init_time = time.time() - start

            # Get memory stats
            stats = memory.get_statistics()

            results = {
                'init_time': init_time,
                'conversations': stats.get('total_conversations', 0),
                'session_id': stats.get('session_id', 'N/A'),
                'memory_dir': stats.get('memory_dir', 'N/A')
            }

        except Exception as e:
            results = {'error': str(e), 'init_time': time.time() - start}

        return results

    def profile_skills_system(self) -> Dict[str, Any]:
        """Profile skills system initialization"""
        print("Profiling Skills System...")

        start = time.time()
        results = {}

        try:
            sys.path.append('.')
            from skills import SkillsManager

            skills = SkillsManager()
            init_time = time.time() - start

            skill_list = skills.list_skills()

            results = {
                'init_time': init_time,
                'skill_count': len(skill_list),
                'skills': skill_list[:5]  # First 5 skills
            }

        except Exception as e:
            results = {'error': str(e), 'init_time': time.time() - start}

        return results

    async def run_full_profile(self) -> Dict[str, Any]:
        """Run complete performance profile"""
        print("Running Neo-Clone Performance Profile")
        print("=" * 50)

        results = {}

        # Profile individual components
        results['model_discovery'] = await self.profile_model_discovery()
        results['memory_system'] = self.profile_memory_system()
        results['skills_system'] = self.profile_skills_system()

        # Calculate totals
        total_time = sum(
            component.get('total_time', component.get('init_time', 0))
            for component in results.values()
            if isinstance(component, dict)
        )

        results['summary'] = {
            'total_init_time': total_time,
            'components_profiled': len(results) - 1,  # Exclude summary
            'timestamp': time.time()
        }

        return results

    def print_results(self, results: Dict[str, Any]):
        """Print formatted results"""
        print("\nPerformance Profile Results")
        print("=" * 50)

        for component, data in results.items():
            if component == 'summary':
                continue

            print(f"\n{component.upper().replace('_', ' ')}:")
            print("-" * 30)

            if 'error' in data:
                print(f"  ERROR: {data['error']}")
                continue

            for key, value in data.items():
                if key == 'skills' and isinstance(value, list):
                    print(f"  {key}: {len(value)} loaded")
                elif isinstance(value, float):
                    print(f"  {key}: {value:.3f}s")
                else:
                    print(f"  {key}: {value}")

        # Summary
        summary = results.get('summary', {})
        print("\nSUMMARY:")
        print("-" * 30)
        print(f"  Total initialization time: {summary.get('total_init_time', 0):.3f}s")
        print(f"  Components profiled: {summary.get('components_profiled', 0)}")

        # Identify bottlenecks
        print("\nBottlenecks:")
        print("-" * 30)

        for component, data in results.items():
            if component == 'summary':
                continue

            init_time = data.get('total_time', data.get('init_time', 0))
            if init_time > 0.5:  # More than 500ms is considered slow
                print(f"  {component}: {init_time:.3f}s (SLOW)")

def main():
    """Main profiling function"""
    profiler = PerformanceProfiler()

    # Run profile
    results = asyncio.run(profiler.run_full_profile())

    # Print results
    profiler.print_results(results)

    # Save results
    import json
    with open('performance_profile.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\nResults saved to performance_profile.json")

if __name__ == "__main__":
    main()