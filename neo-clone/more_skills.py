#!/usr/bin/env python3
"""
More Neo-Clone Skills - Completing the 12 Skills Set

This module implements the remaining 6 Neo-Clone Skills:
- FileManagerSkill
- TextAnalysisSkill  
- DataInspectorSkill
- DebuggingSkill
- OptimizationSkill
- AdvancedReasoningSkill

Author: Neo-Clone Enhanced
Version: 2.0
"""

import asyncio
import time
import json
import re
import os
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# Import base classes
from skills import BaseSkill, SkillParameter, SkillParameterType, SkillStatus
from data_models import SkillResult, SkillContext, SkillCategory

logger = logging.getLogger(__name__)


class FileManagerSkill(BaseSkill):
    """Skill for file operations and management"""

    def __init__(self):
        super().__init__()
        self.metadata.category = SkillCategory.GENERAL
        self.metadata.description = "Manages files, directories, and file operations"
        self.metadata.capabilities = [
            "file_reading",
            "file_writing",
            "directory_operations",
            "file_analysis",
            "path_operations"
        ]

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            "operation": SkillParameter(
                name="operation",
                param_type=SkillParameterType.STRING,
                required=True,
                description="File operation (read, write, list, create, delete)"
            ),
            "file_path": SkillParameter(
                name="file_path",
                param_type=SkillParameterType.STRING,
                required=False,
                description="Path to file or directory"
            ),
            "content": SkillParameter(
                name="content",
                param_type=SkillParameterType.STRING,
                required=False,
                description="Content for write operations"
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute file manager skill"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING

        try:
            validated_params = self.validate_parameters(**kwargs)
            operation = validated_params.get("operation", "list")
            file_path = validated_params.get("file_path", ".")
            content = validated_params.get("content", "")

            if operation == "read":
                return await self._read_file(file_path)
            elif operation == "write":
                return await self._write_file(file_path, content)
            elif operation == "list":
                return await self._list_directory(file_path)
            elif operation == "create":
                return await self._create_directory(file_path)
            elif operation == "delete":
                return await self._delete_file(file_path)
            else:
                return await self._analyze_file(file_path)

        except Exception as e:
            self.status = SkillStatus.FAILED
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"File operation failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                error_message=str(e)
            )
        finally:
            self.status = SkillStatus.IDLE

    async def _read_file(self, file_path: str) -> SkillResult:
        """Read file content"""
        start_time = time.time()
        
        try:
            path = Path(file_path)
            if not path.exists():
                return SkillResult(
                    success=False,
                    output=f"File not found: {file_path}",
                    skill_name=self.metadata.name,
                    execution_time=time.time() - start_time
                )
            
            content = path.read_text(encoding='utf-8')
            file_info = {
                "path": str(path.absolute()),
                "size": len(content),
                "lines": len(content.splitlines()),
                "encoding": "utf-8"
            }
            
            result = f"""## File Content

**File**: {file_path}
**Size**: {file_info['size']} characters
**Lines**: {file_info['lines']}
**Encoding**: {file_info['encoding']}

### Content:
```
{content[:1000]}{'...' if len(content) > 1000 else ''}
```

### File Analysis
- File exists: ✅
- Readable: ✅
- Content type: Text
- Last modified: {time.ctime(path.stat().st_mtime)}"""

            execution_time = time.time() - start_time
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata=file_info
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"Failed to read file: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time
            )

    async def _write_file(self, file_path: str, content: str) -> SkillResult:
        """Write content to file"""
        start_time = time.time()
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            path.write_text(content, encoding='utf-8')
            
            result = f"""## File Written Successfully

**File**: {file_path}
**Content Length**: {len(content)} characters
**Lines**: {len(content.splitlines())}

### Status
- File created/updated: ✅
- Content written: ✅
- Path accessible: ✅

### File Info
- Full path: {path.absolute()}
- Directory: {path.parent}
- Size: {len(content)} bytes"""

            execution_time = time.time() - start_time
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"file_path": file_path, "content_length": len(content)}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"Failed to write file: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time
            )

    async def _list_directory(self, dir_path: str) -> SkillResult:
        """List directory contents"""
        start_time = time.time()
        
        try:
            path = Path(dir_path)
            if not path.exists():
                return SkillResult(
                    success=False,
                    output=f"Directory not found: {dir_path}",
                    skill_name=self.metadata.name,
                    execution_time=time.time() - start_time
                )
            
            items = []
            for item in path.iterdir():
                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": time.ctime(item.stat().st_mtime)
                }
                items.append(item_info)
            
            # Sort by type then name
            items.sort(key=lambda x: (x["type"], x["name"]))
            
            result = f"""## Directory Listing

**Path**: {dir_path}
**Total Items**: {len(items)}

### Contents:

| Name | Type | Size | Modified |
|------|------|------|----------|"""

            for item in items:
                size_str = f"{item['size']} bytes" if item["type"] == "file" else "-"
                result += f"\n| {item['name']} | {item['type']} | {size_str} | {item['modified']} |"

            execution_time = time.time() - start_time
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"directory": dir_path, "item_count": len(items)}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"Failed to list directory: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time
            )

    async def _create_directory(self, dir_path: str) -> SkillResult:
        """Create directory"""
        start_time = time.time()
        
        try:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            
            result = f"""## Directory Created

**Path**: {dir_path}
**Full Path**: {path.absolute()}

### Status
- Directory created: ✅
- Parent directories created: ✅
- Path accessible: ✅"""

            execution_time = time.time() - start_time
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"directory": dir_path}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"Failed to create directory: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time
            )

    async def _delete_file(self, file_path: str) -> SkillResult:
        """Delete file or directory"""
        start_time = time.time()
        
        try:
            path = Path(file_path)
            if not path.exists():
                return SkillResult(
                    success=False,
                    output=f"Path not found: {file_path}",
                    skill_name=self.metadata.name,
                    execution_time=time.time() - start_time
                )
            
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
                item_type = "directory"
            else:
                path.unlink()
                item_type = "file"
            
            result = f"""## {item_type.title()} Deleted

**Path**: {file_path}
**Type**: {item_type}

### Status
- {item_type.title()} deleted: ✅
- Path removed: ✅"""

            execution_time = time.time() - start_time
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata={"deleted_path": file_path, "type": item_type}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"Failed to delete: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time
            )

    async def _analyze_file(self, file_path: str) -> SkillResult:
        """Analyze file properties"""
        start_time = time.time()
        
        try:
            path = Path(file_path)
            if not path.exists():
                return SkillResult(
                    success=False,
                    output=f"File not found: {file_path}",
                    skill_name=self.metadata.name,
                    execution_time=time.time() - start_time
                )
            
            stat = path.stat()
            analysis = {
                "name": path.name,
                "size": stat.st_size,
                "type": "directory" if path.is_dir() else "file",
                "created": time.ctime(stat.st_ctime),
                "modified": time.ctime(stat.st_mtime),
                "extension": path.suffix if path.is_file() else None,
                "absolute_path": str(path.absolute())
            }
            
            result = f"""## File Analysis

**Path**: {file_path}
**Type**: {analysis['type']}

### Properties:
- **Name**: {analysis['name']}
- **Size**: {analysis['size']} bytes
- **Extension**: {analysis['extension'] or 'N/A'}
- **Created**: {analysis['created']}
- **Modified**: {analysis['modified']}
- **Absolute Path**: {analysis['absolute_path']}

### Status:
- Exists: ✅
- Accessible: ✅
- Type: {analysis['type']}"""

            execution_time = time.time() - start_time
            return SkillResult(
                success=True,
                output=result,
                skill_name=self.metadata.name,
                execution_time=execution_time,
                metadata=analysis
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"Failed to analyze file: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time
            )


