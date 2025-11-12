import z from "zod/v4"
import { Tool } from "./tool"
import { ModelRecommendationEngine } from "../provider/recommendation"
import { Log } from "../util/log"

const log = Log.create({ service: "model-selector-tool" })

export const ModelSelectorTool = Tool.define("model-selector", {
  description:
    "Automatically select the best AI model for a given task based on requirements, cost, and capabilities. Uses intelligent analysis to recommend optimal models.",
  parameters: z.object({
    task: z.string().describe("The task or use case for which to select a model"),
    requirements: z
      .object({
        reasoning: z.boolean().optional().describe("Whether advanced reasoning capabilities are needed"),
        toolCalling: z.boolean().optional().describe("Whether tool/function calling is required"),
        temperature: z.boolean().optional().describe("Whether creative/temperature control is needed"),
        attachment: z.boolean().optional().describe("Whether file/attachment handling is needed"),
        contextLength: z.number().optional().describe("Minimum context length required in tokens"),
        cost: z.enum(["free", "budget", "premium"]).optional().describe("Cost preference"),
      })
      .optional()
      .describe("Specific requirements for the model"),
    maxRecommendations: z.number().default(3).describe("Maximum number of recommendations to return"),
    format: z.enum(["simple", "detailed"]).default("simple").describe("Output format"),
  }),
  async execute(params, ctx): Promise<{ title: string; metadata: any; output: string }> {
    try {
      log.info("Selecting model for task", { task: params.task, requirements: params.requirements })

      // Get recommendations using the recommendation engine
      const recommendations = await ModelRecommendationEngine.recommendForTask(params.task)

      // Filter and limit recommendations
      const filtered = recommendations
        .filter((rec) => {
          // Apply additional filters based on requirements
          if (params.requirements) {
            if (params.requirements.reasoning !== undefined && !rec.capabilities.includes("reasoning")) {
              return false
            }
            if (params.requirements.toolCalling !== undefined && !rec.capabilities.includes("tool_calling")) {
              return false
            }
            if (params.requirements.temperature !== undefined && !rec.capabilities.includes("temperature")) {
              return false
            }
            if (params.requirements.attachment !== undefined && !rec.capabilities.includes("attachment")) {
              return false
            }
          }
          return true
        })
        .slice(0, params.maxRecommendations)

      ctx.metadata({
        metadata: {
          task: params.task,
          recommendations_count: filtered.length,
          requirements: params.requirements,
        },
      })

      // Simple format - just return the best model
      const best = filtered[0]
      if (!best) {
        return {
          title: "No suitable models found",
          metadata: {
            task: params.task,
            total_recommendations: 0,
          },
          output: `No models found matching the requirements for task: ${params.task}`,
        }
      }

      let output = `${best.provider}/${best.model} (Score: ${best.score}%, Cost: $${best.cost.toFixed(3)}, Capabilities: ${best.capabilities.join(", ")})\n\nReasoning: ${best.reasoning}`

      if (params.format === "detailed" && filtered.length > 1) {
        output += "\n\nOther recommendations:\n"
        for (let i = 1; i < Math.min(filtered.length, params.maxRecommendations); i++) {
          const rec = filtered[i]
          output += `${i + 1}. ${rec.provider}/${rec.model} (Score: ${rec.score}%)\n`
        }
      }

      return {
        title: `Best Model: ${best.provider}/${best.model}`,
        metadata: {
          task: params.task,
          selected_model: `${best.provider}/${best.model}`,
          score: best.score,
          cost: best.cost,
          capabilities: best.capabilities,
          total_recommendations: filtered.length,
        },
        output,
      }
    } catch (error) {
      log.error("Model selection failed", { error, task: params.task })
      throw new Error(`Failed to select model for task: ${(error as Error).message}`)
    }
  },
})

// Helper function to get the best model for a task (used internally)
export async function selectBestModelForTask(task: string): Promise<{ providerID: string; modelID: string } | null> {
  try {
    const recommendations = await ModelRecommendationEngine.recommendForTask(task)
    const best = recommendations[0]

    if (best && best.score >= 60) {
      // Only use if score is decent
      return {
        providerID: best.provider,
        modelID: best.model,
      }
    }
  } catch (error) {
    log.warn("Failed to select best model", { error, task })
  }

  return null
}

// Integration with session/prompt system for automatic model selection
export async function getRecommendedModelForSession(
  _sessionID: string,
  _currentProviderID: string,
  _currentModelID: string,
): Promise<{ providerID: string; modelID: string } | null> {
  // This could be enhanced to analyze the conversation history and recommend better models
  // For now, just return null to use existing logic
  return null
}
