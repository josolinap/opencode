import { ModelsDev } from "./models"
import { Provider } from "./provider"
import { NeoCloneTool } from "../tool/neo-clone"
import { Log } from "../util/log"
import { Global } from "../global"
import path from "path"
import { z } from "zod/v4"

const log = Log.create({ service: "model-recommendation" })

export interface TaskAnalysis {
  taskType: string
  complexity: "simple" | "medium" | "complex"
  requirements: {
    reasoning: boolean
    toolCalling: boolean
    temperature: boolean
    attachment: boolean
    contextLength: number
    cost: "free" | "budget" | "premium"
  }
  keywords: string[]
}

export interface ModelRecommendation {
  model: string
  provider: string
  score: number
  reasoning: string
  cost: number
  capabilities: string[]
}

const RecommendationCache = z.object({
  task: z.string(),
  recommendations: z.array(
    z.object({
      model: z.string(),
      provider: z.string(),
      score: z.number(),
      reasoning: z.string(),
      cost: z.number(),
      capabilities: z.array(z.string()),
    }),
  ),
  timestamp: z.number(),
})

type RecommendationCache = z.infer<typeof RecommendationCache>

export namespace ModelRecommendationEngine {
  const CACHE_FILE = path.join(Global.Path.cache, "model_recommendations.json")
  const CACHE_TTL = 24 * 60 * 60 * 1000 // 24 hours

  export async function recommendForTask(task: string): Promise<ModelRecommendation[]> {
    // Check cache first
    const cached = await getCachedRecommendations(task)
    if (cached) {
      log.info("Using cached recommendations", { task })
      return cached
    }

    // Analyze the task
    const analysis = await analyzeTask(task)
    log.info("Task analysis complete", { task, analysis })

    // Get recommendations based on analysis
    const recommendations = await generateRecommendations(analysis, task)

    // Cache the results
    await cacheRecommendations(task, recommendations)

    return recommendations
  }

  export async function analyzeTask(task: string): Promise<TaskAnalysis> {
    try {
      // Use Neo-Clone for task analysis
      const neoCloneTool = await NeoCloneTool.init()
      const response = await neoCloneTool.execute(
        {
          message: `Analyze this task and determine its requirements: "${task}". Return a JSON object with: taskType, complexity (simple/medium/complex), requirements object with boolean flags for reasoning, toolCalling, temperature, attachment, and numeric values for contextLength and cost preference (free/budget/premium), and an array of relevant keywords.`,
          mode: "direct",
          timeout: 20000,
        },
        {
          sessionID: "recommendation-session",
          messageID: "task-analysis",
          agent: "system",
          abort: new AbortController().signal,
          metadata: () => {},
        },
      )

      const content = response.output

      // Try to parse JSON response
      const jsonMatch = content.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        try {
          const parsed = JSON.parse(jsonMatch[0])
          return {
            taskType: parsed.taskType || "general",
            complexity: parsed.complexity || "medium",
            requirements: {
              reasoning: parsed.requirements?.reasoning ?? false,
              toolCalling: parsed.requirements?.toolCalling ?? false,
              temperature: parsed.requirements?.temperature ?? false,
              attachment: parsed.requirements?.attachment ?? false,
              contextLength: parsed.requirements?.contextLength || 8000,
              cost: parsed.requirements?.cost || "budget",
            },
            keywords: parsed.keywords || [],
          }
        } catch (e) {
          log.warn("Failed to parse task analysis JSON", { content })
        }
      }
    } catch (error) {
      log.error("Task analysis failed, using fallback", { error, task })
    }

