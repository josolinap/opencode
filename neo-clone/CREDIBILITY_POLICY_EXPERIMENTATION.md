# Credibility Policy & A/B Experimentation Framework

## Overview

This document describes the Credibility Policy Engine and A/B Experimentation Framework for Neo-Clone, providing configurable credibility scoring policies with safe experimentation capabilities for data-driven evolution.

## Architecture

### Policy Engine (`credibility_policy.py`)

The policy engine provides configurable credibility scoring with tunable weights and parameters:

#### Core Components

- **CredibilityPolicy**: Main policy class with configurable weights
- **Policy Loading**: Support for JSON config files and environment variables
- **Feature Flags**: Safe enable/disable with `CREDIBILITY_POLICY_ENABLED`
- **Validation**: Policy configuration validation and error handling

#### Policy Configuration Structure

```json
{
  "name": "default_v1",
  "description": "Conservative credibility scoring with balanced weights",
  "weights": {
    "domain_base_weight": 0.7,
    "content_bonus_weight": 0.2,
    "recency_bonus_weight": 0.1,
    "tld_credibility": {
      "edu": 0.9,
      "gov": 0.9,
      "org": 0.7,
      "com": 0.5
    },
    "high_credibility_domains": ["wikipedia.org", "github.com", "stackoverflow.com"],
    "content_indicators": {
      "positive": {
        "author:": 0.1,
        "references": 0.1,
        "citations": 0.1
      },
      "negative": {
        "buy now": -0.1,
        "sponsored": -0.1,
        "advertisement": -0.1
      }
    },
    "recency_bonuses": {
      "very_recent_days": 1,
      "very_recent_bonus": 0.1,
      "recent_days": 7,
      "recent_bonus": 0.08
    }
  }
}
```

### A/B Experimentation Framework (`credibility_ab_test.py`)

The experimentation framework provides safe A/B testing with variant assignment and telemetry:

#### Core Components

- **CredibilityABTest**: Main experimentation class
- **ExperimentVariant**: Represents policy variants with weights
- **Variant Assignment**: Consistent user-based assignment with rollout control
- **Telemetry Integration**: Automatic metrics collection for experiments

#### Experiment Configuration

```python
experiment = CredibilityABTest("credibility_policy_ab_test")
experiment.add_variant("control", default_policy, weight=1.0)
experiment.add_variant("treatment_a", experimental_policy, weight=1.0)
```

## Policy Configuration

### Loading Policies

#### From JSON File

```python
# Load from config file
policy = CredibilityPolicy.load_policy_from_config("path/to/policy.json")
```

#### From Environment Variable

```bash
export CREDIBILITY_POLICY_CONFIG='{"name": "env_policy", "weights": {...}}'
```

#### Programmatic Configuration

```python
custom_policy = {
    'name': 'custom_v1',
    'weights': {
        'domain_base_weight': 0.8,
        'content_bonus_weight': 0.1,
        'recency_bonus_weight': 0.1,
        # ... other weights
    }
}
policy = CredibilityPolicy(custom_policy)
```

### Policy Weights Explanation

#### Component Weights (Must Sum to 1.0)

- **domain_base_weight**: Weight for domain reputation scoring (0.0-1.0)
- **content_bonus_weight**: Weight for content quality adjustments (0.0-1.0)
- **recency_bonus_weight**: Weight for publication recency bonuses (0.0-1.0)

#### Domain Scoring

- **tld_credibility**: Reputation scores by top-level domain
- **high_credibility_domains**: Domains that override TLD scores (always 0.9)

#### Content Analysis

- **positive indicators**: Keywords that increase credibility
- **negative indicators**: Keywords that decrease credibility

#### Recency Bonuses

- **very_recent_days/bonus**: Days/bonus for very recent content
- **recent_days/bonus**: Days/bonus for recent content
- **month_days/bonus**: Days/bonus for this month
- **year_days/bonus**: Days/bonus for this year

## A/B Experimentation

### Setting Up Experiments

#### Basic Experiment Setup

```python
from credibility_ab_test import CredibilityABTest

# Create experiment with default variants
experiment = CredibilityABTest("my_experiment")

# Add custom variants
experiment.add_variant("variant_b", custom_policy, weight=2.0)  # Higher weight
```

#### Environment Configuration

```bash
# Enable A/B testing
export CREDIBILITY_POLICY_AB_TEST=true

# Set rollout percentage (default: 10%)
export CREDIBILITY_AB_ROLLOUT_PERCENTAGE=25
```

### Variant Assignment

#### Consistent User Assignment

```python
# Same user always gets same variant
variant1 = experiment.assign_variant("user123")
variant2 = experiment.assign_variant("user123")
assert variant1.name == variant2.name  # Consistent
```

#### Rollout Control

```python
# Check if user should participate
if experiment.should_run_experiment("user123"):
    variant = experiment.assign_variant("user123")
    score = variant.compute_credibility(url, content, date_info)
else:
    # Use default policy
    score = default_policy.compute_source_credibility(url, content, date_info)
```

