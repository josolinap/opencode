"""
Credibility A/B Experimentation Framework for Neo-Clone
Provides safe experimentation with credibility scoring policies.
"""

import os
import hashlib
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import policy engine
try:
    from credibility_policy import (
        CredibilityPolicy,
        compute_source_credibility_with_policy,
        CREDIBILITY_POLICY_AB_TEST
    )
except ImportError:
    # Fallback if policy engine not available
    CREDIBILITY_POLICY_AB_TEST = False
    CredibilityPolicy = None
    compute_source_credibility_with_policy = None

# Import telemetry
try:
    from credibility_telemetry import collect_search_metrics
except ImportError:
    def collect_search_metrics(*args, **kwargs):
        return None

class ExperimentVariant:
    """Represents an experiment variant with its policy configuration."""

    def __init__(self, name: str, policy: CredibilityPolicy, weight: float = 1.0):
        """
        Initialize experiment variant.

        Args:
            name: Variant identifier (e.g., 'control', 'treatment_a')
            policy: CredibilityPolicy instance for this variant
            weight: Relative weight for random assignment (higher = more likely)
        """
        self.name = name
        self.policy = policy
        self.weight = weight

    def compute_credibility(self, url: str, content: Optional[str] = None,
                          date_info: Optional[Dict] = None) -> float:
        """Compute credibility score using this variant's policy."""
        return self.policy.compute_source_credibility(url, content, date_info)

    def get_metadata(self) -> Dict[str, Any]:
        """Get variant metadata for telemetry."""
        return {
            'variant_name': self.name,
            'policy_name': self.policy.policy['name'],
            'policy_version': self.policy.policy.get('version', 'unknown'),
            'weight': self.weight
        }


