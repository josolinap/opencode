import { getSkills, findSkillForPrompt, type Skill } from "../../src/agent/skill-registry"
import { test, expect } from "bun:test"

// Basic sanity tests for the extended routing API

test("findSkillForPrompt overload: basic prompts", () => {
  const s1 = findSkillForPrompt("Plan a multi-step workflow")
  expect(s1).toBe("minimax_agent" as any as Skill)

  const s2 = findSkillForPrompt("Generate a Python class for a robot")
  expect(s2).toBe("code_generation" as any as Skill)

  const s3 = findSkillForPrompt("Analyze sentiment of this review")
  expect(s3).toBe("text_analysis" as any as Skill)
})
