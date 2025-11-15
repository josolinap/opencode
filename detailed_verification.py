#!/usr/bin/env python3
"""
Detailed Verification Analysis Script
Author: MiniMax Agent

This script provides detailed analysis of plan compliance with specific recommendations.
"""

# Note: This verification script is designed for the complete MiniMax system
# The src.core.plan_verification import would be available in the full system
# For now, this serves as a placeholder for the complete verification framework

import json
from pathlib import Path

def detailed_verification_analysis():
    """Perform detailed analysis of plan compliance"""
    print("🔍 Detailed Verification Analysis")
    print("=" * 60)

    # Load the plan
    plan_path = "/workspace/data/plans/demo_auth_system_plan.json"

    # Run verification
    verifier = PlanVerificationSystem()
    report = verifier.verify_plan_compliance(plan_path)

    # Display detailed results
    print(f"Plan: {report.plan_name}")
    print(f"Overall Score: {report.overall_score:.1f}%")
    print(f"Total Checks: {report.total_checks}")
    print(f"Passed: {report.passed_checks} | Failed: {report.failed_checks} | Warnings: {report.warning_checks}")
    print("\n" + "=" * 60)

    # Group results by check type
    check_types = {}
    for result in report.results:
        check_type = result.check_name
        if check_type not in check_types:
            check_types[check_type] = []
        check_types[check_type].append(result)

    # Display results by category
    for check_type, results in check_types.items():
        print(f"\n📋 {check_type.upper()}")
        print("-" * 40)

        passed = len([r for r in results if r.status == 'PASS'])
        failed = len([r for r in results if r.status == 'FAIL'])
        warnings = len([r for r in results if r.status == 'WARNING'])

        print(f"Status: {passed} passed, {failed} failed, {warnings} warnings")

        # Show detailed results
        for result in results:
            status_emoji = {
                'PASS': '✅',
                'FAIL': '❌',
                'WARNING': '⚠️',
                'INFO': 'ℹ️'
            }.get(result.status, '❓')

            print(f"\n  {status_emoji} {result.file_path or 'General'}")
            print(f"     Message: {result.message}")
            print(f"     Expected: {result.expected}")
            print(f"     Actual: {result.actual}")
            if result.severity != 'medium':
                print(f"     Severity: {result.severity}")

    # Provide recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)

    failed_results = [r for r in report.results if r.status == 'FAIL']
    warning_results = [r for r in report.results if r.status == 'WARNING']

    if failed_results:
        print("\n🚨 CRITICAL ISSUES TO FIX:")
        for result in failed_results:
            print(f"  • {result.message}")
            if result.file_path:
                print(f"    File: {result.file_path}")

    if warning_results:
        print("\n⚠️  OPTIMIZATION OPPORTUNITIES:")
        for result in warning_results:
            print(f"  • {result.message}")
            if result.file_path:
                print(f"    File: {result.file_path}")

    # Save detailed report
    output_file = "/workspace/data/verification_reports/detailed_analysis.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'report_summary': {
                'plan_name': report.plan_name,
                'overall_score': report.overall_score,
                'timestamp': report.verification_time,
                'summary': report.summary
            },
            'detailed_results': [
                {
                    'check_name': r.check_name,
                    'status': r.status,
                    'message': r.message,
                    'expected': r.expected,
                    'actual': r.actual,
                    'file_path': r.file_path,
                    'severity': r.severity
                }
                for r in report.results
            ]
        }, f, indent=2)

    print(f"\n📄 Detailed report saved to: {output_file}")

    # Show dashboard
    print("\n" + "=" * 60)
    print("📊 VERIFICATION DASHBOARD")
    print("=" * 60)

    dashboard = verifier.get_verification_dashboard([report])
    print(f"Average Score: {dashboard['dashboard_summary']['average_score']:.1f}%")
    print(f"Status Distribution:")
    for status, count in dashboard['dashboard_summary']['status_distribution'].items():
        if count > 0:
            print(f"  • {status.replace('_', ' ').title()}: {count}")

if __name__ == "__main__":
    detailed_verification_analysis()
