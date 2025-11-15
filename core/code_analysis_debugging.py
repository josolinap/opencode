"""
MiniMax Code Analysis & Debugging System
========================================

Comprehensive code analysis and debugging system providing:
- Static Analysis: Code quality, complexity, dependency analysis
- Runtime Debugging: Error tracking, performance profiling, memory monitoring
- Security Scanning: Vulnerability detection, security best practices

Author: MiniMax Agent
Created: 2025-11-13
"""

import ast
import inspect
import linecache
import os
import sys
import time
import traceback
import warnings
import json
import hashlib
import threading
import weakref
from contextlib import contextmanager
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
import re
import subprocess
import importlib.util
import astroid
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import cProfile
import pstats
import memory_profiler
import psutil


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    type: str  # 'error', 'warning', 'info'
    category: str  # 'style', 'complexity', 'security', 'performance', 'dependency'
    file_path: str
    line_number: int
    function_name: Optional[str] = None
    message: str = ""
    severity: int = 1  # 1-5 scale
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability."""
    type: str  # 'sql_injection', 'xss', 'hardcoded_secret', etc.
    severity: str  # 'low', 'medium', 'high', 'critical'
    file_path: str
    line_number: int
    function_name: Optional[str] = None
    description: str = ""
    cve_id: Optional[str] = None
    remediation: str = ""


@dataclass
class PerformanceMetrics:
    """Performance metrics for runtime analysis."""
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    file_path: str
    line_number: int
    call_count: int = 1


@dataclass
class DebugReport:
    """Comprehensive debug report."""
    timestamp: str
    total_issues: int
    static_analysis: Dict[str, Any]
    security_scan: Dict[str, Any]
    runtime_debugging: Dict[str, Any]
    overall_score: float
    recommendations: List[str]


class StaticAnalyzer:
    """Static code analysis engine."""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
        self.complexity_cache: Dict[str, int] = {}
        
    def analyze_file(self, file_path: str) -> List[CodeIssue]:
        """Analyze a single file for static issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse AST
            tree = ast.parse(source, filename=file_path)
            
            # Run various static analysis checks
            self._check_code_style(file_path, source)
            self._check_complexity(tree, file_path)
            self._check_imports(tree, file_path)
            self._check_naming_conventions(tree, file_path)
            self._check_dead_code(tree, file_path)
            self._check_exception_handling(tree, file_path)
            
            return self.issues
            
        except Exception as e:
            return [CodeIssue(
                type="error",
                category="parsing",
                file_path=file_path,
                line_number=1,
                message=f"Failed to parse file: {str(e)}",
                severity=4
            )]
    
    def _check_code_style(self, file_path: str, source: str):
        """Check for code style issues."""
        lines = source.split('\n')
        
        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append(CodeIssue(
                    type="warning",
                    category="style",
                    file_path=file_path,
                    line_number=i,
                    message=f"Line too long ({len(line)} > 120 characters)",
                    severity=2,
                    suggestions=["Break long lines into multiple lines"]
                ))
            
            # Check for tabs vs spaces
            if line.startswith('\t'):
                self.issues.append(CodeIssue(
                    type="warning",
                    category="style",
                    file_path=file_path,
                    line_number=i,
                    message="Line starts with tab instead of spaces",
                    severity=1,
                    suggestions=["Replace tabs with 4 spaces"]
                ))
        
        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                self.issues.append(CodeIssue(
                    type="warning",
                    category="style",
                    file_path=file_path,
                    line_number=i,
                    message="Trailing whitespace found",
                    severity=1,
                    suggestions=["Remove trailing whitespace"]
                ))
    
    def _check_complexity(self, tree: ast.AST, file_path: str):
        """Check for cyclomatic complexity issues."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.issues.append(CodeIssue(
                        type="warning",
                        category="complexity",
                        file_path=file_path,
                        line_number=node.lineno,
                        function_name=node.name,
                        message=f"High cyclomatic complexity ({complexity})",
                        severity=3,
                        suggestions=["Break down into smaller functions", "Use early returns"]
                    ))
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, (ast.ExceptHandler,)):
                complexity += 1
            elif isinstance(child, (ast.BoolOp,)):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_imports(self, tree: ast.AST, file_path: str):
        """Check for import-related issues."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                else:  # ImportFrom
                    for alias in node.names:
                        imports.append(alias.name)
        
        # Check for unused imports (simplified)
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
        
        # This is a simplified check - real unused import detection is more complex
        common_modules = {'sys', 'os', 'json', 'time', 'datetime', 'pathlib', 'typing'}
        for imp in imports:
            if imp not in used_names and imp not in common_modules:
                self.issues.append(CodeIssue(
                    type="warning",
                    category="dependency",
                    file_path=file_path,
                    line_number=node.lineno if 'node' in locals() else 1,
                    message=f"Potential unused import: {imp}",
                    severity=2,
                    suggestions=["Remove unused imports to improve code clarity"]
                ))
    
    def _check_naming_conventions(self, tree: ast.AST, file_path: str):
        """Check for naming convention issues."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function names
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    self.issues.append(CodeIssue(
                        type="warning",
                        category="style",
                        file_path=file_path,
                        line_number=node.lineno,
                        function_name=node.name,
                        message=f"Function name should be snake_case: {node.name}",
                        severity=1,
                        suggestions=["Use snake_case for function names"]
                    ))
            
            elif isinstance(node, ast.ClassDef):
                # Check class names
                if not re.match(r'^[A-Z][A-Za-z0-9]*$', node.name):
                    self.issues.append(CodeIssue(
                        type="warning",
                        category="style",
                        file_path=file_path,
                        line_number=node.lineno,
                        function_name=node.name,
                        message=f"Class name should be PascalCase: {node.name}",
                        severity=1,
                        suggestions=["Use PascalCase for class names"]
                    ))
    
    def _check_dead_code(self, tree: ast.AST, file_path: str):
        """Check for dead code patterns."""
        # Look for unreachable code after returns
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function_dead_code(node, file_path)
    
    def _check_function_dead_code(self, func_node: ast.FunctionDef, file_path: str):
        """Check for dead code in a function."""
        statements = func_node.body
        has_return = False
        
        for i, stmt in enumerate(statements):
            if isinstance(stmt, ast.Return):
                has_return = True
            elif has_return and not isinstance(stmt, (ast.Pass, ast.Return)):
                # This is dead code
                self.issues.append(CodeIssue(
                    type="warning",
                    category="performance",
                    file_path=file_path,
                    line_number=stmt.lineno,
                    function_name=func_node.name,
                    message="Unreachable code after return statement",
                    severity=2,
                    suggestions=["Remove unreachable code"]
                ))
                break
    
    def _check_exception_handling(self, tree: ast.AST, file_path: str):
        """Check for exception handling issues."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check for bare except
                for handler in node.handlers:
                    if handler.type is None:
                        self.issues.append(CodeIssue(
                            type="warning",
                            category="error_handling",
                            file_path=file_path,
                            line_number=handler.lineno,
                            message="Bare except clause found",
                            severity=2,
                            suggestions=["Use specific exception types", "Log the exception"]
                        ))


