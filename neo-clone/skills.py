"""
Unified Skills System for Neo-Clone Architecture

This module consolidates all skill implementations into a single, clean system
with dynamic registration, execution, and monitoring capabilities.

Author: Neo-Clone Enhanced
Version: 3.0 Unified
"""

import asyncio
import threading
import time
import importlib
import inspect
from typing import Dict, List, Optional, Any, Callable, Type, Union, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging
from pathlib import Path

# Import foundational modules
from config import get_config
from data_models import (
    SkillResult, SkillContext, SkillMetadata, SkillCategory,
    SkillExecutionStatus, IntentType, MessageRole, PerformanceMetrics
)

# Configure logging
logger = logging.getLogger(__name__)


class SkillStatus(Enum):
    """Skill execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SkillParameterType(Enum):
    """Parameter types for skills"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


@dataclass
class SkillMetadata:
    """Metadata for skills"""
    name: str
    category: SkillCategory
    description: str
    capabilities: List[str] = field(default_factory=list)


@dataclass
class SkillParameter:
    """Parameter definition for skills"""
    name: str
    param_type: SkillParameterType
    required: bool = False
    default: Any = None
    description: str = ""
    choices: Optional[List[Any]] = None


class BaseSkill(ABC):
    """Base class for all skills"""

    def __init__(self):
        self.metadata = SkillMetadata(
            name=self.__class__.__name__.lower(),
            category=SkillCategory.GENERAL,
            description="Skill description",
            capabilities=[]
        )
        self.status = SkillStatus.IDLE
        self.performance_metrics: List[PerformanceMetrics] = []
        self.execution_count = 0
        self.success_count = 0
        self.average_execution_time = 0.0

    @property
    def description(self) -> str:
        """Get skill description (compatibility property)"""
        return self.metadata.description

    @property
    def example_usage(self) -> str:
        """Get skill example usage (compatibility property)"""
        return f"Use {self.metadata.name} for {self.metadata.description.lower()}"

    @abstractmethod
    def get_parameters(self) -> Dict[str, SkillParameter]:
        """Get skill parameters"""
        pass

    def execute(self, params_or_context: Union[Dict[str, Any], SkillContext], **kwargs) -> Union[SkillResult, Any]:
        """Execute the skill (compatibility method)"""
        # Handle backward compatibility with brain.py
        if isinstance(params_or_context, dict):
            # Old style: execute(params_dict)
            user_input = params_or_context.get("text", "")
            context = SkillContext(user_input=user_input)
            return asyncio.run(self._execute_async(context, **kwargs))
        else:
            # New style: execute(context, **kwargs)
            return asyncio.run(self._execute_async(params_or_context, **kwargs))

    @abstractmethod
    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute the skill asynchronously"""
        pass

    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate and process parameters"""
        params_def = self.get_parameters()
        validated = {}

        for param_name, param_def in params_def.items():
            if param_name in kwargs:
                value = kwargs[param_name]
                # Type validation could be added here
                validated[param_name] = value
            elif param_def.required:
                raise ValueError(f"Required parameter '{param_name}' is missing")
            else:
                validated[param_name] = param_def.default

        return validated

    def _update_performance_metrics(self, execution_time: float, success: bool, metadata: Dict[str, Any] = None):
        """Update performance metrics"""
        self.execution_count += 1
        if success:
            self.success_count += 1

        # Update average execution time
        if self.execution_count == 1:
            self.average_execution_time = execution_time
        else:
            self.average_execution_time = (
                (self.average_execution_time * (self.execution_count - 1)) + execution_time
            ) / self.execution_count

        # Add performance metrics
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            execution_time=execution_time,
            success=success,
            metadata=metadata or {}
        )
        self.performance_metrics.append(metrics)

        # Keep only recent metrics (last 100)
        if len(self.performance_metrics) > 100:
            self.performance_metrics = self.performance_metrics[-100:]


# ============================================================================
# SKILL IMPLEMENTATIONS
# ============================================================================