### Experiment Telemetry

#### Automatic Telemetry Collection

```python
# Experiment automatically collects telemetry
score, metadata = experiment.compute_credibility_with_experiment(
    url, content, date_info, user_id="user123"
)

if metadata:
    print(f"Variant: {metadata['variant_name']}")
    print(f"Latency: {metadata['latency_ms']}ms")
    print(f"Policy: {metadata['policy_name']}")
```

#### Telemetry Data Structure

```json
{
  "event_type": "credibility_experiment_metrics",
  "experiment_name": "credibility_policy_ab_test",
  "variant_name": "treatment_a",
  "policy_name": "experimental_v1",
  "latency_elapsed_ms": 2.34,
  "credibility_score": 0.85,
  "url_domain": "example.com",
  "has_content": true,
  "has_date_info": true,
  "timestamp": "2025-11-16T15:30:00Z"
}
```

## Usage Examples

### Basic Policy Usage

```python
from credibility_policy import compute_source_credibility_with_policy

# Use active policy
score = compute_source_credibility_with_policy(
    "https://wikipedia.org/article",
    "Academic content with references",
    {"recency_days": 7}
)
```

### Experiment Integration

```python
from credibility_ab_test import compute_credibility_with_ab_test

# Automatic experiment handling
score = compute_credibility_with_ab_test(
    "https://example.com/page",
    "Content here",
    {"recency_days": 30},
    user_id="user123"  # For consistent variant assignment
)
```

### Advanced Experiment Control

```python
experiment = get_experiment_instance()

# Check experiment participation
if experiment.should_run_experiment("user123"):
    # Run experiment with telemetry
    score, metadata = experiment.compute_credibility_with_experiment(
        url, content, date_info, "user123"
    )

    # Log experiment metadata
    if metadata:
        logger.info(f"Experiment: {metadata['experiment_name']}, "
                   f"Variant: {metadata['variant_name']}")
else:
    # Use standard policy
    score = compute_source_credibility_with_policy(url, content, date_info)
```

## Rollout Strategy

### Phase 1: Policy Testing (Development)

```bash
# Test policies locally without experiments
export CREDIBILITY_POLICY_ENABLED=true
export CREDIBILITY_POLICY_AB_TEST=false

# Load custom policy for testing
export CREDIBILITY_POLICY_CONFIG='{...}'
```

### Phase 2: Controlled Experiment (Staging)

```bash
# Enable experiments with low rollout
export CREDIBILITY_POLICY_AB_TEST=true
export CREDIBILITY_AB_ROLLOUT_PERCENTAGE=10

# Monitor telemetry for 1-2 days
```

### Phase 3: Gradual Rollout (Production)

```bash
# Increase rollout percentage gradually
export CREDIBILITY_AB_ROLLOUT_PERCENTAGE=25  # Week 1
export CREDIBILITY_AB_ROLLOUT_PERCENTAGE=50  # Week 2
export CREDIBILITY_AB_ROLLOUT_PERCENTAGE=100 # Week 3
```

### Phase 4: Policy Promotion (Post-Experiment)

```bash
# Disable experiments
export CREDIBILITY_POLICY_AB_TEST=false

# Update default policy based on experiment results
# Deploy new default policy configuration
```

### Rollback Plan

```bash
# Immediate rollback to safe state
export CREDIBILITY_POLICY_ENABLED=false
export CREDIBILITY_POLICY_AB_TEST=false

# All credibility scoring falls back to neutral (0.5)
# No behavioral changes, maintains system stability
```

## Monitoring & Analytics

### Experiment Metrics

#### Key Performance Indicators

- **Credibility Score Distribution**: Average scores by variant
- **Latency Impact**: Performance overhead of different policies
- **User Experience**: Correlation with user satisfaction metrics
- **Conversion Rates**: Impact on downstream user actions

#### Telemetry Queries

```sql
-- Average credibility by variant
SELECT variant_name, AVG(credibility_score) as avg_score
FROM credibility_experiment_metrics
GROUP BY variant_name;

-- Latency comparison
SELECT variant_name, AVG(latency_elapsed_ms) as avg_latency
FROM credibility_experiment_metrics
GROUP BY variant_name;

-- Daily experiment participation
SELECT DATE(timestamp) as day, COUNT(*) as experiments
FROM credibility_experiment_metrics
GROUP BY DATE(timestamp);
```

### Policy Performance Monitoring

#### Dashboard Metrics

- **Policy Usage**: Which policies are active and their performance
- **Error Rates**: Policy computation failures by variant
- **Score Ranges**: Distribution of credibility scores over time
- **A/B Balance**: Ensuring proper variant distribution

## Governance & Compliance

### Policy Version Control

```json
{
  "name": "default_v2",
  "version": "2.0.0",
  "created_at": "2025-11-16T00:00:00Z",
  "approved_by": "credibility_review_board",
  "change_log": [
    "Increased content analysis weight from 0.2 to 0.3",
    "Added new high-credibility domains",
    "Enhanced recency bonus for very recent content"
  ]
}
```

