"""
Web Search Skill for Neo-Clone
Provides web search capabilities using various search engines, search result extraction and formatting,
quick fact checking and information lookup, and multiple search result format options.

Enhanced with source credibility and recency scoring for improved result quality assessment.

## Credibility & Recency Features

When WEBSEARCH_CREDIBILITY_ENABLED=true (default), the web search skill provides:

### Credibility Scoring
- Domain-based reputation scoring (.edu/.gov = 0.9, .org = 0.7, .com = 0.5)
- Known high-credibility domains (Wikipedia, GitHub, etc. = 0.9)
- Content quality indicators (author mentions, citations, academic terms)
- Commercial bias penalties
- Recency bonuses for recent content

### Recency Extraction
- Automatic date extraction from content and metadata
- Multiple date format support (ISO, US, text formats)
- Fallback to 30-day estimate when dates unavailable
- Days since publication calculation

### Enhanced Output Schema
```json
{
  "sources": [
    {
      "url": "https://example.com",
      "title": "Result Title",
      "snippet": "Content snippet...",
      "credibility": 0.85,
      "recencyDays": 15
    }
  ],
  "overallCredibility": 0.72,
  "results": [...]  // Backward compatibility
}
```

### Telemetry & Monitoring
- Lightweight per-search metrics collection
- Credibility distribution analysis (5 buckets: 0.0-0.2, 0.2-0.4, etc.)
- Performance timing and success rates
- JSON log output for dashboards and alerting
- Feature flag controlled (WEBSEARCH_CREDIBILITY_ENABLED)

### Backward Compatibility
- All new fields are optional
- Old consumers continue working unchanged
- 'results' key maintained alongside new 'sources' key
- Feature can be disabled without code changes
"""

from skills import BaseSkill, SkillResult
from functools import lru_cache
import json
import re
from typing import Dict, Any, Optional, List, Tuple
import logging
from urllib.parse import quote, urljoin
from datetime import datetime, timedelta
import hashlib
import os

# Import credibility telemetry
try:
    from credibility_telemetry import collect_search_metrics
except ImportError:
    # Fallback if telemetry module not available
    def collect_search_metrics(*args, **kwargs):
        return None

# Import shared credibility scorer
try:
    from credibility_scorer import compute_source_credibility as shared_compute_credibility
except ImportError:
    # Fallback to local implementation if shared utility not available
    shared_compute_credibility = None

logger = logging.getLogger(__name__)

# Feature flag for gradual rollout
WEBSEARCH_CREDIBILITY_ENABLED = os.getenv('WEBSEARCH_CREDIBILITY_ENABLED', 'true').lower() == 'true'