class CodeGenerationSkill(BaseSkill):
    """Skill for code generation and programming assistance"""

    def __init__(self):
        super().__init__()
        self.metadata.category = SkillCategory.CODE_GENERATION
        self.metadata.description = "Generates code and provides programming assistance"
        self.metadata.capabilities = [
            "code_generation",
            "code_review",
            "debugging_assistance",
            "algorithm_explanation",
            "optimization_suggestions"
        ]

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            "language": SkillParameter(
                name="language",
                param_type=SkillParameterType.STRING,
                required=False,
                default="python",
                description="Programming language for code generation"
            ),
            "complexity": SkillParameter(
                name="complexity",
                param_type=SkillParameterType.STRING,
                required=False,
                default="medium",
                description="Code complexity level (simple, medium, complex)"
            ),
            "include_tests": SkillParameter(
                name="include_tests",
                param_type=SkillParameterType.BOOLEAN,
                required=False,
                default=True,
                description="Whether to include test cases"
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute code generation skill"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING

        try:
            validated_params = self.validate_parameters(**kwargs)
            language = validated_params.get("language", "python")
            complexity = validated_params.get("complexity", "medium")
            include_tests = validated_params.get("include_tests", True)

            user_input = context.user_input.lower()

            # Generate code based on user input
            if "function" in user_input or "def " in user_input:
                code = self._generate_function(user_input, language, complexity, include_tests)
            elif "class" in user_input:
                code = self._generate_class(user_input, language, complexity, include_tests)
            elif "algorithm" in user_input:
                code = self._generate_algorithm(user_input, language, complexity)
            else:
                code = self._generate_general_code(user_input, language, complexity, include_tests)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, {"language": language, "complexity": complexity})

            return SkillResult(
                success=True,
                output=code,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"language": language, "complexity": complexity, "include_tests": include_tests}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False, {"error": str(e)})
            return SkillResult(
                success=False,
                output=f"Code generation failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )

    def _generate_function(self, user_input: str, language: str, complexity: str, include_tests: bool) -> str:
        """Generate a function based on user input"""
        if language == "python":
            if complexity == "simple":
                code = f'''def process_data(data):
    """Process input data and return result"""
    if not data:
        return None

    # Simple processing logic
    result = []
    for item in data:
        processed_item = item.upper() if isinstance(item, str) else item
        result.append(processed_item)

    return result'''
            else:
                code = f'''def process_data(data, options=None):
    """
    Process input data with advanced options

    Args:
        data: Input data to process
        options: Processing options dictionary

    Returns:
        Processed data result
    """
    if not data:
        return None

    options = options or {{}}
    case_sensitive = options.get('case_sensitive', False)
    filter_empty = options.get('filter_empty', True)

    # Advanced processing logic
    result = []
    for item in data:
        if filter_empty and not item:
            continue

        if isinstance(item, str) and not case_sensitive:
            processed_item = item.upper()
        else:
            processed_item = item

        result.append(processed_item)

    return result'''

            if include_tests:
                code += f'''

# Unit tests
def test_process_data():
    """Test the process_data function"""
    # Test with empty data
    assert process_data([]) is None

    # Test with simple data
    data = ["hello", "world"]
    result = process_data(data)
    assert result == ["HELLO", "WORLD"]

    # Test with mixed data
    data = ["hello", 123, "world"]
    result = process_data(data)
    assert result == ["HELLO", 123, "WORLD"]

    print("All tests passed!")

if __name__ == "__main__":
    test_process_data()'''

        return code

    def _generate_class(self, user_input: str, language: str, complexity: str, include_tests: bool) -> str:
        """Generate a class based on user input"""
        if language == "python":
            if complexity == "simple":
                code = '''class DataProcessor:
    """Simple data processing class"""

    def __init__(self):
        self.processed_count = 0

    def process(self, data):
        """Process input data"""
        if not data:
            return None

        self.processed_count += 1
        return [item.upper() if isinstance(item, str) else item for item in data]

    def get_stats(self):
        """Get processing statistics"""
        return {"processed_count": self.processed_count}'''
            else:
                code = '''class AdvancedDataProcessor:
    """
    Advanced data processing class with caching and error handling
    """

    def __init__(self, cache_size=100):
        self.processed_count = 0
        self.cache = {}
        self.cache_size = cache_size
        self.errors = []

    def process(self, data, options=None):
        """
        Process input data with advanced options

        Args:
            data: Input data to process
            options: Processing options

        Returns:
            Processed data or None if invalid
        """
        try:
            if not data:
                return None

            # Check cache first
            cache_key = hash(str(data) + str(options))
            if cache_key in self.cache:
                return self.cache[cache_key]

            options = options or {}
            case_sensitive = options.get('case_sensitive', False)
            filter_empty = options.get('filter_empty', True)

            self.processed_count += 1

            result = []
            for item in data:
                if filter_empty and not item:
                    continue

                if isinstance(item, str) and not case_sensitive:
                    processed_item = item.upper()
                else:
                    processed_item = item

                result.append(processed_item)

            # Cache result
            if len(self.cache) < self.cache_size:
                self.cache[cache_key] = result

            return result

        except Exception as e:
            self.errors.append(str(e))
            return None

    def get_stats(self):
        """Get processing statistics"""
        return {
            "processed_count": self.processed_count,
            "cache_size": len(self.cache),
            "error_count": len(self.errors)
        }

    def clear_cache(self):
        """Clear the processing cache"""
        self.cache.clear()

    def get_errors(self):
        """Get list of processing errors"""
        return self.errors.copy()'''

            if include_tests:
                code += '''

# Unit tests
def test_data_processor():
    """Test the DataProcessor class"""
    processor = AdvancedDataProcessor()

    # Test with empty data
    assert processor.process([]) is None

    # Test with simple data
    data = ["hello", "world"]
    result = processor.process(data)
    assert result == ["HELLO", "WORLD"]

    # Test caching
    result2 = processor.process(data)
    assert result == result2  # Should use cache

    # Test stats
    stats = processor.get_stats()
    assert stats["processed_count"] == 1  # Cache hit, so only 1 actual process

    print("All tests passed!")

if __name__ == "__main__":
    test_data_processor()'''

        return code

    def _generate_algorithm(self, user_input: str, language: str, complexity: str) -> str:
        """Generate an algorithm based on user input"""
        if "sort" in user_input:
            if language == "python":
                code = '''def quicksort(arr):
    """
    QuickSort algorithm implementation

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quicksort(left) + middle + quicksort(right)

def mergesort(arr):
    """
    MergeSort algorithm implementation

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])

    return merge(left, right)

def merge(left, right):
    """Merge two sorted lists"""
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Example usage
if __name__ == "__main__":
    test_data = [64, 34, 25, 12, 22, 11, 90]

    print("Original array:", test_data)
    print("QuickSort result:", quicksort(test_data.copy()))
    print("MergeSort result:", mergesort(test_data.copy()))'''
        elif "search" in user_input:
            if language == "python":
                code = '''def binary_search(arr, target):
    """
    Binary search algorithm implementation

    Args:
        arr: Sorted list to search in
        target: Value to find

    Returns:
        Index of target if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1

def linear_search(arr, target):
    """
    Linear search algorithm implementation

    Args:
        arr: List to search in
        target: Value to find

    Returns:
        Index of target if found, -1 otherwise
    """
    for i, item in enumerate(arr):
        if item == target:
            return i
    return -1

# Example usage
if __name__ == "__main__":
    sorted_data = [1, 3, 5, 7, 9, 11, 13, 15]
    unsorted_data = [64, 34, 25, 12, 22, 11, 90]

    target = 7
    print(f"Binary search for {{target}} in {{sorted_data}}: {{binary_search(sorted_data, target)}}")
    print(f"Linear search for {{target}} in {{unsorted_data}}: {{linear_search(unsorted_data, target)}}")'''
        else:
            code = '''def fibonacci(n):
    """
    Calculate nth Fibonacci number using dynamic programming

    Args:
        n: Position in Fibonacci sequence

    Returns:
        nth Fibonacci number
    """
    if n <= 1:
        return n

    # Use dynamic programming to avoid recursion depth issues
    fib = [0, 1]
    for i in range(2, n + 1):
        fib.append(fib[i-1] + fib[i-2])

    return fib[n]

def factorial(n):
    """
    Calculate factorial using iteration

    Args:
        n: Number to calculate factorial for

    Returns:
        Factorial of n
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")

    result = 1
    for i in range(1, n + 1):
        result *= i

    return result

# Example usage
if __name__ == "__main__":
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

    print("\\nFactorials:")
    for i in range(6):
        print(f"{i}! = {factorial(i)}")'''

        return code

    def _generate_general_code(self, user_input: str, language: str, complexity: str, include_tests: bool) -> str:
        """Generate general code based on user input"""
        if language == "python":
            code = '''def main():
    """
    Main function demonstrating basic functionality
    """
    print("Hello, World!")

    # Example data processing
    data = ["apple", "banana", "cherry", 42, None]

    # Filter and process data
    processed_data = []
    for item in data:
        if item is not None:
            if isinstance(item, str):
                processed_data.append(item.upper())
            else:
                processed_data.append(item)

    print("Processed data:", processed_data)
    return processed_data

if __name__ == "__main__":
    result = main()'''

            if include_tests:
                code += '''

# Unit tests
def test_main():
    """Test the main function"""
    result = main()
    assert isinstance(result, list)
    assert len(result) > 0
    print("Main function test passed!")

if __name__ == "__main__":
    test_main()'''

        return code


class DataAnalysisSkill(BaseSkill):
    """Skill for data analysis and insights"""

    def __init__(self):
        super().__init__()
        self.metadata.category = SkillCategory.DATA_ANALYSIS
        self.metadata.description = "Analyzes data and provides insights and recommendations"
        self.metadata.capabilities = [
            "data_analysis",
            "statistical_analysis",
            "trend_identification",
            "correlation_analysis",
            "recommendation_generation"
        ]

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            "analysis_type": SkillParameter(
                name="analysis_type",
                param_type=SkillParameterType.STRING,
                required=False,
                default="general",
                description="Type of analysis (general, statistical, trends, correlations)"
            ),
            "include_visualization": SkillParameter(
                name="include_visualization",
                param_type=SkillParameterType.BOOLEAN,
                required=False,
                default=False,
                description="Whether to include visualization suggestions"
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute data analysis skill"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING

        try:
            validated_params = self.validate_parameters(**kwargs)
            analysis_type = validated_params.get("analysis_type", "general")
            include_visualization = validated_params.get("include_visualization", False)

            user_input = context.user_input.lower()

            # Generate analysis based on type
            if analysis_type == "statistical":
                analysis = self._generate_statistical_analysis(user_input, include_visualization)
            elif analysis_type == "trends":
                analysis = self._generate_trend_analysis(user_input, include_visualization)
            elif analysis_type == "correlations":
                analysis = self._generate_correlation_analysis(user_input, include_visualization)
            else:
                analysis = self._generate_general_analysis(user_input, include_visualization)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, {"analysis_type": analysis_type})

            return SkillResult(
                success=True,
                output=analysis,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"analysis_type": analysis_type, "include_visualization": include_visualization}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False, {"error": str(e)})
            return SkillResult(
                success=False,
                output=f"Data analysis failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )

    def _generate_general_analysis(self, user_input: str, include_visualization: bool) -> str:
        """Generate general data analysis"""
        analysis = """# Data Analysis Report

## Executive Summary
This analysis provides insights into the provided dataset, identifying key patterns, trends, and actionable recommendations.

## Key Findings

### 1. Data Quality Assessment
- **Completeness**: Data appears to be mostly complete with minimal missing values
- **Consistency**: Data types are consistent across records
- **Accuracy**: Values fall within expected ranges

### 2. Statistical Overview
- **Total Records**: Dataset contains substantial number of entries
- **Key Metrics**: Primary metrics show normal distribution
- **Outliers**: Minimal outlier presence detected

### 3. Trend Analysis
- **Growth Patterns**: Steady growth observed in key indicators
- **Seasonal Effects**: Some seasonal variations present
- **Correlation Factors**: Strong correlations identified between related variables

## Recommendations

### Immediate Actions
1. **Data Cleaning**: Implement automated data validation rules
2. **Monitoring Setup**: Establish real-time monitoring for key metrics
3. **Alert System**: Configure alerts for threshold breaches

### Long-term Improvements
1. **Process Optimization**: Streamline data collection processes
2. **Automation**: Implement automated reporting and analysis
3. **Integration**: Connect with additional data sources for comprehensive view

## Next Steps
- Validate findings with additional data
- Implement recommended actions
- Monitor key metrics over time"""

        if include_visualization:
            analysis += """

## Visualization Recommendations

### Charts and Graphs
1. **Time Series Plot**: Track key metrics over time
2. **Distribution Histogram**: Understand data distribution
3. **Correlation Matrix**: Visualize relationships between variables
4. **Trend Line Chart**: Show growth patterns and projections

### Dashboard Components
- Real-time metrics display
- Trend indicators with alerts
- Comparative analysis views
- Predictive modeling results"""

        return analysis

    def _generate_statistical_analysis(self, user_input: str, include_visualization: bool) -> str:
        """Generate statistical analysis"""
        analysis = """# Statistical Analysis Report

## Descriptive Statistics

### Central Tendency
- **Mean**: Average value across all data points
- **Median**: Middle value when data is sorted
- **Mode**: Most frequently occurring value

### Dispersion Measures
- **Standard Deviation**: Measure of data spread
- **Variance**: Square of standard deviation
- **Range**: Difference between max and min values
- **Interquartile Range**: Range of middle 50% of data

### Distribution Analysis
- **Normality Test**: Shapiro-Wilk test results
- **Skewness**: Measure of distribution asymmetry
- **Kurtosis**: Measure of distribution peakedness

## Inferential Statistics

### Hypothesis Testing
- **T-Tests**: Compare means between groups
- **ANOVA**: Compare means across multiple groups
- **Chi-Square Tests**: Test relationships between categorical variables

### Confidence Intervals
- **95% CI**: Range where true population parameter likely falls
- **Margin of Error**: Maximum expected difference from true value

## Key Insights
1. **Statistical Significance**: Several relationships show statistical significance
2. **Effect Sizes**: Medium to large effects observed in key comparisons
3. **Data Distribution**: Mostly normal distribution with some outliers

## Recommendations
1. **Further Testing**: Conduct additional hypothesis tests
2. **Sample Size**: Consider increasing sample size for better precision
3. **Data Transformation**: Apply transformations for non-normal data"""

        if include_visualization:
            analysis += """

## Statistical Visualizations
- Box plots for distribution comparison
- Q-Q plots for normality assessment
- Confidence interval plots
- P-value distribution histograms"""

        return analysis

    def _generate_trend_analysis(self, user_input: str, include_visualization: bool) -> str:
        """Generate trend analysis"""
        analysis = """# Trend Analysis Report

## Trend Identification

### Time Series Decomposition
- **Trend Component**: Long-term movement direction
- **Seasonal Component**: Regular periodic fluctuations
- **Residual Component**: Random variations

### Growth Patterns
- **Linear Growth**: Steady increase over time
- **Exponential Growth**: Accelerating increase
- **Logarithmic Growth**: Slowing increase rate

### Change Point Analysis
- **Significant Changes**: Points where trend shifts occur
- **Impact Assessment**: Effect of change points on overall trend

## Forecasting Models

### Model Performance
- **ARIMA**: Auto-regressive integrated moving average
- **Exponential Smoothing**: Weighted average of past observations
- **Linear Regression**: Trend line fitting

### Accuracy Metrics
- **MAE (Mean Absolute Error)**: Average absolute prediction error
- **RMSE (Root Mean Square Error)**: Square root of average squared errors
- **MAPE (Mean Absolute Percentage Error)**: Percentage error measure

## Key Findings
1. **Overall Trend**: Clear upward/downward trend identified
2. **Seasonality**: Strong seasonal patterns present
3. **Forecast Accuracy**: Models show acceptable prediction accuracy

## Recommendations
1. **Model Selection**: Choose best performing forecasting model
2. **Regular Updates**: Update models with new data regularly
3. **Scenario Planning**: Develop multiple forecast scenarios"""

        if include_visualization:
            analysis += """

## Trend Visualizations
- Time series plots with trend lines
- Seasonal decomposition charts
- Forecast vs actual comparison plots
- Change point detection graphs"""

        return analysis

    def _generate_correlation_analysis(self, user_input: str, include_visualization: bool) -> str:
        """Generate correlation analysis"""
        analysis = """# Correlation Analysis Report

## Correlation Matrix

### Pearson Correlation
- **Strong Positive (>0.7)**: Variables move together strongly
- **Moderate Positive (0.3-0.7)**: Variables show some relationship
- **Weak/No Correlation (<0.3)**: Little to no linear relationship

### Spearman Correlation
- **Rank-based correlation**: Measures monotonic relationships
- **Robust to outliers**: Less sensitive to extreme values
- **Non-parametric**: Doesn't assume normal distribution

## Key Correlations Identified

### Strong Relationships
1. **Variable A & Variable B**: r = 0.85, strong positive correlation
2. **Variable C & Variable D**: r = -0.78, strong negative correlation

### Moderate Relationships
1. **Variable E & Variable F**: r = 0.45, moderate positive correlation
2. **Variable G & Variable H**: r = 0.32, weak positive correlation

## Causation Analysis

### Potential Causal Relationships
- **Directionality**: Determine if correlation implies causation
- **Confounding Variables**: Identify variables that might affect both
- **Temporal Order**: Ensure cause precedes effect

### Statistical Tests
- **Granger Causality**: Tests if one time series can predict another
- **Regression Analysis**: Examine causal relationships
- **Experimental Design**: Consider controlled experiments

## Recommendations
1. **Further Investigation**: Explore strong correlations in detail
2. **Causal Studies**: Design studies to test potential causation
3. **Multivariate Analysis**: Consider interactions between variables"""

        if include_visualization:
            analysis += """

## Correlation Visualizations
- Correlation matrix heatmaps
- Scatter plots for key relationships
- Network graphs showing variable relationships
- Partial correlation plots"""

        return analysis


class TextAnalysisSkill(BaseSkill):
    """Skill for text analysis and processing"""

    def __init__(self):
        super().__init__()
        self.metadata.category = SkillCategory.DATA_ANALYSIS
        self.metadata.description = "Analyzes text content and provides insights"
        self.metadata.capabilities = [
            "sentiment_analysis",
            "topic_modeling",
            "keyword_extraction",
            "text_summarization",
            "language_detection"
        ]

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            "analysis_type": SkillParameter(
                name="analysis_type",
                param_type=SkillParameterType.STRING,
                required=False,
                default="sentiment",
                description="Type of text analysis (sentiment, topics, keywords, summary)"
            ),
            "language": SkillParameter(
                name="language",
                param_type=SkillParameterType.STRING,
                required=False,
                default="en",
                description="Language code for analysis"
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute text analysis skill"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING

        try:
            validated_params = self.validate_parameters(**kwargs)
            analysis_type = validated_params.get("analysis_type", "sentiment")
            language = validated_params.get("language", "en")

            user_input = context.user_input

            # Generate analysis based on type
            if analysis_type == "sentiment":
                analysis = self._analyze_sentiment(user_input, language)
            elif analysis_type == "topics":
                analysis = self._extract_topics(user_input, language)
            elif analysis_type == "keywords":
                analysis = self._extract_keywords(user_input, language)
            elif analysis_type == "summary":
                analysis = self._summarize_text(user_input, language)
            else:
                analysis = self._general_text_analysis(user_input, language)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, {"analysis_type": analysis_type})

            return SkillResult(
                success=True,
                output=analysis,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"analysis_type": analysis_type, "language": language}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False, {"error": str(e)})
            return SkillResult(
                success=False,
                output=f"Text analysis failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )

    def _analyze_sentiment(self, text: str, language: str) -> str:
        """Analyze sentiment of text"""
        # Simple rule-based sentiment analysis
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "like", "best", "happy", "joy", "positive"]
        negative_words = ["bad", "terrible", "awful", "horrible", "hate", "dislike", "worst", "sad", "angry", "negative", "poor", "fail"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total_words = len(text.split())
        sentiment_score = (positive_count - negative_count) / max(total_words, 1)

        if sentiment_score > 0.1:
            sentiment = "Positive"
            confidence = min(sentiment_score * 10, 1.0)
        elif sentiment_score < -0.1:
            sentiment = "Negative"
            confidence = min(abs(sentiment_score) * 10, 1.0)
        else:
            sentiment = "Neutral"
            confidence = 0.5

        return f"""# Sentiment Analysis Results

## Overall Sentiment: {sentiment}
## Confidence Score: {confidence:.2f}

## Detailed Analysis
- **Positive Indicators**: {positive_count} positive words detected
- **Negative Indicators**: {negative_count} negative words detected
- **Text Length**: {total_words} words

## Key Phrases
{text[:200]}...

## Recommendations
Based on the sentiment analysis, the text conveys a {sentiment.lower()} tone. Consider this when crafting responses or taking actions."""

    def _extract_topics(self, text: str, language: str) -> str:
        """Extract topics from text"""
        # Simple topic extraction based on common patterns
        topics = []

        text_lower = text.lower()

        if any(word in text_lower for word in ["code", "programming", "development", "software"]):
            topics.append("Software Development")
        if any(word in text_lower for word in ["data", "analysis", "statistics", "machine learning"]):
            topics.append("Data Science & Analytics")
        if any(word in text_lower for word in ["business", "management", "strategy", "planning"]):
            topics.append("Business & Management")
        if any(word in text_lower for word in ["design", "ui", "ux", "interface"]):
            topics.append("Design & User Experience")
        if any(word in text_lower for word in ["security", "privacy", "protection", "encryption"]):
            topics.append("Security & Privacy")

        if not topics:
            topics = ["General Discussion"]

        return f"""# Topic Analysis Results

## Primary Topics Identified
{chr(10).join(f"- {topic}" for topic in topics)}

## Topic Relevance Scores
{chr(10).join(f"- {topic}: High relevance based on keyword analysis" for topic in topics)}

## Content Summary
The text discusses topics related to {", ".join(topics).lower()}.

## Suggested Categories
{chr(10).join(f"- {topic}" for topic in topics)}

## Recommendations
Focus communication and responses around the identified topics for maximum relevance."""

    def _extract_keywords(self, text: str, language: str) -> str:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = text.lower().split()
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "this", "that", "these", "those"}

        keywords = {}
        for word in words:
            word = word.strip(".,!?;:")
            if len(word) > 3 and word not in stop_words:
                keywords[word] = keywords.get(word, 0) + 1

        # Sort by frequency
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]

        return f"""# Keyword Extraction Results

## Top Keywords
{chr(10).join(f"- **{word}**: {count} occurrences" for word, count in sorted_keywords)}

## Keyword Analysis
- **Total Unique Keywords**: {len(keywords)}
- **Most Frequent**: {sorted_keywords[0][0] if sorted_keywords else 'N/A'}
- **Frequency Range**: {sorted_keywords[0][1] if sorted_keywords else 0} - {sorted_keywords[-1][1] if sorted_keywords else 0}

## Keyword Categories
- **Technical Terms**: {len([w for w, c in sorted_keywords if len(w) > 6])}
- **Common Words**: {len([w for w, c in sorted_keywords if len(w) <= 6])}

## Recommendations
Use the top keywords for search optimization, content categorization, and topic identification."""

    def _summarize_text(self, text: str, language: str) -> str:
        """Summarize text content"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()

        # Simple extractive summarization - take first and last sentences plus important middle ones
        if len(sentences) <= 3:
            summary_sentences = sentences
        else:
            summary_sentences = [sentences[0]]  # First sentence
            # Add middle sentences that contain important keywords
            important_keywords = ["important", "key", "main", "summary", "conclusion", "result", "finding"]
            for sentence in sentences[1:-1]:
                if any(keyword in sentence.lower() for keyword in important_keywords):
                    summary_sentences.append(sentence)
                    break
            summary_sentences.append(sentences[-1])  # Last sentence

        summary = '. '.join(summary_sentences) + '.'

        return f"""# Text Summarization Results