class SecurityScanner:
    """Security vulnerability scanner."""
    
    def __init__(self):
        self.vulnerabilities: List[SecurityVulnerability] = []
        self.security_patterns = self._load_security_patterns()
    
    def _load_security_patterns(self) -> Dict[str, Dict]:
        """Load security vulnerability patterns."""
        return {
            'sql_injection': {
                'patterns': [
                    r'execute\s*\(\s*["\'][^"\']*\s*%\s*',
                    r'execute\s*\(\s*f["\'][^"\']*{[^}]+}[^"\']*',
                    r'cursor\.execute\s*\(\s*["\'][^"\']*\s*%\s*',
                ],
                'severity': 'high',
                'description': 'Potential SQL injection vulnerability'
            },
            'hardcoded_secrets': {
                'patterns': [
                    r'["\'][A-Za-z0-9+/]{40,}["\']',  # Base64-like strings
                    r'(?i)(password|secret|key|token)\s*=\s*["\'][^"\']{10,}["\']',
                    r'["\'][0-9a-f]{32,}["\']',  # Hex strings (MD5, UUID)
                ],
                'severity': 'medium',
                'description': 'Potential hardcoded secret detected'
            },
            'eval_usage': {
                'patterns': [
                    r'\beval\s*\(',
                    r'\bexec\s*\(',
                ],
                'severity': 'high',
                'description': 'Use of eval() or exec() functions'
            },
            'subprocess_shell': {
                'patterns': [
                    r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
                    r'subprocess\.run\s*\([^)]*shell\s*=\s*True',
                ],
                'severity': 'medium',
                'description': 'Shell=True in subprocess calls'
            },
            'file_traversal': {
                'patterns': [
                    r'\.\./',
                    r'\.\.\\',
                ],
                'severity': 'medium',
                'description': 'Potential path traversal vulnerability'
            }
        }
    
    def scan_file(self, file_path: str) -> List[SecurityVulnerability]:
        """Scan a file for security vulnerabilities."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for vuln_type, vuln_data in self.security_patterns.items():
                for pattern in vuln_data['patterns']:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            self.vulnerabilities.append(SecurityVulnerability(
                                type=vuln_type,
                                severity=vuln_data['severity'],
                                file_path=file_path,
                                line_number=line_num,
                                description=vuln_data['description']
                            ))
            
            # Additional AST-based checks
            try:
                tree = ast.parse(content)
                self._check_ast_security(tree, file_path)
            except:
                pass  # Skip AST analysis if parsing fails
            
            return self.vulnerabilities
            
        except Exception as e:
            return [SecurityVulnerability(
                type="scan_error",
                severity="low",
                file_path=file_path,
                line_number=1,
                description=f"Failed to scan file: {str(e)}"
            )]
    
    def _check_ast_security(self, tree: ast.AST, file_path: str):
        """Check for security issues using AST analysis."""
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile']:
                        self.vulnerabilities.append(SecurityVulnerability(
                            type="dangerous_functions",
                            severity="high",
                            file_path=file_path,
                            line_number=node.lineno,
                            description=f"Use of dangerous function: {node.func.id}"
                        ))
                
                # Check for subprocess calls with shell=True
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['call', 'run', 'Popen']:
                        # Check for shell=True keyword argument
                        for keyword in node.keywords:
                            if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant):
                                if keyword.value.value is True:
                                    self.vulnerabilities.append(SecurityVulnerability(
                                        type="subprocess_shell",
                                        severity="medium",
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        description="shell=True in subprocess call"
                                    ))


class RuntimeDebugger:
    """Runtime debugging and profiling system."""
    
    def __init__(self):
        self.performance_metrics: List[PerformanceMetrics] = []
        self.error_logs: List[Dict[str, Any]] = []
        self.memory_snapshots: List[Dict[str, Any]] = []
        self.is_profiling = False
        self.profiler = None
        
    @contextmanager
    def profile_function(self, function_name: str, file_path: str, line_number: int):
        """Profile a function execution."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        try:
            yield
        except Exception as e:
            self._log_error(e, function_name, file_path, line_number)
            raise
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = max(0, end_cpu - start_cpu)
            
            self.performance_metrics.append(PerformanceMetrics(
                function_name=function_name,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                file_path=file_path,
                line_number=line_number
            ))
    
    def start_profiling(self):
        """Start comprehensive profiling."""
        self.is_profiling = True
        self.profiler = cProfile.Profile()
        self.profiler.enable()
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop profiling and return results."""
        if not self.is_profiling or self.profiler is None:
            return {}
        
        self.profiler.disable()
        self.is_profiling = False
        
        # Get profiling stats
        stats = pstats.Stats(self.profiler)
        
        profiling_results = {
            'total_calls': stats.total_calls,
            'function_times': {}
        }
        
        # Extract function timing data
        for (filename, line, function), (cc, nc, tt, ct, callers) in stats.stats.items():
            rel_filename = filename.split('/')[-1]
            profiling_results['function_times'][f"{rel_filename}:{function}"] = {
                'calls': nc,
                'time': tt,
                'cumulative_time': ct
            }
        
        self.profiler = None
        return profiling_results
    
    def _log_error(self, error: Exception, function_name: str, file_path: str, line_number: int):
        """Log an error with context."""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'function_name': function_name,
            'file_path': file_path,
            'line_number': line_number,
            'stack_trace': traceback.format_exc(),
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024
            }
        }
        self.error_logs.append(error_info)
    
    def get_memory_snapshot(self) -> Dict[str, Any]:
        """Get current memory snapshot."""
        process = psutil.Process()
        return {
            'timestamp': datetime.now().isoformat(),
            'rss_memory': process.memory_info().rss / 1024 / 1024,  # MB
            'vms_memory': process.memory_info().vms / 1024 / 1024,  # MB
            'memory_percent': process.memory_percent(),
            'cpu_percent': process.cpu_percent(),
            'open_files': len(process.open_files()),
            'threads': process.num_threads()
        }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics."""
        if not self.performance_metrics:
            return {'analysis': 'No performance data available'}
        
        # Group metrics by function
        function_metrics = defaultdict(list)
        for metric in self.performance_metrics:
            function_metrics[metric.function_name].append(metric)
        
        analysis = {
            'total_functions': len(function_metrics),
            'slowest_functions': [],
            'memory_intensive_functions': [],
            'most_called_functions': [],
            'performance_summary': {}
        }
        
        # Calculate averages and find issues
        for func_name, metrics in function_metrics.items():
            avg_time = sum(m.execution_time for m in metrics) / len(metrics)
            avg_memory = sum(m.memory_usage for m in metrics) / len(metrics)
            call_count = len(metrics)
            
            analysis['performance_summary'][func_name] = {
                'avg_execution_time': avg_time,
                'avg_memory_usage': avg_memory,
                'call_count': call_count,
                'total_time': sum(m.execution_time for m in metrics)
            }
        
        # Find problematic functions
        sorted_by_time = sorted(
            analysis['performance_summary'].items(),
            key=lambda x: x[1]['avg_execution_time'],
            reverse=True
        )
        analysis['slowest_functions'] = sorted_by_time[:5]
        
        sorted_by_memory = sorted(
            analysis['performance_summary'].items(),
            key=lambda x: x[1]['avg_memory_usage'],
            reverse=True
        )
        analysis['memory_intensive_functions'] = sorted_by_memory[:5]
        
        sorted_by_calls = sorted(
            analysis['performance_summary'].items(),
            key=lambda x: x[1]['call_count'],
            reverse=True
        )
        analysis['most_called_functions'] = sorted_by_calls[:5]
        
        return analysis


