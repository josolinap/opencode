"""
Credibility Telemetry Module for Web Search
Provides lightweight observability for credibility and recency enhancements.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Feature flag - must match web_search.py
WEBSEARCH_CREDIBILITY_ENABLED = os.getenv('WEBSEARCH_CREDIBILITY_ENABLED', 'true').lower() == 'true'

class CredibilityTelemetry:
    """
    Lightweight telemetry collector for web search credibility metrics.

    Only active when WEBSEARCH_CREDIBILITY_ENABLED is True.
    Emits JSON telemetry to logs for monitoring and canary rollouts.
    """

    # Credibility score buckets for distribution tracking
    CREDIBILITY_BUCKETS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    def __init__(self):
        self._telemetry_log = []
        self._max_log_size = 1000  # Keep last 1000 entries in memory

    def collect_search_metrics(self, query: str, search_type: str, sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Collect and emit telemetry for a web search operation.

        Args:
            query: The search query
            search_type: Type of search (general, news, etc.)
            sources: List of enhanced source objects with credibility data

        Returns:
            Telemetry data dict if enabled, None if disabled
        """
        if not WEBSEARCH_CREDIBILITY_ENABLED:
            return None

        start_time = time.time()

        try:
            # Basic counts
            total_sources_considered = len(sources)
            credible_sources = [s for s in sources if 'credibility' in s]
            credible_sources_count = len(credible_sources)

            # Credibility metrics
            average_credibility = 0.0
            credibility_distribution = [0] * (len(self.CREDIBILITY_BUCKETS) - 1)

            if credible_sources:
                credibility_scores = [s['credibility'] for s in credible_sources]
                average_credibility = sum(credibility_scores) / len(credibility_scores)

                # Build distribution buckets
                for score in credibility_scores:
                    for i, bucket_start in enumerate(self.CREDIBILITY_BUCKETS[:-1]):
                        bucket_end = self.CREDIBILITY_BUCKETS[i + 1]
                        if bucket_start <= score < bucket_end:
                            credibility_distribution[i] += 1
                            break
                    # Handle edge case for score == 1.0
                    if score == 1.0:
                        credibility_distribution[-1] += 1

            # Recency metrics
            recency_sources = [s for s in sources if 'recencyDays' in s]
            avg_recency_days = None
            if recency_sources:
                recency_days = [s['recencyDays'] for s in recency_sources]
                avg_recency_days = sum(recency_days) / len(recency_days)

            # Calculate latency
            latency_elapsed_ms = (time.time() - start_time) * 1000

            # Build telemetry payload
            telemetry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'web_search_credibility_metrics',
                'query': query,
                'search_type': search_type,
                'total_sources_considered': total_sources_considered,
                'credible_sources_count': credible_sources_count,
                'average_credibility': round(average_credibility, 3),
                'credibility_distribution': credibility_distribution,
                'avg_recency_days': round(avg_recency_days, 1) if avg_recency_days is not None else None,
                'latency_elapsed_ms': round(latency_elapsed_ms, 2),
                'feature_enabled': True
            }

            # Emit telemetry
            self._emit_telemetry(telemetry)

            logger.debug(f"Credibility telemetry collected: {total_sources_considered} sources, avg_credibility={average_credibility:.2f}")
            return telemetry

        except Exception as e:
            logger.warning(f"Failed to collect credibility telemetry: {e}")
            return None

    def _emit_telemetry(self, telemetry: Dict[str, Any]):
        """
        Emit telemetry to configured sinks.

        Currently supports:
        - In-memory log for testing/debugging
        - JSON log file for monitoring
        """
        # Add to in-memory log (for testing and debugging)
        self._telemetry_log.append(telemetry)
        if len(self._telemetry_log) > self._max_log_size:
            self._telemetry_log.pop(0)

        # Emit to JSON log file
        try:
            log_file = os.path.join(os.path.dirname(__file__), 'logs', 'credibility_telemetry.jsonl')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(telemetry) + '\n')

        except Exception as e:
            logger.warning(f"Failed to write telemetry to file: {e}")

    def get_recent_telemetry(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent telemetry entries for monitoring/debugging.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent telemetry entries (newest first)
        """
        return list(reversed(self._telemetry_log[-limit:]))

    def clear_telemetry_log(self):
        """Clear the in-memory telemetry log (for testing)"""
        self._telemetry_log.clear()

    @classmethod
    def get_bucket_labels(cls) -> List[str]:
        """
        Get human-readable labels for credibility distribution buckets.

        Returns:
            List of bucket range labels
        """
        labels = []
        for i, start in enumerate(cls.CREDIBILITY_BUCKETS[:-1]):
            end = cls.CREDIBILITY_BUCKETS[i + 1]
            labels.append(f"{start:.1f}-{end:.1f}")
        return labels


# Global telemetry instance
_telemetry = CredibilityTelemetry()

def collect_search_metrics(query: str, search_type: str, sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Convenience function to collect search metrics.

    Returns telemetry data if enabled, None if disabled.
    """
    return _telemetry.collect_search_metrics(query, search_type, sources)

def get_recent_telemetry(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent telemetry entries for monitoring."""
    return _telemetry.get_recent_telemetry(limit)

def clear_telemetry_log():
    """Clear telemetry log (for testing)."""
    _telemetry.clear_telemetry_log()


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Credibility Telemetry Module Test")
    print("=" * 50)

    # Test with feature enabled
    print("\n--- Testing with WEBSEARCH_CREDIBILITY_ENABLED=true ---")

    # Sample sources with credibility data
    test_sources = [
        {'url': 'https://wikipedia.org/test', 'title': 'Wiki Article', 'credibility': 0.9, 'recencyDays': 30},
        {'url': 'https://example.com/test', 'title': 'Regular Site', 'credibility': 0.5, 'recencyDays': 100},
        {'url': 'https://news.example.com/test', 'title': 'News Article', 'credibility': 0.7, 'recencyDays': 1},
        {'url': 'https://blog.example.com/test', 'title': 'Blog Post', 'credibility': 0.3},  # No recency
    ]

    telemetry = collect_search_metrics("test query", "general", test_sources)

    if telemetry:
        print("✅ Telemetry collected:")
        print(f"  Total sources: {telemetry['total_sources_considered']}")
        print(f"  Credible sources: {telemetry['credible_sources_count']}")
        print(".2f")
        print(f"  Credibility distribution: {telemetry['credibility_distribution']}")
        print(f"  Avg recency days: {telemetry['avg_recency_days']}")
        print(".1f")

        # Show bucket labels
        bucket_labels = CredibilityTelemetry.get_bucket_labels()
        print(f"  Distribution buckets: {bucket_labels}")
    else:
        print("❌ Telemetry not collected (feature disabled)")

    # Test with feature disabled
    print("\n--- Testing with WEBSEARCH_CREDIBILITY_ENABLED=false ---")
    os.environ['WEBSEARCH_CREDIBILITY_ENABLED'] = 'false'

    # Reimport to get new flag value
    import importlib
    import credibility_telemetry
    importlib.reload(credibility_telemetry)

    telemetry_disabled = credibility_telemetry.collect_search_metrics("test query", "general", test_sources)

    if telemetry_disabled is None:
        print("✅ Telemetry correctly disabled")
    else:
        print("❌ Telemetry should be disabled")

    # Reset
    os.environ['WEBSEARCH_CREDIBILITY_ENABLED'] = 'true'

    print("\n--- Recent Telemetry ---")
    recent = get_recent_telemetry(2)
    print(f"Recent entries: {len(recent)}")

    print("\n✅ Credibility Telemetry Module Test Complete")
