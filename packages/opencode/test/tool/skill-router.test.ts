import { getSkills, type Skill } from "../../src/agent/skill-registry"
import { test, expect } from "bun:test"

// Isolated tests for routing logic without full runtime config

function routePromptToSkillIsolated(prompt: string): Skill {
  const p = (prompt ?? "").toLowerCase()
  const skills = getSkills()

  // Quick planning cue overrides to minimize latency
  if (/[\b]plan|multi-?step|reasoning|workflow[\b]/.test(p)) return "minimax_agent" as any as Skill

  for (const s of skills) {
    // Check each keyword for a match; supports single-word and multi-word keywords
    for (const kw of s.keywords) {
      const keywordWords = kw.toLowerCase().split(/\s+/)
      if (keywordWords.length === 1) {
        if (p.includes(kw.toLowerCase())) return s.name as any as Skill
      } else {
        if (keywordWords.every((word) => p.includes(word))) return s.name as any as Skill
      }
    }
  }

  return "web_search" as Skill
}

test("route to minimax_agent for planning prompts", () => {
  const skill = routePromptToSkillIsolated("Plan a multi-step workflow")
  expect(skill).toBe("minimax_agent" as any)
})

test("route to code_generation for code prompts", () => {
  const skill = routePromptToSkillIsolated("Generate a Python class for a robot")
  expect(skill).toBe("code_generation" as any)
})

test("route to text_analysis for sentiment prompts", () => {
  const skill = routePromptToSkillIsolated("Analyze sentiment of this review")
  expect(skill).toBe("text_analysis" as any)
})

test("route to data_inspector for data prompts", () => {
  const skill = routePromptToSkillIsolated("Analyze this CSV dataset")
  expect(skill).toBe("data_inspector" as any)
})

test("route to web_search as fallback for unknown prompts", () => {
  const skill = routePromptToSkillIsolated("What is the weather today?")
  expect(skill).toBe("web_search" as any)
})