class CodeAnalysisDebuggingSystem:
    """Main code analysis and debugging system."""
    
    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        self.security_scanner = SecurityScanner()
        self.runtime_debugger = RuntimeDebugger()
        self.analysis_cache: Dict[str, Any] = {}
        
    def analyze_directory(self, directory_path: str, include_files: List[str] = None) -> DebugReport:
        """Perform comprehensive analysis of a directory."""
        start_time = time.time()
        
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Determine which files to analyze
        if include_files:
            files_to_analyze = [directory / f for f in include_files if (directory / f).exists()]
        else:
            files_to_analyze = list(directory.rglob("*.py"))
        
        if not files_to_analyze:
            return DebugReport(
                timestamp=datetime.now().isoformat(),
                total_issues=0,
                static_analysis={'message': 'No Python files found'},
                security_scan={'message': 'No files analyzed'},
                runtime_debugging={'message': 'No runtime data'},
                overall_score=100.0,
                recommendations=['No files to analyze']
            )
        
        # Run static analysis
        all_static_issues = []
        all_security_vulns = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit static analysis tasks
            static_futures = {executor.submit(self.static_analyzer.analyze_file, str(f)): f for f in files_to_analyze}
            
            # Submit security scanning tasks
            security_futures = {executor.submit(self.security_scanner.scan_file, str(f)): f for f in files_to_analyze}
            
            # Collect static analysis results
            for future in as_completed(static_futures):
                try:
                    issues = future.result()
                    all_static_issues.extend(issues)
                except Exception as e:
                    print(f"Static analysis failed for {static_futures[future]}: {e}")
            
            # Collect security scanning results
            for future in as_completed(security_futures):
                try:
                    vulns = future.result()
                    all_security_vulns.extend(vulns)
                except Exception as e:
                    print(f"Security scan failed for {security_futures[future]}: {e}")
        
        # Analyze static issues
        static_analysis = self._analyze_static_issues(all_static_issues)
        
        # Analyze security vulnerabilities
        security_analysis = self._analyze_security_vulnerabilities(all_security_vulns)
        
        # Runtime debugging (if profiling is active)
        runtime_analysis = {}
        if self.runtime_debugger.is_profiling:
            runtime_analysis = self.runtime_debugger.analyze_performance()
        else:
            runtime_analysis = {'message': 'No runtime profiling data'}
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(static_analysis, security_analysis, runtime_analysis)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(static_analysis, security_analysis, runtime_analysis)
        
        analysis_time = time.time() - start_time
        
        return DebugReport(
            timestamp=datetime.now().isoformat(),
            total_issues=len(all_static_issues) + len(all_security_vulns),
            static_analysis=static_analysis,
            security_scan=security_analysis,
            runtime_debugging=runtime_analysis,
            overall_score=overall_score,
            recommendations=recommendations
        )
    
    def analyze_file(self, file_path: str) -> DebugReport:
        """Analyze a single file."""
        directory = Path(file_path).parent
        filename = Path(file_path).name
        return self.analyze_directory(str(directory), [filename])
    
    def _analyze_static_issues(self, issues: List[CodeIssue]) -> Dict[str, Any]:
        """Analyze static analysis issues."""
        if not issues:
            return {
                'total_issues': 0,
                'severity_breakdown': {},
                'category_breakdown': {},
                'top_issues': [],
                'score': 100
            }
        
        # Count by severity
        severity_counts = Counter(issue.severity for issue in issues)
        
        # Count by category
        category_counts = Counter(issue.category for issue in issues)
        
        # Get top issues
        top_issues = sorted(issues, key=lambda x: x.severity, reverse=True)[:10]
        
        # Calculate score (higher is better)
        max_possible_score = len(issues) * 5  # Max severity is 5
        actual_score = sum((5 - issue.severity + 1) for issue in issues)
        score = (actual_score / max_possible_score * 100) if max_possible_score > 0 else 100
        
        return {
            'total_issues': len(issues),
            'severity_breakdown': dict(severity_counts),
            'category_breakdown': dict(category_counts),
            'top_issues': [
                {
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'message': issue.message,
                    'severity': issue.severity,
                    'category': issue.category,
                    'suggestions': issue.suggestions
                }
                for issue in top_issues
            ],
            'score': min(score, 100)
        }
    
    def _analyze_security_vulnerabilities(self, vulns: List[SecurityVulnerability]) -> Dict[str, Any]:
        """Analyze security vulnerabilities."""
        if not vulns:
            return {
                'total_vulnerabilities': 0,
                'severity_breakdown': {},
                'type_breakdown': {},
                'critical_issues': [],
                'security_score': 100
            }
        
        # Count by severity
        severity_counts = Counter(vuln.severity for vuln in vulns)
        
        # Count by type
        type_counts = Counter(vuln.type for vuln in vulns)
        
        # Get critical issues
        critical_issues = [vuln for vuln in vulns if vuln.severity in ['high', 'critical']]
        
        # Calculate security score
        severity_weights = {'low': 1, 'medium': 3, 'high': 5, 'critical': 7}
        max_score = len(vulns) * 7
        actual_score = sum(severity_weights.get(vuln.severity, 1) for vuln in vulns)
        security_score = max(0, 100 - (actual_score / max_score * 100)) if max_score > 0 else 100
        
        return {
            'total_vulnerabilities': len(vulns),
            'severity_breakdown': dict(severity_counts),
            'type_breakdown': dict(type_counts),
            'critical_issues': [
                {
                    'file': vuln.file_path,
                    'line': vuln.line_number,
                    'type': vuln.type,
                    'severity': vuln.severity,
                    'description': vuln.description
                }
                for vuln in critical_issues
            ],
            'security_score': min(security_score, 100)
        }
    
    def _calculate_overall_score(self, static_analysis: Dict, security_analysis: Dict, runtime_analysis: Dict) -> float:
        """Calculate overall code quality score."""
        scores = []
        
        # Static analysis score
        if 'score' in static_analysis:
            scores.append(static_analysis['score'])
        
        # Security score
        if 'security_score' in security_analysis:
            scores.append(security_analysis['security_score'])
        
        # Runtime performance score (based on analysis quality)
        if runtime_analysis and 'performance_summary' in runtime_analysis:
            performance_data = runtime_analysis['performance_summary']
            if performance_data:
                # Penalize slow functions
                slow_functions = [func for func, data in performance_data.items() 
                                if data['avg_execution_time'] > 1.0]  # > 1 second
                performance_score = max(0, 100 - len(slow_functions) * 10)
                scores.append(performance_score)
        
        return sum(scores) / len(scores) if scores else 100.0
    
    def _generate_recommendations(self, static_analysis: Dict, security_analysis: Dict, runtime_analysis: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Static analysis recommendations
        if static_analysis.get('total_issues', 0) > 0:
            if static_analysis['severity_breakdown'].get(4, 0) > 0:
                recommendations.append("Address high-severity code issues first")
            
            if static_analysis['category_breakdown'].get('complexity', 0) > 0:
                recommendations.append("Consider refactoring complex functions to reduce cyclomatic complexity")
            
            if static_analysis['category_breakdown'].get('style', 0) > 0:
                recommendations.append("Adopt consistent code formatting standards")
        
        # Security recommendations
        if security_analysis.get('total_vulnerabilities', 0) > 0:
            if security_analysis['severity_breakdown'].get('high', 0) > 0:
                recommendations.append("URGENT: Address high-severity security vulnerabilities immediately")
            
            if security_analysis['type_breakdown'].get('sql_injection', 0) > 0:
                recommendations.append("Use parameterized queries to prevent SQL injection attacks")
            
            if security_analysis['type_breakdown'].get('hardcoded_secrets', 0) > 0:
                recommendations.append("Move secrets to environment variables or secure configuration")
        
        # Runtime performance recommendations
        if runtime_analysis and 'performance_summary' in runtime_analysis:
            performance_data = runtime_analysis['performance_summary']
            if performance_data:
                slow_functions = [func for func, data in performance_data.items() 
                                if data['avg_execution_time'] > 1.0]
                if slow_functions:
                    recommendations.append(f"Optimize slow functions: {', '.join(slow_functions[:3])}")
        
        if not recommendations:
            recommendations.append("Code quality is good! Continue following best practices.")
        
        return recommendations
    
    def save_report(self, report: DebugReport, output_path: str):
        """Save analysis report to file."""
        report_dict = asdict(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)
    
    def generate_markdown_report(self, report: DebugReport, output_path: str):
        """Generate a markdown report from analysis results."""
        markdown = f"""# Code Analysis & Debugging Report

**Generated:** {report.timestamp}  
**Overall Score:** {report.overall_score:.1f}/100  
**Total Issues:** {report.total_issues}

## Executive Summary

This report provides a comprehensive analysis of code quality, security, and performance based on {report.total_issues} identified issues.

### Key Metrics
- **Static Analysis Score:** {report.static_analysis.get('score', 'N/A'):.1f}/100
- **Security Score:** {report.security_scan.get('security_score', 'N/A'):.1f}/100
- **Runtime Analysis:** {len(report.runtime_debugging.get('performance_summary', {}))} functions analyzed

## Static Analysis Results

### Issue Breakdown
- **Total Issues:** {report.static_analysis.get('total_issues', 0)}
- **By Severity:** {report.static_analysis.get('severity_breakdown', {})}
- **By Category:** {report.static_analysis.get('category_breakdown', {})}

### Top Issues
"""
        
        for issue in report.static_analysis.get('top_issues', []):
            markdown += f"- **{issue['file']}:{issue['line']}** [{issue['category']}] {issue['message']} (Severity: {issue['severity']})\n"
        
        markdown += "\n## Security Analysis\n\n"
        markdown += f"- **Total Vulnerabilities:** {report.security_scan.get('total_vulnerabilities', 0)}\n"
        markdown += f"- **By Severity:** {report.security_scan.get('severity_breakdown', {})}\n"
        markdown += f"- **By Type:** {report.security_scan.get('type_breakdown', {})}\n\n"
        
        if report.security_scan.get('critical_issues'):
            markdown += "### Critical Security Issues\n"
            for vuln in report.security_scan['critical_issues']:
                markdown += f"- **{vuln['file']}:{vuln['line']}** [{vuln['type']}] {vuln['description']} (Severity: {vuln['severity']})\n"
            markdown += "\n"
        
        markdown += "## Runtime Performance\n\n"
        if report.runtime_debugging.get('performance_summary'):
            markdown += "### Function Performance Summary\n"
            for func, data in report.runtime_debugging['performance_summary'].items():
                markdown += f"- **{func}**: {data['avg_execution_time']:.3f}s avg ({data['call_count']} calls)\n"
        
        markdown += "\n## Recommendations\n\n"
        for i, rec in enumerate(report.recommendations, 1):
            markdown += f"{i}. {rec}\n"
        
        markdown += "\n---\n*Report generated by MiniMax Code Analysis & Debugging System*\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)


def main():
    """Demo function for the Code Analysis & Debugging System."""
    print("🔍 MiniMax Code Analysis & Debugging System")
    print("=" * 50)
    
    # Initialize the system
    analyzer = CodeAnalysisDebuggingSystem()
    
    # Demo analysis of the src directory
    src_path = "/workspace/src"
    
    try:
        print(f"Analyzing directory: {src_path}")
        report = analyzer.analyze_directory(src_path)
        
        print(f"\n📊 Analysis Complete!")
        print(f"Overall Score: {report.overall_score:.1f}/100")
        print(f"Total Issues: {report.total_issues}")
        print(f"Static Analysis Score: {report.static_analysis.get('score', 0):.1f}/100")
        print(f"Security Score: {report.security_scan.get('security_score', 0):.1f}/100")
        
        print("\n🔧 Top Recommendations:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"{i}. {rec}")
        
        # Save detailed reports
        json_report_path = "/workspace/data/code_analysis_report.json"
        markdown_report_path = "/workspace/data/code_analysis_report.md"
        
        analyzer.save_report(report, json_report_path)
        analyzer.generate_markdown_report(report, markdown_report_path)
        
        print(f"\n📄 Detailed reports saved:")
        print(f"- JSON: {json_report_path}")
        print(f"- Markdown: {markdown_report_path}")
        
        return report
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()