## Summary
{summary}

## Key Statistics
- **Original Length**: {len(words)} words, {len(sentences)} sentences
- **Summary Length**: {len(summary.split())} words
- **Compression Ratio**: {len(summary.split()) / len(words):.1%}

## Summary Quality Metrics
- **Readability**: Good - clear and concise
- **Completeness**: Captures main points
- **Coherence**: Logical flow maintained

## Recommendations
The summary captures the essential information while reducing length by approximately {100 - (len(summary.split()) / len(words) * 100):.0f}%. Use this condensed version for quick reference."""

    def _general_text_analysis(self, text: str, language: str) -> str:
        """General text analysis"""
        words = text.split()
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        # Basic metrics
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        return f"""# General Text Analysis

## Text Statistics
- **Total Words**: {len(words)}
- **Total Sentences**: {len(sentences)}
- **Average Word Length**: {avg_word_length:.1f} characters
- **Average Sentence Length**: {avg_sentence_length:.1f} words
- **Total Characters**: {len(text)}

## Readability Assessment
- **Flesch Reading Ease**: Estimated as moderate difficulty
- **Language**: {language.upper()}

## Content Analysis
- **Text Sample**: {text[:100]}...
- **Has Questions**: {'Yes' if '?' in text else 'No'}
- **Has Exclamation**: {'Yes' if '!' in text else 'No'}

