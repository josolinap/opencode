import { describe, expect, test, beforeEach } from "bun:test"
import { routePromptToSkill } from "../src/agent/skill-router"
import { findSkillForPrompt, getSkills } from "../src/agent/skill-registry"
import { Config } from "../src/config/config"

describe("skill-router", () => {
  beforeEach(() => {
    // Mock Config.get to return empty config for tests
    Config.get = async () => ({ skillRouting: {} }) as any
  })
  test("routes code_generation from code prompts", async () => {
    const skill = await routePromptToSkill("Please generate Python code for a classifier")
    expect(skill).toBe("code_generation")
  })

  test("routes text_analysis from sentiment prompts", async () => {
    const skill = await routePromptToSkill("Analyze the sentiment of this review")
    expect(skill).toBe("text_analysis")
  })

  test("routes data_inspector from data prompts", async () => {
    const skill = await routePromptToSkill("Summarize the CSV data and show stats")
    expect(skill).toBe("data_inspector")
  })

  test("routes ml_training from training prompts", async () => {
    const skill = await routePromptToSkill("Train a model using this dataset")
    expect(skill).toBe("ml_training")
  })

  test("routes file_manager from file prompts", async () => {
    const skill = await routePromptToSkill("Read this directory and list files")
    expect(skill).toBe("file_manager")
  })

  test("routes web_search for generic questions", async () => {
    const skill = await routePromptToSkill("What is the capital of France?")
    // default fallback tends toward web_search for generic questions
    expect(skill).toBe("web_search")
  })

  test("routes minimax_agent for planning cues", async () => {
    const skill = await routePromptToSkill("Plan a multi-step reasoning process to solve this")
    expect(skill).toBe("minimax_agent")
  })

  test("handles edge cases", async () => {
    expect(await routePromptToSkill("")).toBe("web_search") // empty prompt
    expect(await routePromptToSkill("   ")).toBe("web_search") // whitespace
    expect(await routePromptToSkill(null as any)).toBe("web_search") // null
    expect(await routePromptToSkill("Plan and code and analyze data")).toBe("data_inspector") // multiple cues, but analyze matches data
  })

  test("respects config disabled skills", async () => {
    // Mock config with disabled skills
    const originalGet = Config.get
    Config.get = async () => ({ skillRouting: { disabledSkills: ["code_generation"] } }) as any
    try {
      expect(await routePromptToSkill("Generate Python code")).toBe("web_search") // code_generation disabled, fallback
      expect(await routePromptToSkill("Analyze sentiment")).toBe("text_analysis") // not disabled
    } finally {
      Config.get = originalGet
    }
  })

  test("respects config custom priorities", async () => {
    // Mock config with custom priorities
    const originalGet = Config.get
    Config.get = async () => ({ skillRouting: { customPriorities: { data_inspector: 15 } } }) as any // boost data_inspector above minimax
    try {
      expect(await routePromptToSkill("Plan and analyze data")).toBe("data_inspector") // data_inspector now highest
    } finally {
      Config.get = originalGet
    }
  })

  test("routePromptToSkill respects override skill", async () => {
    const skill = await routePromptToSkill("Random prompt", "code_generation")
    expect(skill).toBe("code_generation")
  })

  test("handles edge cases", async () => {
    expect(await routePromptToSkill("")).toBe("web_search") // empty prompt
    expect(await routePromptToSkill("   ")).toBe("web_search") // whitespace
    expect(await routePromptToSkill(null as any)).toBe("web_search") // null
    expect(await routePromptToSkill("Plan and code and analyze data")).toBe("data_inspector") // multiple cues, but analyze matches data
  })

  test("respects config disabled skills", async () => {
    // Mock config with disabled skills
    const originalGet = Config.get
    Config.get = async () => ({ skillRouting: { disabledSkills: ["code_generation"] } }) as any
    try {
      expect(await routePromptToSkill("Generate Python code")).toBe("web_search") // code_generation disabled, fallback
      expect(await routePromptToSkill("Analyze sentiment")).toBe("text_analysis") // not disabled
    } finally {
      Config.get = originalGet
    }
  })

  test("respects config custom priorities", async () => {
    // Mock config with custom priorities
    const originalGet = Config.get
    Config.get = async () => ({ skillRouting: { customPriorities: { data_inspector: 15 } } }) as any // boost data_inspector above minimax
    try {
      expect(await routePromptToSkill("Plan and analyze data")).toBe("data_inspector") // data_inspector now highest
    } finally {
      Config.get = originalGet
    }
  })
})
