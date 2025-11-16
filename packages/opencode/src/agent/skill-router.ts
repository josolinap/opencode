import { type Skill, type SkillDefinition, getSkills } from "./skill-registry"
import { Config } from "../config/config"
import { withTelemetry } from "../util/telemetry"
import { ensureMinimaxLoaded } from "./minimax-loader"

export type { Skill }

/**
 * Routes a user prompt to the most appropriate Neo-Clone skill.
 * Uses registry-based keyword matching with priority ordering for deterministic results.
 * Respects user config for disabled skills and custom priorities.
 * Supports override for testing/debugging scenarios.
 *
 * @param prompt - The user's input text
 * @param overrideSkill - Optional: force a specific skill (bypasses matching)
 * @returns The routed skill name
 */
export async function routePromptToSkill(prompt: string, overrideSkill?: Skill): Promise<Skill> {
  return withTelemetry("skill_router", prompt, async () => {
    if (overrideSkill) {
      if (overrideSkill === "minimax_agent") {
        // Even when overridden, attempt to preload minimax model for faster responses
        await ensureMinimaxLoaded()
      }
      return overrideSkill // Manual override for testing or user preference
    }

    const config = await Config.get()
    const skillConfig = config.skillRouting

    // Use registry-based routing for deterministic mapping
    const p = (prompt ?? "").toLowerCase()
    const promptWords = p.split(/\s+/)
    let skills = getSkills()

    // Apply custom priorities
    if (skillConfig?.customPriorities) {
      skills = skills.map((s) => ({
        ...s,
        priority: skillConfig.customPriorities![s.name] ?? s.priority,
      }))
      skills.sort((a, b) => b.priority - a.priority)
    }

    const matches: { skill: SkillDefinition; matchCount: number; exactPhraseMatches: number }[] = []

    for (const s of skills) {
      // Apply disabled list
      if (skillConfig?.disabledSkills?.includes(s.name as any)) continue
      let matchCount = 0
      let exactPhraseMatches = 0

      // Check each keyword for a match; supports single-word and multi-word keywords
      for (const kw of s.keywords) {
        const keywordWords = kw.toLowerCase().split(/\s+/)
        if (keywordWords.length === 1) {
          // Single word: check for exact word match
          if (promptWords.includes(kw.toLowerCase())) {
            matchCount++
          }
        } else {
          // Multi-word phrase: all words must be present
          if (keywordWords.every((word) => promptWords.includes(word))) {
            matchCount++
            exactPhraseMatches++
          }
        }
      }

      if (matchCount > 0) {
        matches.push({ skill: s, matchCount, exactPhraseMatches })
      }
    }

    if (matches.length > 0) {
      // Sort by: exact phrase matches first, then match count, then priority
      matches.sort((a, b) => {
        // Prioritize exact phrase matches (more specific)
        if (a.exactPhraseMatches !== b.exactPhraseMatches) {
          return b.exactPhraseMatches - a.exactPhraseMatches
        }
        // Then by total match count
        if (a.matchCount !== b.matchCount) {
          return b.matchCount - a.matchCount
        }
        // Finally by priority
        return b.skill.priority - a.skill.priority
      })

      const bestMatch = matches[0].skill
      if (bestMatch.name === "minimax_agent") await ensureMinimaxLoaded()
      return bestMatch.name as any as Skill
    }

    return "web_search" as Skill
  })
}