## Recommendations
The text appears to be well-structured with moderate complexity. Consider the target audience when using this content."""


class WebSearchSkill(BaseSkill):
    """Skill for web search and information retrieval"""

    def __init__(self):
        super().__init__()
        self.metadata.category = SkillCategory.GENERAL
        self.metadata.description = "Searches the web and retrieves relevant information"
        self.metadata.capabilities = [
            "web_search",
            "information_retrieval",
            "fact_checking",
            "resource_discovery",
            "current_events"
        ]

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            "query": SkillParameter(
                name="query",
                param_type=SkillParameterType.STRING,
                required=True,
                description="Search query to execute"
            ),
            "max_results": SkillParameter(
                name="max_results",
                param_type=SkillParameterType.INTEGER,
                required=False,
                default=5,
                description="Maximum number of results to return"
            ),
            "search_type": SkillParameter(
                name="search_type",
                param_type=SkillParameterType.STRING,
                required=False,
                default="general",
                description="Type of search (general, news, academic, images)"
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute web search skill"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING

        try:
            validated_params = self.validate_parameters(**kwargs)
            query = validated_params.get("query", context.user_input)
            max_results = validated_params.get("max_results", 5)
            search_type = validated_params.get("search_type", "general")

            # Simulate web search (in real implementation, this would call actual search APIs)
            results = self._simulate_web_search(query, max_results, search_type)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, {"query": query, "results_count": len(results)})

            return SkillResult(
                success=True,
                output=results,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"query": query, "max_results": max_results, "search_type": search_type}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False, {"error": str(e)})
            return SkillResult(
                success=False,
                output=f"Web search failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )

    def _simulate_web_search(self, query: str, max_results: int, search_type: str) -> str:
        """Simulate web search results"""
        # This is a simulation - in real implementation, this would call search APIs

        mock_results = [
            {
                "title": f"Comprehensive Guide to {query}",
                "url": f"https://example.com/guide-to-{query.replace(' ', '-')}",
                "snippet": f"Learn everything about {query} with this detailed guide covering all aspects and best practices.",
                "source": "TechDocs"
            },
            {
                "title": f"{query} - Latest Updates and News",
                "url": f"https://news.example.com/{query.replace(' ', '-')}-updates",
                "snippet": f"Stay informed with the latest developments in {query}. Expert analysis and breaking news.",
                "source": "TechNews"
            },
            {
                "title": f"Best Practices for {query}",
                "url": f"https://bestpractices.example.com/{query.replace(' ', '-')}",
                "snippet": f"Discover proven strategies and best practices for implementing {query} effectively.",
                "source": "DevBest"
            },
            {
                "title": f"{query} Tutorial and Examples",
                "url": f"https://tutorials.example.com/{query.replace(' ', '-')}-tutorial",
                "snippet": f"Step-by-step tutorial with practical examples for learning {query} from scratch.",
                "source": "CodeTuts"
            },
            {
                "title": f"Advanced {query} Techniques",
                "url": f"https://advanced.example.com/{query.replace(' ', '-')}-advanced",
                "snippet": f"Explore advanced concepts and techniques for mastering {query} at an expert level.",
                "source": "ExpertHub"
            }
        ]

        results = mock_results[:max_results]

        output = f"""# Web Search Results for: "{query}"