    // Fallback analysis
    return fallbackTaskAnalysis(task)
  }

  async function generateRecommendations(
    analysis: TaskAnalysis,
    _originalTask: string,
  ): Promise<ModelRecommendation[]> {
    const providers = await Provider.list()
    const allModels: Array<{
      provider: string
      model: string
      info: ModelsDev.Model
    }> = []

    // Collect all available models
    for (const [providerID, provider] of Object.entries(providers)) {
      for (const [modelID, model] of Object.entries(provider.info.models)) {
        allModels.push({ provider: providerID, model: modelID, info: model })
      }
    }

    // Score models based on requirements
    const scoredModels = allModels.map((model) => {
      const score = calculateModelScore(model, analysis)
      const capabilities = []
      if (model.info.reasoning) capabilities.push("reasoning")
      if (model.info.tool_call) capabilities.push("tool_calling")
      if (model.info.temperature) capabilities.push("temperature")
      if (model.info.attachment) capabilities.push("attachment")

      return {
        model: model.model,
        provider: model.provider,
        score,
        reasoning: generateReasoning(model, analysis, score),
        cost: model.info.cost.input + model.info.cost.output,
        capabilities,
      }
    })

    // Sort by score and return top recommendations
    return scoredModels.sort((a, b) => b.score - a.score).slice(0, 10)
  }

  function calculateModelScore(model: { info: ModelsDev.Model }, analysis: TaskAnalysis): number {
    let score = 50 // Base score

    // Capability matching
    if (analysis.requirements.reasoning && model.info.reasoning) score += 20
    if (analysis.requirements.toolCalling && model.info.tool_call) score += 15
    if (analysis.requirements.temperature && model.info.temperature) score += 10
    if (analysis.requirements.attachment && model.info.attachment) score += 10

    // Context length requirements
    const contextRatio = model.info.limit.context / analysis.requirements.contextLength
    if (contextRatio >= 1) {
      score += 15
    } else if (contextRatio >= 0.5) {
      score += 5
    }

    // Cost preferences
    const isFree = model.info.cost.input === 0 && model.info.cost.output === 0
    if (analysis.requirements.cost === "free" && isFree) {
      score += 25
    } else if (analysis.requirements.cost === "budget" && model.info.cost.input <= 1 && model.info.cost.output <= 4) {
      score += 15
    } else if (analysis.requirements.cost === "premium") {
      score += 10
    }

    // Complexity adjustments
    if (analysis.complexity === "complex" && model.info.reasoning) score += 10
    if (analysis.complexity === "simple" && !model.info.reasoning) score += 5

    // Penalize experimental models for production tasks
    if (model.info.experimental) score -= 10

    return Math.max(0, Math.min(100, score))
  }

  function generateReasoning(model: { info: ModelsDev.Model }, analysis: TaskAnalysis, score: number): string {
    const reasons = []

    if (analysis.requirements.reasoning && model.info.reasoning) {
      reasons.push("supports reasoning")
    }
    if (analysis.requirements.toolCalling && model.info.tool_call) {
      reasons.push("supports tool calling")
    }
    if (model.info.limit.context >= analysis.requirements.contextLength) {
      reasons.push(`${model.info.limit.context} token context`)
    }

    const isFree = model.info.cost.input === 0 && model.info.cost.output === 0
    if (isFree) {
      reasons.push("free to use")
    } else {
      reasons.push(`$${model.info.cost.input}/$${model.info.cost.output} per 1M tokens`)
    }

    if (score >= 80) reasons.push("excellent match")
    else if (score >= 60) reasons.push("good match")
    else if (score >= 40) reasons.push("adequate match")
    else reasons.push("basic match")

    return reasons.join(", ")
  }

  function fallbackTaskAnalysis(task: string): TaskAnalysis {
    const lowerTask = task.toLowerCase()

    // Simple keyword-based analysis
    const reasoningKeywords = ["reason", "analyze", "think", "logic", "solve", "complex"]
    const toolKeywords = ["tool", "function", "call", "api", "search", "web"]
    const creativeKeywords = ["write", "create", "generate", "design", "creative"]
    const attachmentKeywords = ["image", "file", "upload", "document", "pdf"]

    const hasReasoning = reasoningKeywords.some((k) => lowerTask.includes(k))
    const hasTools = toolKeywords.some((k) => lowerTask.includes(k))
    const hasCreativity = creativeKeywords.some((k) => lowerTask.includes(k))
    const hasAttachments = attachmentKeywords.some((k) => lowerTask.includes(k))

    let complexity: "simple" | "medium" | "complex" = "medium"
    if (lowerTask.includes("complex") || lowerTask.includes("advanced") || hasReasoning) {
      complexity = "complex"
    } else if (lowerTask.includes("simple") || lowerTask.includes("basic")) {
      complexity = "simple"
    }

    let contextLength = 8000
    if (complexity === "complex") contextLength = 32000
    else if (complexity === "simple") contextLength = 4000

    let cost: "free" | "budget" | "premium" = "budget"
    if (lowerTask.includes("free") || lowerTask.includes("cheap")) cost = "free"
    if (lowerTask.includes("premium") || lowerTask.includes("best")) cost = "premium"

    return {
      taskType: "general",
      complexity,
      requirements: {
        reasoning: hasReasoning,
        toolCalling: hasTools,
        temperature: hasCreativity,
        attachment: hasAttachments,
        contextLength,
        cost,
      },
      keywords: [],
    }
  }

  async function getCachedRecommendations(task: string): Promise<ModelRecommendation[] | null> {
    try {
      const file = Bun.file(CACHE_FILE)
      if (!(await file.exists())) return null

      const data = await file.json()
      const cache = RecommendationCache.parse(data)

      // Check if cache is still valid
      if (Date.now() - cache.timestamp > CACHE_TTL) return null

      // Simple similarity check - could be improved
      if (
        cache.task.toLowerCase().includes(task.toLowerCase()) ||
        task.toLowerCase().includes(cache.task.toLowerCase())
      ) {
        return cache.recommendations
      }
    } catch (error) {
      log.warn("Failed to read recommendation cache", { error })
    }

    return null
  }

  async function cacheRecommendations(task: string, recommendations: ModelRecommendation[]) {
    try {
      const cache: RecommendationCache = {
        task,
        recommendations,
        timestamp: Date.now(),
      }

      await Bun.write(CACHE_FILE, JSON.stringify(cache, null, 2))
    } catch (error) {
      log.warn("Failed to cache recommendations", { error })
    }
  }

  export async function clearCache() {
    try {
      await Bun.write(CACHE_FILE, "{}")
      log.info("Recommendation cache cleared")
    } catch (error) {
      log.warn("Failed to clear recommendation cache", { error })
    }
  }
}
