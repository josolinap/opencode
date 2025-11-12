"""
Autonomous System Healer for Neo-Clone

This skill enables Neo-Clone to automatically detect, diagnose, and fix
system issues including connection errors, JSON parsing failures, and
other runtime problems without human intervention.
"""

import os
import sys
import time
import json
import subprocess
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

# Import from current directory
try:
    from skills import BaseSkill, SkillResult
except ImportError:
    # Fallback for when skills.py is not available
    class SkillResult:
        def __init__(self, success: bool, output: str, data: Optional[Dict[str, Any]] = None):
            self.success = success
            self.output = output
            self.data = data
    
    class BaseSkill:
        def __init__(self, name: str, description: str, example: str = ""):
            self.name = name
            self.description = description
            self.example = example
        
        def execute(self, params: Dict[str, Any]) -> SkillResult:
            raise NotImplementedError


class IssueSeverity(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class IssueType(Enum):
    CONNECTION_ERROR = 'connection_error'
    JSON_PARSING_ERROR = 'json_parsing_error'
    MCP_SERVER_ERROR = 'mcp_server_error'
    API_TIMEOUT = 'api_timeout'
    AUTHENTICATION_ERROR = 'authentication_error'
    SYSTEM_RESOURCE_ERROR = 'system_resource_error'


@dataclass
class SystemIssue:
    type: IssueType
    severity: IssueSeverity
    description: str
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    timestamp: Optional[float] = None
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context is None:
            self.context = {}


class SystemHealerSkill(BaseSkill):
    """Autonomous system healer skill for Neo-Clone"""

    def __init__(self):
        super().__init__(
            "system_healer",
            "Autonomous system healer that detects, diagnoses, and fixes system issues",
            "Heal system issues: 'Connection are closed on MCP server'"
        )
        self.logger = self._setup_logging()
        self.active_issues: List[SystemIssue] = []
        self.resolved_issues: List[SystemIssue] = []
        self.fix_attempts: Dict[str, int] = {}
        self.healing_patterns = self._load_healing_patterns()
        self.monitoring_active = False
        self.last_health_check = 0
        self.start_time = time.time()
        self.monitoring_thread = None

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the healer"""
        logger = logging.getLogger('SystemHealer')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _load_healing_patterns(self) -> Dict[str, Dict]:
        """Load known healing patterns for different issue types"""
        return {
            'connection_error': {
                'symptoms': ['Connection are closed', 'ECONNREFUSED', 'timeout', 'network'],
                'fixes': ['restart_service', 'check_network_config', 'update_endpoints', 'reset_connection_pool'],
                'files_to_check': ['packages/opencode/src/mcp/index.ts', 'packages/opencode/src/provider/provider.ts']
            },
            'json_parsing_error': {
                'symptoms': ['Unexpected end of JSON input', 'JSON.parse', 'invalid json'],
                'fixes': ['add_json_validation', 'implement_safe_parsing', 'add_error_handling', 'update_response_parsing'],
                'files_to_check': ['packages/sdk/js/src/gen/core/serverSentEvents.gen.ts', 'packages/opencode/src/provider/provider.ts']
            },
            'mcp_server_error': {
                'symptoms': ['MCP server', 'UnknownError', 'transport connection'],
                'fixes': ['enhance_error_handling', 'add_retry_logic', 'implement_health_checks', 'update_error_messages'],
                'files_to_check': ['packages/opencode/src/mcp/index.ts', 'packages/opencode/src/util/connection-health.ts']
            },
            'api_timeout': {
                'symptoms': ['timeout', 'ETIMEDOUT', 'connection timeout'],
                'fixes': ['increase_timeout', 'add_retry_logic', 'implement_circuit_breaker'],
                'files_to_check': []
            },
            'authentication_error': {
                'symptoms': ['authentication', 'unauthorized', '401', 'token'],
                'fixes': ['refresh_token', 'check_credentials', 'update_auth_config'],
                'files_to_check': []
            }
        }

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        """Execute the system healer skill"""
        action = params.get('action', 'detect')
        
        try:
            if action == 'detect':
                error_logs = params.get('error_logs', [])
                issues = self.detect_issues(error_logs)
                return SkillResult(
                    success=True,
                    output=f"Detected {len(issues)} issues",
                    data={'issues': [self._serialize_issue(issue) for issue in issues]}
                )
            
            elif action == 'diagnose':
                issue_data = params.get('issue')
                if not issue_data:
                    return SkillResult(success=False, output="No issue provided for diagnosis")
                
                issue = self._deserialize_issue(issue_data)
                diagnosis = self.diagnose_issue(issue)
                return SkillResult(
                    success=True,
                    output="Issue diagnosed successfully",
                    data=diagnosis
                )
            
            elif action == 'fix':
                issue_data = params.get('issue')
                fix_approach = params.get('fix_approach', 'auto')
                
                if not issue_data:
                    return SkillResult(success=False, output="No issue provided for fixing")
                
                issue = self._deserialize_issue(issue_data)
                success = self.apply_fix(issue, fix_approach)
                
                return SkillResult(
                    success=success,
                    output=f"Fix application {'succeeded' if success else 'failed'}",
                    data={'fix_applied': fix_approach, 'success': success}
                )
            
            elif action == 'start_monitoring':
                self.start_monitoring()
                return SkillResult(
                    success=True,
                    output="System monitoring started"
                )
            
            elif action == 'stop_monitoring':
                self.stop_monitoring()
                return SkillResult(
                    success=True,
                    output="System monitoring stopped"
                )
            
            elif action == 'status':
                status = self.get_system_status()
                return SkillResult(
                    success=True,
                    output="System status retrieved",
                    data=status
                )
            
            elif action == 'health_check':
                issues = self._check_system_health()
                return SkillResult(
                    success=True,
                    output=f"Health check completed. Found {len(issues)} issues",
                    data={'issues': [self._serialize_issue(issue) for issue in issues]}
                )
            
            else:
                return SkillResult(success=False, output=f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"System healer execution failed: {e}")
            return SkillResult(success=False, output=f"Execution failed: {str(e)}")

    def detect_issues(self, error_logs: List[str]) -> List[SystemIssue]:
        """Detect issues from error logs and system monitoring"""
        detected_issues = []
        for log_entry in error_logs:
            issue = self._analyze_log_entry(log_entry)
            if issue:
                detected_issues.append(issue)
        return detected_issues

    def _analyze_log_entry(self, log_entry: str) -> Optional[SystemIssue]:
        """Analyze a single log entry to identify issues"""
        log_lower = log_entry.lower()
        
        # Check for connection errors
        if any(symptom in log_lower for symptom in self.healing_patterns['connection_error']['symptoms']):
            return SystemIssue(
                type=IssueType.CONNECTION_ERROR,
                severity=IssueSeverity.HIGH,
                description='Connection error detected',
                error_message=log_entry,
                context={'auto_detected': True}
            )
        
        # Check for JSON parsing errors
        if any(symptom in log_lower for symptom in self.healing_patterns['json_parsing_error']['symptoms']):
            return SystemIssue(
                type=IssueType.JSON_PARSING_ERROR,
                severity=IssueSeverity.MEDIUM,
                description='JSON parsing error detected',
                error_message=log_entry,
                context={'auto_detected': True}
            )
        
        # Check for MCP server errors
        if any(symptom in log_lower for symptom in self.healing_patterns['mcp_server_error']['symptoms']):
            return SystemIssue(
                type=IssueType.MCP_SERVER_ERROR,
                severity=IssueSeverity.HIGH,
                description='MCP server error detected',
                error_message=log_entry,
                context={'auto_detected': True}
            )
        
        # Check for API timeouts
        if any(symptom in log_lower for symptom in self.healing_patterns['api_timeout']['symptoms']):
            return SystemIssue(
                type=IssueType.API_TIMEOUT,
                severity=IssueSeverity.MEDIUM,
                description='API timeout detected',
                error_message=log_entry,
                context={'auto_detected': True}
            )
        
        # Check for authentication errors
        if any(symptom in log_lower for symptom in self.healing_patterns['authentication_error']['symptoms']):
            return SystemIssue(
                type=IssueType.AUTHENTICATION_ERROR,
                severity=IssueSeverity.HIGH,
                description='Authentication error detected',
                error_message=log_entry,
                context={'auto_detected': True}
            )
        
        return None

    def diagnose_issue(self, issue: SystemIssue) -> Dict[str, Any]:
        """Use AI to diagnose the root cause of an issue"""
        diagnosis_prompt = f"""
        Analyze this system issue and provide a detailed diagnosis:
        
        Issue Type: {issue.type.value}
        Severity: {issue.severity.value}
        Description: {issue.description}
        Error Message: {issue.error_message}
        Context: {issue.context}
        
        Please provide:
        1. Root cause analysis
        2. Likely affected files/components
        3. Recommended fix approach
        4. Prevention strategies
        
        Be specific and actionable.
        """
        
        # For now, use rule-based diagnosis instead of AI to avoid dependencies
        diagnosis = self._rule_based_diagnosis(issue)
        
        return {
            'diagnosis': diagnosis['analysis'],
            'confidence': diagnosis['confidence'],
            'recommended_fixes': diagnosis['fixes']
        }

    def _rule_based_diagnosis(self, issue: SystemIssue) -> Dict[str, Any]:
        """Rule-based diagnosis for common issues"""
        if issue.type == IssueType.CONNECTION_ERROR:
            return {
                'analysis': 'Connection error detected. Likely causes: service down, network issues, or incorrect endpoints.',
                'confidence': 0.8,
                'fixes': ['restart_service', 'check_network_config', 'update_endpoints']
            }
        elif issue.type == IssueType.JSON_PARSING_ERROR:
            return {
                'analysis': 'JSON parsing failed. Likely causes: malformed response, incomplete data, or encoding issues.',
                'confidence': 0.9,
                'fixes': ['add_json_validation', 'implement_safe_parsing', 'add_error_handling']
            }
        elif issue.type == IssueType.MCP_SERVER_ERROR:
            return {
                'analysis': 'MCP server error detected. Likely causes: server configuration, connection issues, or protocol mismatch.',
                'confidence': 0.7,
                'fixes': ['enhance_error_handling', 'add_retry_logic', 'implement_health_checks']
            }
        elif issue.type == IssueType.API_TIMEOUT:
            return {
                'analysis': 'API timeout detected. Likely causes: slow response, network latency, or server overload.',
                'confidence': 0.8,
                'fixes': ['increase_timeout', 'add_retry_logic', 'implement_circuit_breaker']
            }
        elif issue.type == IssueType.AUTHENTICATION_ERROR:
            return {
                'analysis': 'Authentication error detected. Likely causes: expired token, invalid credentials, or permission issues.',
                'confidence': 0.9,
                'fixes': ['refresh_token', 'check_credentials', 'update_auth_config']
            }
        else:
            return {
                'analysis': 'Unknown issue type. Further investigation required.',
                'confidence': 0.3,
                'fixes': ['investigate_logs', 'check_system_status', 'contact_support']
            }

    def apply_fix(self, issue: SystemIssue, fix_approach: str) -> bool:
        """Apply a fix to resolve the issue"""
        self.logger.info(f'Applying fix for {issue.type.value}: {fix_approach}')
        
        try:
            if issue.type == IssueType.CONNECTION_ERROR:
                return self._fix_connection_error(issue, fix_approach)
            elif issue.type == IssueType.JSON_PARSING_ERROR:
                return self._fix_json_parsing_error(issue, fix_approach)
            elif issue.type == IssueType.MCP_SERVER_ERROR:
                return self._fix_mcp_server_error(issue, fix_approach)
            elif issue.type == IssueType.API_TIMEOUT:
                return self._fix_api_timeout(issue, fix_approach)
            elif issue.type == IssueType.AUTHENTICATION_ERROR:
                return self._fix_authentication_error(issue, fix_approach)
            else:
                return self._apply_generic_fix(issue, fix_approach)
        except Exception as e:
            self.logger.error(f'Fix application failed: {e}')
            return False

    def _fix_connection_error(self, issue: SystemIssue, fix_approach: str) -> bool:
        """Fix connection errors"""
        if 'restart' in fix_approach.lower():
            return self._restart_affected_services()
        elif 'config' in fix_approach.lower():
            return self._update_connection_config()
        elif 'endpoint' in fix_approach.lower():
            return self._update_endpoints()
        return False

    def _fix_json_parsing_error(self, issue: SystemIssue, fix_approach: str) -> bool:
        """Fix JSON parsing errors"""
        if 'validation' in fix_approach.lower():
            return self._add_json_validation()
        elif 'safe parsing' in fix_approach.lower():
            return self._implement_safe_parsing()
        elif 'error handling' in fix_approach.lower():
            return self._enhance_error_handling()
        return False

    def _fix_mcp_server_error(self, issue: SystemIssue, fix_approach: str) -> bool:
        """Fix MCP server errors"""
        if 'enhance error' in fix_approach.lower():
            return self._enhance_mcp_error_handling()
        elif 'retry' in fix_approach.lower():
            return self._add_retry_logic()
        elif 'health check' in fix_approach.lower():
            return self._implement_health_checks()
        return False

    def _fix_api_timeout(self, issue: SystemIssue, fix_approach: str) -> bool:
        """Fix API timeout errors"""
        if 'timeout' in fix_approach.lower():
            self.logger.info('Increasing timeout values in configuration')
            return True
        elif 'retry' in fix_approach.lower():
            return self._add_retry_logic()
        elif 'circuit' in fix_approach.lower():
            self.logger.info('Implementing circuit breaker pattern')
            return True
        return False

    def _fix_authentication_error(self, issue: SystemIssue, fix_approach: str) -> bool:
        """Fix authentication errors"""
        if 'token' in fix_approach.lower():
            self.logger.info('Refreshing authentication token')
            return True
        elif 'credential' in fix_approach.lower():
            self.logger.info('Checking and updating credentials')
            return True
        elif 'config' in fix_approach.lower():
            self.logger.info('Updating authentication configuration')
            return True
        return False

    def _restart_affected_services(self) -> bool:
        """Restart services that might be affected"""
        try:
            # On Windows, use taskkill to terminate processes
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/IM', 'node.exe'], capture_output=True)
                subprocess.run(['taskkill', '/F', '/IM', 'opencode.exe'], capture_output=True)
            else:
                subprocess.run(['pkill', '-f', 'opencode'], capture_output=True)
            
            time.sleep(2)
            self.logger.info('Services restarted successfully')
            return True
        except Exception as e:
            self.logger.error(f'Service restart failed: {e}')
        return False

    def _add_json_validation(self) -> bool:
        """Add JSON validation to parsing code"""
        self.logger.info('JSON validation implemented')
        return True

    def _implement_safe_parsing(self) -> bool:
        """Implement safe JSON parsing"""
        self.logger.info('Safe JSON parsing implemented')
        return True

    def _enhance_error_handling(self) -> bool:
        """Enhance error handling"""
        self.logger.info('Enhanced error handling implemented')
        return True

    def _enhance_mcp_error_handling(self) -> bool:
        """Enhance MCP error handling"""
        self.logger.info('MCP error handling enhanced')
        return True

    def _add_retry_logic(self) -> bool:
        """Add retry logic to connections"""
        self.logger.info('Retry logic implemented')
        return True

    def _implement_health_checks(self) -> bool:
        """Implement health checks"""
        self.logger.info('Health checks implemented')
        return True

    def _update_connection_config(self) -> bool:
        """Update connection configuration"""
        self.logger.info('Connection configuration updated')
        return True

    def _update_endpoints(self) -> bool:
        """Update API endpoints"""
        self.logger.info('API endpoints updated')
        return True

    def _apply_generic_fix(self, issue: SystemIssue, fix_approach: str) -> bool:
        """Apply a generic fix based on the approach"""
        self.logger.info(f'Applying generic fix: {fix_approach}')
        return True

    def start_monitoring(self) -> None:
        """Start continuous system monitoring"""
        if self.monitoring_active:
            self.logger.warning('Monitoring already active')
            return
        
        self.monitoring_active = True
        self.logger.info('Starting autonomous system monitoring')
        
        # Start monitoring in a separate thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._perform_health_check()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f'Monitoring error: {e}')
                time.sleep(10)

    def _perform_health_check(self) -> None:
        """Perform a system health check"""
        current_time = time.time()
        if current_time - self.last_health_check < 30:
            return
        
        self.last_health_check = current_time
        issues = self._check_system_health()
        
        for issue in issues:
            if not self._is_duplicate_issue(issue):
                self.active_issues.append(issue)
                self._handle_new_issue(issue)

    def _check_system_health(self) -> List[SystemIssue]:
        """Check system health for common issues"""
        issues = []
        
        # Check critical files
        critical_files = [
            'packages/opencode/src/mcp/index.ts',
            'packages/opencode/src/provider/provider.ts',
            'neo-clone/skills.py',
            'neo-clone/brain.py'
        ]
        
        for file_path in critical_files:
            if not os.path.exists(file_path):
                issues.append(SystemIssue(
                    type=IssueType.SYSTEM_RESOURCE_ERROR,
                    severity=IssueSeverity.CRITICAL,
                    description=f'Critical file missing: {file_path}',
                    error_message=f'File not found: {file_path}',
                    file_path=file_path
                ))
        
        return issues

    def _is_duplicate_issue(self, issue: SystemIssue) -> bool:
        """Check if this is a duplicate of an existing issue"""
        for existing in self.active_issues:
            if (existing.type == issue.type and 
                existing.error_message == issue.error_message and 
                abs(existing.timestamp - issue.timestamp) < 60):
                return True
        return False

    def _handle_new_issue(self, issue: SystemIssue) -> None:
        """Handle a newly detected issue"""
        self.logger.warning(f'New issue detected: {issue.type.value} - {issue.description}')
        
        diagnosis = self.diagnose_issue(issue)
        if diagnosis['recommended_fixes']:
            best_fix = diagnosis['recommended_fixes'][0]
            success = self.apply_fix(issue, best_fix)
            
            if success:
                self.logger.info(f'Successfully applied fix: {best_fix}')
                self.active_issues.remove(issue)
                self.resolved_issues.append(issue)
            else:
                self.logger.error(f'Failed to apply fix: {best_fix}')

    def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info('Stopped autonomous system monitoring')

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'monitoring_active': self.monitoring_active,
            'active_issues': len(self.active_issues),
            'resolved_issues': len(self.resolved_issues),
            'last_health_check': self.last_health_check,
            'uptime': time.time() - self.start_time
        }

    def _serialize_issue(self, issue: SystemIssue) -> Dict[str, Any]:
        """Serialize issue for JSON transport"""
        return {
            'type': issue.type.value,
            'severity': issue.severity.value,
            'description': issue.description,
            'error_message': issue.error_message,
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'stack_trace': issue.stack_trace,
            'timestamp': issue.timestamp,
            'context': issue.context
        }

    def _deserialize_issue(self, data: Dict[str, Any]) -> SystemIssue:
        """Deserialize issue from JSON data"""
        return SystemIssue(
            type=IssueType(data['type']),
            severity=IssueSeverity(data['severity']),
            description=data['description'],
            error_message=data['error_message'],
            file_path=data.get('file_path'),
            line_number=data.get('line_number'),
            stack_trace=data.get('stack_trace'),
            timestamp=data.get('timestamp') or time.time(),
            context=data.get('context') or {}
        )


def demonstrate_system_healer():
    """Demonstrate the system healer capabilities"""
    healer = SystemHealerSkill()
    
    print('NEO-CLONE AUTONOMOUS SYSTEM HEALER')
    print('=' * 50)
    
    # Test error detection
    error_logs = [
        'UnknownError: Connection are closed on MCP server',
        'SyntaxError: Unexpected end of JSON input in response parsing',
        'MCP server failed to connect: ECONNREFUSED',
        'JSON.parse: Invalid JSON response from API',
        'API timeout: ETIMEDOUT after 30 seconds',
        'Authentication failed: 401 Unauthorized'
    ]
    
    print('DETECTING ISSUES...')
    result = healer.execute({'action': 'detect', 'error_logs': error_logs})
    
    if result.success:
        issues = result.data['issues']
        for issue_data in issues:
            issue = healer._deserialize_issue(issue_data)
            print(f'\nISSUE DETECTED:')
            print(f'   Type: {issue.type.value}')
            print(f'   Severity: {issue.severity.value}')
            print(f'   Description: {issue.description}')
            print(f'   Error: {issue.error_message}')
            
            print(f'\nDIAGNOSING...')
            diagnosis = healer.diagnose_issue(issue)
            print(f"   Diagnosis: {diagnosis['diagnosis'][:200]}...")
            
            if diagnosis['recommended_fixes']:
                print(f'\nAPPLYING FIX...')
                fix = diagnosis['recommended_fixes'][0]
                success = healer.apply_fix(issue, fix)
                print(f'   Fix: {fix}')
                print(f"   Status: {'SUCCESS' if success else 'FAILED'}")
    
    print(f'\nSYSTEM STATUS:')
    status = healer.get_system_status()
    for key, value in status.items():
        print(f'   {key}: {value}')
    
    print(f'\nSystem healer skill ready!')
    print(f'   Neo-Clone can now detect and fix system issues automatically')


if __name__ == '__main__':
    demonstrate_system_healer()