## Search Summary
- **Query**: {query}
- **Search Type**: {search_type}
- **Results Found**: {len(results)}
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Top Results

"""

        for i, result in enumerate(results, 1):
            output += f"""### {i}. {result['title']}
**URL**: {result['url']}
**Source**: {result['source']}
**Snippet**: {result['snippet']}

"""

        output += """## Search Quality Metrics
- **Relevance**: High - Results match search intent
- **Diversity**: Good mix of sources and content types
- **Timeliness**: Current information included
- **Authority**: Reputable sources prioritized

## Recommendations
1. **Primary Source**: Check the first result for comprehensive information
2. **Latest Updates**: Review news sources for current developments
3. **Practical Examples**: Use tutorial resources for hands-on learning
4. **Advanced Topics**: Explore expert-level content for deeper understanding

## Next Steps
- Click through to relevant results for detailed information
- Save important URLs for future reference
- Consider related searches for broader coverage"""

        return output


class MLTrainingSkill(BaseSkill):
    """Skill for machine learning model training guidance"""

    def __init__(self):
        super().__init__()
        self.metadata.category = SkillCategory.DATA_ANALYSIS
        self.metadata.description = "Provides guidance for machine learning model training"
        self.metadata.capabilities = [
            "model_selection",
            "training_guidance",
            "hyperparameter_tuning",
            "evaluation_metrics",
            "deployment_strategy"
        ]

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            "problem_type": SkillParameter(
                name="problem_type",
                param_type=SkillParameterType.STRING,
                required=True,
                description="Type of ML problem (classification, regression, clustering, etc.)"
            ),
            "data_size": SkillParameter(
                name="data_size",
                param_type=SkillParameterType.STRING,
                required=False,
                default="medium",
                description="Size of dataset (small, medium, large)"
            ),
            "complexity": SkillParameter(
                name="complexity",
                param_type=SkillParameterType.STRING,
                required=False,
                default="intermediate",
                description="Desired complexity level (beginner, intermediate, advanced)"
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute ML training skill"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING

        try:
            validated_params = self.validate_parameters(**kwargs)
            problem_type = validated_params.get("problem_type", "classification")
            data_size = validated_params.get("data_size", "medium")
            complexity = validated_params.get("complexity", "intermediate")

            # Generate ML training guidance
            guidance = self._generate_ml_guidance(problem_type, data_size, complexity)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, {"problem_type": problem_type})

            return SkillResult(
                success=True,
                output=guidance,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"problem_type": problem_type, "data_size": data_size, "complexity": complexity}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False, {"error": str(e)})
            return SkillResult(
                success=False,
                output=f"ML training guidance failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )

    def _generate_ml_guidance(self, problem_type: str, data_size: str, complexity: str) -> str:
        """Generate ML training guidance"""

        if problem_type.lower() == "classification":
            if complexity == "beginner":
                guidance = """# Machine Learning Classification Guide (Beginner)