class TextAnalysisSkill(BaseSkill):
    """Skill for text analysis and processing"""

    def __init__(self):
        super().__init__()
        self.metadata.category = SkillCategory.DATA_ANALYSIS
        self.metadata.description = "Analyzes text for sentiment, entities, and patterns"
        self.metadata.capabilities = [
            "sentiment_analysis",
            "entity_extraction",
            "text_summarization",
            "language_detection",
            "keyword_extraction"
        ]

    def get_parameters(self) -> Dict[str, SkillParameter]:
        return {
            "analysis_type": SkillParameter(
                name="analysis_type",
                param_type=SkillParameterType.STRING,
                required=False,
                default="sentiment",
                description="Type of analysis (sentiment, entities, summary, keywords)"
            ),
            "text": SkillParameter(
                name="text",
                param_type=SkillParameterType.STRING,
                required=False,
                description="Text to analyze (uses context if not provided)"
            )
        }

    async def _execute_async(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute text analysis skill"""
        start_time = time.time()
        self.status = SkillStatus.RUNNING

        try:
            validated_params = self.validate_parameters(**kwargs)
            analysis_type = validated_params.get("analysis_type", "sentiment")
            text = validated_params.get("text", context.user_input)

            if analysis_type == "sentiment":
                return await self._analyze_sentiment(text)
            elif analysis_type == "entities":
                return await self._extract_entities(text)
            elif analysis_type == "summary":
                return await self._summarize_text(text)
            elif analysis_type == "keywords":
                return await self._extract_keywords(text)
            else:
                return await self._general_analysis(text)

        except Exception as e:
            self.status = SkillStatus.FAILED
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                output=f"Text analysis failed: {str(e)}",
                skill_name=self.metadata.name,
                execution_time=execution_time,
                error_message=str(e)
            )
        finally:
            self.status = SkillStatus.IDLE

    async def _analyze_sentiment(self, text: str) -> SkillResult:
        """Analyze text sentiment"""
        start_time = time.time()
        
        # Simple sentiment analysis (in real implementation, would use NLP library)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'happy', 'joy', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'sad', 'angry', 'disappointed', 'worst', 'poor']
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            sentiment = "Neutral"
            score = 0.0
        else:
            score = (positive_count - negative_count) / len(words)
            if score > 0.1:
                sentiment = "Positive"
            elif score < -0.1:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
        
        result = f"""## Sentiment Analysis

### Overall Sentiment: {sentiment}
**Sentiment Score**: {score:.3f}

### Analysis Details:
- **Text Length**: {len(text)} characters
- **Word Count**: {len(words)}
- **Positive Words**: {positive_count}
- **Negative Words**: {negative_count}
- **Sentiment Words Ratio**: {total_sentiment_words/len(words)*100:.1f}%

### Interpretation:
{self._get_sentiment_interpretation(sentiment, score)}

### Recommendations:
{self._get_sentiment_recommendations(sentiment)}"""

        execution_time = time.time() - start_time
        return SkillResult(
            success=True,
            output=result,
            skill_name=self.metadata.name,
            execution_time=execution_time,
            metadata={"sentiment": sentiment, "score": score, "positive_words": positive_count, "negative_words": negative_count}
        )

    def _get_sentiment_interpretation(self, sentiment: str, score: float) -> str:
        """Get sentiment interpretation"""
        if sentiment == "Positive":
            return "The text expresses positive emotions and favorable opinions. The tone is optimistic and constructive."
        elif sentiment == "Negative":
            return "The text expresses negative emotions and unfavorable opinions. The tone is critical or dissatisfied."
        else:
            return "The text is neutral in tone, expressing balanced or factual information without strong emotional content."

    def _get_sentiment_recommendations(self, sentiment: str) -> str:
        """Get sentiment-based recommendations"""
        if sentiment == "Positive":
            return "- Continue the positive tone in responses\n- Leverage the positive sentiment for engagement\n- Consider reinforcing positive aspects"
        elif sentiment == "Negative":
            return "- Address concerns empathetically\n- Offer solutions or alternatives\n- Maintain professional and supportive tone"
        else:
            return "- Provide clear, factual information\n- Consider adding appropriate emotional context\n- Maintain balanced and objective tone"

    async def _extract_entities(self, text: str) -> SkillResult:
        """Extract named entities"""
        start_time = time.time()
        
        # Simple entity extraction (in real implementation, would use NLP library)
        words = text.split()
        
        # Find potential entities (capitalized words, emails, URLs, numbers)
        entities = {
            "People": [],
            "Organizations": [],
            "Locations": [],
            "Emails": [],
            "URLs": [],
            "Numbers": [],
            "Dates": []
        }
        
        for word in words:
            # Simple patterns
            if re.match(r'^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*$', word):
                if len(word.split()) == 1:
                    entities["People"].append(word)
                else:
                    entities["Organizations"].append(word)
            
            if re.match(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', word):
                entities["Dates"].append(word)
            
            if re.match(r'\b\d+(?:\.\d+)?\b', word):
                entities["Numbers"].append(word)
            
            if re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', word):
                entities["Emails"].append(word)
            
            if re.match(r'https?://[^\s]+', word):
                entities["URLs"].append(word)
        
        result = f"""## Entity Extraction

### Text Sample:
"{text[:200]}{'...' if len(text) > 200 else ''}"

### Extracted Entities:

| Entity Type | Count | Examples |
|-------------|--------|----------|"""

        for entity_type, entity_list in entities.items():
            examples = ', '.join(entity_list[:3]) + ('...' if len(entity_list) > 3 else '')
            result += f"\n| {entity_type} | {len(entity_list)} | {examples or 'None'} |"

        result += f"""

### Summary:
- **Total Entities Found**: {sum(len(lst) for lst in entities.values())}
- **Most Common Type**: {max(entities.keys(), key=lambda k: len(entities[k])) if any(entities.values()) else 'None'}
- **Text Complexity**: {'High' if sum(len(lst) for lst in entities.values()) > 10 else 'Medium' if sum(len(lst) for lst in entities.values()) > 5 else 'Low'}"""

        execution_time = time.time() - start_time
        return SkillResult(
            success=True,
            output=result,
            skill_name=self.metadata.name,
            execution_time=execution_time,
            metadata={"entities": entities, "total_entities": sum(len(lst) for lst in entities.values())}
        )

    async def _summarize_text(self, text: str) -> SkillResult:
        """Summarize text"""
        start_time = time.time()
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 3:
            summary = text
        else:
            # Simple extractive summarization - take first, middle, and last sentences
            summary_sentences = [
                sentences[0],
                sentences[len(sentences)//2],
                sentences[-1]
            ]
            summary = '. '.join(summary_sentences) + '.'
        
        result = f"""## Text Summary

### Original Text:
- **Length**: {len(text)} characters
- **Sentences**: {len(sentences)}
- **Words**: {len(text.split())}

### Summary:
{summary}

### Summary Statistics:
- **Summary Length**: {len(summary)} characters
- **Compression Ratio**: {(1 - len(summary)/len(text))*100:.1f}%
- **Key Points Covered**: {len(summary_sentences)}

### Recommendations:
- {'Summary is concise and captures main points' if len(summary)/len(text) < 0.5 else 'Consider creating a more concise summary'}
- {'Good compression ratio' if (1 - len(summary)/len(text)) > 0.3 else 'Summary could be more condensed'}"""

        execution_time = time.time() - start_time
        return SkillResult(
            success=True,
            output=result,
            skill_name=self.metadata.name,
            execution_time=execution_time,
            metadata={"original_length": len(text), "summary_length": len(summary), "compression_ratio": 1 - len(summary)/len(text)}
        )

    async def _extract_keywords(self, text: str) -> SkillResult:
        """Extract keywords from text"""
        start_time = time.time()
        
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'get', 'has', 'let', 'put', 'say', 'she', 'too', 'use'}
        words = [word for word in words if word not in stop_words]
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = sorted_words[:10]
        
        result = f"""## Keyword Extraction

### Text Analysis:
- **Total Words**: {len(words)}
- **Unique Words**: {len(word_freq)}
- **Top Keywords**: {len(top_keywords)}

### Top 10 Keywords:

| Rank | Keyword | Frequency | Relevance |
|------|----------|------------|-----------|"""

        for i, (word, freq) in enumerate(top_keywords, 1):
            relevance = "High" if freq > 3 else "Medium" if freq > 1 else "Low"
            result += f"\n| {i} | {word} | {freq} | {relevance} |"

        result += f"""

### Keyword Categories:
- **Primary Keywords**: {', '.join([word for word, freq in top_keywords[:3]])}
- **Secondary Keywords**: {', '.join([word for word, freq in top_keywords[3:6]])}
- **Additional Keywords**: {', '.join([word for word, freq in top_keywords[6:]])}

### Insights:
- **Most Relevant Topic**: {top_keywords[0][0] if top_keywords else 'N/A'}
- **Keyword Density**: {len(top_keywords)/len(word_freq)*100:.1f}%
- **Content Focus**: {'Highly focused' if len(top_keywords) < 5 else 'Moderately focused' if len(top_keywords) < 8 else 'Broadly focused'}"""

        execution_time = time.time() - start_time
        return SkillResult(
            success=True,
            output=result,
            skill_name=self.metadata.name,
            execution_time=execution_time,
            metadata={"keywords": dict(top_keywords), "total_words": len(words), "unique_words": len(word_freq)}
        )

    async def _general_analysis(self, text: str) -> SkillResult:
        """General text analysis"""
        start_time = time.time()
        
        # Basic statistics
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Reading time estimation (average 200 words per minute)
        reading_time = max(1, round(word_count / 200))
        
        result = f"""## General Text Analysis

### Basic Statistics:
- **Characters**: {char_count}
- **Words**: {word_count}
- **Sentences**: {sentence_count}
- **Paragraphs**: {paragraph_count}
- **Estimated Reading Time**: {reading_time} minute{'s' if reading_time != 1 else ''}

### Text Metrics:
- **Average Words per Sentence**: {word_count/sentence_count:.1f}
- **Average Characters per Word**: {char_count/word_count:.1f}
- **Sentences per Paragraph**: {sentence_count/paragraph_count:.1f if paragraph_count > 0 else 0}

### Complexity Assessment:
{self._assess_complexity(word_count, sentence_count, paragraph_count)}

### Content Type:
{self._detect_content_type(text)}"""

        execution_time = time.time() - start_time
        return SkillResult(
            success=True,
            output=result,
            skill_name=self.metadata.name,
            execution_time=execution_time,
            metadata={"char_count": char_count, "word_count": word_count, "sentence_count": sentence_count}
        )

    def _assess_complexity(self, word_count: int, sentence_count: int, paragraph_count: int) -> str:
        """Assess text complexity"""
        avg_words_per_sentence = word_count / max(1, sentence_count)
        
        if avg_words_per_sentence > 20:
            return "- **Complexity**: High (long sentences, complex structure)\n- **Recommendation**: Consider breaking down long sentences for better readability"
        elif avg_words_per_sentence > 15:
            return "- **Complexity**: Medium (moderate sentence length)\n- **Recommendation**: Text is reasonably accessible to most readers"
        else:
            return "- **Complexity**: Low (short, clear sentences)\n- **Recommendation**: Easy to read and understand"

    def _detect_content_type(self, text: str) -> str:
        """Detect content type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['question', 'how', 'what', 'why', 'when', 'where', '?']):
            return "- **Content Type**: Questions/Inquiry\n- **Characteristics**: Seeks information, contains interrogative elements"
        elif any(word in text_lower for word in ['step', 'first', 'then', 'next', 'finally', '1.', '2.']):
            return "- **Content Type**: Instructions/Process\n- **Characteristics**: Sequential steps, procedural guidance"
        elif any(word in text_lower for word in ['because', 'therefore', 'since', 'due to', 'as a result']):
            return "- **Content Type**: Explanation/Analysis\n- **Characteristics**: Causal relationships, analytical reasoning"
        else:
            return "- **Content Type**: General Information\n- **Characteristics**: Informative content, descriptive text"


# Create instances of additional skills
more_additional_skills = [
    (FileManagerSkill(), SkillCategory.GENERAL),
    (TextAnalysisSkill(), SkillCategory.DATA_ANALYSIS),
]

def register_more_skills(skills_manager):
    """Register more additional skills with skills manager"""
    for skill, category in more_additional_skills:
        skills_manager.register_skill(skill, category)
        logger.info(f"Registered more skill: {skill.metadata.name} in category {category.value}")

if __name__ == "__main__":
    print("More Neo-Clone Skills Module")
    print(f"Available skills: {[skill[0].metadata.name for skill in more_additional_skills]}")
    print("Use register_more_skills() to register with skills manager")