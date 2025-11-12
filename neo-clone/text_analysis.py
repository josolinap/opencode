"""
Text Analysis Skill for Neo-Clone
Advanced text analysis with sentiment classification, keyword extraction, summarization, and content moderation.
"""

from skills import BaseSkill, SkillResult
from functools import lru_cache
import hashlib
import re
import logging
from typing import Dict, List, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)

class TextAnalysisSkill(BaseSkill):

    def __init__(self):
        super().__init__(
            name='text_analysis',
            description='Advanced text analysis with sentiment classification, keyword extraction, summarization, and content moderation.',
            example='Analyze the sentiment and extract keywords from a customer review.'
        )
        self._cache = {}
        self._max_cache_size = 50

    @property
    def parameters(self):
        return {
            'text': 'string - The text to analyze',
            'analysis_type': 'string - Type of analysis (sentiment, keywords, summary, moderation, all). Default: all',
            'max_keywords': 'integer - Maximum number of keywords to extract (default: 10)',
            'summary_length': 'string - Summary length (short, medium, long). Default: medium'
        }

    def execute(self, params):
        """Execute text analysis with given parameters"""
        try:
            text = params.get('text', '')
            analysis_type = params.get('analysis_type', 'all')
            max_keywords = params.get('max_keywords', 10)
            summary_length = params.get('summary_length', 'medium')

            # Generate cache key
            cache_key = hashlib.md5(f'{text}_{analysis_type}_{max_keywords}_{summary_length}'.encode()).hexdigest()
            
            # Check cache first
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                cached_result['cached'] = True
                return SkillResult(True, "Text analysis completed (cached)", cached_result)

            # Validate input
            if not text.strip():
                return SkillResult(False, "No text provided for analysis")

            # Perform analysis
            result = self._analyze_text(text, analysis_type, max_keywords, summary_length)
            
            # Add to cache
            self._add_to_cache(cache_key, result)

            return SkillResult(True, "Text analysis completed successfully", result)

        except Exception as e:
            logger.error(f"Text analysis failed: {str(e)}")
            return SkillResult(False, f"Text analysis failed: {str(e)}")

    def _analyze_text(self, text: str, analysis_type: str, max_keywords: int, summary_length: str) -> Dict[str, Any]:
        """Perform comprehensive text analysis"""
        result = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'analysis_type': analysis_type,
            'cached': False
        }

        # Try enhanced analysis if available
        try:
            enhanced_result = self._enhanced_analysis(text, analysis_type, max_keywords, summary_length)
            if enhanced_result:
                result.update(enhanced_result)
                return result
        except Exception as e:
            logger.warning(f"Enhanced analysis failed, using fallback: {str(e)}")

        # Fallback analysis
        if analysis_type == 'all' or analysis_type == 'sentiment':
            result['sentiment'] = self._analyze_sentiment(text)
        
        if analysis_type == 'all' or analysis_type == 'keywords':
            result['keywords'] = self._extract_keywords(text, max_keywords)
        
        if analysis_type == 'all' or analysis_type == 'summary':
            result['summary'] = self._generate_summary(text, summary_length)
        
        if analysis_type == 'all' or analysis_type == 'moderation':
            result['moderation'] = self._moderate_content(text)

        return result

    def _enhanced_analysis(self, text: str, analysis_type: str, max_keywords: int, summary_length: str) -> Optional[Dict[str, Any]]:
        """Try to use enhanced OpenCode integration for analysis"""
        try:
            from enhanced_opencode_integration import EnhancedOpenCodeIntegration
            integration = EnhancedOpenCodeIntegration()
            
            prompt = self._build_analysis_prompt(text, analysis_type, max_keywords, summary_length)
            result = integration.generate_response(prompt=prompt, model='opencode/big-pickle', max_tokens=500)
            
            if result.get('success'):
                return self._parse_opencode_response(result.get('response', ''), analysis_type)
        except ImportError:
            logger.warning("Enhanced OpenCode integration not available")
        except Exception as e:
            logger.error(f"Enhanced analysis error: {str(e)}")
        
        return None

    def _build_analysis_prompt(self, text: str, analysis_type: str, max_keywords: int, summary_length: str) -> str:
        """Build prompt for enhanced analysis"""
        prompt = f"""
Analyze the following text:

Text: "{text}"

Analysis type: {analysis_type}
Max keywords: {max_keywords}
Summary length: {summary_length}

Please provide:
"""
        
        if analysis_type in ['all', 'sentiment']:
            prompt += "- Sentiment analysis (positive, negative, neutral with confidence score)\n"
        
        if analysis_type in ['all', 'keywords']:
            prompt += f"- Top {max_keywords} keywords with relevance scores\n"
        
        if analysis_type in ['all', 'summary']:
            prompt += f"- {summary_length} summary\n"
        
        if analysis_type in ['all', 'moderation']:
            prompt += "- Content moderation check (toxicity, spam, etc.)\n"
        
        prompt += "\nProvide results in JSON format."
        return prompt

    def _parse_opencode_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse response from enhanced analysis"""
        try:
            # Try to extract JSON from response
            import json
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        
        # Fallback to basic analysis
        return self._fallback_analysis(response, analysis_type, 10, 'medium')

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Basic sentiment analysis"""
        # Simple keyword-based sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'best', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst', 'poor', 'disappointing', 'sucks']
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            sentiment = 'neutral'
            confidence = 0.5
        elif positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(positive_count / total_sentiment_words + 0.3, 1.0)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(negative_count / total_sentiment_words + 0.3, 1.0)
        else:
            sentiment = 'neutral'
            confidence = 0.6
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_words': positive_count,
            'negative_words': negative_count
        }

    def _extract_keywords(self, text: str, max_keywords: int) -> List[Dict[str, Any]]:
        """Extract keywords from text"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
        
        # Clean and tokenize text
        words = re.findall(r'\b\w+\b', text.lower())
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Get top keywords
        keywords = []
        for word, count in word_counts.most_common(max_keywords):
            relevance = min(count / len(words) * 10, 1.0)  # Normalize relevance
            keywords.append({
                'keyword': word,
                'frequency': count,
                'relevance': relevance
            })
        
        return keywords

    def _generate_summary(self, text: str, length: str) -> str:
        """Generate text summary"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return "No content to summarize"
        
        # Determine number of sentences based on length
        if length == 'short':
            num_sentences = min(1, len(sentences))
        elif length == 'medium':
            num_sentences = min(3, len(sentences))
        else:  # long
            num_sentences = min(5, len(sentences))
        
        # Simple extractive summarization - take first sentences
        summary = '. '.join(sentences[:num_sentences])
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary

    def _moderate_content(self, text: str) -> Dict[str, Any]:
        """Basic content moderation"""
        # Simple keyword-based moderation
        toxic_words = ['toxic', 'hate', 'kill', 'die', 'stupid', 'idiot', 'dumb', 'ugly', 'disgusting']
        spam_indicators = ['buy now', 'click here', 'free money', 'guarantee', 'limited time', 'act now']
        
        text_lower = text.lower()
        toxic_count = sum(1 for word in toxic_words if word in text_lower)
        spam_count = sum(1 for phrase in spam_indicators if phrase in text_lower)
        
        toxicity_score = min(toxic_count / len(text.split()) * 10, 1.0) if text.split() else 0
        spam_score = min(spam_count / len(text.split()) * 5, 1.0) if text.split() else 0
        
        # Overall safety score
        safety_score = 1.0 - max(toxicity_score, spam_score)
        
        return {
            'toxicity_score': toxicity_score,
            'spam_score': spam_score,
            'safety_score': safety_score,
            'is_safe': safety_score > 0.7,
            'flags': []
        }

    def _fallback_analysis(self, text: str, analysis_type: str, max_keywords: int, summary_length: str) -> Dict[str, Any]:
        """Fallback analysis when enhanced methods fail"""
        result = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'analysis_type': analysis_type,
            'cached': False
        }
        
        if analysis_type in ['all', 'sentiment']:
            result['sentiment'] = self._analyze_sentiment(text)
        
        if analysis_type in ['all', 'keywords']:
            result['keywords'] = self._extract_keywords(text, max_keywords)
        
        if analysis_type in ['all', 'summary']:
            result['summary'] = self._generate_summary(text, summary_length)
        
        if analysis_type in ['all', 'moderation']:
            result['moderation'] = self._moderate_content(text)
        
        return result

    def _add_to_cache(self, key: str, value: Dict[str, Any]):
        """Add result to cache with size management"""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = value.copy()

# Test the skill
if __name__ == "__main__":
    skill = TextAnalysisSkill()
    
    # Test with sample text
    test_text = "I really love this product! It's amazing and works great. The quality is excellent and I would definitely recommend it to anyone."
    
    result = skill.execute({
        "text": test_text,
        "analysis_type": "all",
        "max_keywords": 5,
        "summary_length": "short"
    })
    
    print(f"Analysis successful: {result.success}")
    print(f"Output: {result.output}")
    if result.data:
        print(f"Sentiment: {result.data.get('sentiment', {})}")
        print(f"Keywords: {result.data.get('keywords', [])}")
        print(f"Summary: {result.data.get('summary', '')}")