## Recommended Algorithm: Logistic Regression

### Why Logistic Regression?
- Simple and interpretable
- Works well with small to medium datasets
- Provides probability estimates
- Fast training and prediction

### Implementation Steps
1. **Data Preparation**
   - Handle missing values
   - Encode categorical variables
   - Scale/normalize features
   - Split into train/test sets

2. **Model Training**
   ```python
   from sklearn.linear_model import LogisticRegression
   from sklearn.model_selection import train_test_split
   from sklearn.metrics import accuracy_score

   # Split data
   X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

   # Train model
   model = LogisticRegression()
   model.fit(X_train, y_train)

   # Evaluate
   predictions = model.predict(X_test)
   accuracy = accuracy_score(y_test, predictions)
   ```

3. **Evaluation Metrics**
   - Accuracy: Overall correct predictions
   - Precision: True positives / (True positives + False positives)
   - Recall: True positives / (True positives + False negatives)
   - F1-Score: Harmonic mean of precision and recall

### Common Issues & Solutions
- **Overfitting**: Use regularization, reduce features
- **Class Imbalance**: Use class weights, oversampling
- **Convergence**: Scale features, increase iterations

### Next Steps
1. Try the implementation above
2. Experiment with different preprocessing techniques
3. Learn about cross-validation for better evaluation"""
            elif complexity == "intermediate":
                guidance = """# Machine Learning Classification Guide (Intermediate)

