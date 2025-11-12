from functools import lru_cache
'\nlogging_system.py - Comprehensive Logging for Neo-Clone\n\nImplements:\n- Structured logging of all user interactions\n- Skill execution tracking with timestamps\n- Performance metrics and error logging\n- Configurable log levels and output formats\n- Log rotation and management\n'
import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import threading
import time

@dataclass
class InteractionLog:
    timestamp: str
    session_id: str
    event_type: str
    user_input: Optional[str] = None
    intent: Optional[str] = None
    skill_used: Optional[str] = None
    response: Optional[str] = None
    execution_time_ms: Optional[float] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class NeoLogger:

    def __init__(self, log_dir: str='data/logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._lock = threading.Lock()
        self._setup_loggers()
        self.interaction_log_file = self.log_dir / 'interactions.jsonl'

    def _setup_loggers(self):
        """Setup various loggers for different purposes"""
        self.app_logger = logging.getLogger('neo.app')
        self.app_logger.setLevel(logging.INFO)
        self.skill_logger = logging.getLogger('neo.skills')
        self.skill_logger.setLevel(logging.INFO)
        self.perf_logger = logging.getLogger('neo.performance')
        self.perf_logger.setLevel(logging.DEBUG)
        self.error_logger = logging.getLogger('neo.errors')
        self.error_logger.setLevel(logging.ERROR)
        detailed_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
        simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self._setup_file_handler(self.app_logger, 'neo.log', detailed_formatter, max_bytes=10 * 1024 * 1024, backup_count=5)
        self._setup_file_handler(self.skill_logger, 'skills.log', simple_formatter, max_bytes=5 * 1024 * 1024, backup_count=3)
        self._setup_file_handler(self.perf_logger, 'performance.log', simple_formatter, max_bytes=5 * 1024 * 1024, backup_count=3)
        self._setup_file_handler(self.error_logger, 'errors.log', detailed_formatter, max_bytes=10 * 1024 * 1024, backup_count=5)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.WARNING)
        self.app_logger.addHandler(console_handler)
        self.error_logger.addHandler(console_handler)

    def _setup_file_handler(self, logger: logging.Logger, filename: str, formatter: logging.Formatter, max_bytes: int, backup_count: int):
        """Setup rotating file handler for a logger"""
        file_path = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(file_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def log_user_message(self, message: str, metadata: Optional[Dict[str, Any]]=None):
        """Log a user message"""
        log_entry = InteractionLog(timestamp=datetime.now().isoformat(), session_id=self.session_id, event_type='user_message', user_input=message, metadata=metadata)
        self._write_interaction_log(log_entry)
        self.app_logger.info(f"User message: {message[:100]}{('...' if len(message) > 100 else '')}")

    def log_skill_execution(self, skill_name: str, user_input: str, response: str, success: bool=True, execution_time_ms: Optional[float]=None, error_message: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None):
        """Log skill execution details"""
        log_entry = InteractionLog(timestamp=datetime.now().isoformat(), session_id=self.session_id, event_type='skill_execution', user_input=user_input, skill_used=skill_name, response=response, success=success, execution_time_ms=execution_time_ms, error_message=error_message, metadata=metadata)
        self._write_interaction_log(log_entry)
        if success:
            self.skill_logger.info(f"Skill '{skill_name}' executed successfully in {execution_time_ms:.2f}ms")
        else:
            self.error_logger.error(f"Skill '{skill_name}' failed: {error_message}")

    def log_system_event(self, event_type: str, message: str, metadata: Optional[Dict[str, Any]]=None):
        """Log system events"""
        log_entry = InteractionLog(timestamp=datetime.now().isoformat(), session_id=self.session_id, event_type='system', response=message, metadata=metadata)
        self._write_interaction_log(log_entry)
        self.app_logger.info(f'System event [{event_type}]: {message}')

    def log_error(self, error_type: str, error_message: str, context: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None):
        """Log errors with context"""
        log_entry = InteractionLog(timestamp=datetime.now().isoformat(), session_id=self.session_id, event_type='error', error_message=error_message, metadata={'error_type': error_type, 'context': context, **(metadata or {})})
        self._write_interaction_log(log_entry)
        self.error_logger.error(f'[{error_type}] {error_message}' + (f' | Context: {context}' if context else ''))

    def log_performance(self, operation: str, execution_time_ms: float, metadata: Optional[Dict[str, Any]]=None):
        """Log performance metrics"""
        self.perf_logger.debug(f'Performance [{operation}]: {execution_time_ms:.2f}ms')
        log_entry = InteractionLog(timestamp=datetime.now().isoformat(), session_id=self.session_id, event_type='performance', execution_time_ms=execution_time_ms, metadata={'operation': operation, **(metadata or {})})
        self._write_interaction_log(log_entry)

    def _write_interaction_log(self, log_entry: InteractionLog):
        """Write structured interaction log to JSONL file"""
        with self._lock:
            try:
                with open(self.interaction_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(log_entry), ensure_ascii=False) + '\n')
            except Exception as e:
                self.error_logger.error(f'Failed to write interaction log: {e}')

    @lru_cache(maxsize=128)
    def get_recent_logs(self, event_type: Optional[str]=None, limit: int=100) -> list:
        """Get recent log entries"""
        try:
            logs = []
            if self.interaction_log_file.exists():
                with open(self.interaction_log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if event_type is None or entry.get('event_type') == event_type:
                                logs.append(entry)
                                if len(logs) >= limit:
                                    break
                        except json.JSONDecodeError:
                            continue
            return logs
        except Exception as e:
            self.error_logger.error(f'Failed to read interaction logs: {e}')
            return []

    def get_skill_statistics(self) -> Dict[str, Any]:
        """Get skill usage statistics from logs"""
        try:
            skill_stats = {}
            recent_logs = self.get_recent_logs(limit=1000)
            for entry in recent_logs:
                if entry.get('event_type') == 'skill_execution':
                    skill_name = entry.get('skill_used')
                    if skill_name:
                        if skill_name not in skill_stats:
                            skill_stats[skill_name] = {'total_calls': 0, 'successful_calls': 0, 'failed_calls': 0, 'average_execution_time': 0, 'total_execution_time': 0}
                        stats = skill_stats[skill_name]
                        stats['total_calls'] += 1
                        if entry.get('success'):
                            stats['successful_calls'] += 1
                        else:
                            stats['failed_calls'] += 1
                        exec_time = entry.get('execution_time_ms')
                        if exec_time:
                            stats['total_execution_time'] += exec_time
                            stats['average_execution_time'] = stats['total_execution_time'] / stats['total_calls']
            return skill_stats
        except Exception as e:
            self.error_logger.error(f'Failed to get skill statistics: {e}')
            return {}

    def export_logs(self, output_file: str, format_type: str='json', event_type: Optional[str]=None, limit: Optional[int]=None):
        """Export logs to file"""
        try:
            logs = self.get_recent_logs(event_type=event_type, limit=limit or 1000)
            if format_type.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
            elif format_type.lower() == 'txt':
                with open(output_file, 'w', encoding='utf-8') as f:
                    for entry in logs:
                        f.write(f"[{entry.get('timestamp', 'N/A')}] ")
                        f.write(f"[{entry.get('event_type', 'unknown')}] ")
                        if entry.get('user_input'):
                            f.write(f"User: {entry['user_input'][:100]}... ")
                        if entry.get('skill_used'):
                            f.write(f"Skill: {entry['skill_used']} ")
                        if entry.get('success') is not None:
                            f.write(f"Success: {entry['success']} ")
                        if entry.get('execution_time_ms'):
                            f.write(f"Time: {entry['execution_time_ms']:.2f}ms ")
                        if entry.get('error_message'):
                            f.write(f"Error: {entry['error_message']}")
                        f.write('\n')
        except Exception as e:
            self.error_logger.error(f'Failed to export logs: {e}')

    def clear_old_logs(self, days_to_keep: int=30):
        """Clear logs older than specified days"""
        try:
            cutoff_time = time.time() - days_to_keep * 24 * 60 * 60
            for log_file in [self.interaction_log_file]:
                if log_file.exists():
                    recent_logs = []
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                entry_time = datetime.fromisoformat(entry.get('timestamp', '')).timestamp()
                                if entry_time > cutoff_time:
                                    recent_logs.append(entry)
                            except (json.JSONDecodeError, ValueError, OSError):
                                continue
                    with open(log_file, 'w', encoding='utf-8') as f:
                        for entry in recent_logs:
                            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            self.app_logger.info(f'Cleared logs older than {days_to_keep} days')
        except Exception as e:
            self.error_logger.error(f'Failed to clear old logs: {e}')

def log_execution_time(logger: NeoLogger, operation: str):
    """Decorator to log execution time of functions"""

    def decorator(func):

        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                logger.log_performance(operation, execution_time, {'function': func.__name__, 'args_count': len(args), 'kwargs_count': len(kwargs), 'success': True})
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.log_performance(operation, execution_time, {'function': func.__name__, 'error': str(e), 'success': False})
                raise
        return wrapper
    return decorator
_logger_instance = None

def get_logger() -> NeoLogger:
    """Get global logger instance (singleton pattern)"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = NeoLogger()
    return _logger_instance

class SkillExecutionContext:

    def __init__(self, logger: NeoLogger, skill_name: str, user_input: str):
        self.logger = logger
        self.skill_name = skill_name
        self.user_input = user_input
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = (time.time() - self.start_time) * 1000 if self.start_time else None
        if exc_val:
            self.logger.log_skill_execution(skill_name=self.skill_name, user_input=self.user_input, response='', success=False, execution_time_ms=execution_time, error_message=str(exc_val))
        else:
            self.logger.log_skill_execution(skill_name=self.skill_name, user_input=self.user_input, response='Skill executed successfully', success=True, execution_time_ms=execution_time)