### Experiment Documentation

- **Hypothesis**: What the experiment aims to test
- **Variants**: Clear description of each policy variant
- **Success Metrics**: How to measure experiment success
- **Duration**: Planned experiment timeline
- **Rollback Criteria**: When to abort the experiment

### Audit Trail

- **Policy Changes**: Version history with approval records
- **Experiment Results**: Complete telemetry data retention
- **Decision Records**: Rationale for policy updates
- **Impact Analysis**: Before/after performance comparisons

## Best Practices

### Policy Design

1. **Start Conservative**: Begin with proven, safe weightings
2. **Small Changes**: Test incremental policy modifications
3. **Weight Balance**: Ensure component weights sum to 1.0
4. **Domain Coverage**: Include comprehensive TLD and domain lists

### Experiment Management

1. **Clear Hypotheses**: Define what each variant aims to improve
2. **Statistical Power**: Ensure adequate sample sizes for significance
3. **Consistent Assignment**: Use user IDs for stable variant assignment
4. **Gradual Rollout**: Start small, increase based on monitoring

### Monitoring & Alerting

1. **Performance Alerts**: Monitor for latency regressions
2. **Data Quality**: Validate telemetry data integrity
3. **Experiment Balance**: Ensure proper variant distribution
4. **Error Tracking**: Monitor policy computation failures

## Troubleshooting

### Common Issues

#### Policy Not Loading

```python
# Check configuration
policy = CredibilityPolicy.load_policy_from_config()
print(f"Loaded: {policy.policy['name']}")

# Check environment
import os
print(f"Config env: {os.getenv('CREDIBILITY_POLICY_CONFIG')}")
```

#### Experiment Not Running

```python
# Check flags
from credibility_ab_test import CREDIBILITY_POLICY_AB_TEST
print(f"AB Test enabled: {CREDIBILITY_POLICY_AB_TEST}")

# Check rollout percentage
experiment = get_experiment_instance()
print(f"Rollout: {experiment.rollout_percentage}%")
```

#### Telemetry Not Collected

```python
# Check telemetry import
try:
    from credibility_telemetry import collect_search_metrics
    print("Telemetry available")
except ImportError:
    print("Telemetry not available - using fallback")
```

### Performance Optimization

#### Policy Caching

```python
# Policies are cached globally
policy1 = get_policy_instance()
policy2 = get_policy_instance()
assert policy1 is policy2  # Same instance
```

#### Experiment Optimization

```python
# Pre-compute variant assignments for high-traffic scenarios
user_variant_cache = {}

def get_user_variant(user_id):
    if user_id not in user_variant_cache:
        experiment = get_experiment_instance()
        if experiment.should_run_experiment(user_id):
            user_variant_cache[user_id] = experiment.assign_variant(user_id)
        else:
            user_variant_cache[user_id] = None
    return user_variant_cache[user_id]
```

## Migration Guide

### From Static Scoring to Policy Engine

#### Before (Static)

```python
def compute_credibility(url, content):
    # Hardcoded logic
    if 'wikipedia.org' in url:
        return 0.9
    # ... more hardcoded rules
```

#### After (Policy-Based)

```python
def compute_credibility(url, content, date_info=None):
    policy = get_policy_instance()
    return policy.compute_source_credibility(url, content, date_info)
```

### Adding Experimentation

#### Minimal Integration

```python
# Add to existing credibility computation
from credibility_ab_test import compute_credibility_with_ab_test

def compute_credibility(url, content, date_info=None, user_id=None):
    return compute_credibility_with_ab_test(url, content, date_info, user_id)
```

#### Full Experiment Control

```python
from credibility_ab_test import get_experiment_instance

def compute_credibility_with_experiment_tracking(url, content, date_info=None, user_id=None):
    experiment = get_experiment_instance()

    score, metadata = experiment.compute_credibility_with_experiment(
        url, content, date_info, user_id
    )

    # Log experiment metadata for analysis
    if metadata:
        logger.info(f"Credibility experiment: {metadata}")

    return score
```

## Future Enhancements

### Advanced Policy Features

- **Machine Learning Models**: ML-based credibility prediction
- **Dynamic Weights**: Context-aware weight adjustment
- **User Feedback**: Reputation systems with user input
- **Cross-Source Validation**: Fact-checking integration

### Experimentation Improvements

- **Multi-Armed Bandits**: Dynamic traffic allocation
- **Segmented Experiments**: Different policies for different user segments
- **Automated Rollout**: ML-driven rollout percentage optimization
- **Long-term Testing**: Extended experiment durations with seasonal analysis

### Monitoring Enhancements

- **Real-time Dashboards**: Live experiment monitoring
- **Automated Alerts**: Anomaly detection and alerting
- **Causal Inference**: Advanced statistical analysis of experiment impact
- **User Journey Tracking**: End-to-end impact measurement

This framework provides a solid foundation for data-driven credibility scoring evolution while maintaining system stability and governance compliance.
