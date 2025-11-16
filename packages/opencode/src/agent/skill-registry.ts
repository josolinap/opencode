/**
 * Type alias for Skill names
 */
export type Skill =
  | "minimax_agent"
  | "code_generation"
  | "text_analysis"
  | "ml_training"
  | "data_inspector"
  | "database_admin"
  | "security_auditor"
  | "api_designer"
  | "documentation_writer"
  | "performance_optimizer"
  | "testing_specialist"
  | "file_manager"
  | "web_search"

/**
 * Defines a Neo-Clone skill with routing metadata.
 * Skills are matched based on keywords in user prompts, with higher priority taking precedence.
 */
export interface SkillDefinition {
  name: Skill
  description: string
  keywords: string[] // Triggers for routing; can be single words or phrases
  priority: number // Higher = checked first; ensures deterministic routing (e.g., planning > code gen)
}

/**
 * Registry of all available Neo-Clone skills.
 * Add new skills here with unique names, descriptions, keyword triggers, and priorities.
 * Priorities ensure multi-keyword prompts route to the most specific skill (e.g., "plan code" -> minimax_agent).
 */
export const SKILL_REGISTRY: SkillDefinition[] = [
  {
    name: "minimax_agent",
    description: "Dynamic reasoning, intent analysis, and skill generation for complex multi-step tasks",
    keywords: ["multi-step", "complex reasoning", "strategic planning", "orchestrate", "coordinate", "plan.*reasoning"],
    priority: 10,
  },
  {
    name: "code_generation",
    description: "Generates/explains Python ML code snippets and algorithms",
    keywords: ["generate code", "code snippet", "python code", "algorithm", "class definition", "function code"],
    priority: 9,
  },
  {
    name: "text_analysis",
    description: "Advanced sentiment analysis, language detection, and content moderation with multi-language support",
    keywords: [
      "sentiment",
      "analyze.*sentiment",
      "tone analysis",
      "content moderation",
      "emotion detection",
      "feeling analysis",
    ],
    priority: 8,
  },
  {
    name: "ml_training",
    description: "Provides ML model training guidance and recommendations",
    keywords: ["train model", "machine learning", "ml training", "model evaluation"],
    priority: 7,
  },
  {
    name: "data_inspector",
    description: "Analyzes CSV/JSON data and provides summaries",
    keywords: ["analyze data", "data summary", "data stats", "csv", "json", "dataset", "data insights"],
    priority: 6,
  },
  {
    name: "database_admin",
    description: "SQL queries, database design, schema optimization, and data modeling",
    keywords: ["sql", "database", "query", "schema", "table", "index", "join", "select", "insert", "update"],
    priority: 6,
  },
  {
    name: "security_auditor",
    description: "Code security analysis, vulnerability scanning, and security best practices",
    keywords: ["security", "vulnerability", "audit", "scan", "exploit", "injection", "xss", "csrf", "encryption"],
    priority: 6,
  },
  {
    name: "api_designer",
    description: "REST API design, OpenAPI specifications, and API testing",
    keywords: ["api", "rest", "openapi", "swagger", "endpoint", "http", "json", "request", "response"],
    priority: 6,
  },
  {
    name: "documentation_writer",
    description: "Auto-generate documentation, READMEs, API docs, and technical writing",
    keywords: ["documentation", "readme", "docs", "technical writing", "api docs", "markdown", "guide"],
    priority: 5,
  },
  {
    name: "performance_optimizer",
    description: "Code profiling, bottleneck identification, and performance optimization",
    keywords: ["performance", "optimize", "bottleneck", "profiling", "speed", "efficiency", "memory", "cpu"],
    priority: 5,
  },
  {
    name: "testing_specialist",
    description: "Generate test cases, test automation, and quality assurance",
    keywords: ["test", "testing", "unit test", "integration test", "automation", "qa", "coverage"],
    priority: 5,
  },
  {
    name: "file_manager",
    description: "Read files, analyze content, manage directories",
    keywords: ["read file", "open file", "list directory", "file directory"],
    priority: 5,
  },
  {
    name: "web_search",
    description: "Search the web, fact-check information, find resources",
    keywords: ["search", "internet", "web", "lookup", "online"],
    priority: 4,
  },
]

/**
 * Returns all skills sorted by priority (highest first).
 * Used by the router to check skills in deterministic order.
 */
export function getSkills(): SkillDefinition[] {
  return [...SKILL_REGISTRY].sort((a, b) => b.priority - a.priority)
}

/**
 * Find the skill for a prompt with optional routing options.
 * Overloads:
 *  - findSkillForPrompt(prompt: string): Skill | null
 *  - findSkillForPrompt(prompt: string, options): Skill | null
 */
export function findSkillForPrompt(prompt: string): Skill | null
export function findSkillForPrompt(
  prompt: string,
  options?: { disabledSkills?: string[]; customPriorities?: Record<string, number> },
): Skill | null
export function findSkillForPrompt(
  prompt: string,
  options: { disabledSkills?: string[]; customPriorities?: Record<string, number> } = {},
): Skill | null {
  const p = (prompt ?? "").toLowerCase()
  const promptWords = p.split(/\s+/)

  // Get skills with config applied
  const skills = getSkills().filter((skill) => !options.disabledSkills?.includes(skill.name))

  // Apply custom priorities
  for (const skill of skills) {
    if (options.customPriorities?.[skill.name] !== undefined) {
      skill.priority = options.customPriorities[skill.name]
    }
  }

  // Re-sort by priority after adjustments
  skills.sort((a, b) => b.priority - a.priority)

  for (const skill of skills) {
    for (const keyword of skill.keywords) {
      const keywordWords = keyword.toLowerCase().split(/\s+/)
      if (keywordWords.length === 1) {
        // Single word: substring match (e.g., "search" in "web search")
        if (p.includes(keyword.toLowerCase())) {
          return skill.name
        }
      } else {
        // Phrase: all words must be present (e.g., "read file" requires both "read" and "file")
        if (keywordWords.every((word) => promptWords.includes(word))) {
          return skill.name
        }
      }
    }
  }
  return null
}
