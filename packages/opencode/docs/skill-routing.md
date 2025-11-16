# Neo-Clone Skill Routing & Telemetry

## Overview

Neo-Clone uses a registry-based routing system to map user prompts to the most appropriate skill. The system supports priority ordering, disabled skills, custom priorities, and telemetry for observability.

## Routing Logic

1. **Override Check**: If an override skill is provided, it's returned immediately
2. **Planning Cues**: Quick regex check for planning keywords (plan, multi-step, reasoning, workflow) routes to `minimax_agent`
3. **Registry-Based Matching**: Iterates through skills in priority order, matching keywords:
   - Single-word keywords: substring match
   - Multi-word keywords: all words must be present
4. **Fallback**: Returns `web_search` if no match found

## Skill Registry

Skills are defined with:

- `name`: Skill identifier
- `description`: What the skill does
- `keywords`: Array of trigger words/phrases
- `priority`: Higher numbers checked first

## Telemetry

All routing operations are wrapped with telemetry to capture:

- Latency (ms)
- Success/failure status
- Error messages
- Skill usage counts
- Timestamps

## Usage Examples

```typescript
// Basic routing
const skill = await routePromptToSkill("Generate Python code")
// Returns: "code_generation"

// With override
const skill = await routePromptToSkill("any prompt", "text_analysis")
// Returns: "text_analysis"

// Telemetry summary
const summary = telemetry.getSummary()
// Returns: { total: 10, successes: 9, failures: 1, successRate: 90, ... }
```

## Testing

- Isolated unit tests verify routing logic without runtime dependencies
- Integration tests available for full runtime scenarios
- Telemetry tests ensure proper event recording and summary calculation