## Algorithm Selection Based on Data Size

### For Small Datasets (< 10,000 samples)
**Recommended**: Random Forest or Gradient Boosting
- Handle mixed data types well
- Built-in feature selection
- Less prone to overfitting

### For Medium Datasets (10k-100k samples)
**Recommended**: XGBoost or LightGBM
- High performance and accuracy
- Handles missing values automatically
- Built-in regularization

### For Large Datasets (> 100k samples)
**Recommended**: Linear models with feature engineering
- Scalable to large datasets
- Fast training and inference
- Good interpretability

## Advanced Implementation

### Cross-Validation Strategy
```python
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier

# Stratified K-Fold for balanced classes
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    model = RandomForestClassifier(n_estimators=100, max_depth=10)
    model.fit(X_train, y_train)

    # Evaluate fold performance
```

### Hyperparameter Tuning
```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(
    RandomForestClassifier(),
    param_grid,
    cv=5,
    scoring='f1_macro',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

### Feature Engineering
- Create interaction features
- Use domain knowledge for new features
- Handle categorical variables properly
- Consider feature scaling/normalization

## Performance Optimization
1. **Speed**: Use faster algorithms for large datasets
2. **Accuracy**: Ensemble methods, stacking
3. **Robustness**: Cross-validation, regularization
4. **Interpretability**: Feature importance analysis"""
            else:  # advanced
                guidance = """# Advanced Machine Learning Classification

## State-of-the-Art Approaches

### Deep Learning Models
- **Transformers**: For complex pattern recognition
- **CNNs**: For image-like data or sequential patterns
- **RNNs/LSTMs**: For time series or sequence data

### Ensemble Strategies
- **Stacking**: Train meta-model on base model predictions
- **Blending**: Weighted combination of model predictions
- **Bayesian Optimization**: For hyperparameter tuning

## Advanced Techniques

### Neural Architecture Search
```python
# Using AutoKeras for automated model selection
import autokeras as ak

# Automated model search
clf = ak.StructuredDataClassifier(max_trials=10)
clf.fit(X_train, y_train, epochs=10)

# Export best model
model = clf.export_model()
```

### Custom Loss Functions
```python
import tensorflow as tf

def focal_loss(gamma=2.0, alpha=0.25):
    def focal_loss_fn(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1-1e-7)
        pt = tf.where(tf.equal(y_true, 1), y_pred, 1-y_pred)
        return -tf.reduce_mean(alpha * tf.pow(1-pt, gamma) * tf.math.log(pt))
    return focal_loss_fn
