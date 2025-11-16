# Cross-Skill Credibility Standardization

## Overview

This document describes the implementation of shared credibility scoring utilities across Neo-Clone skills, providing consistent, governance-friendly credibility assessment for data sources and web content.

## Architecture

### Shared Utility: `credibility_scorer.py`

The `credibility_scorer.py` module provides a centralized credibility assessment system with the following components:

#### Main API
```python
from credibility_scorer import compute_source_credibility

# Simple usage
score = compute_source_credibility("https://wikipedia.org/article", "content here")

# Advanced usage with date info
score = compute_source_credibility(
    "https://example.com/page",
    "content with references",
    {"recency_days": 7}
)
```

#### CredibilityScorer Class
- **Domain-based scoring**: TLD reputation (.edu=0.9, .gov=0.9, .com=0.5, etc.)
- **High-credibility domains**: Known trustworthy sources (Wikipedia, GitHub, academic institutions)
- **Content quality analysis**: Positive indicators (citations, author attribution) and negative indicators (advertising, clickbait)
- **Recency bonuses**: Recent content gets credibility boosts
- **Feature flag control**: `CREDIBILITY_ENABLED` flag for safe rollout

## Scoring Algorithm

### Base Score (Domain Reputation)
```python
# High credibility domains override TLD scores
HIGH_CREDIBILITY_DOMAINS = {
    'wikipedia.org', 'github.com', 'stackoverflow.com',
    'arxiv.org', 'nature.com', 'science.org',
    'ieee.org', 'acm.org', 'mit.edu', 'stanford.edu',
    # ... and more
}

# TLD-based scoring
TLD_CREDIBILITY = {
    'edu': 0.9, 'gov': 0.9, 'org': 0.7, 'com': 0.5,
    'net': 0.4, 'io': 0.6, 'ai': 0.7, 'news': 0.6,
    # ... and more
}
```

### Content Quality Adjustments
```python
CONTENT_INDICATORS = {
    'positive': {
        'author:': 0.1, 'references': 0.1, 'citations': 0.1,
        'methodology': 0.1, 'abstract': 0.1, 'doi:': 0.1,
        # ... academic and quality indicators
    },
    'negative': {
        'buy now': -0.1, 'sponsored': -0.1, 'advertisement': -0.1,
        'click here': -0.1, 'limited time': -0.1,
        # ... commercial and low-quality indicators
    }
}
```

### Recency Bonuses
```python
def _compute_recency_bonus(recency_days: int) -> float:
    if recency_days <= 1: return 0.1    # Very recent
    elif recency_days <= 7: return 0.08  # This week
    elif recency_days <= 30: return 0.05 # This month
    elif recency_days <= 365: return 0.02 # This year
    else: return 0.0                      # Older
```

### Final Score Calculation
```python
final_score = base_score + content_adjustment + recency_bonus
final_score = max(0.0, min(1.0, final_score))  # Clamp to [0.0, 1.0]
```

## Credibility Score Ranges

| Range | Score | Description |
|-------|-------|-------------|
| Very High | 0.8-1.0 | Highly credible sources (academic, government, established news) |
| High | 0.6-0.8 | Generally trustworthy sources with good indicators |
| Moderate | 0.4-0.6 | Neutral credibility, typical commercial content |
| Low | 0.2-0.4 | Questionable sources, potential bias or low quality |
| Very Low | 0.0-0.2 | Unreliable sources, high risk of misinformation |

## Skill Integration Examples

### Web Search Skill (`web_search.py`)

```python
# Import shared utility
try:
    from credibility_scorer import compute_source_credibility as shared_compute_credibility
except ImportError:
    shared_compute_credibility = None

# Use in search results processing
if shared_compute_credibility:
    credibility = shared_compute_credibility(url, snippet, recency_info)
else:
    credibility = self.compute_source_credibility(url, snippet, recency_info)  # Fallback
```

### Data Inspector Skill (`data_inspector.py`)

```python
# Import shared utility
try:
    from credibility_scorer import compute_source_credibility
except ImportError:
    def compute_source_credibility(*args, **kwargs): return 0.5

# Analyze URLs found in data
def _analyze_data_credibility(self, rows, headers):
    # Extract URLs from text fields
    found_urls = []
    for row in rows:
        for header in headers:
            value = str(row.get(header, ''))
            # URL regex extraction...

    # Score each URL
    for url in found_urls:
        score = compute_source_credibility(url, context_around_url)
        # Store results...
```

## Feature Flag Control