class CredibilityABTest:
    """
    A/B experimentation framework for credibility scoring policies.

    Supports multiple variants with configurable rollout percentages,
    automatic variant assignment, and telemetry collection.
    """

    def __init__(self, experiment_name: str = "credibility_policy_ab_test"):
        """
        Initialize A/B test framework.

        Args:
            experiment_name: Unique experiment identifier
        """
        self.experiment_name = experiment_name
        self.variants: Dict[str, ExperimentVariant] = {}
        self.rollout_percentage = int(os.getenv('CREDIBILITY_AB_ROLLOUT_PERCENTAGE', '10'))
        self._variant_weights: List[Tuple[str, float]] = []

        # Initialize default variants
        self._setup_default_variants()

        # Build weighted selection list
        self._build_weighted_selection()

    def _setup_default_variants(self):
        """Set up default A/B test variants."""
        if not CredibilityPolicy:
            logger.warning("CredibilityPolicy not available, cannot set up variants")
            return

        # Control variant (current default policy)
        control_policy = CredibilityPolicy()
        self.add_variant("control", control_policy, weight=1.0)

        # Treatment variant (experimental policy)
        treatment_policy = CredibilityPolicy(CredibilityPolicy.EXPERIMENTAL_POLICY_B)
        self.add_variant("treatment_a", treatment_policy, weight=1.0)

    def add_variant(self, name: str, policy: CredibilityPolicy, weight: float = 1.0):
        """
        Add an experiment variant.

        Args:
            name: Variant identifier
            policy: CredibilityPolicy for this variant
            weight: Relative selection weight
        """
        self.variants[name] = ExperimentVariant(name, policy, weight)
        self._build_weighted_selection()

    def _build_weighted_selection(self):
        """Build weighted list for random variant selection."""
        self._variant_weights = []
        for variant in self.variants.values():
            self._variant_weights.extend([variant.name] * int(variant.weight * 10))

    def should_run_experiment(self, user_id: Optional[str] = None) -> bool:
        """
        Determine if experiment should run for this request.

        Args:
            user_id: Optional user identifier for consistent assignment

        Returns:
            True if experiment should run, False otherwise
        """
        if not CREDIBILITY_POLICY_AB_TEST:
            return False

        # Check rollout percentage
        if user_id:
            # Use user_id for consistent assignment
            hash_value = int(hashlib.md5(f"{self.experiment_name}:{user_id}".encode()).hexdigest(), 16)
            user_percentage = (hash_value % 100) + 1
        else:
            # Random assignment for anonymous requests
            user_percentage = random.randint(1, 100)

        return user_percentage <= self.rollout_percentage

    def assign_variant(self, user_id: Optional[str] = None) -> ExperimentVariant:
        """
        Assign experiment variant for this request.

        Args:
            user_id: Optional user identifier for consistent assignment

        Returns:
            Assigned ExperimentVariant
        """
        if not self._variant_weights:
            # Fallback to control if no variants configured
            return self.variants.get("control", list(self.variants.values())[0])

        if user_id:
            # Consistent assignment based on user_id
            hash_value = int(hashlib.md5(f"{self.experiment_name}:{user_id}:variant".encode()).hexdigest(), 16)
            variant_index = hash_value % len(self._variant_weights)
            variant_name = self._variant_weights[variant_index]
        else:
            # Random assignment
            variant_name = random.choice(self._variant_weights)

        return self.variants[variant_name]

    def compute_credibility_with_experiment(
        self,
        url: str,
        content: Optional[str] = None,
        date_info: Optional[Dict] = None,
        user_id: Optional[str] = None,
        collect_telemetry: bool = True
    ) -> Tuple[float, Optional[Dict[str, Any]]]:
        """
        Compute credibility score with experiment assignment and telemetry.

        Args:
            url: Source URL to evaluate
            content: Optional content for analysis
            date_info: Optional date information
            user_id: Optional user identifier for consistent variant assignment
            collect_telemetry: Whether to collect experiment telemetry

        Returns:
            Tuple of (credibility_score, experiment_metadata)
            experiment_metadata is None if experiment not run
        """
        if not self.should_run_experiment(user_id):
            # No experiment - use default policy
            if compute_source_credibility_with_policy:
                score = compute_source_credibility_with_policy(url, content, date_info)
            else:
                score = 0.5  # Neutral fallback
            return score, None

        # Run experiment
        variant = self.assign_variant(user_id)
        start_time = time.time()

        try:
            # Compute score with assigned variant
            score = variant.compute_credibility(url, content, date_info)
            latency = time.time() - start_time

            # Prepare experiment metadata with consistent snake_case naming
            experiment_metadata = {
                'experiment_name': self.experiment_name,
                'variant_name': variant.name,
                'policy_name': variant.policy.policy['name'],
                'policy_version': variant.policy.policy.get('version', 'unknown'),
                'latency_ms': round(latency * 1000, 2),
                'timestamp': datetime.now().isoformat(),
                'rollout_percentage': self.rollout_percentage,
                'credibility_score': round(score, 3),
                'url_domain_hash': self._hash_domain(url),  # Privacy: hash instead of raw domain
                'has_content': bool(content),
                'has_date_info': bool(date_info),
                'user_id_hash': self._hash_user_id(user_id) if user_id else None  # Privacy: hash user_id
            }

            # Collect telemetry if enabled
            if collect_telemetry and collect_search_metrics:
                # Create mock search metrics for experiment telemetry
                experiment_telemetry = {
                    'event_type': 'credibility_experiment_metrics',
                    'experiment_name': self.experiment_name,
                    'variant_name': variant.name,
                    'policy_name': variant.policy.policy['name'],
                    'latency_elapsed_ms': latency * 1000,
                    'credibility_score': score,
                    'url_domain': self._extract_domain(url),
                    'has_content': bool(content),
                    'has_date_info': bool(date_info),
                    'timestamp': datetime.now().isoformat()
                }

                # Use existing telemetry infrastructure
                collect_search_metrics("experiment_test", "experiment", [])

            return score, experiment_metadata

        except Exception as e:
            logger.warning(f"Experiment computation failed: {e}")
            # Fallback to default
            if compute_source_credibility_with_policy:
                score = compute_source_credibility_with_policy(url, content, date_info)
            else:
                score = 0.5
            return score, None

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL for telemetry."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower() if parsed.netloc else None
        except Exception:
            return None

    def _hash_domain(self, url: str) -> Optional[str]:
        """Create privacy-safe hash of domain for telemetry."""
        domain = self._extract_domain(url)
        if domain:
            # Use SHA256 for privacy-safe hashing
            return hashlib.sha256(f"domain:{domain}".encode()).hexdigest()[:16]
        return None

    def _hash_user_id(self, user_id: str) -> str:
        """Create privacy-safe hash of user ID for telemetry."""
        return hashlib.sha256(f"user:{user_id}".encode()).hexdigest()[:16]

    def get_experiment_stats(self) -> Dict[str, Any]:
        """Get experiment statistics and configuration."""
        variant_stats = {}
        for name, variant in self.variants.items():
            variant_stats[name] = {
                'policy_name': variant.policy.policy['name'],
                'weight': variant.weight,
                'policy_info': variant.policy.get_policy_info()
            }

        return {
            'experiment_name': self.experiment_name,
            'enabled': CREDIBILITY_POLICY_AB_TEST,
            'rollout_percentage': self.rollout_percentage,
            'variants': variant_stats,
            'total_variants': len(self.variants)
        }


