import { telemetry } from "../../src/util/telemetry"
import { test, expect } from "bun:test"

test("telemetry records events correctly", () => {
  telemetry.clear()
  telemetry.record({
    skill: "test_skill",
    prompt: "test prompt",
    latencyMs: 100,
    success: true,
    timestamp: Date.now(),
  } as any)

  const events = telemetry.getEvents()
  expect(events).toHaveLength(1)
  expect(events[0].skill).toBe("test_skill")
  expect(events[0].success).toBe(true)
  // Ensure privacy: prompt should not be stored; instead a promptHash should exist
  // @ts-ignore
  expect((events[0] as any).prompt).toBeUndefined()
  // @ts-ignore
  expect((events[0] as any).promptHash).toBeDefined()
})

test("telemetry summary calculates metrics", () => {
  telemetry.clear()
  telemetry.record({ skill: "skill1", success: true, timestamp: Date.now() })
  telemetry.record({ skill: "skill1", success: false, timestamp: Date.now() })
  telemetry.record({ skill: "skill2", success: true, timestamp: Date.now() })

  const summary = telemetry.getSummary()
  expect(summary.total).toBe(3)
  expect(summary.successes).toBe(2)
  expect(summary.failures).toBe(1)
  expect(summary.successRate).toBeCloseTo(66.67, 1)
  expect(summary.skillCounts.skill1).toBe(2)
  expect(summary.skillCounts.skill2).toBe(1)
})
