"""
Data Inspector Skill for Neo-Clone
Advanced data inspection with statistical analysis, data quality assessment, and insights generation for CSV, JSON, and text files.
"""

from skills import BaseSkill, SkillParameter, SkillParameterType, SkillStatus
from data_models import SkillResult, SkillContext, SkillCategory
import os
import json
import csv
import time
from collections import Counter, defaultdict
from datetime import datetime
import statistics
from functools import lru_cache
from typing import Dict, Any, Optional, List, Union
import logging
import hashlib

logger = logging.getLogger(__name__)

class DataInspectorSkill(BaseSkill):

    def __init__(self):
        super().__init__()
        self.metadata.name = 'DataInspectorSkill'
        self.metadata.category = SkillCategory.DATA_ANALYSIS
        self.metadata.description = 'Advanced data inspection with statistical analysis, data quality assessment, and insights generation for CSV, JSON, and text files.'
        self.metadata.capabilities = [
            "csv_analysis",
            "json_analysis", 
            "text_analysis",
            "data_quality_assessment",
            "statistical_analysis"
        ]
        self._cache = {}
        self._max_cache_size = 50

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            'file_path': SkillParameter(
                name='file_path',
                param_type=SkillParameterType.STRING,
                required=True,
                description='Path to data file to analyze'
            ),
            'data_type': SkillParameter(
                name='data_type',
                param_type=SkillParameterType.STRING,
                required=False,
                default='',
                description='Type of data file (csv, json, txt). Auto-detected if not specified'
            ),
            'analysis_depth': SkillParameter(
                name='analysis_depth',
                param_type=SkillParameterType.STRING,
                required=False,
                default='detailed',
                description='Depth of analysis (basic, detailed, comprehensive). Default: detailed'
            ),
            'sample_size': SkillParameter(
                name='sample_size',
                param_type=SkillParameterType.INTEGER,
                required=False,
                default=1000,
                description='Number of rows to sample for large files (default: 1000)'
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute data inspection with given parameters"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING
        
        try:
            validated_params = self.validate_parameters(**kwargs)
            file_path = validated_params.get('file_path', '')
            data_type = validated_params.get('data_type', '')
            analysis_depth = validated_params.get('analysis_depth', 'detailed')
            sample_size = validated_params.get('sample_size', 1000)

            # Generate cache key
            cache_key = hashlib.md5(f'{file_path}_{data_type}_{analysis_depth}_{sample_size}'.encode()).hexdigest()
            
            # Check cache first
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                cached_result['cached'] = True
                return SkillResult(
                    success=True,
                    output="Data inspection completed (cached)",
                    skill_name=self.metadata.name,
                    execution_time=0.001,
                    metadata=cached_result
                )

            # Validate input
            if not file_path or not os.path.exists(file_path):
                return SkillResult(
                    success=False,
                    output=f"File not found: {file_path}",
                    skill_name=self.metadata.name,
                    execution_time=0.001,
                    error_message="File not found"
                )

            # Auto-detect data type if not specified
            if not data_type:
                data_type = self._detect_file_type(file_path)

            # Perform analysis based on data type
            if data_type == 'csv':
                result = self._analyze_csv(file_path, analysis_depth, sample_size)
            elif data_type == 'json':
                result = self._analyze_json(file_path, analysis_depth)
            elif data_type == 'txt':
                result = self._analyze_text(file_path, analysis_depth)
            else:
                return SkillResult(
                    success=False,
                    output=f"Unsupported data type: {data_type}",
                    skill_name=self.metadata.name,
                    execution_time=0.001,
                    error_message="Unsupported data type"
                )

# Add to cache
            self._add_to_cache(cache_key, result)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, {"file_type": data_type})
            
            return SkillResult(
                success=True,
                output=f"Data inspection completed for {os.path.basename(file_path)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata=result
            )

        except Exception as e:
            self.status = SkillStatus.FAILED
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False, {"error": str(e)})
            
            logger.error(f"Data inspection failed: {str(e)}")
            return SkillResult(
                success=False,
                output=f"Data inspection failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                error_message=str(e)
            )
        finally:
            self.status = SkillStatus.IDLE

    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension"""
        _, ext = os.path.splitext(file_path.lower())
        if ext == '.csv':
            return 'csv'
        elif ext == '.json':
            return 'json'
        elif ext in ['.txt', '.log', '.md']:
            return 'txt'
        else:
            # Try to detect by content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('{') or first_line.startswith('['):
                        return 'json'
                    elif ',' in first_line and any(char in first_line for char in ['"', "'"]):
                        return 'csv'
                    else:
                        return 'txt'
            except Exception:
                return 'txt'

    def _analyze_csv(self, file_path: str, analysis_depth: str, sample_size: int) -> Dict[str, Any]:
        """Analyze CSV file"""
        try:
            # Read CSV file
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                rows = list(reader)

            # Limit sample size for large files
            if len(rows) > sample_size:
                rows = rows[:sample_size]
                is_sample = True
            else:
                is_sample = False

            # Basic statistics
            result = {
                'file_type': 'csv',
                'file_path': file_path,
                'total_rows': len(rows),
                'total_columns': len(headers),
                'headers': headers,
                'is_sample': is_sample,
                'sample_size': sample_size if is_sample else len(rows),
                'analysis_depth': analysis_depth,
                'cached': False
            }

            if analysis_depth in ['detailed', 'comprehensive']:
                # Column analysis
                column_analysis = {}
                for header in headers:
                    column_data = [row.get(header, '') for row in rows if row.get(header)]
                    
                    if column_data:
                        # Detect data type
                        data_type = self._detect_column_type(column_data)
                        
                        analysis = {
                            'data_type': data_type,
                            'non_null_count': len(column_data),
                            'null_count': len(rows) - len(column_data),
                            'unique_count': len(set(str(v) for v in column_data))
                        }

                        if data_type == 'numeric':
                            numeric_values = [float(v) for v in column_data if self._is_numeric(v)]
                            if numeric_values:
                                analysis.update({
                                    'min': min(numeric_values),
                                    'max': max(numeric_values),
                                    'mean': statistics.mean(numeric_values),
                                    'median': statistics.median(numeric_values),
                                    'std_dev': statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                                })

                        elif data_type == 'text':
                            text_lengths = [len(str(v)) for v in column_data]
                            if text_lengths:
                                analysis.update({
                                    'avg_length': statistics.mean(text_lengths),
                                    'min_length': min(text_lengths),
                                    'max_length': max(text_lengths)
                                })

                        column_analysis[header] = analysis

                result['column_analysis'] = column_analysis

            if analysis_depth == 'comprehensive':
                # Data quality assessment
                result['data_quality'] = self._assess_data_quality(rows, headers)

            return result

        except Exception as e:
            logger.error(f"CSV analysis failed: {str(e)}")
            return {'error': f'CSV analysis failed: {str(e)}'}

    def _analyze_json(self, file_path: str, analysis_depth: str) -> Dict[str, Any]:
        """Analyze JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            result = {
                'file_type': 'json',
                'file_path': file_path,
                'analysis_depth': analysis_depth,
                'cached': False
            }

            if isinstance(data, list):
                result['structure'] = 'array'
                result['total_items'] = len(data)
                result['sample_items'] = data[:5]  # First 5 items as sample

                if analysis_depth in ['detailed', 'comprehensive'] and data:
                    # Analyze first item structure
                    first_item = data[0]
                    result['item_structure'] = self._analyze_json_structure(first_item)

            elif isinstance(data, dict):
                result['structure'] = 'object'
                result['total_keys'] = len(data)
                result['keys'] = list(data.keys())
                result['sample_data'] = {k: data[k] for k in list(data.keys())[:5]}

                if analysis_depth in ['detailed', 'comprehensive']:
                    result['key_analysis'] = {}
                    for key, value in data.items():
                        result['key_analysis'][key] = {
                            'type': type(value).__name__,
                            'size': len(str(value)) if value else 0
                        }

            else:
                result['structure'] = 'primitive'
                result['value'] = data
                result['type'] = type(data).__name__

            return result

        except Exception as e:
            logger.error(f"JSON analysis failed: {str(e)}")
            return {'error': f'JSON analysis failed: {str(e)}'}

    def _analyze_text(self, file_path: str, analysis_depth: str) -> Dict[str, Any]:
        """Analyze text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            words = content.split()
            sentences = [s.strip() for s in content.split('.') if s.strip()]

            result = {
                'file_type': 'text',
                'file_path': file_path,
                'total_characters': len(content),
                'total_words': len(words),
                'total_lines': len(lines),
                'total_sentences': len(sentences),
                'analysis_depth': analysis_depth,
                'cached': False
            }

            if analysis_depth in ['detailed', 'comprehensive']:
                # Word frequency analysis
                word_freq = Counter(word.lower().strip('.,!?;:"()[]{}') for word in words if word.strip('.,!?;:"()[]{}'))
                result['most_common_words'] = word_freq.most_common(10)

                # Line length statistics
                line_lengths = [len(line) for line in lines]
                if line_lengths:
                    result['line_stats'] = {
                        'avg_length': statistics.mean(line_lengths),
                        'min_length': min(line_lengths),
                        'max_length': max(line_lengths)
                    }

            if analysis_depth == 'comprehensive':
                # Text quality metrics
                result['text_quality'] = {
                    'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
                    'avg_chars_per_word': len(content) / len(words) if words else 0,
                    'empty_lines': sum(1 for line in lines if not line.strip())
                }

            return result

        except Exception as e:
            logger.error(f"Text analysis failed: {str(e)}")
            return {'error': f'Text analysis failed: {str(e)}'}

    def _detect_column_type(self, column_data: List[str]) -> str:
        """Detect the data type of a column"""
        if not column_data:
            return 'empty'

        # Check for numeric
        numeric_count = sum(1 for v in column_data if self._is_numeric(v))
        if numeric_count / len(column_data) > 0.8:
            return 'numeric'

        # Check for boolean
        bool_values = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f'}
        bool_count = sum(1 for v in column_data if str(v).lower() in bool_values)
        if bool_count / len(column_data) > 0.8:
            return 'boolean'

        # Check for date
        date_count = 0
        for v in column_data[:10]:  # Check first 10 values
            try:
                # Simple date detection
                if any(char in str(v) for char in ['-', '/', ':']) and len(str(v)) > 6:
                    date_count += 1
            except Exception:
                continue
        if date_count / min(len(column_data), 10) > 0.6:
            return 'date'

        return 'text'

    def _is_numeric(self, value: str) -> bool:
        """Check if a value is numeric"""
        try:
            float(str(value).replace(',', '').replace('$', ''))
            return True
        except (ValueError, TypeError):
            return False

    def _analyze_json_structure(self, obj: Any, max_depth: int = 3) -> Dict[str, Any]:
        """Analyze the structure of a JSON object"""
        if max_depth <= 0:
            return {'type': type(obj).__name__, 'max_depth_reached': True}

        if isinstance(obj, dict):
            return {
                'type': 'object',
                'keys': list(obj.keys()),
                'key_count': len(obj),
                'nested_structure': {
                    key: self._analyze_json_structure(value, max_depth - 1)
                    for key, value in list(obj.items())[:5]  # Limit to first 5 keys
                }
            }
        elif isinstance(obj, list):
            return {
                'type': 'array',
                'length': len(obj),
                'item_types': list(set(type(item).__name__ for item in obj[:10])),
                'sample_items': obj[:3]
            }
        else:
            return {
                'type': type(obj).__name__,
                'value': str(obj)[:100] if obj else None,
                'length': len(str(obj)) if obj else 0
            }

    def _assess_data_quality(self, rows: List[Dict], headers: List[str]) -> Dict[str, Any]:
        """Assess data quality of CSV data"""
        quality_metrics = {
            'completeness': {},
            'consistency': {},
            'overall_score': 0
        }

        total_cells = len(rows) * len(headers)
        null_cells = 0

        # Completeness analysis
        for header in headers:
            non_null_count = sum(1 for row in rows if row.get(header))
            completeness = non_null_count / len(rows) if rows else 0
            quality_metrics['completeness'][header] = completeness
            null_cells += len(rows) - non_null_count

        # Overall completeness
        quality_metrics['overall_completeness'] = (total_cells - null_cells) / total_cells if total_cells > 0 else 0

        # Consistency analysis (for numeric columns)
        numeric_columns = []
        for header in headers:
            column_data = [row.get(header) for row in rows if row.get(header)]
            if column_data and self._detect_column_type(column_data) == 'numeric':
                numeric_columns.append(header)

        quality_metrics['numeric_columns'] = numeric_columns
        quality_metrics['consistency_score'] = len(numeric_columns) / len(headers) if headers else 0

        # Overall quality score
        quality_metrics['overall_score'] = (quality_metrics['overall_completeness'] + quality_metrics['consistency_score']) / 2

        return quality_metrics

    def _add_to_cache(self, key: str, value: Dict[str, Any]):
        """Add result to cache with size management"""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = value.copy()

# Test the skill
if __name__ == "__main__":
    skill = DataInspectorSkill()
    
    # Create a sample CSV file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age,city,salary\n")
        f.write("John,25,New York,50000\n")
        f.write("Jane,30,London,60000\n")
        f.write("Bob,35,Paris,70000\n")
        sample_file = f.name

    try:
        # Test the skill
        result = skill.execute({
            "file_path": sample_file,
            "analysis_depth": "detailed"
        })
        
        print(f"Analysis successful: {result.success}")
        print(f"Output: {result.output}")
        if result.data:
            print(f"File type: {result.data.get('file_type', 'N/A')}")
            print(f"Total rows: {result.data.get('total_rows', 0)}")
            print(f"Total columns: {result.data.get('total_columns', 0)}")
    finally:
        # Clean up
        os.unlink(sample_file)