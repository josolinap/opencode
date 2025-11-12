"""
Web Search Skill for Neo-Clone
Provides web search capabilities using various search engines, search result extraction and formatting, 
quick fact checking and information lookup, and multiple search result format options.
"""

from skills import BaseSkill, SkillResult
from functools import lru_cache
import json
import re
from typing import Dict, Any, Optional, List
import logging
from urllib.parse import quote, urljoin
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class WebSearchSkill(BaseSkill):

    def __init__(self):
        super().__init__(
            name='web_search',
            description='Searches the web for information, facts, and current data',
            example='Search for Python tutorials, find latest news, or look up information about AI'
        )
        self._cache = {}
        self._max_cache_size = 100

    @property
    def parameters(self):
        return {
            'query': 'string - The search query',
            'search_type': 'string - Type of search (general, news, fact_check). Default: general',
            'max_results': 'integer - Maximum number of results (default: 10)',
            'include_snippets': 'boolean - Include search snippets (default: true)'
        }

    def execute(self, params):
        """Execute web search with given parameters"""
        try:
            # Support both old and new parameter formats
            if 'text' in params:
                # Legacy format - extract query from text
                text = params.get('text', '').lower()
                search_query = self._extract_search_query(text)
                search_type = self._determine_search_type(text)
            else:
                # New format
                search_query = params.get('query', '')
                search_type = params.get('search_type', 'general')
            
            max_results = params.get('max_results', 10)
            include_snippets = params.get('include_snippets', True)

            # Generate cache key
            cache_key = hashlib.md5(f'{search_query}_{search_type}_{max_results}_{include_snippets}'.encode()).hexdigest()
            
            # Check cache first
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                cached_result['cached'] = True
                return SkillResult(True, "Web search completed (cached)", cached_result)

            # Validate input
            if not search_query.strip():
                return SkillResult(False, "No search query provided. Please specify what to search for.")

            # Perform search
            result = self._perform_search(search_query, search_type, max_results, include_snippets)
            
            # Add to cache
            self._add_to_cache(cache_key, result)

            return SkillResult(True, f"Web search completed for '{search_query}'", result)

        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return SkillResult(False, f"Web search failed: {str(e)}")

    def _perform_search(self, query: str, search_type: str, max_results: int, include_snippets: bool) -> Dict[str, Any]:
        """Perform the actual search"""
        try:
            # Try enhanced search if available
            enhanced_result = self._enhanced_search(query, search_type, max_results)
            if enhanced_result:
                return enhanced_result
        except Exception as e:
            logger.warning(f"Enhanced search failed, using fallback: {str(e)}")

        # Fallback search
        if search_type == 'fact_check':
            return self._fact_check(query)
        elif search_type == 'news':
            return self._search_news(query, max_results)
        else:
            return self._general_search(query, max_results, include_snippets)

    def _enhanced_search(self, query: str, search_type: str, max_results: int) -> Optional[Dict[str, Any]]:
        """Try to use enhanced search capabilities"""
        try:
            # Try to use requests for actual web search (mock implementation)
            # In a real implementation, this would use search APIs
            return None  # Placeholder - would implement actual search
        except Exception as e:
            logger.error(f"Enhanced search error: {str(e)}")
            return None

    def _extract_search_query(self, text: str) -> str:
        """Extract search query from user text"""
        # Look for quoted text
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', text)
        if quoted_matches:
            return quoted_matches[0]
        
        # Look for search keywords
        search_patterns = [
            r'search for (.+?)(?:\.|$)',
            r'find (.+?)(?:\.|$)',
            r'look up (.+?)(?:\.|$)',
            r'what is (.+?)(?:\.|$)',
            r'who is (.+?)(?:\.|$)',
            r'where is (.+?)(?:\.|$)',
            r'how to (.+?)(?:\.|$)',
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, use the whole text as query
        return text.strip()

    def _determine_search_type(self, text: str) -> str:
        """Determine the type of search based on text"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['fact check', 'verify', 'true or false', 'is it true']):
            return 'fact_check'
        elif any(keyword in text_lower for keyword in ['news', 'latest', 'recent', 'breaking', 'today']):
            return 'news'
        else:
            return 'general'

    def _general_search(self, query: str, max_results: int = 10, include_snippets: bool = True) -> Dict[str, Any]:
        """General web search (mock implementation)"""
        # Mock search results - in real implementation, this would call search APIs
        mock_results = [
            {
                'title': f'Search result for "{query}" - Example 1',
                'url': f'https://example.com/search?q={quote(query)}&result=1',
                'snippet': f'This is a mock search result snippet for {query}. It contains relevant information about the topic.',
                'relevance': 0.95
            },
            {
                'title': f'Search result for "{query}" - Example 2',
                'url': f'https://example.com/search?q={quote(query)}&result=2',
                'snippet': f'Another mock search result for {query} with different information and perspective.',
                'relevance': 0.87
            },
            {
                'title': f'Search result for "{query}" - Example 3',
                'url': f'https://example.com/search?q={quote(query)}&result=3',
                'snippet': f'Third mock result providing additional context about {query}.',
                'relevance': 0.78
            }
        ]
        
        # Limit results
        results = mock_results[:max_results]
        
        # Remove snippets if not requested
        if not include_snippets:
            for result in results:
                result.pop('snippet', None)
        
        return {
            'query': query,
            'search_type': 'general',
            'total_results': len(results),
            'results': results,
            'cached': False,
            'search_time': datetime.now().isoformat(),
            'disclaimer': 'This is a mock search implementation. In production, this would use real search APIs.'
        }

    def _search_news(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """News search (mock implementation)"""
        mock_news = [
            {
                'title': f'Latest News: {query} - Breaking Update',
                'url': f'https://news.example.com/{quote(query)}',
                'snippet': f'Breaking news about {query}. Recent developments and updates.',
                'source': 'Mock News Source',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'relevance': 0.92
            },
            {
                'title': f'{query} - Recent Developments',
                'url': f'https://news.example.com/{quote(query)}-2',
                'snippet': f'More news coverage about {query} with expert analysis.',
                'source': 'Another News Source',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'relevance': 0.85
            }
        ]
        
        return {
            'query': query,
            'search_type': 'news',
            'total_results': len(mock_news[:max_results]),
            'results': mock_news[:max_results],
            'cached': False,
            'search_time': datetime.now().isoformat(),
            'disclaimer': 'This is a mock news search implementation.'
        }

    def _fact_check(self, query: str) -> Dict[str, Any]:
        """Fact checking (mock implementation)"""
        # Mock fact check result
        return {
            'query': query,
            'search_type': 'fact_check',
            'claim': query,
            'verdict': 'Unable to verify',
            'confidence': 0.5,
            'explanation': f'This is a mock fact check for the claim: "{query}". In a real implementation, this would check against fact-checking databases.',
            'sources': [
                {
                    'name': 'Mock Fact Check Source',
                    'url': 'https://factcheck.example.com',
                    'reliability': 'High'
                }
            ],
            'cached': False,
            'check_time': datetime.now().isoformat(),
            'disclaimer': 'This is a mock fact checking implementation.'
        }

    def _add_to_cache(self, key: str, value: Dict[str, Any]):
        """Add result to cache with size management"""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = value.copy()

# Test the skill
if __name__ == "__main__":
    skill = WebSearchSkill()
    
    # Test with different search types
    test_cases = [
        {"text": "search for Python tutorials"},
        {"query": "machine learning", "search_type": "general"},
        {"text": "latest news about AI", "search_type": "news"},
        {"text": "fact check: is the earth round?", "search_type": "fact_check"}
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        result = skill.execute(test_case)
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")
        if result.data:
            print(f"Results found: {result.data.get('total_results', 0)}")
            if result.data.get('results'):
                print(f"First result: {result.data['results'][0].get('title', 'N/A')}")