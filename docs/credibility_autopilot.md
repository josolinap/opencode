# Credibility Autopilot: Governance & Operations Guide

## Overview

The Credibility Autopilot is a safe, auditable autonomous task continuation capability within Neo-Clone. It enables the system to automatically schedule follow-up tasks based on web search results, creating seamless task progression while maintaining full governance and observability.

## Architecture

### Core Components

- **`src/brain/autopilot.ts`**: Core autonomy logic with safety gates and health monitoring
- **`src/brain/index.ts`**: Central export for brain capabilities and policy management
- **`src/storage/feature-flags.ts`**: `autonomy.continue.enabled` flag (default: false)
- **Integration**: Multiple Neo-Clone skills call autopilot after producing results

### Cross-Skill Integration

The ATC capability has been successfully extended to multiple Neo-Clone skills:

#### Web Search (`websearch.ts`)
- **Trigger**: After search results are returned
- **Context**: Search query and results summary
- **Follow-up**: Related searches, fact-checking, deeper analysis

#### Data Inspector (`datainspector.ts`)
- **Trigger**: After data analysis is complete
- **Context**: Dataset characteristics (missing data, size, numeric fields)
- **Follow-up**: Data cleaning, relationship analysis, quality improvements

#### Code Search (`codesearch.ts`)
- **Trigger**: After code search results are returned
- **Context**: Search query and code content analysis
- **Follow-up**: Error handling improvements, testing strategies, performance optimizations, security reviews, refactoring opportunities, concurrency improvements, database optimizations, API design enhancements

#### Text Analysis (`textanalysis.ts`)
- **Trigger**: After sentiment analysis is complete
- **Context**: Sentiment scores, confidence levels, language detection, subjectivity
- **Follow-up**: Sentiment amplification strategies, negative sentiment mitigation, content engagement improvements, long-form content organization, multilingual localization strategies

#### Future Skills (Ready for Extension)
- **Any Tool**: Pattern established for consistent ATC integration

### Safety Mechanisms

1. **Feature Flag Gate**: `AUTONOMOUS_CONTINUE_ENABLED=false` by default
2. **Approval Requirements**: Optional manual approval for sensitive operations
3. **Session Validation**: Requires valid session context
4. **Error Isolation**: Autonomy failures don't break core functionality
5. **Infinite Loop Prevention**: Max depth (3 levels) and max tasks per session (5)
6. **Health Monitoring**: Real-time tracking of autonomy decisions and error rates
7. **Automatic Rollback**: Feature can be disabled if error rates exceed thresholds

## Governance Model

### Decision Framework

Autonomous continuation is **only enabled** when:
- Feature flag `autonomy.continue.enabled` is explicitly set to `true`
- Session context is valid and complete
- No approval requirements are triggered
- Previous operations completed successfully

### Audit Trail

All autonomy decisions are logged through the existing telemetry system:

```json
{
  "event": "autonomy.schedule_next_task",
  "sessionID": "session-123",
  "currentTaskId": "task-456",
  "autoTaskId": "auto-1692384000000",
  "variantName": "default",
  "policyVersion": "1.0.0",
  "outcome": "scheduled",
  "autonomyEnabled": true,
  "timestamp": 1692384000000
}
```

### Rollback Procedures

**Immediate Disable**:
```bash
export AUTONOMOUS_CONTINUE_ENABLED=false
```

**Selective Disable** (by session):
```bash
# Disable for specific problematic sessions
curl -X POST /api/sessions/{sessionId}/autonomy/disable
```

## Operational Guidelines

### Enablement Process

1. **Development Testing**: Enable in isolated test environments first
2. **Canary Deployment**: 1-5% of sessions with full monitoring
3. **Gradual Rollout**: Increase percentage based on success metrics
4. **Full Production**: 100% deployment with automated safeguards

### Success Metrics

- **Task Completion Rate**: >95% of autonomous tasks should complete successfully
- **User Satisfaction**: No degradation in user experience
- **Error Rate**: <5% autonomy-related errors
- **Performance Impact**: <2ms average latency increase

### Monitoring Dashboards

#### Key Metrics to Monitor

1. **Autonomy Usage**
   ```
   SELECT COUNT(*) as autonomy_events,
          DATE(timestamp) as day
   FROM telemetry_events
   WHERE event LIKE 'autonomy.%'
   GROUP BY DATE(timestamp)
   ```

2. **Success Rates**
   ```
   SELECT outcome, COUNT(*) as count
   FROM telemetry_events
   WHERE event = 'autonomy.schedule_next_task'
   GROUP BY outcome
   ```

3. **Performance Impact**
   ```
   SELECT AVG(latency_ms) as avg_latency,
          percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency
   FROM telemetry_events
   WHERE autonomy_enabled = true
   ```