class WebSearchSkill(BaseSkill):

    def __init__(self):
        super().__init__(
            name='web_search',
            description='Searches the web for information, facts, and current data',
            example='Search for Python tutorials, find latest news, or look up information about AI'
        )
        self._cache = {}
        self._max_cache_size = 100

        # Credibility scoring configuration
        self._credible_domains = {
            'edu': 0.9,      # Educational institutions
            'gov': 0.9,      # Government sites
            'org': 0.7,      # Non-profits (varies)
            'com': 0.5,      # Commercial (neutral)
            'net': 0.4,      # Network services
            'io': 0.6,       # Tech startups
            'ai': 0.7,       # AI-specific domains
            'news': 0.6,     # News aggregators
        }

        # Known high-credibility domains
        self._high_credibility_domains = {
            'wikipedia.org', 'github.com', 'stackoverflow.com',
            'arxiv.org', 'nature.com', 'science.org',
            'ieee.org', 'acm.org', 'mit.edu', 'stanford.edu',
            'harvard.edu', 'berkeley.edu', 'ox.ac.uk', 'cam.ac.uk'
        }

    def compute_source_credibility(self, url: str, page_content: Optional[str] = None, date_info: Optional[Dict[str, Any]] = None) -> float:
        """
        Compute credibility score for a source (0.0-1.0)

        Lightweight heuristics based on:
        - Domain reputation (.edu, .gov, .org, etc.)
        - Known high-credibility domains
        - Content quality indicators (author, citations, etc.)
        - Date recency bonus

        Args:
            url: Source URL
            page_content: Optional page content for analysis
            date_info: Optional date information

        Returns:
            Credibility score between 0.0 and 1.0
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Base score from domain
            base_score = 0.5  # Neutral default

            # Check for high-credibility domains
            if any(cred_domain in domain for cred_domain in self._high_credibility_domains):
                base_score = 0.9
            else:
                # Check TLD credibility
                tld = domain.split('.')[-1] if '.' in domain else ''
                if tld in self._credible_domains:
                    base_score = self._credible_domains[tld]

            # Content-based adjustments (if content available)
            content_bonus = 0.0
            if page_content:
                content_lower = page_content.lower()

                # Author indicators
                if any(indicator in content_lower for indicator in ['author:', 'by ', 'written by', 'contributor']):
                    content_bonus += 0.1

                # Citation indicators
                if any(indicator in content_lower for indicator in ['references', 'citations', 'sources', 'et al']):
                    content_bonus += 0.1

                # Academic/indepth indicators
                if any(indicator in content_lower for indicator in ['abstract', 'methodology', 'conclusion', 'doi:']):
                    content_bonus += 0.1

                # Commercial bias penalty
                if any(indicator in content_lower for indicator in ['buy now', 'limited time', 'sponsored', 'advertisement']):
                    content_bonus -= 0.1

            # Date recency bonus (if available)
            recency_bonus = 0.0
            if date_info and date_info.get('recency_days') is not None:
                days = date_info['recency_days']
                if days <= 7:  # Very recent
                    recency_bonus = 0.1
                elif days <= 30:  # Recent
                    recency_bonus = 0.05
                elif days <= 365:  # This year
                    recency_bonus = 0.02

            # Calculate final score
            final_score = min(1.0, max(0.0, base_score + content_bonus + recency_bonus))

            logger.debug(f"Credibility score for {domain}: {final_score:.2f} (base: {base_score:.2f}, content: {content_bonus:.2f}, recency: {recency_bonus:.2f})")
            return final_score

        except Exception as e:
            logger.warning(f"Error computing credibility for {url}: {e}")
            return 0.5  # Neutral fallback

    def extract_recency_info(self, url: str, page_content: Optional[str] = None, published_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Extract publication/update date and compute recency

        Args:
            url: Source URL
            page_content: Optional page content to analyze
            published_date: Optional pre-extracted date string

        Returns:
            Dict with recency_days and metadata, or None if no date found
        """
        try:
            # If we already have a published date, use it
            if published_date:
                try:
                    pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                    days_since = (datetime.now() - pub_date).days
                    return {
                        'recency_days': max(0, days_since),
                        'publication_date': published_date,
                        'source': 'provided'
                    }
                except (ValueError, AttributeError):
                    pass

            # Try to extract from content
            if page_content:
                # Common date patterns
                date_patterns = [
                    r'published:\s*([A-Za-z]{3}\s+\d{1,2},?\s+\d{4})',  # "Published: Jan 15, 2024"
                    r'updated:\s*([A-Za-z]{3}\s+\d{1,2},?\s+\d{4})',    # "Updated: Jan 15, 2024"
                    r'date:\s*([A-Za-z]{3}\s+\d{1,2},?\s+\d{4})',       # "Date: Jan 15, 2024"
                    r'(\d{4}-\d{2}-\d{2})',                              # ISO format
                    r'(\d{1,2}/\d{1,2}/\d{4})',                         # US format
                    r'([A-Za-z]{3}\s+\d{1,2},?\s+\d{4})',              # "Jan 15, 2024"
                ]

                for pattern in date_patterns:
                    match = re.search(pattern, page_content, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        try:
                            # Try different date parsing approaches
                            if '-' in date_str:  # ISO format
                                pub_date = datetime.fromisoformat(date_str)
                            elif '/' in date_str:  # US format
                                pub_date = datetime.strptime(date_str, '%m/%d/%Y')
                            else:  # Text format
                                pub_date = datetime.strptime(date_str, '%b %d, %Y')

                            days_since = (datetime.now() - pub_date).days
                            return {
                                'recency_days': max(0, days_since),
                                'publication_date': pub_date.isoformat(),
                                'source': 'extracted'
                            }
                        except (ValueError, AttributeError):
                            continue

            # Fallback: estimate based on URL patterns or domain age
            # For mock data, we'll use a reasonable default
            return {
                'recency_days': 30,  # Assume 30 days old if no date found
                'publication_date': None,
                'source': 'estimated'
            }

        except Exception as e:
            logger.warning(f"Error extracting recency for {url}: {e}")
            return None

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
                'url': f'https://wikipedia.org/search?q={quote(query)}&result=1',
                'snippet': f'This is a mock search result snippet for {query}. It contains relevant information about the topic with references and citations.',
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
                'url': f'https://news.example.com/search?q={quote(query)}&result=3',
                'snippet': f'Third mock result providing additional context about {query}.',
                'relevance': 0.78
            }
        ]

        # Limit results
        results = mock_results[:max_results]

        # Add credibility and recency scoring if enabled
        enhanced_sources = []
        credibility_scores = []

        for result in results:
            url = result['url']
            snippet = result.get('snippet', '')

            # Extract recency information
            recency_info = None
            if WEBSEARCH_CREDIBILITY_ENABLED:
                recency_info = self.extract_recency_info(url, snippet)

            # Compute credibility score using shared utility when available
            credibility = 0.5  # Default neutral score
            if WEBSEARCH_CREDIBILITY_ENABLED:
                if shared_compute_credibility:
                    # Use shared credibility scorer
                    credibility = shared_compute_credibility(url, snippet, recency_info)
                else:
                    # Fallback to local implementation
                    credibility = self.compute_source_credibility(url, snippet, recency_info)

            # Build enhanced source object
            enhanced_source = {
                'url': url,
                'title': result['title'],
                'snippet': result.get('snippet') if include_snippets else None,
            }

            # Add optional enhanced fields only if enabled
            if WEBSEARCH_CREDIBILITY_ENABLED:
                enhanced_source['credibility'] = round(credibility, 2)
                if recency_info:
                    enhanced_source['recencyDays'] = recency_info.get('recency_days')

            enhanced_sources.append(enhanced_source)
            credibility_scores.append(credibility)

        # Calculate overall credibility
        overall_credibility = 0.0
        if WEBSEARCH_CREDIBILITY_ENABLED and credibility_scores:
            overall_credibility = sum(credibility_scores) / len(credibility_scores)

        # Build response
        response = {
            'query': query,
            'search_type': 'general',
            'total_results': len(enhanced_sources),
            'sources': enhanced_sources,  # Changed from 'results' to 'sources' for new schema
            'cached': False,
            'search_time': datetime.now().isoformat(),
            'disclaimer': 'This is a mock search implementation. In production, this would use real search APIs.'
        }

        # Add enhanced fields only if enabled
        if WEBSEARCH_CREDIBILITY_ENABLED:
            response['overallCredibility'] = round(overall_credibility, 2)

        # Maintain backward compatibility - also include 'results' key
        response['results'] = enhanced_sources

        # Collect telemetry for credibility metrics
        if WEBSEARCH_CREDIBILITY_ENABLED:
            collect_search_metrics(query, 'general', enhanced_sources)

        return response

    def _search_news(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """News search (mock implementation)"""
        mock_news = [
            {
                'title': f'Latest News: {query} - Breaking Update',
                'url': f'https://bbc.co.uk/news/{quote(query)}',
                'snippet': f'Breaking news about {query}. Recent developments and updates. Published: {datetime.now().strftime("%b %d, %Y")}',
                'source': 'BBC News',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'relevance': 0.92
            },
            {
                'title': f'{query} - Recent Developments',
                'url': f'https://reuters.com/{quote(query)}-2',
                'snippet': f'More news coverage about {query} with expert analysis. Updated: {datetime.now().strftime("%b %d, %Y")}',
                'source': 'Reuters',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'relevance': 0.85
            }
        ]

        # Limit results
        results = mock_news[:max_results]

        # Add credibility and recency scoring if enabled
        enhanced_sources = []
        credibility_scores = []

        for result in results:
            url = result['url']
            snippet = result.get('snippet', '')
            published_date = result.get('published_date')

            # Extract recency information
            recency_info = None
            if WEBSEARCH_CREDIBILITY_ENABLED:
                recency_info = self.extract_recency_info(url, snippet, published_date)

            # Compute credibility score using shared utility when available
            credibility = 0.5  # Default neutral score
            if WEBSEARCH_CREDIBILITY_ENABLED:
                if shared_compute_credibility:
                    # Use shared credibility scorer
                    credibility = shared_compute_credibility(url, snippet, recency_info)
                else:
                    # Fallback to local implementation
                    credibility = self.compute_source_credibility(url, snippet, recency_info)

            # Build enhanced source object
            enhanced_source = {
                'url': url,
                'title': result['title'],
                'snippet': snippet,
            }

            # Add optional enhanced fields only if enabled
            if WEBSEARCH_CREDIBILITY_ENABLED:
                enhanced_source['credibility'] = round(credibility, 2)
                if recency_info:
                    enhanced_source['recencyDays'] = recency_info.get('recency_days')

            enhanced_sources.append(enhanced_source)
            credibility_scores.append(credibility)

        # Calculate overall credibility
        overall_credibility = 0.0
        if WEBSEARCH_CREDIBILITY_ENABLED and credibility_scores:
            overall_credibility = sum(credibility_scores) / len(credibility_scores)

        # Build response
        response = {
            'query': query,
            'search_type': 'news',
            'total_results': len(enhanced_sources),
            'sources': enhanced_sources,  # Changed from 'results' to 'sources' for new schema
            'cached': False,
            'search_time': datetime.now().isoformat(),
            'disclaimer': 'This is a mock news search implementation.'
        }

        # Add enhanced fields only if enabled
        if WEBSEARCH_CREDIBILITY_ENABLED:
            response['overallCredibility'] = round(overall_credibility, 2)

        # Maintain backward compatibility - also include 'results' key
        response['results'] = enhanced_sources

        # Collect telemetry for credibility metrics
        if WEBSEARCH_CREDIBILITY_ENABLED:
            collect_search_metrics(query, 'news', enhanced_sources)

        return response

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
    import os

    # Test credibility and recency features
    print("=== Testing Enhanced Web Search with Credibility & Recency ===\n")

    # Test with feature enabled (default)
    print("--- Testing with WEBSEARCH_CREDIBILITY_ENABLED=true ---")
    skill = WebSearchSkill()

    # Test general search with enhanced features
    result = skill.execute({"query": "Python programming", "search_type": "general"})
    print(f"Success: {result.success}")
    if result.data and 'sources' in result.data:
        print(f"Total sources: {result.data['total_results']}")
        if 'overallCredibility' in result.data:
            print(f"Overall credibility: {result.data['overallCredibility']}")
        for i, source in enumerate(result.data['sources'][:2]):  # Show first 2
            print(f"  Source {i+1}: {source['title'][:50]}...")
            if 'credibility' in source:
                print(f"    Credibility: {source['credibility']}")
            if 'recencyDays' in source:
                print(f"    Recency: {source['recencyDays']} days")

    print("\n--- Testing with WEBSEARCH_CREDIBILITY_ENABLED=false ---")
    # Test with feature disabled
    os.environ['WEBSEARCH_CREDIBILITY_ENABLED'] = 'false'
    skill_disabled = WebSearchSkill()
    result_disabled = skill_disabled.execute({"query": "Python programming", "search_type": "general"})
    print(f"Success: {result_disabled.success}")
    if result_disabled.data and 'sources' in result_disabled.data:
        print(f"Total sources: {result_disabled.data['total_results']}")
        has_credibility = any('credibility' in source for source in result_disabled.data['sources'])
        print(f"Has credibility scores: {has_credibility}")
        has_overall = 'overallCredibility' in result_disabled.data
        print(f"Has overall credibility: {has_overall}")

    # Reset for other tests
    os.environ['WEBSEARCH_CREDIBILITY_ENABLED'] = 'true'

    print("\n--- Testing News Search with Enhanced Features ---")
    news_result = skill.execute({"query": "AI developments", "search_type": "news"})
    print(f"Success: {news_result.success}")
    if news_result.data and 'sources' in news_result.data:
        print(f"Total news sources: {news_result.data['total_results']}")
        if 'overallCredibility' in news_result.data:
            print(f"Overall credibility: {news_result.data['overallCredibility']}")

    print("\n=== Enhanced Web Search Testing Complete ===")
