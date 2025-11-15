"""
Plan Verification System for OpenCode Spec-Driven Development
Author: MiniMax Agent

This module verifies that code changes adhere to the generated implementation plan.
It provides verification reports and fix suggestions to ensure plan compliance.
"""

import os
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

@dataclass
class VerificationResult:
    """Result of a single verification check"""
    check_name: str
    status: str  # PASS, FAIL, WARNING, INFO
    message: str
    expected: str
    actual: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    severity: str = "medium"  # low, medium, high, critical

@dataclass
class VerificationReport:
    """Complete verification report for a plan"""
    plan_name: str
    verification_time: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    overall_score: float
    results: List[VerificationResult]
    summary: str

class PlanVerificationSystem:
    """System for verifying code adherence to implementation plans"""
    
    def __init__(self, workspace_dir: str = "/workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.plans_dir = self.workspace_dir / "data" / "plans"
        self.verification_cache = {}
        
    def verify_plan_compliance(self, plan_path: str, actual_code_dir: str = None) -> VerificationReport:
        """
        Verify that actual code changes comply with a generated plan
        
        Args:
            plan_path: Path to the generated implementation plan JSON
            actual_code_dir: Directory to verify (defaults to workspace root)
            
        Returns:
            VerificationReport with detailed verification results
        """
        if actual_code_dir is None:
            actual_code_dir = str(self.workspace_dir)
            
        try:
            # Load the implementation plan
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
            
            plan_name = plan_data.get('plan_name', 'Unknown Plan')
            
            # Initialize verification results
            verification_results = []
            
            # 1. Verify file structure compliance
            file_results = self._verify_file_structure(plan_data, actual_code_dir)
            verification_results.extend(file_results)
            
            # 2. Verify phase execution compliance
            phase_results = self._verify_phase_execution(plan_data, actual_code_dir)
            verification_results.extend(phase_results)
            
            # 3. Verify technology implementation
            tech_results = self._verify_technology_implementation(plan_data, actual_code_dir)
            verification_results.extend(tech_results)
            
            # 4. Verify code quality and structure
            quality_results = self._verify_code_quality(plan_data, actual_code_dir)
            verification_results.extend(quality_results)
            
            # 5. Verify dependencies and imports
            dependency_results = self._verify_dependencies(plan_data, actual_code_dir)
            verification_results.extend(dependency_results)
            
            # Calculate summary statistics
            total_checks = len(verification_results)
            passed_checks = len([r for r in verification_results if r.status == 'PASS'])
            failed_checks = len([r for r in verification_results if r.status == 'FAIL'])
            warning_checks = len([r for r in verification_results if r.status == 'WARNING'])
            
            overall_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
            
            # Generate summary
            summary = self._generate_verification_summary(
                plan_name, passed_checks, failed_checks, warning_checks, overall_score
            )
            
            # Create verification report
            report = VerificationReport(
                plan_name=plan_name,
                verification_time=datetime.now().isoformat(),
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=warning_checks,
                warning_checks=warning_checks,
                overall_score=overall_score,
                results=verification_results,
                summary=summary
            )
            
            return report
            
        except Exception as e:
            # Return error report if verification fails
            return VerificationReport(
                plan_name="Error Plan",
                verification_time=datetime.now().isoformat(),
                total_checks=0,
                passed_checks=0,
                failed_checks=0,
                warning_checks=0,
                overall_score=0.0,
                results=[],
                summary=f"Verification failed with error: {str(e)}"
            )
    
    def _verify_file_structure(self, plan_data: Dict, actual_dir: str) -> List[VerificationResult]:
        """Verify that required files from the plan exist and match expectations"""
        results = []
        
        if 'files' not in plan_data:
            return results
            
        planned_files = plan_data['files']
        actual_path = Path(actual_dir)
        
        for file_info in planned_files:
            file_path = file_info.get('path', '')
            if not file_path:
                continue
                
            # Skip absolute paths or special paths
            if file_path.startswith('/') or file_path.startswith('http'):
                continue
                
            full_file_path = actual_path / file_path
            
            # Check if file exists
            if full_file_path.exists():
                # Verify file content matches planned complexity
                try:
                    with open(full_file_path, 'r') as f:
                        content = f.read()
                    
                    actual_lines = len(content.splitlines())
                    planned_lines = file_info.get('estimated_lines', 0)
                    
                    # Check if file size is reasonable (within 200% of expected)
                    if actual_lines > 0 and planned_lines > 0:
                        if planned_lines * 2 >= actual_lines >= planned_lines * 0.3:
                            results.append(VerificationResult(
                                check_name="File Size Compliance",
                                status="PASS",
                                message=f"File {file_path} has reasonable size ({actual_lines} lines)",
                                expected=f"{planned_lines} lines",
                                actual=f"{actual_lines} lines",
                                file_path=file_path,
                                severity="medium"
                            ))
                        else:
                            results.append(VerificationResult(
                                check_name="File Size Compliance",
                                status="WARNING",
                                message=f"File {file_path} size differs significantly from plan",
                                expected=f"{planned_lines} lines",
                                actual=f"{actual_lines} lines",
                                file_path=file_path,
                                severity="medium"
                            ))
                    else:
                        results.append(VerificationResult(
                            check_name="File Exists",
                            status="PASS",
                            message=f"File {file_path} exists",
                            expected="File exists",
                            actual="File exists",
                            file_path=file_path,
                            severity="low"
                        ))
                        
                except Exception as e:
                    results.append(VerificationResult(
                        check_name="File Content Read",
                        status="WARNING",
                        message=f"Could not read file {file_path}: {str(e)}",
                        expected="File readable",
                        actual="Read error",
                        file_path=file_path,
                        severity="medium"
                    ))
            else:
                results.append(VerificationResult(
                    check_name="File Exists",
                    status="FAIL",
                    message=f"Planned file {file_path} is missing",
                    expected="File exists",
                    actual="File missing",
                    file_path=file_path,
                    severity="high"
                ))
        
        return results
    
    def _verify_phase_execution(self, plan_data: Dict, actual_dir: str) -> List[VerificationResult]:
        """Verify that implementation phases were completed"""
        results = []
        
        if 'phases' not in plan_data:
            return results
            
        phases = plan_data['phases']
        
        # Check if each phase has corresponding implementation
        for i, phase in enumerate(phases, 1):
            phase_name = phase.get('name', f'Phase {i}')
            
            # Look for phase completion indicators
            phase_files = phase.get('files', [])
            phase_dependencies = phase.get('dependencies', [])
            
            # Check if dependencies are resolved
            dependency_issues = []
            for dep in phase_dependencies:
                # Simplified dependency check
                if not self._check_dependency_resolution(dep, actual_dir):
                    dependency_issues.append(dep)
            
            if dependency_issues:
                results.append(VerificationResult(
                    check_name="Phase Dependencies",
                    status="WARNING",
                    message=f"Phase {i} ({phase_name}) has unresolved dependencies",
                    expected="All dependencies resolved",
                    actual=f"Unresolved: {', '.join(dependency_issues)}",
                    severity="high"
                ))
            else:
                results.append(VerificationResult(
                    check_name="Phase Dependencies",
                    status="PASS",
                    message=f"Phase {i} ({phase_name}) dependencies are resolved",
                    expected="Dependencies resolved",
                    actual="Dependencies resolved",
                    severity="low"
                ))
        
        return results
    
    def _verify_technology_implementation(self, plan_data: Dict, actual_dir: str) -> List[VerificationResult]:
        """Verify that planned technologies are properly implemented"""
        results = []
        
        technologies = plan_data.get('technologies', {})
        
        for tech_name, tech_info in technologies.items():
            if tech_name.lower() == 'python':
                # Check Python-specific implementations
                python_files = list(Path(actual_dir).rglob('*.py'))
                if python_files:
                    results.append(VerificationResult(
                        check_name="Python Implementation",
                        status="PASS",
                        message=f"Python files found ({len(python_files)} files)",
                        expected="Python files",
                        actual=f"{len(python_files)} files",
                        severity="medium"
                    ))
                else:
                    results.append(VerificationResult(
                        check_name="Python Implementation",
                        status="FAIL",
                        message="No Python files found for planned Python implementation",
                        expected="Python files",
                        actual="No Python files",
                        severity="high"
                    ))
            
            elif tech_name.lower() == 'fastapi':
                # Check for FastAPI-specific patterns
                found_fastapi = False
                for py_file in Path(actual_dir).rglob('*.py'):
                    try:
                        with open(py_file, 'r') as f:
                            content = f.read()
                        if 'FastAPI' in content or 'fastapi' in content:
                            found_fastapi = True
                            break
                    except:
                        continue
                
                if found_fastapi:
                    results.append(VerificationResult(
                        check_name="FastAPI Implementation",
                        status="PASS",
                        message="FastAPI framework detected in implementation",
                        expected="FastAPI usage",
                        actual="FastAPI found",
                        severity="medium"
                    ))
                else:
                    results.append(VerificationResult(
                        check_name="FastAPI Implementation",
                        status="FAIL",
                        message="FastAPI framework not found in planned implementation",
                        expected="FastAPI usage",
                        actual="FastAPI not found",
                        severity="high"
                    ))
            
            elif tech_name.lower() == 'sqlalchemy':
                # Check for SQLAlchemy patterns
                found_sqlalchemy = False
                for py_file in Path(actual_dir).rglob('*.py'):
                    try:
                        with open(py_file, 'r') as f:
                            content = f.read()
                        if 'SQLAlchemy' in content or 'sqlalchemy' in content:
                            found_sqlalchemy = True
                            break
                    except:
                        continue
                
                if found_sqlalchemy:
                    results.append(VerificationResult(
                        check_name="SQLAlchemy Implementation",
                        status="PASS",
                        message="SQLAlchemy ORM detected in implementation",
                        expected="SQLAlchemy usage",
                        actual="SQLAlchemy found",
                        severity="medium"
                    ))
                else:
                    results.append(VerificationResult(
                        check_name="SQLAlchemy Implementation",
                        status="WARNING",
                        message="SQLAlchemy ORM not detected (may be optional)",
                        expected="SQLAlchemy usage",
                        actual="SQLAlchemy not found",
                        severity="low"
                    ))
        
        return results
    
    def _verify_code_quality(self, plan_data: Dict, actual_dir: str) -> List[VerificationResult]:
        """Verify code quality and structure compliance"""
        results = []
        
        # Find all Python files
        python_files = list(Path(actual_dir).rglob('*.py'))
        
        if not python_files:
            results.append(VerificationResult(
                check_name="Code Quality - Python Files",
                status="WARNING",
                message="No Python files found for quality assessment",
                expected="Python files to assess",
                actual="No Python files",
                severity="medium"
            ))
            return results
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for py_file in python_files[:10]:  # Limit to first 10 files for performance
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count lines
                lines = content.splitlines()
                total_lines += len(lines)
                
                # Parse AST for functions and classes
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1
                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1
                except:
                    pass
                    
            except Exception as e:
                results.append(VerificationResult(
                    check_name="File Parse Error",
                    status="WARNING",
                    message=f"Could not parse {py_file.name}: {str(e)}",
                    expected="Valid Python syntax",
                    actual="Parse error",
                    file_path=str(py_file),
                    severity="medium"
                ))
        
        # Check line count per file (quality metric)
        if python_files:
            avg_lines = total_lines / len(python_files)
            if avg_lines > 500:
                results.append(VerificationResult(
                    check_name="Code Organization",
                    status="WARNING",
                    message=f"Average file size is high ({avg_lines:.1f} lines). Consider splitting files.",
                    expected="Files < 500 lines",
                    actual=f"{avg_lines:.1f} lines average",
                    severity="medium"
                ))
            else:
                results.append(VerificationResult(
                    check_name="Code Organization",
                    status="PASS",
                    message=f"File organization looks good ({avg_lines:.1f} lines average)",
                    expected="Reasonable file sizes",
                    actual=f"{avg_lines:.1f} lines average",
                    severity="low"
                ))
        
        # Check function-to-class ratio
        if total_classes > 0:
            function_ratio = total_functions / total_classes
            if function_ratio > 20:
                results.append(VerificationResult(
                    check_name="Code Structure",
                    status="WARNING",
                    message="High function-to-class ratio. Consider better OOP design.",
                    expected="Balanced OOP structure",
                    actual=f"{function_ratio:.1f} functions per class",
                    severity="medium"
                ))
            else:
                results.append(VerificationResult(
                    check_name="Code Structure",
                    status="PASS",
                    message="Good function-to-class ratio",
                    expected="Balanced OOP structure",
                    actual=f"{function_ratio:.1f} functions per class",
                    severity="low"
                ))
        
        return results
    
    def _verify_dependencies(self, plan_data: Dict, actual_dir: str) -> List[VerificationResult]:
        """Verify that dependencies are properly handled"""
        results = []
        
        actual_path = Path(actual_dir)
        
        # Check for requirements.txt or pyproject.toml
        requirements_files = [
            actual_path / "requirements.txt",
            actual_path / "pyproject.toml",
            actual_path / "Pipfile",
            actual_path / "poetry.lock"
        ]
        
        found_requirements = any(req_file.exists() for req_file in requirements_files)
        
        if found_requirements:
            results.append(VerificationResult(
                check_name="Dependency Management",
                status="PASS",
                message="Dependency management file found",
                expected="Requirements file",
                actual="Requirements file exists",
                severity="medium"
            ))
        else:
            results.append(VerificationResult(
                check_name="Dependency Management",
                status="WARNING",
                message="No requirements file found. Consider adding one.",
                expected="Requirements file",
                actual="No requirements file",
                severity="low"
            ))
        
        # Check for __init__.py files in package structure
        init_files = list(actual_path.rglob('__init__.py'))
        if init_files:
            results.append(VerificationResult(
                check_name="Package Structure",
                status="PASS",
                message=f"Package structure detected ({len(init_files)} __init__.py files)",
                expected="Proper Python package structure",
                actual=f"{len(init_files)} __init__.py files",
                severity="low"
            ))
        else:
            results.append(VerificationResult(
                check_name="Package Structure",
                status="INFO",
                message="No package structure detected (may not be needed)",
                expected="Package structure if needed",
                actual="No package structure",
                severity="low"
            ))
        
        return results
    
    def _check_dependency_resolution(self, dependency: str, actual_dir: str) -> bool:
        """Check if a dependency is resolved in the implementation"""
        # Simplified dependency check
        # In a real implementation, this would be more sophisticated
        
        dep_lower = dependency.lower()
        actual_path = Path(actual_dir)
        
        # Check if dependency name appears in import statements
        for py_file in actual_path.rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Simple import check
                if dep_lower in content.lower():
                    return True
            except:
                continue
        
        # Check if dependency appears in requirements
        req_files = [
            actual_path / "requirements.txt",
            actual_path / "pyproject.toml",
            actual_path / "Pipfile"
        ]
        
        for req_file in req_files:
            if req_file.exists():
                try:
                    with open(req_file, 'r') as f:
                        content = f.read()
                    if dep_lower in content.lower():
                        return True
                except:
                    continue
        
        return False
    
    def _generate_verification_summary(self, plan_name: str, passed: int, failed: int, warnings: int, score: float) -> str:
        """Generate a summary of the verification results"""
        if score >= 90:
            status = "EXCELLENT"
        elif score >= 80:
            status = "GOOD"
        elif score >= 70:
            status = "ACCEPTABLE"
        elif score >= 50:
            status = "NEEDS IMPROVEMENT"
        else:
            status = "CRITICAL ISSUES"
        
        summary = f"""
Plan Verification Summary for: {plan_name}
Overall Score: {score:.1f}% ({status})
Passed Checks: {passed}
Failed Checks: {failed}
Warnings: {warnings}

"""
        
        if failed == 0:
            summary += "✅ Implementation fully complies with the plan!"
        elif failed <= 2:
            summary += "⚠️  Minor deviations from plan detected. Review recommended."
        else:
            summary += "❌ Significant deviations from plan. Immediate attention required."
        
        if warnings > 0:
            summary += f"\n📝 {warnings} warnings detected. Consider reviewing for optimization opportunities."
        
        return summary
    
    def save_verification_report(self, report: VerificationReport, output_path: str = None) -> str:
        """Save verification report to file"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/workspace/data/verification_reports/verification_{timestamp}.json"
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert report to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        return output_path
    
    def get_verification_dashboard(self, recent_reports: List[VerificationReport] = None) -> Dict[str, Any]:
        """Generate a dashboard view of verification status"""
        if recent_reports is None:
            # Load recent reports from disk
            reports_dir = Path("/workspace/data/verification_reports")
            recent_reports = []
            
            if reports_dir.exists():
                for report_file in sorted(reports_dir.glob("verification_*.json"), reverse=True)[:10]:
                    try:
                        with open(report_file, 'r') as f:
                            report_dict = json.load(f)
                        recent_reports.append(VerificationReport(**report_dict))
                    except:
                        continue
        
        if not recent_reports:
            return {"message": "No verification reports found"}
        
        # Calculate dashboard metrics
        scores = [report.overall_score for report in recent_reports]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Count status distribution
        status_counts = {"excellent": 0, "good": 0, "acceptable": 0, "needs_improvement": 0, "critical": 0}
        
        for score in scores:
            if score >= 90:
                status_counts["excellent"] += 1
            elif score >= 80:
                status_counts["good"] += 1
            elif score >= 70:
                status_counts["acceptable"] += 1
            elif score >= 50:
                status_counts["needs_improvement"] += 1
            else:
                status_counts["critical"] += 1
        
        return {
            "dashboard_summary": {
                "total_reports": len(recent_reports),
                "average_score": avg_score,
                "latest_report": recent_reports[0].verification_time if recent_reports else None,
                "status_distribution": status_counts
            },
            "recent_trends": [
                {
                    "timestamp": report.verification_time,
                    "plan_name": report.plan_name,
                    "score": report.overall_score,
                    "passed_checks": report.passed_checks,
                    "failed_checks": report.failed_checks
                }
                for report in recent_reports[:5]
            ]
        }

def verify_latest_plan(workspace_dir: str = "/workspace") -> VerificationReport:
    """Convenience function to verify the most recent implementation plan"""
    plans_dir = Path(workspace_dir) / "data" / "plans"
    
    if not plans_dir.exists():
        raise FileNotFoundError(f"Plans directory not found: {plans_dir}")
    
    # Find the most recent plan file
    plan_files = list(plans_dir.glob("*.json"))
    if not plan_files:
        raise FileNotFoundError("No plan files found")
    
    latest_plan = max(plan_files, key=lambda f: f.stat().st_mtime)
    
    verifier = PlanVerificationSystem(workspace_dir)
    return verifier.verify_plan_compliance(str(latest_plan))

if __name__ == "__main__":
    # Demo verification
    print("🧪 Plan Verification System Demo")
    print("=" * 50)
    
    try:
        report = verify_latest_plan()
        print(f"Plan: {report.plan_name}")
        print(f"Score: {report.overall_score:.1f}%")
        print(f"Checks: {report.passed_checks}/{report.total_checks} passed")
        print(f"\nSummary:\n{report.summary}")
        
        # Save report
        output_path = report.verification_time.replace(":", "-").replace(".", "-")
        saved_path = f"/workspace/data/verification_reports/demo_report.json"
        verifier = PlanVerificationSystem()
        final_path = verifier.save_verification_report(report, saved_path)
        print(f"\nReport saved to: {final_path}")
        
    except Exception as e:
        print(f"Verification failed: {str(e)}")
        print("This is expected if no plans have been generated yet.")