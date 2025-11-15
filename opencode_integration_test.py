#!/usr/bin/env python3
"""
OpenCode Integration Test
=========================

Quick test to verify all OpenCode improvements are working correctly.
This script can be run locally to test the improved components.

Author: MiniMax Agent
Version: 3.0
"""

import sys
import os
import time
from datetime import datetime

def test_unified_brain():
    """Test the unified brain system"""
    print("🧠 Testing Unified Brain System...")
    
    try:
        from opencode_unified_brain import UnifiedBrain, MemoryType, ProcessingMode
        
        # Create brain instance
        brain = UnifiedBrain()
        
        # Test memory system
        brain.memory.store("test_key", "test_value", MemoryType.WORKING)
        retrieved = brain.memory.retrieve("test_key")
        assert retrieved == "test_value", "Memory system test failed"
        
        # Test model selection
        model = brain.model_engine.select_model("coding", complexity="moderate")
        assert model in brain.model_engine.models, "Model selection failed"
        
        # Test skill system
        skills = brain.skill_system.list_skills()
        assert len(skills) > 0, "Skills system failed"
        
        print("  ✅ Memory system working")
        print("  ✅ Model selection working")
        print(f"  ✅ {len(skills)} skills loaded")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Unified brain test failed: {e}")
        return False

def test_skills_manager():
    """Test the skills manager"""
    print("🔧 Testing Skills Manager...")
    
    try:
        from opencode_skills_manager import SkillsManager
        
        # Create skills manager
        manager = SkillsManager()
        
        # Test skill listing
        skills = manager.list_skills()
        assert len(skills) > 0, "No skills loaded"
        
        # Test skill execution
        test_code = """
def hello():
    return "Hello, World!"
"""
        
        result = manager.execute_skill("analyze_python_syntax", code=test_code)
        assert result['success'], f"Skill execution failed: {result.get('error')}"
        
        print(f"  ✅ {len(skills)} skills loaded")
        print("  ✅ Skill execution working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Skills manager test failed: {e}")
        return False

def test_performance_monitor():
    """Test the performance monitor"""
    print("📊 Testing Performance Monitor...")
    
    try:
        from opencode_performance_monitor import PerformanceMonitor
        
        # Create monitor
        monitor = PerformanceMonitor(max_history_size=100)
        
        # Record some test metrics
        monitor.record_skill_execution("test_skill", 0.5, True)
        monitor.record_skill_execution("test_skill", 0.3, False, "Test error")
        monitor.record_model_performance("test_model", "test_provider", 1.5, True, 1024)
        
        # Get system status
        status = monitor.get_current_system_status()
        assert 'cpu' in status, "System status failed"
        
        # Get performance report
        overall = monitor.get_overall_performance()
        assert 'request_statistics' in overall, "Performance report failed"
        
        print("  ✅ System monitoring working")
        print("  ✅ Performance tracking working")
        print(f"  ✅ {overall['request_statistics']['total_requests']} requests tracked")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance monitor test failed: {e}")
        return False

def test_integration():
    """Test integration between components"""
    print("🔗 Testing Component Integration...")
    
    try:
        from opencode_unified_brain import UnifiedBrain
        from opencode_skills_manager import SkillsManager
        from opencode_performance_monitor import PerformanceMonitor, BrainPerformanceIntegration
        
        # Create integrated system
        brain = UnifiedBrain()
        monitor = PerformanceMonitor()
        integration = BrainPerformanceIntegration(brain, monitor)
        
        # Test skill execution with monitoring
        def dummy_skill():
            time.sleep(0.1)
            return "Skill result"
            
        result = integration.wrap_skill_execution("test_skill", dummy_skill)
        assert result == "Skill result", "Integration test failed"
        
        # Check if monitoring recorded the execution
        skill_perf = monitor.get_skill_performance(1)  # Last minute
        assert skill_perf['total_executions'] > 0, "Skill monitoring failed"
        
        print("  ✅ Component integration working")
        print("  ✅ Performance monitoring integration working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def run_performance_benchmark():
    """Run a simple performance benchmark"""
    print("⚡ Running Performance Benchmark...")
    
    try:
        from opencode_skills_manager import SkillsManager
        
        manager = SkillsManager()
        
        # Benchmark skill execution
        start_time = time.time()
        successful_executions = 0
        total_executions = 10
        
        for i in range(total_executions):
            result = manager.execute_skill("analyze_python_syntax", 
                                         code=f"# Test code {i}\ndef test(): pass")
            if result['success']:
                successful_executions += 1
                
        execution_time = time.time() - start_time
        avg_time = execution_time / total_executions
        success_rate = (successful_executions / total_executions) * 100
        
        print(f"  ✅ {total_executions} skill executions completed")
        print(f"  ✅ Average execution time: {avg_time:.3f}s")
        print(f"  ✅ Success rate: {success_rate:.1f}%")
        
        # Benchmark memory operations
        from opencode_unified_brain import UnifiedBrain
        brain = UnifiedBrain()
        
        start_time = time.time()
        for i in range(100):
            brain.memory.store(f"bench_key_{i}", f"value_{i}")
        memory_time = time.time() - start_time
        
        print(f"  ✅ Memory operations: 100 writes in {memory_time:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance benchmark failed: {e}")
        return False

def show_system_info():
    """Show system information"""
    print("💻 System Information:")
    print(f"  Python version: {sys.version}")
    print(f"  Platform: {sys.platform}")
    print(f"  Current time: {datetime.now()}")
    
    try:
        import psutil
        print(f"  CPU cores: {psutil.cpu_count()}")
        print(f"  Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    except ImportError:
        print("  psutil not installed (needed for performance monitoring)")

def main():
    """Main test runner"""
    print("🚀 OpenCode Integration Test Suite v3.0")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    show_system_info()
    print()
    
    # Run all tests
    tests = [
        ("Unified Brain", test_unified_brain),
        ("Skills Manager", test_skills_manager),
        ("Performance Monitor", test_performance_monitor),
        ("Integration", test_integration),
        ("Performance Benchmark", run_performance_benchmark)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ {test_name} crashed: {e}")
            results.append((test_name, False))
            
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your OpenCode improvements are working correctly!")
        print("\nNext steps:")
        print("1. Deploy to remote machine")
        print("2. Run: python opencode_launcher.py")
        print("3. Enjoy the improved OpenCode system!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        print("Please check the error messages above and ensure all dependencies are installed.")
        
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())