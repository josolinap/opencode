from functools import lru_cache
'\nfile_manager.py - File Operations Skill for Neo-Clone\n\nProvides:\n- File and directory information\n- Text file reading and analysis\n- File size and type detection\n- Directory listing and navigation hints\n- File search functionality\n'
import os
import json
import csv
from pathlib import Path
from typing import Dict, Any
import logging
from skills import BaseSkill
logger = logging.getLogger(__name__)

class FileManagerSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name='file_manager',
            description='Manages file operations: reads files, shows directory info, analyzes file contents',
            example='Show me information about this file, read a text file, or list directory contents'
        )

    @lru_cache(maxsize=128)
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get('text', '').lower()
        file_path = self._extract_file_path(text)
        if not file_path:
            return {'error': 'No file path found in request. Please specify a file path.', 'usage': "Try: 'read /path/to/file.txt' or 'show info about file.py'"}
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {'error': f'File or directory not found: {file_path}', 'suggestions': ['Check if the file path is correct', 'Use absolute paths when possible', 'Ensure proper file permissions']}
            if any((word in text for word in ['read', 'show', 'display', 'content'])):
                return self._read_file(file_path)
            elif any((word in text for word in ['info', 'information', 'details', 'size'])):
                return self._file_info(file_path)
            elif any((word in text for word in ['list', 'directory', 'ls', 'show files'])):
                return self._list_directory(file_path)
            elif any((word in text for word in ['search', 'find', 'grep'])):
                search_term = self._extract_search_term(text)
                return self._search_file(file_path, search_term)
            else:
                return self._file_info(file_path)
        except PermissionError:
            return {'error': f'Permission denied accessing: {file_path}', 'suggestion': 'Check file/directory permissions or try running with appropriate privileges'}
        except Exception as e:
            logger.error(f'File operation error: {e}')
            return {'error': f'File operation failed: {str(e)}', 'file_path': str(file_path)}

    def _extract_file_path(self, text: str) -> str:
        """Extract file path from user text"""
        import re
        quoted_paths = re.findall('["\\\']([^"\\\']+)["\\\']', text)
        if quoted_paths:
            return quoted_paths[0]
        path_patterns = ['/[^\\s]+', '[A-Za-z]:\\\\[^\\s]+', '\\./[^\\s]+', '[^\\s]+\\.(py|js|ts|json|yaml|yml|txt|csv|md|rst|log|ini|cfg|conf)']
        for pattern in path_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        words = text.split()
        for word in words:
            if '.' in word and len(word) > 1:
                return word
        return ''

    def _extract_search_term(self, text: str) -> str:
        """Extract search term from text"""
        import re
        quoted_terms = re.findall('["\\\']([^"\\\']+)["\\\']', text)
        if quoted_terms:
            return quoted_terms[0]
        for word in text.split():
            if word.lower() in ['for', 'find', 'search'] and text.split().index(word) < len(text.split()) - 1:
                return text.split()[text.split().index(word) + 1]
        return 'text'

    def _read_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and analyze file content"""
        if file_path.is_dir():
            return {'type': 'directory', 'path': str(file_path), 'message': f"{file_path} is a directory. Use 'list' to see contents."}
        file_size = file_path.stat().st_size
        max_read_size = 50 * 1024
        if file_size > max_read_size:
            return {'type': 'large_file', 'path': str(file_path), 'size': self._format_size(file_size), 'line_count': self._count_lines(file_path), 'message': f'File is too large to read entirely ({self._format_size(file_size)}). Reading first part...', 'content': self._read_partial_file(file_path, max_read_size), 'suggestion': 'Consider using search to find specific content in large files'}
        try:
            content = self._read_file_by_type(file_path)
            return {'type': 'file', 'path': str(file_path), 'size': self._format_size(file_size), 'line_count': self._count_lines(file_path), 'content': content, 'analysis': self._analyze_content(content, file_path.suffix)}
        except UnicodeDecodeError:
            return {'type': 'binary_file', 'path': str(file_path), 'size': self._format_size(file_size), 'message': 'Binary file detected. Content cannot be displayed as text.', 'suggestion': 'Use specialized tools to view this file type'}

    def _read_file_by_type(self, file_path: Path) -> str:
        """Read file content based on file type"""
        suffix = file_path.suffix.lower()
        if suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2, ensure_ascii=False)
        elif suffix == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 10:
                    return ''.join(lines[:10]) + f'\n... ({len(lines)} total lines)'
                else:
                    return ''.join(lines)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 5000:
                    return content[:5000] + f'\n... (truncated, {len(content)} total characters)'
                return content

    def _read_partial_file(self, file_path: Path, max_size: int) -> str:
        """Read first part of a large file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(max_size) + f'\n... (truncated at {max_size} bytes)'

    def _file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed file information"""
        stat = file_path.stat()
        info = {'path': str(file_path.absolute()), 'name': file_path.name, 'type': 'directory' if file_path.is_dir() else 'file', 'size': self._format_size(stat.st_size), 'size_bytes': stat.st_size, 'created': self._format_timestamp(stat.st_ctime), 'modified': self._format_timestamp(stat.st_mtime), 'accessed': self._format_timestamp(stat.st_atime)}
        if not file_path.is_dir():
            info['extension'] = file_path.suffix
            info['mime_type'] = self._get_mime_type(file_path)
            info['readable'] = os.access(file_path, os.R_OK)
            info['writable'] = os.access(file_path, os.W_OK)
            info['executable'] = os.access(file_path, os.X_OK)
        return info

    def _list_directory(self, dir_path: Path) -> Dict[str, Any]:
        """List directory contents"""
        if not dir_path.is_dir():
            return {'error': f'{dir_path} is not a directory', 'path': str(dir_path)}
        try:
            items = []
            total_size = 0
            for item in sorted(dir_path.iterdir()):
                try:
                    stat = item.stat()
                    item_info = {'name': item.name, 'type': 'directory' if item.is_dir() else 'file', 'size': self._format_size(stat.st_size), 'modified': self._format_timestamp(stat.st_mtime)}
                    items.append(item_info)
                    total_size += stat.st_size
                except (OSError, PermissionError):
                    items.append({'name': item.name, 'type': 'error', 'message': 'Permission denied'})
            return {'type': 'directory', 'path': str(dir_path.absolute()), 'item_count': len(items), 'total_size': self._format_size(total_size), 'items': items}
        except PermissionError:
            return {'error': f'Permission denied accessing directory: {dir_path}', 'path': str(dir_path)}

    def _search_file(self, file_path: Path, search_term: str) -> Dict[str, Any]:
        """Search for term in file content"""
        if not file_path.is_file():
            return {'error': f'{file_path} is not a file', 'path': str(file_path)}
        try:
            matches = []
            line_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line_count += 1
                    if search_term.lower() in line.lower():
                        matches.append({'line_number': line_count, 'content': line.rstrip()})
                        if len(matches) >= 20:
                            break
            return {'type': 'search_results', 'path': str(file_path), 'search_term': search_term, 'matches_found': len(matches), 'total_lines': line_count, 'matches': matches, 'summary': f"Found '{search_term}' in {len(matches)} lines out of {line_count} total lines"}
        except Exception as e:
            return {'error': f'Search failed: {str(e)}', 'path': str(file_path), 'search_term': search_term}

    def _analyze_content(self, content: str, file_type: str) -> Dict[str, Any]:
        """Analyze file content based on type"""
        analysis = {'content_length': len(content), 'line_count': content.count('\n') + 1}
        if file_type.lower() == '.py':
            analysis['analysis_type'] = 'Python code'
            analysis['functions'] = content.count('def ')
            analysis['classes'] = content.count('class ')
            analysis['imports'] = content.count('import ') + content.count('from ')
        elif file_type.lower() == '.json':
            analysis['analysis_type'] = 'JSON data'
            try:
                data = json.loads(content)
                analysis['top_level_keys'] = list(data.keys()) if isinstance(data, dict) else 'Array data'
            except json.JSONDecodeError:
                analysis['note'] = 'Invalid JSON format'
        elif file_type.lower() == '.csv':
            analysis['analysis_type'] = 'CSV data'
            lines = content.split('\n')
            if lines:
                analysis['columns'] = len(lines[0].split(',')) if lines[0] else 0
                analysis['data_rows'] = len([l for l in lines[1:] if l.strip()]) if len(lines) > 1 else 0
        return analysis

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.1f} PB'

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp to readable string"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum((1 for _ in f))
        except:
            return 0

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file"""
        import mimetypes
        (mime_type, _) = mimetypes.guess_type(str(file_path))
        return mime_type or 'unknown'
file_manager_skill = FileManagerSkill()