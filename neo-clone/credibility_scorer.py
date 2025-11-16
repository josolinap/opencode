"""
Shared Credibility Scoring Utility for Neo-Clone Skills
Provides consistent, governance-friendly credibility assessment across all skills.
"""

import re
from typing import Dict, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Feature flag for credibility enhancements
CREDIBILITY_ENABLED = True  # Can be controlled via environment variable

class CredibilityScorer:
    """
    Centralized credibility scoring utility for Neo-Clone skills.

    Provides consistent credibility assessment based on:
    - Domain reputation (TLD-based scoring)
    - Known high-credibility domains
    - Content quality indicators
    - Publication recency bonuses
    """

    # Credibility scores by top-level domain
    TLD_CREDIBILITY: Dict[str, float] = {
        'edu': 0.9,      # Educational institutions
        'gov': 0.9,      # Government sites
        'org': 0.7,      # Non-profits (varies)
        'com': 0.5,      # Commercial (neutral)
        'net': 0.4,      # Network services
        'io': 0.6,       # Tech startups
        'ai': 0.7,       # AI-specific domains
        'news': 0.6,     # News aggregators
        'info': 0.4,     # Information sites
        'biz': 0.3,      # Business sites
    }

    # Known high-credibility domains (override TLD scores)
    HIGH_CREDIBILITY_DOMAINS: set = {
        'wikipedia.org', 'github.com', 'stackoverflow.com',
        'arxiv.org', 'nature.com', 'science.org',
        'ieee.org', 'acm.org', 'mit.edu', 'stanford.edu',
        'harvard.edu', 'berkeley.edu', 'ox.ac.uk', 'cam.ac.uk',
        'nih.gov', 'cdc.gov', 'who.int', 'un.org',
        'bbc.co.uk', 'reuters.com', 'ap.org', 'npr.org'
    }

    # Content quality indicators and their score adjustments
    CONTENT_INDICATORS = {
        'positive': {
            'author:': 0.1,      # Author attribution
            'by ': 0.1,          # Author byline
            'written by': 0.1,   # Author credit
            'contributor': 0.1,  # Contributor mention
            'references': 0.1,   # References section
            'citations': 0.1,    # Citations present
            'sources': 0.1,      # Sources mentioned
            'et al': 0.1,        # Academic citation style
            'abstract': 0.1,     # Academic abstract
            'methodology': 0.1,  # Research methodology
            'conclusion': 0.1,   # Research conclusion
            'doi:': 0.1,         # Digital object identifier
        },
        'negative': {
            'buy now': -0.1,     # Commercial intent
            'limited time': -0.1, # Urgency tactics
            'sponsored': -0.1,   # Sponsored content
            'advertisement': -0.1, # Advertising
            'click here': -0.1,  # Clickbait patterns
        }
    }

    @classmethod
    def compute_source_credibility(
        cls,
        url: str,
        content: Optional[str] = None,
        date_info: Optional[Union[Dict, str, datetime]] = None
    ) -> float:
        """
        Compute credibility score for a source (0.0-1.0).

        This is the main API for credibility assessment across Neo-Clone skills.

        Args:
            url: Source URL to evaluate
            content: Optional text content for quality analysis
            date_info: Optional date information (dict with 'recency_days', or date string, or datetime)

        Returns:
            Credibility score between 0.0 and 1.0

        Example:
            >>> score = CredibilityScorer.compute_source_credibility(
            ...     "https://wikipedia.org/article",
            ...     "This article has references and citations.",
            ...     {"recency_days": 30}
            ... )
            >>> print(f"Credibility: {score}")
            Credibility: 0.95
        """
        if not CREDIBILITY_ENABLED:
            return 0.5  # Neutral default when disabled

        try:
            # Extract domain from URL
            domain = cls._extract_domain(url)
            if not domain:
                return 0.5  # Neutral for invalid URLs

            # Base score from domain reputation
            base_score = cls._compute_domain_score(domain)

            # Content-based adjustments
            content_adjustment = 0.0
            if content:
                content_adjustment = cls._analyze_content_quality(content)

            # Recency bonus
            recency_bonus = 0.0
            if date_info is not None:
                recency_days = cls._extract_recency_days(date_info)
                if recency_days is not None:
                    recency_bonus = cls._compute_recency_bonus(recency_days)

            # Calculate final score
            final_score = base_score + content_adjustment + recency_bonus
            final_score = max(0.0, min(1.0, final_score))  # Clamp to [0.0, 1.0]

            logger.debug(
                f"Credibility score for {domain}: {final_score:.2f} "
                f"(base: {base_score:.2f}, content: {content_adjustment:.2f}, recency: {recency_bonus:.2f})"
            )

            return final_score

        except Exception as e:
            logger.warning(f"Error computing credibility for {url}: {e}")
            return 0.5  # Safe fallback

    @classmethod
    def _extract_domain(cls, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            if not url or not isinstance(url, str):
                return None

            from urllib.parse import urlparse
            parsed = urlparse(url)

            # Check if we got a valid netloc
            if not parsed.netloc:
                return None

            return parsed.netloc.lower()
        except Exception:
            return None

    @classmethod
    def _compute_domain_score(cls, domain: str) -> float:
        """Compute base credibility score from domain."""
        # Check for high-credibility domains first
        if any(hc_domain in domain for hc_domain in cls.HIGH_CREDIBILITY_DOMAINS):
            return 0.9

        # Fall back to TLD-based scoring
        tld = domain.split('.')[-1] if '.' in domain else ''
        return cls.TLD_CREDIBILITY.get(tld, 0.5)  # Default neutral

    @classmethod
    def _analyze_content_quality(cls, content: str) -> float:
        """Analyze content for quality indicators."""
        if not content:
            return 0.0

        content_lower = content.lower()
        adjustment = 0.0

        # Positive indicators
        for indicator, bonus in cls.CONTENT_INDICATORS['positive'].items():
            if indicator in content_lower:
                adjustment += bonus

        # Negative indicators
        for indicator, penalty in cls.CONTENT_INDICATORS['negative'].items():
            if indicator in content_lower:
                adjustment += penalty

        return adjustment

    @classmethod
    def _extract_recency_days(cls, date_info: Union[Dict, str, datetime]) -> Optional[int]:
        """Extract recency in days from various date formats."""
        try:
            if isinstance(date_info, dict):
                return date_info.get('recency_days')
            elif isinstance(date_info, str):
                # Try ISO format
                pub_date = datetime.fromisoformat(date_info.replace('Z', '+00:00'))
                days_since = (datetime.now() - pub_date).days
                return max(0, days_since)
            elif isinstance(date_info, datetime):
                days_since = (datetime.now() - date_info).days
                return max(0, days_since)
        except Exception:
            pass
        return None

    @classmethod
    def _compute_recency_bonus(cls, recency_days: int) -> float:
        """Compute recency bonus based on days since publication."""
        if recency_days <= 1:      # Very recent (today/yesterday)
            return 0.1
        elif recency_days <= 7:    # This week
            return 0.08
        elif recency_days <= 30:   # This month
            return 0.05
        elif recency_days <= 365:  # This year
            return 0.02
        else:                      # Older
            return 0.0

    @classmethod
    def get_credibility_ranges(cls) -> Dict[str, str]:
        """
        Get human-readable descriptions of credibility score ranges.

        Returns:
            Dict mapping range names to descriptions
        """
        return {
            'very_high': '0.8-1.0: Highly credible sources (academic, government, established news)',
            'high': '0.6-0.8: Generally trustworthy sources with good indicators',
            'moderate': '0.4-0.6: Neutral credibility, typical commercial content',
            'low': '0.2-0.4: Questionable sources, potential bias or low quality',
            'very_low': '0.0-0.2: Unreliable sources, high risk of misinformation'
        }


# Convenience function for easy importing
def compute_source_credibility(
    url: str,
    content: Optional[str] = None,
    date_info: Optional[Union[Dict, str, datetime]] = None
) -> float:
    """
    Compute credibility score for a source.

    This is the main API function that skills should import and use.

    Args:
        url: Source URL
        content: Optional content for quality analysis
        date_info: Optional date information

    Returns:
        Credibility score between 0.0 and 1.0
    """
    return CredibilityScorer.compute_source_credibility(url, content, date_info)


# Test and example usage
if __name__ == "__main__":
    print("🧪 Credibility Scorer Utility Test")
    print("=" * 50)

    # Test cases
    test_cases = [
        ("https://wikipedia.org/python", "Article with references and citations", {"recency_days": 30}),
        ("https://github.com/user/repo", "Open source repository", None),
        ("https://example.com/blog", "Buy now! Limited time offer sponsored content", {"recency_days": 1}),
        ("https://news.example.com/story", "Breaking news with author attribution", {"recency_days": 7}),
        ("https://randomsite.biz", "Unreliable content", None),
    ]

    print("\n--- Credibility Scoring Examples ---")
    for url, content, date_info in test_cases:
        score = compute_source_credibility(url, content, date_info)
        print("30")

    print("\n--- Credibility Ranges ---")
    ranges = CredibilityScorer.get_credibility_ranges()
    for range_name, description in ranges.items():
        print(f"{range_name}: {description}")

    print("\n✅ Credibility Scorer Utility Test Complete")