### Environment Variable
```bash
# Enable credibility features
export CREDIBILITY_ENABLED=true

# Disable credibility features (rollback)
export CREDIBILITY_ENABLED=false
```

### Code-Level Control
```python
# In credibility_scorer.py
CREDIBILITY_ENABLED = True  # Default enabled

# Skills check this flag
if not CREDIBILITY_ENABLED:
    return 0.5  # Neutral fallback
```

## Rollout Strategy

### Phase 1: Canary Deployment
- Enable for 10% of users initially
- Monitor performance impact and credibility score distributions
- Validate that shared utility works across skills

### Phase 2: Limited Rollout
- Enable for 50% of users
- Monitor user satisfaction and search quality metrics
- Ensure backward compatibility

### Phase 3: Full Rollout
- Enable for 100% of users
- Continuous monitoring of credibility distributions
- Tune scoring heuristics based on real usage data

### Rollback Plan
```bash
# Immediate rollback if issues detected
export CREDIBILITY_ENABLED=false
# All skills automatically fall back to neutral scoring
```

## Testing Strategy

### Unit Tests (`tests/test_credibility_scorer.py`)
- **Range validation**: Scores always in [0.0, 1.0]
- **Deterministic scoring**: Same inputs produce same outputs
- **Domain scoring**: TLD and high-credibility domain logic
- **Content analysis**: Positive/negative indicator detection
- **Recency bonuses**: Date-based score adjustments
- **Error handling**: Graceful handling of invalid inputs
- **Feature flags**: Enable/disable behavior

### Integration Tests
- **Cross-skill usage**: Web search and data inspector integration
- **Backward compatibility**: Old behavior preserved when utility unavailable
- **Performance**: Minimal latency impact
- **Fallback behavior**: Graceful degradation

## Performance Considerations

### Latency Impact
- **Typical scoring time**: < 1ms per URL
- **Batch processing**: Efficient for multiple URLs
- **Caching**: Results can be cached at skill level
- **Feature flag**: Zero impact when disabled

### Memory Usage
- **Lightweight**: No large data structures
- **Static data**: Domain lists loaded once
- **No external dependencies**: Pure Python implementation

## Governance & Compliance

### Consistent Scoring
- **Single source of truth**: All skills use same scoring logic
- **Version control**: Changes to scoring affect all skills uniformly
- **Audit trail**: Centralized logic simplifies compliance reviews

### Transparency
- **Explainable scores**: Clear factors contribute to final score
- **Range documentation**: Well-defined credibility levels
- **Override capability**: Feature flags for emergency control

## Future Extensions

### Enhanced Scoring Factors
- **Social signals**: Citation counts, backlinks
- **Content analysis**: ML-based quality assessment
- **User feedback**: Reputation systems
- **Cross-referencing**: Fact-checking integration

### Additional Skills
- **Code search**: Repository credibility scoring
- **News aggregator**: Source reliability assessment
- **Research assistant**: Academic paper credibility
- **Content analyzer**: Multi-modal credibility assessment

## Migration Guide

### For Existing Skills
1. **Add import**: Import `compute_source_credibility` from `credibility_scorer`
2. **Replace local logic**: Use shared utility instead of custom scoring
3. **Add fallback**: Handle ImportError gracefully
4. **Test integration**: Ensure backward compatibility
5. **Update documentation**: Reference shared scoring system

### For New Skills
1. **Import utility**: Always use shared credibility scorer
2. **Follow patterns**: Consistent parameter handling
3. **Add feature flags**: Respect global enable/disable settings
4. **Document usage**: Explain credibility integration

## Monitoring & Observability

### Telemetry Integration
- **Credibility distributions**: Track score distributions across searches
- **Performance metrics**: Monitor scoring latency and success rates
- **Usage patterns**: Understand which skills use credibility scoring
- **Quality metrics**: Correlate credibility scores with user satisfaction

### Dashboards
- **Credibility trends**: Average scores over time
- **Source quality**: Distribution of high/low credibility sources
- **Performance impact**: Latency percentiles and error rates
- **Feature adoption**: Percentage of skills using shared utility

## Conclusion

The cross-skill credibility standardization provides a robust, consistent, and governable approach to credibility assessment across Neo-Clone skills. By centralizing scoring logic, we ensure:

- **Consistency**: Same scoring rules across all skills
- **Maintainability**: Single location for scoring updates
- **Governance**: Easier audits and compliance reviews
- **Performance**: Efficient, lightweight implementation
- **Safety**: Feature flags and graceful fallbacks

This foundation enables reliable credibility assessment while maintaining the flexibility to extend and improve scoring algorithms as new requirements emerge.
