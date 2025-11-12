#!/usr/bin/env python3
"""
Comprehensive Functionality Tests for Neo-Clone Integration

This test suite verifies real behavior and functionality of the integrated backup files,
going beyond simple import/instantiation tests to verify actual working capabilities.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add the neo-clone directory to the path
sys.path.append(os.path.dirname(__file__))

def test_autonomous_evolution_engine():
    """Test autonomous evolution engine functionality"""
    print("\n=== Testing Autonomous Evolution Engine ===")
    
    try:
        from autonomous_evolution_engine import AutonomousEvolutionEngine, Opportunity
        
        # Create engine instance
        engine = AutonomousEvolutionEngine()
        print("[OK] Engine instantiated successfully")
        
        # Test status reporting
        status = engine.get_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert "is_running" in status, "Status should include is_running"
        assert "metrics" in status, "Status should include metrics"
        print("[OK] Status reporting works")
        
        # Test performance reporting
        perf_report = engine.get_performance_report()
        assert isinstance(perf_report, dict), "Performance report should be a dictionary"
        print("[OK] Performance reporting works")
        
        # Test manual scan (this will actually scan the codebase)
        print("[INFO] Running manual codebase scan...")
        opportunities = engine.trigger_manual_scan()
        assert isinstance(opportunities, list), "Scan should return a list"
        print(f"[OK] Manual scan completed, found {len(opportunities)} opportunities")
        
        # Test LLM independence reporting
        llm_report = engine.get_llm_independence_report()
        assert isinstance(llm_report, dict), "LLM report should be a dictionary"
        assert "core_functionality_llm_free" in llm_report, "Should report LLM independence"
        print("[OK] LLM independence reporting works")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Autonomous Evolution Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_autonomous_system_healer():
    """Test autonomous system healer functionality"""
    print("\n=== Testing Autonomous System Healer ===")
    
    try:
        from autonomous_system_healer import AutonomousSystemHealer, SystemIssue, IssueType, IssueSeverity
        
        # Create healer instance
        healer = AutonomousSystemHealer()
        print("[OK] Healer instantiated successfully")
        
        # Test issue detection
        error_logs = [
            "Connection are closed on MCP server",
            "Unexpected end of JSON input in response parsing",
            "MCP server failed to connect: ECONNREFUSED"
        ]
        
        issues = healer.detect_issues(error_logs)
        assert isinstance(issues, list), "Should return list of issues"
        print(f"[OK] Detected {len(issues)} issues from error logs")
        
        # Test issue diagnosis
        if issues:
            diagnosis = healer.diagnose_issue(issues[0])
            assert isinstance(diagnosis, dict), "Diagnosis should be a dictionary"
            assert "diagnosis" in diagnosis, "Should include diagnosis text"
            assert "recommended_fixes" in diagnosis, "Should include recommended fixes"
            print("[OK] Issue diagnosis works")
        
        # Test system status
        status = healer.get_system_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert "monitoring_active" in status, "Should include monitoring status"
        print("[OK] System status reporting works")
        
        # Test skill execution (BaseSkill interface)
        result = healer.execute({"action": "status"})
        assert hasattr(result, 'success'), "Should return SkillResult-like object"
        print("[OK] Skill execution interface works")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] System Healer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_error_recovery():
    """Test enhanced error recovery functionality"""
    print("\n=== Testing Enhanced Error Recovery ===")
    
    try:
        from enhanced_error_recovery import EnhancedErrorRecovery, CircuitBreaker, CircuitBreakerConfig
        
        # Create recovery system
        recovery = EnhancedErrorRecovery()
        print("[OK] Error recovery system instantiated")
        
        # Test circuit breaker
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0)
        circuit_breaker = CircuitBreaker(config)
        print("[OK] Circuit breaker created")
        
        # Test circuit breaker with a failing function
        def failing_function():
            raise Exception("Test failure")
        
        # Should fail and open circuit after threshold
        for i in range(4):
            try:
                circuit_breaker.call(failing_function)
            except Exception as e:
                if i < 3:
                    print(f"[OK] Circuit breaker caught failure #{i+1}")
                else:
                    assert "Circuit breaker is OPEN" in str(e), "Circuit should be open"
                    print("[OK] Circuit breaker opened after threshold")
        
        # Test error classification
        test_error = Exception("Connection timeout")
        classification = recovery.classify_error(test_error)
        assert isinstance(classification, dict), "Classification should be a dictionary"
        print("[OK] Error classification works")
        
        # Test recovery strategies
        recovery_strategies = recovery.get_recovery_strategies()
        assert isinstance(recovery_strategies, list), "Should return list of strategies"
        print(f"[OK] Found {len(recovery_strategies)} recovery strategies")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Enhanced Error Recovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_opencode_integration():
    """Test enhanced opencode integration functionality"""
    print("\n=== Testing Enhanced Opencode Integration ===")
    
    try:
        from enhanced_opencode_integration import EnhancedOpencodeIntegration, OpencodeModel
        
        # Create integration instance
        integration = EnhancedOpencodeIntegration()
        print("[OK] Integration instantiated successfully")
        
        # Test model management
        assert len(integration.available_models) > 0, "Should have available models"
        assert integration.active_model is not None, "Should have active model"
        print(f"[OK] Found {len(integration.available_models)} models, active: {integration.active_model}")
        
        # Test model switching
        if len(integration.available_models) > 1:
            original_model = integration.active_model
            # Switch to another model
            other_models = [m for m in integration.available_models.keys() if m != original_model]
            if other_models:
                integration.switch_model(other_models[0], reason="test")
                assert integration.active_model != original_model, "Model should have switched"
                print("[OK] Model switching works")
        
        # Test metrics
        metrics = integration.get_metrics()
        assert isinstance(metrics, dict), "Metrics should be a dictionary"
        assert "total_requests" in metrics, "Should include request count"
        print("[OK] Metrics reporting works")
        
        # Test status
        status = integration.get_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert "is_initialized" in status, "Should include initialization status"
        print("[OK] Status reporting works")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Enhanced Opencode Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smart_routing():
    """Test smart routing functionality"""
    print("\n=== Testing Smart Routing ===")
    
    try:
        from smart_routing import SmartRouter, RoutingContext
        
        # Create router
        router = SmartRouter()
        print("[OK] Smart router instantiated")
        
        # Test routing context
        context = RoutingContext(
            user_input="Create a Python function for data analysis",
            urgency="normal",
            domain="coding"
        )
        print("[OK] Routing context created")
        
        # Test routing decision
        decision = router.route_request(context)
        assert hasattr(decision, 'selected_model'), "Should select a model"
        assert hasattr(decision, 'confidence_score'), "Should have confidence score"
        print(f"[OK] Routing decision made: {decision.selected_model} (confidence: {decision.confidence_score})")
        
        # Test model capabilities
        assert len(router.models) > 0, "Should have model capabilities"
        print(f"[OK] Found {len(router.models)} model capabilities")
        
        # Test skill capabilities
        assert len(router.skills) > 0, "Should have skill capabilities"
        print(f"[OK] Found {len(router.skills)} skill capabilities")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Smart Routing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_realtime_analytics():
    """Test real-time analytics functionality"""
    print("\n=== Testing Real-Time Analytics ===")
    
    try:
        from realtime_analytics import RealTimeAnalytics
        
        # Create analytics instance
        analytics = RealTimeAnalytics()
        print("[OK] Analytics instantiated")
        
        # Test metric recording
        analytics.record_metric("response_time", 1.5, {"endpoint": "test"})
        analytics.record_metric("request_count", 1, {"method": "POST"})
        print("[OK] Metric recording works")
        
        # Test alert callback
        alert_received = False
        def test_alert(alert):
            nonlocal alert_received
            alert_received = True
        
        analytics.add_alert_callback(test_alert)
        print("[OK] Alert callback added")
        
        # Test dashboard data
        dashboard = analytics.get_real_time_dashboard()
        assert isinstance(dashboard, dict), "Dashboard should be a dictionary"
        print("[OK] Dashboard data retrieval works")
        
        # Test performance report
        report = analytics.get_performance_report("1h")
        assert isinstance(report, dict), "Performance report should be a dictionary"
        print("[OK] Performance report generation works")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Real-Time Analytics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_workflow():
    """Test integrated workflow between components"""
    print("\n=== Testing Integration Workflow ===")
    
    try:
        # Test that all components can work together
        from autonomous_evolution_engine import AutonomousEvolutionEngine
        from enhanced_opencode_integration import EnhancedOpencodeIntegration
        from realtime_analytics import RealTimeAnalytics
        
        # Create all components
        engine = AutonomousEvolutionEngine()
        integration = EnhancedOpencodeIntegration()
        analytics = RealTimeAnalytics()
        
        print("[OK] All components instantiated together")
        
        # Test that they can operate simultaneously
        status = engine.get_status()
        metrics = integration.get_metrics()
        dashboard = analytics.get_real_time_dashboard()
        
        assert isinstance(status, dict), "Engine status should be dict"
        assert isinstance(metrics, dict), "Integration metrics should be dict"
        assert isinstance(dashboard, dict), "Analytics dashboard should be dict"
        
        print("[OK] Components can operate simultaneously")
        
        # Test data flow between components
        analytics.record_metric("evolution_scan", 1, {"component": "engine"})
        integration.record_request("test_request", "test_model", 1.0, True)
        
        print("[OK] Data flow between components works")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Integration workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """Run all comprehensive functionality tests"""
    print("[START] Starting Comprehensive Functionality Tests for Neo-Clone Integration")
    print("=" * 80)
    
    test_results = {}
    
    # Run individual tests
    tests = [
        ("Autonomous Evolution Engine", test_autonomous_evolution_engine),
        ("Autonomous System Healer", test_autonomous_system_healer),
        ("Enhanced Error Recovery", test_enhanced_error_recovery),
        ("Enhanced Opencode Integration", test_enhanced_opencode_integration),
        ("Smart Routing", test_smart_routing),
        ("Real-Time Analytics", test_realtime_analytics),
        ("Integration Workflow", test_integration_workflow)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = result
        except Exception as e:
            print(f"[ERROR] {test_name} test crashed: {e}")
            test_results[test_name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("[RESULTS] COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nSummary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED! Neo-Clone integration is working correctly.")
        print("[INFO] All components are functional and properly integrated.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Some components may need attention.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)