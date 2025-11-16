"""
Credibility Policy Engine for Neo-Clone
Provides configurable credibility scoring policies with A/B experimentation support.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Feature flags
CREDIBILITY_POLICY_ENABLED = os.getenv('CREDIBILITY_POLICY_ENABLED', 'true').lower() == 'true'
CREDIBILITY_POLICY_AB_TEST = os.getenv('CREDIBILITY_POLICY_AB_TEST', 'false').lower() == 'true'

class CredibilityPolicy:
    """
    Configurable credibility scoring policy engine.

    Allows tuning of credibility scoring weights and parameters through configuration,
    with support for A/B experimentation and safe rollbacks.
    """

    # Default policy configuration (conservative, production-safe)
    DEFAULT_POLICY = {
        'name': 'default_v1',
        'description': 'Conservative credibility scoring with balanced weights',
        'weights': {
            'domain_base_weight': 0.7,      # Weight for domain reputation (0.0-1.0)
            'content_bonus_weight': 0.2,    # Weight for content quality bonuses (0.0-1.0)
            'recency_bonus_weight': 0.1,    # Weight for recency bonuses (0.0-1.0)
            'tld_credibility': {            # TLD reputation scores
                'edu': 0.9, 'gov': 0.9, 'org': 0.7, 'com': 0.5,
                'net': 0.4, 'io': 0.6, 'ai': 0.7, 'news': 0.6,
                'info': 0.4, 'biz': 0.3, 'dev': 0.5, 'app': 0.4,
                'blog': 0.3, 'site': 0.3, 'online': 0.3, 'web': 0.3
            },
            'high_credibility_domains': [   # Domains that override TLD scores
                'wikipedia.org', 'github.com', 'stackoverflow.com',
                'arxiv.org', 'nature.com', 'science.org',
                'ieee.org', 'acm.org', 'mit.edu', 'stanford.edu',
                'harvard.edu', 'berkeley.edu', 'ox.ac.uk', 'cam.ac.uk',
                'nih.gov', 'cdc.gov', 'who.int', 'un.org',
                'bbc.co.uk', 'reuters.com', 'ap.org', 'npr.org',
                'nytimes.com', 'washingtonpost.com', 'wsj.com'
            ],
            'content_indicators': {
                'positive': {
                    'author:': 0.1, 'by ': 0.1, 'written by': 0.1,
                    'contributor': 0.1, 'references': 0.1, 'citations': 0.1,
                    'sources': 0.1, 'et al': 0.1, 'abstract': 0.1,
                    'methodology': 0.1, 'conclusion': 0.1, 'doi:': 0.1,
                    'peer reviewed': 0.1, 'published in': 0.1
                },
                'negative': {
                    'buy now': -0.1, 'limited time': -0.1, 'sponsored': -0.1,
                    'advertisement': -0.1, 'click here': -0.1, 'subscribe now': -0.1,
                    'free trial': -0.1, 'special offer': -0.1, 'breaking news': -0.05
                }
            },
            'recency_bonuses': {
                'very_recent_days': 1, 'very_recent_bonus': 0.1,
                'recent_days': 7, 'recent_bonus': 0.08,
                'month_days': 30, 'month_bonus': 0.05,
                'year_days': 365, 'year_bonus': 0.02
            }
        },
        'version': '1.0.0',
        'created_at': '2025-11-16T00:00:00Z'
    }

    # Experimental policy B (more aggressive scoring)
    EXPERIMENTAL_POLICY_B = {
        'name': 'experimental_v1',
        'description': 'More aggressive credibility scoring with enhanced content analysis',
        'weights': {
            'domain_base_weight': 0.6,      # Slightly lower domain weight
            'content_bonus_weight': 0.3,    # Higher content weight
            'recency_bonus_weight': 0.1,    # Same recency weight
            'tld_credibility': {            # More nuanced TLD scoring
                'edu': 0.95, 'gov': 0.95, 'org': 0.8, 'com': 0.4,
                'net': 0.35, 'io': 0.7, 'ai': 0.8, 'news': 0.7,
                'info': 0.45, 'biz': 0.25, 'dev': 0.6, 'app': 0.5,
                'blog': 0.35, 'site': 0.35, 'online': 0.35, 'web': 0.35
            },
            'high_credibility_domains': [   # Expanded list
                'wikipedia.org', 'github.com', 'stackoverflow.com',
                'arxiv.org', 'nature.com', 'science.org', 'sciencedirect.com',
                'ieee.org', 'acm.org', 'mit.edu', 'stanford.edu', 'harvard.edu',
                'berkeley.edu', 'ox.ac.uk', 'cam.ac.uk', 'imperial.ac.uk',
                'nih.gov', 'cdc.gov', 'who.int', 'un.org', 'worldbank.org',
                'bbc.co.uk', 'reuters.com', 'ap.org', 'npr.org', 'cnn.com',
                'nytimes.com', 'washingtonpost.com', 'wsj.com', 'economist.com'
            ],
            'content_indicators': {
                'positive': {
                    'author:': 0.12, 'by ': 0.12, 'written by': 0.12,
                    'contributor': 0.12, 'references': 0.12, 'citations': 0.12,
                    'sources': 0.12, 'et al': 0.12, 'abstract': 0.12,
                    'methodology': 0.12, 'conclusion': 0.12, 'doi:': 0.15,
                    'peer reviewed': 0.15, 'published in': 0.12,
                    'research shows': 0.08, 'study finds': 0.08,
                    'according to': 0.06, 'experts say': 0.06
                },
                'negative': {
                    'buy now': -0.12, 'limited time': -0.12, 'sponsored': -0.12,
                    'advertisement': -0.12, 'click here': -0.12, 'subscribe now': -0.12,
                    'free trial': -0.12, 'special offer': -0.12, 'breaking news': -0.08,
                    'viral': -0.06, 'trending': -0.04, 'hot take': -0.08
                }
            },
            'recency_bonuses': {
                'very_recent_days': 1, 'very_recent_bonus': 0.12,
                'recent_days': 7, 'recent_bonus': 0.09,
                'month_days': 30, 'month_bonus': 0.06,
                'year_days': 365, 'year_bonus': 0.03
            }
        },
        'version': '1.0.0-experimental',
        'created_at': '2025-11-16T00:00:00Z'
    }

    def __init__(self, policy_config: Optional[Dict[str, Any]] = None):
        """
        Initialize credibility policy with configuration.

        Args:
            policy_config: Policy configuration dict, uses DEFAULT_POLICY if None
        """
        self.policy = policy_config or self.DEFAULT_POLICY.copy()
        self._validate_policy()

    def _validate_policy(self):
        """Validate policy configuration structure."""
        required_keys = ['name', 'weights']
        for key in required_keys:
            if key not in self.policy:
                raise ValueError(f"Policy missing required key: {key}")

        weights = self.policy['weights']
        required_weights = ['domain_base_weight', 'content_bonus_weight', 'recency_bonus_weight']
        for weight in required_weights:
            if weight not in weights:
                raise ValueError(f"Policy weights missing required key: {weight}")

        # Validate weight ranges
        total_weight = (
            weights['domain_base_weight'] +
            weights['content_bonus_weight'] +
            weights['recency_bonus_weight']
        )
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point variance
            logger.warning(f"Policy weights don't sum to 1.0: {total_weight}")

    @classmethod
    def load_policy_from_config(cls, config_path: Optional[str] = None) -> 'CredibilityPolicy':
        """
        Load policy from configuration file or environment.

        Args:
            config_path: Path to JSON config file, or None to use defaults

        Returns:
            CredibilityPolicy instance
        """
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded credibility policy from {config_path}")
                return cls(config)
            except Exception as e:
                logger.warning(f"Failed to load policy from {config_path}: {e}")

        # Try environment variable
        env_config = os.getenv('CREDIBILITY_POLICY_CONFIG')
        if env_config:
            try:
                config = json.loads(env_config)
                logger.info("Loaded credibility policy from environment")
                return cls(config)
            except Exception as e:
                logger.warning(f"Failed to load policy from environment: {e}")

        # Fallback to default
        logger.info("Using default credibility policy")
        return cls()

    def compute_source_credibility(
        self,
        url: str,
        content: Optional[str] = None,
        date_info: Optional[Union[Dict, str, datetime]] = None
    ) -> float:
        """
        Compute credibility score using policy configuration.

        This is the main API that applies the policy's weights and rules.

        Args:
            url: Source URL to evaluate
            content: Optional text content for quality analysis
            date_info: Optional date information

        Returns:
            Credibility score between 0.0 and 1.0
        """
        if not CREDIBILITY_POLICY_ENABLED:
            return 0.5  # Neutral default when disabled

        try:
            # Extract domain
            domain = self._extract_domain(url)
            if not domain:
                return 0.5

            # Calculate components using policy weights
            domain_score = self._compute_domain_score(domain)
            content_adjustment = self._compute_content_adjustment(content or "")
            recency_bonus = self._compute_recency_bonus(date_info)

            # Apply weights - but high credibility domains get full score
            weights = self.policy['weights']
            if domain_score >= 0.9:  # High credibility domain
                final_score = domain_score  # No weighting for high credibility domains
            else:
                final_score = (
                    domain_score * weights['domain_base_weight'] +
                    content_adjustment * weights['content_bonus_weight'] +
                    recency_bonus * weights['recency_bonus_weight']
                )

            # Clamp to valid range
            final_score = max(0.0, min(1.0, final_score))

            logger.debug(
                f"Policy '{self.policy['name']}' scored {domain}: {final_score:.2f} "
                f"(domain: {domain_score:.2f}, content: {content_adjustment:.2f}, recency: {recency_bonus:.2f})"
            )

            return final_score

        except Exception as e:
            logger.warning(f"Policy credibility computation failed for {url}: {e}")
            return 0.5

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            if not url or not isinstance(url, str):
                return None
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower() if parsed.netloc else None
        except Exception:
            return None

    def _compute_domain_score(self, domain: str) -> float:
        """Compute domain reputation score using policy."""
        weights = self.policy['weights']

        # Check high credibility domains first
        if any(hc_domain in domain for hc_domain in weights['high_credibility_domains']):
            return 0.9

        # Fall back to TLD scoring
        tld = domain.split('.')[-1] if '.' in domain else ''
        return weights['tld_credibility'].get(tld, 0.5)

    def _compute_content_adjustment(self, content: str) -> float:
        """Compute content quality adjustment using policy."""
        if not content:
            return 0.0

        weights = self.policy['weights']['content_indicators']
        content_lower = content.lower()
        adjustment = 0.0

        # Positive indicators
        for indicator, bonus in weights['positive'].items():
            if indicator in content_lower:
                adjustment += bonus

        # Negative indicators
        for indicator, penalty in weights['negative'].items():
            if indicator in content_lower:
                adjustment += penalty

        return adjustment

    def _compute_recency_bonus(self, date_info: Optional[Union[Dict, str, datetime]]) -> float:
        """Compute recency bonus using policy."""
        if not date_info:
            return 0.0

        try:
            # Extract days since publication
            recency_days = self._extract_recency_days(date_info)
            if recency_days is None:
                return 0.0

            # Apply policy bonuses
            bonuses = self.policy['weights']['recency_bonuses']
            if recency_days <= bonuses['very_recent_days']:
                return bonuses['very_recent_bonus']
            elif recency_days <= bonuses['recent_days']:
                return bonuses['recent_bonus']
            elif recency_days <= bonuses['month_days']:
                return bonuses['month_bonus']
            elif recency_days <= bonuses['year_days']:
                return bonuses['year_bonus']
            else:
                return 0.0

        except Exception:
            return 0.0

    def _extract_recency_days(self, date_info: Union[Dict, str, datetime]) -> Optional[int]:
        """Extract recency in days from date info."""
        try:
            if isinstance(date_info, dict):
                return date_info.get('recency_days')
            elif isinstance(date_info, str):
                pub_date = datetime.fromisoformat(date_info.replace('Z', '+00:00'))
                return (datetime.now() - pub_date).days
            elif isinstance(date_info, datetime):
                return (datetime.now() - date_info).days
        except Exception:
            pass
        return None

    def get_policy_info(self) -> Dict[str, Any]:
        """Get policy metadata for telemetry and debugging."""
        return {
            'name': self.policy['name'],
            'version': self.policy.get('version', 'unknown'),
            'description': self.policy.get('description', ''),
            'weights_summary': {
                'domain_weight': self.policy['weights']['domain_base_weight'],
                'content_weight': self.policy['weights']['content_bonus_weight'],
                'recency_weight': self.policy['weights']['recency_bonus_weight']
            }
        }


# Global policy instance (lazy loaded)
_policy_instance: Optional[CredibilityPolicy] = None

def get_policy_instance() -> CredibilityPolicy:
    """Get or create global policy instance."""
    global _policy_instance
    if _policy_instance is None:
        _policy_instance = CredibilityPolicy.load_policy_from_config()
    return _policy_instance

def compute_source_credibility_with_policy(
    url: str,
    content: Optional[str] = None,
    date_info: Optional[Union[Dict, str, datetime]] = None
) -> float:
    """
    Compute credibility score using the active policy.

    This is the main API function that skills should use when policy
    experimentation is enabled.

    Args:
        url: Source URL
        content: Optional content for quality analysis
        date_info: Optional date information

    Returns:
        Credibility score between 0.0 and 1.0
    """
    policy = get_policy_instance()
    return policy.compute_source_credibility(url, content, date_info)


# Test and example usage
if __name__ == "__main__":
    print("🧪 Credibility Policy Engine Test")
    print("=" * 50)

    # Test default policy
    print("\n1️⃣ Default Policy Test")
    policy = CredibilityPolicy()
    test_cases = [
        ("https://wikipedia.org/test", "Academic content with references"),
        ("https://github.com/user/repo", "Open source repository"),
        ("https://example.com/blog", "Buy now! Limited time offer"),
        ("https://bbc.co.uk/news", "Breaking news story"),
    ]

    for url, content in test_cases:
        score = policy.compute_source_credibility(url, content, {"recency_days": 7})
        print("30")

    # Test experimental policy
    print("\n2️⃣ Experimental Policy B Test")
    exp_policy = CredibilityPolicy(CredibilityPolicy.EXPERIMENTAL_POLICY_B)

    for url, content in test_cases:
        score = exp_policy.compute_source_credibility(url, content, {"recency_days": 7})
        print("30")

    # Test policy loading
    print("\n3️⃣ Policy Loading Test")
    loaded_policy = CredibilityPolicy.load_policy_from_config()
    print(f"Loaded policy: {loaded_policy.policy['name']}")
    print(f"Version: {loaded_policy.policy.get('version', 'unknown')}")

    print("\n✅ Credibility Policy Engine Test Complete")