# Global experiment instance
_experiment_instance: Optional[CredibilityABTest] = None

def get_experiment_instance() -> CredibilityABTest:
    """Get or create global experiment instance."""
    global _experiment_instance
    if _experiment_instance is None:
        _experiment_instance = CredibilityABTest()
    return _experiment_instance

def compute_credibility_with_ab_test(
    url: str,
    content: Optional[str] = None,
    date_info: Optional[Dict] = None,
    user_id: Optional[str] = None
) -> float:
    """
    Compute credibility score with A/B experimentation.

    This is the main API that skills should use when A/B testing is enabled.

    Args:
        url: Source URL
        content: Optional content for analysis
        date_info: Optional date information
        user_id: Optional user identifier for consistent variant assignment

    Returns:
        Credibility score between 0.0 and 1.0
    """
    experiment = get_experiment_instance()
    score, _ = experiment.compute_credibility_with_experiment(
        url, content, date_info, user_id
    )
    return score


# Test and example usage
if __name__ == "__main__":
    print("🧪 Credibility A/B Experimentation Framework Test")
    print("=" * 60)

    # Test experiment setup
    print("\n1️⃣ Experiment Setup Test")
    experiment = CredibilityABTest()
    stats = experiment.get_experiment_stats()
    print(f"Experiment: {stats['experiment_name']}")
    print(f"Enabled: {stats['enabled']}")
    print(f"Rollout: {stats['rollout_percentage']}%")
    print(f"Variants: {list(stats['variants'].keys())}")

    # Test variant assignment
    print("\n2️⃣ Variant Assignment Test")
    test_user_ids = ["user_1", "user_2", "user_3", "user_4", "user_5"]

    for user_id in test_user_ids:
        should_run = experiment.should_run_experiment(user_id)
        if should_run:
            variant = experiment.assign_variant(user_id)
            print(f"User {user_id}: {variant.name} ({variant.policy.policy['name']})")
        else:
            print(f"User {user_id}: No experiment (outside rollout)")

    # Test credibility computation with experiment
    print("\n3️⃣ Credibility Computation with Experiment")
    test_cases = [
        ("https://wikipedia.org/test", "Academic content with references"),
        ("https://github.com/user/repo", "Open source repository"),
        ("https://example.com/blog", "Buy now! Limited time offer"),
    ]

    for url, content in test_cases:
        score, metadata = experiment.compute_credibility_with_experiment(
            url, content, {"recency_days": 7}, "test_user"
        )
        if metadata:
            print("30")
        else:
            print("30")

    # Test experiment statistics
    print("\n4️⃣ Experiment Statistics")
    stats = experiment.get_experiment_stats()
    print(f"Total variants configured: {stats['total_variants']}")

    for variant_name, variant_info in stats['variants'].items():
        print(f"  {variant_name}: {variant_info['policy_name']}")

    print("\n✅ Credibility A/B Experimentation Framework Test Complete")