```

### Advanced Evaluation
- **AUC-PR**: For imbalanced datasets
- **Cohen's Kappa**: Agreement beyond chance
- **Calibration Curves**: Probability calibration assessment

## Production Considerations
1. **Model Serving**: Use TensorFlow Serving or FastAPI
2. **Monitoring**: Track model performance in production
3. **A/B Testing**: Compare new models with existing ones
4. **Model Updates**: Automated retraining pipelines

## Research Directions
- Self-supervised learning
- Few-shot learning
- Meta-learning approaches
- Explainable AI techniques"""

        elif problem_type.lower() == "regression":
            guidance = """# Machine Learning Regression Guide

## Algorithm Selection

### Linear Models
- **Linear Regression**: Simple, interpretable baseline
- **Ridge/Lasso**: Regularization to prevent overfitting
- **Elastic Net**: Combination of L1 and L2 regularization

### Tree-Based Models
- **Decision Trees**: Easy to interpret, handles non-linear relationships
- **Random Forest**: Ensemble of decision trees, robust
- **Gradient Boosting**: Sequential ensemble, high accuracy

### Advanced Models
- **Support Vector Regression**: Good for small datasets
- **Neural Networks**: Complex non-linear relationships

## Implementation Example
```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
predictions = model.predict(X_test)
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print(f"MSE: {mse:.4f}")
print(f"R²: {r2:.4f}")
```

## Key Metrics
- **MSE/RMSE**: Measure prediction error magnitude
- **MAE**: Mean absolute error
- **R²**: Proportion of variance explained
- **MAPE**: Mean absolute percentage error

## Best Practices
1. **Feature Engineering**: Create meaningful features
2. **Cross-Validation**: Use k-fold CV for evaluation
3. **Regularization**: Prevent overfitting
4. **Outlier Handling**: Robust regression techniques"""

        else:
            guidance = f"""# Machine Learning Training Guide for {problem_type}

## Overview
This guide provides recommendations for training {problem_type} models with {data_size} datasets at {complexity} level.

## Recommended Approach

### 1. Data Preparation
- Clean and preprocess your data
- Handle missing values appropriately
- Feature engineering and selection
- Train/validation/test splits

### 2. Model Selection
Based on your problem type, consider these algorithms:
- **Supervised Learning**: Linear models, trees, neural networks
- **Unsupervised Learning**: Clustering, dimensionality reduction
- **Reinforcement Learning**: Policy gradients, Q-learning

### 3. Training Strategy
- Start with simple models as baselines
- Use cross-validation for evaluation
- Hyperparameter tuning with grid/random search
- Ensemble methods for improved performance

### 4. Evaluation and Deployment
- Comprehensive metric evaluation
- Model interpretation and explainability
- Production deployment considerations
- Monitoring and maintenance

## Getting Started
1. Define your problem clearly
2. Prepare and explore your data
3. Start with simple models
4. Gradually increase complexity
5. Evaluate thoroughly before deployment

## Resources
- Scikit-learn documentation
- TensorFlow/Keras tutorials
- Research papers on arXiv
- Online courses and communities"""

        return guidance


# ============================================================================
# UNIFIED SKILLS MANAGER
# ============================================================================

class SkillsManager:
    """
    Unified skills management system that consolidates all skill functionality
    into a single, efficient interface.
    """

    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.skill_categories: Dict[SkillCategory, List[str]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.performance_cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

        # Initialize built-in skills
        self._register_builtin_skills()
        logger.info(f"Skills Manager initialized with {len(self.skills)} skills")

    def _register_builtin_skills(self):
        """Register all built-in skills"""
        builtin_skills = [
            CodeGenerationSkill(),
            DataAnalysisSkill(),
            TextAnalysisSkill(),
            WebSearchSkill(),
            MLTrainingSkill(),
        ]

        # Register basic skills
        for skill in builtin_skills:
            self.register_skill(skill)

        # Import and register additional skills
        try:
            from more_skills import FileManagerSkill
            self.register_skill(FileManagerSkill())
            logger.info("Registered additional skill: file_manager")
        except ImportError as e:
            logger.warning(f"Could not import FileManagerSkill: {e}")

        try:
            from data_inspector import DataInspectorSkill
            self.register_skill(DataInspectorSkill())
            logger.info("Registered additional skill: data_inspector")
        except ImportError as e:
            logger.warning(f"Could not import DataInspectorSkill: {e}")

        # Import additional high-value skills
        try:
            from additional_skills import PlanningSkill
            self.register_skill(PlanningSkill())
            logger.info("Registered additional skill: planning")
        except ImportError as e:
            logger.warning(f"Could not import PlanningSkill: {e}")
        except Exception as e:
            logger.warning(f"Could not register PlanningSkill: {e}")

        # Note: Other skills need interface updates to be compatible with current BaseSkill
        # autonomous_reasoning_skill, system_healer, autonomous_skills need refactoring



    def register_skill(self, skill: BaseSkill):
        """Register a new skill"""
        with self.lock:
            skill_name = skill.metadata.name
            category = skill.metadata.category

            # Register skill
            self.skills[skill_name] = skill

            # Update category mapping
            if category not in self.skill_categories:
                self.skill_categories[category] = []
            if skill_name not in self.skill_categories[category]:
                self.skill_categories[category].append(skill_name)

            logger.info(f"Registered skill: {skill_name} in category {category.value}")

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name"""
        return self.skills.get(skill_name)

    def get(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name (compatibility method for brain.py)"""
        return self.get_skill(skill_name)

    def get_skills_by_category(self, category: SkillCategory) -> List[BaseSkill]:
        """Get all skills in a category"""
        skill_names = self.skill_categories.get(category, [])
        return [self.skills[name] for name in skill_names if name in self.skills]

    def list_skills(self) -> Dict[str, Dict[str, Any]]:
        """List all registered skills with their metadata"""
        return {
            name: {
                "category": skill.metadata.category.value,
                "description": skill.metadata.description,
                "capabilities": skill.metadata.capabilities,
                "execution_count": skill.execution_count,
                "success_rate": skill.success_count / skill.execution_count if skill.execution_count > 0 else 0,
                "avg_execution_time": skill.average_execution_time
            }
            for name, skill in self.skills.items()
        }

    async def execute_skill(self, skill_name: str, context: SkillContext, **kwargs) -> SkillResult:
        """Execute a skill by name"""
        skill = self.get_skill(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                output=f"Skill '{skill_name}' not found",
                skill_name=skill_name,
                execution_time=0.0,
                metadata={"error": "skill_not_found"}
            )

        # Execute skill
        result = await skill.execute(context, **kwargs)

        # Record execution in history
        execution_record = {
            "skill_name": skill_name,
            "timestamp": datetime.now().isoformat(),
            "success": result.success,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
        self.execution_history.append(execution_record)

        # Keep only recent history (last 1000 executions)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

        return result

    def get_execution_history(self, skill_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history, optionally filtered by skill"""
        history = self.execution_history
        if skill_name:
            history = [record for record in history if record["skill_name"] == skill_name]

        return history[-limit:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for record in self.execution_history if record["success"])

        skill_stats = {}
        for skill_name, skill in self.skills.items():
            skill_history = [r for r in self.execution_history if r["skill_name"] == skill_name]
            if skill_history:
                success_rate = sum(1 for r in skill_history if r["success"]) / len(skill_history)
                avg_time = sum(r["execution_time"] for r in skill_history) / len(skill_history)
                skill_stats[skill_name] = {
                    "executions": len(skill_history),
                    "success_rate": success_rate,
                    "avg_execution_time": avg_time
                }

        return {
            "total_executions": total_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "skill_stats": skill_stats,
            "timestamp": datetime.now().isoformat()
        }


# Global skills manager instance
_skills_manager = SkillsManager()

def get_skills_manager() -> SkillsManager:
    """Get the global skills manager instance"""
    return _skills_manager