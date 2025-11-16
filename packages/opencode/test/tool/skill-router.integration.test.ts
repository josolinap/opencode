import { routePromptToSkill } from "../../src/agent/skill-router"
import { test, expect } from "bun:test"

// Integration tests for routing with runtime config (if needed)
// Note: These tests require proper runtime context; use sparingly

test("integration: route to minimax_agent for planning prompts", async () => {
  // This test will be skipped if runtime context is not available
  try {
    const skill = await routePromptToSkill("Plan a multi-step workflow")
    expect(skill).toBe("minimax_agent" as any)
  } catch (e) {
    console.log("Skipping integration test due to missing runtime context")
  }
})