## Privacy & Security

### Data Protection

- **No Raw PII**: All telemetry uses hashed identifiers
- **Session Correlation**: Session IDs remain unhashed for debugging
- **Content Anonymization**: Task content is not logged in telemetry
- **Query Protection**: Search queries are hashed before logging

### Privacy Controls

```typescript
// Example: Privacy-safe telemetry
{
  urlDomainHash: sha256("example.com"),     // Hashed domain
  userIdHash: sha256("user123"),            // Hashed user ID
  sessionID: "session-456",                 // Raw for correlation
  promptHash: sha256("search query")        // Hashed content
}
```

## Rollout Strategy

### Phase 1: Development (Week 1-2)
- Enable in development environment only
- Test with synthetic workloads
- Validate telemetry and error handling

### Phase 2: Staging Canary (Week 3-4)
```bash
export AUTONOMOUS_CONTINUE_ENABLED=true
export AUTONOMOUS_CANARY_PERCENTAGE=5
```
- 5% of sessions get autonomy enabled
- Full monitoring and alerting active
- Daily reviews of autonomy behavior

### Phase 3: Production Ramp (Week 5-8)
- Gradual percentage increase: 5% → 10% → 25% → 50% → 100%
- Automated rollback triggers based on error rates
- Stakeholder reviews at each milestone

### Phase 4: Full Production (Week 9+)
- 100% deployment with ongoing monitoring
- Automated performance optimization
- Continuous improvement based on telemetry

## Error Handling & Recovery

### Common Failure Modes

1. **Todo System Unavailable**
   - Autonomy silently fails, core functionality continues
   - Logged as `autonomy.error.todo_unavailable`

2. **Session Context Invalid**
   - Autonomy blocked, logged as `autonomy.blocked.invalid_session`

3. **Approval Required**
   - Autonomy blocked, logged as `autonomy.blocked.approval_required`

### Recovery Procedures

**Automatic Recovery**:
- System automatically retries failed operations
- Exponential backoff for transient failures
- Circuit breaker pattern for persistent issues

**Manual Intervention**:
```bash
# Force disable autonomy for specific session
export AUTONOMOUS_CONTINUE_BLOCKED_SESSIONS="session-123,session-456"

# Emergency disable all autonomy
export AUTONOMOUS_CONTINUE_ENABLED=false
```

## Testing Strategy

### Unit Tests (`test/brain/autopilot.test.ts`)
- Core autonomy logic validation
- Feature flag integration
- Error handling scenarios

### Integration Tests (`test/tool/websearch.autopilot.integ.test.ts`)
- End-to-end autonomy flow
- Web search + autopilot integration
- Privacy and telemetry validation

### Privacy Tests
- Verify no PII in telemetry streams
- Validate hashing mechanisms
- Check data anonymization

## Compliance & Audit

### Regulatory Compliance

- **Data Protection**: All user data properly anonymized
- **Audit Trail**: Complete record of autonomy decisions
- **Accountability**: Clear ownership and approval processes

### Audit Procedures

**Monthly Audits**:
- Review autonomy usage patterns
- Validate privacy controls
- Assess performance impact

**Incident Response**:
- Automated alerts for anomalies
- Immediate rollback capabilities
- Post-mortem analysis procedures

## Future Enhancements

### Planned Features

1. **Context-Aware Autonomy**: Task-specific continuation logic
2. **User Preferences**: Individual autonomy settings
3. **Advanced Scheduling**: Priority-based task queuing
4. **Multi-Step Workflows**: Complex autonomous sequences

### Research Areas

1. **Success Prediction**: ML models for autonomy success rates
2. **User Impact Analysis**: Measuring autonomy value to users
3. **Optimization**: Reducing latency and improving reliability

## Support & Contacts

### Technical Support
- **Development**: autonomy-dev@neo-clone.internal
- **Operations**: autonomy-ops@neo-clone.internal
- **Security**: security@neo-clone.internal

### Documentation
- **API Reference**: `/docs/api/autopilot`
- **Telemetry Schema**: `/docs/telemetry/autonomy`
- **Troubleshooting**: `/docs/troubleshooting/autonomy`

---

## Quick Reference

### Enable Autonomy
```bash
export AUTONOMOUS_CONTINUE_ENABLED=true
```

### Monitor Health
```bash
# Check autonomy metrics
curl /api/metrics/autonomy

# View recent events
curl /api/telemetry/autonomy/recent
```

### Emergency Disable
```bash
export AUTONOMOUS_CONTINUE_ENABLED=false
# Restart services to pick up flag change
```

### Key Metrics
- Autonomy events per day
- Success rate (>95%)
- Error rate (<5%)
- Performance impact (<2ms)

---

*This document is maintained by the Credibility Engineering team. Last updated: 2025-11-16*
