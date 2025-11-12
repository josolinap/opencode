// Core dependencies
import { Instance } from "../../project/instance"
import { Provider } from "../../provider/provider"
import { ModelsDev } from "../../provider/models"
import { ModelRecommendationEngine } from "../../provider/recommendation"
import type { ModelRecommendation } from "../../provider/recommendation"
import { ProviderConfigManager } from "../../provider/config"
import { cmd } from "./cmd"
import { Log } from "../../util/log"
import { exit } from "process"

// Logger for models command operations
const log = Log.create({ service: "models-command" })

interface ModelFilter {
  provider?: string
  name?: string
  cost?: "free" | "paid"
  capabilities?: string[]
  limit?: number
}

/**
 * CLI command for managing AI models and providers
 */
export const ModelsCommand = cmd({
  command: "models [action]",
  describe: "Query, filter, and manage AI models and providers from Models.dev database",
  builder: (yargs) =>
    yargs
      .positional("action", {
        describe: "Action to perform: list, search, recommend, info, free",
        type: "string",
        default: "list",
      })
      .option("provider", {
        alias: "p",
        describe: "Filter by provider ID",
        type: "string",
      })
      .option("name", {
        alias: "n",
        describe: "Filter by model name (partial match)",
        type: "string",
      })
      .option("cost", {
        alias: "c",
        describe: "Filter by cost: free, paid (default: free)",
        type: "string",
        choices: ["free", "paid"],
        default: "free",
      })
      .option("capabilities", {
        alias: "cap",
        describe: "Filter by capabilities (comma-separated): reasoning,tool_call,temperature,attachment",
        type: "string",
      })
      .option("limit", {
        alias: "l",
        describe: "Limit number of results",
        type: "number",
        default: 50,
      })
      .option("task", {
        alias: "t",
        describe: "Task description for recommendations",
        type: "string",
      })
      .option("format", {
        alias: "f",
        describe: "Output format: table, json, csv",
        type: "string",
        default: "table",
        choices: ["table", "json", "csv"],
      })
      .option("cache", {
        describe: "Force refresh model cache",
        type: "boolean",
        default: false,
      }),
  handler: async (argv) => {
    await Instance.provide({
      directory: process.cwd(),
      async fn() {
        const action = argv.action as string
        const cache = argv.cache as boolean

        if (cache) {
          console.log("Refreshing model cache...")
          await ModelsDev.refresh()
        }

        switch (action) {
          case "list":
            await listModels(argv)
            break
          case "search":
            await searchModels(argv)
            break
          case "recommend":
            await recommendModels(argv)
            break
          case "info":
            await showModelInfo(argv)
            break
          case "providers":
            await listProviders(argv)
            break
          case "provider":
            await manageProvider(argv)
            break
          case "free":
            await listFreeModels(argv)
            break
          default:
            console.log("Available actions: list, search, recommend, info, providers, provider, free")
            console.log("Use --help for more information")
        }
      },
    })
  },
})

// ==================== MODEL QUERY FUNCTIONS ====================

async function listFreeModels(argv: any) {
  console.log("🆓 Free Models Available for OpenCode Integration")
  console.log("=".repeat(60))

  // Force cost to be free
  argv.cost = "free"
  await listModels(argv)
}

async function listModels(argv: any) {
  const providers = await Provider.list()
  const filters = buildFilters(argv)

  const models = await getFilteredModels(providers, filters)

  if (argv.format === "json") {
    console.log(JSON.stringify(models, null, 2))
  } else if (argv.format === "csv") {
    outputModelsCSV(models)
  } else {
    outputModelsTable(models)
  }
}

async function searchModels(argv: any) {
  const providers = await Provider.list()
  const filters = buildFilters(argv)

  const models = await getFilteredModels(providers, filters)

  if (models.length === 0) {
    console.log("No models found matching the criteria.")
    return
  }

  console.log(`Found ${models.length} model(s) matching criteria:\n`)

  if (argv.format === "json") {
    console.log(JSON.stringify(models, null, 2))
  } else if (argv.format === "csv") {
    outputModelsCSV(models)
  } else {
    outputModelsTable(models)
  }
}

async function recommendModels(argv: any) {
  const task = argv.task as string
  if (!task) {
    console.error("Error: --task is required for recommendations")
    exit(1)
  }

  console.log(`Getting model recommendations for task: "${task}"`)

  try {
    // Use the new recommendation engine
    const recommendations = await ModelRecommendationEngine.recommendForTask(task)

    if (argv.format === "json") {
      console.log(JSON.stringify(recommendations, null, 2))
    } else {
      outputRecommendationsTable(recommendations)
    }
  } catch (error) {
    log.error("Failed to get recommendations", { error, task })
    console.error("Failed to get model recommendations. Using fallback method...")

    // Fallback to basic filtering
    const providers = await Provider.list()
    const filters = buildFilters(argv)
    const models = await getFilteredModels(providers, filters)

    console.log(`Found ${models.length} potential model(s) for your task:\n`)
    outputModelsTable(models.slice(0, 5))
  }
}

async function showModelInfo(argv: any) {
  const modelId = argv._[1] as string
  if (!modelId) {
    console.error("Error: Model ID is required for info command")
    console.log("Usage: opencode models info <provider/model>")
    exit(1)
  }

  const [providerID, modelID] = modelId.split("/")
  if (!providerID || !modelID) {
    console.error("Error: Invalid model format. Use <provider/model>")
    exit(1)
  }

  try {
    const model = await Provider.getModel(providerID, modelID)

    if (argv.format === "json") {
      console.log(
        JSON.stringify(
          {
            id: model.modelID,
            provider: model.providerID,
            name: model.info.name,
            release_date: model.info.release_date,
            capabilities: {
              reasoning: model.info.reasoning,
              tool_call: model.info.tool_call,
              temperature: model.info.temperature,
              attachment: model.info.attachment,
            },
            cost: model.info.cost,
            limits: model.info.limit,
            experimental: model.info.experimental,
          },
          null,
          2,
        ),
      )
    } else {
      console.log(`Model: ${model.providerID}/${model.modelID}`)
      console.log(`Name: ${model.info.name}`)
      console.log(`Release Date: ${model.info.release_date}`)
      console.log(`Capabilities:`)
      console.log(`  - Reasoning: ${model.info.reasoning ? "Yes" : "No"}`)
      console.log(`  - Tool Calling: ${model.info.tool_call ? "Yes" : "No"}`)
      console.log(`  - Temperature Control: ${model.info.temperature ? "Yes" : "No"}`)
      console.log(`  - Attachments: ${model.info.attachment ? "Yes" : "No"}`)
      console.log(`Cost (per 1M tokens):`)
      console.log(`  - Input: $${model.info.cost.input}`)
      console.log(`  - Output: $${model.info.cost.output}`)
      console.log(`  - Cache Read: $${model.info.cost.cache_read || "N/A"}`)
      console.log(`  - Cache Write: $${model.info.cost.cache_write || "N/A"}`)
      console.log(`Limits:`)
      console.log(`  - Context: ${model.info.limit.context} tokens`)
      console.log(`  - Output: ${model.info.limit.output} tokens`)
      if (model.info.experimental) {
        console.log(`⚠️  This is an experimental model`)
      }
    }
  } catch (error) {
    console.error(`Error: Model ${providerID}/${modelID} not found`)
    process.exit(1)
  }
}

// ==================== UTILITY FUNCTIONS ====================

function buildFilters(argv: any): ModelFilter {
  const filters: ModelFilter = {}

  if (argv.provider) filters.provider = argv.provider
  if (argv.name) filters.name = argv.name
  if (argv.cost) filters.cost = argv.cost
  if (argv.capabilities) {
    filters.capabilities = argv.capabilities.split(",").map((c: string) => c.trim())
  }
  if (argv.limit) filters.limit = argv.limit

  return filters
}

async function getFilteredModels(providers: Record<string, any>, filters: ModelFilter): Promise<any[]> {
  const models: any[] = []

  for (const [providerID, provider] of Object.entries(providers)) {
    if (filters.provider && !providerID.includes(filters.provider)) continue

    for (const [modelID, model] of Object.entries(provider.info.models as Record<string, ModelsDev.Model>)) {
      if (
        filters.name &&
        !model.name.toLowerCase().includes(filters.name.toLowerCase()) &&
        !modelID.toLowerCase().includes(filters.name.toLowerCase())
      )
        continue

      if (filters.cost) {
        const isFree = model.cost.input === 0 && model.cost.output === 0
        if (filters.cost === "free" && !isFree) continue
        if (filters.cost === "paid" && isFree) continue
      }

      if (filters.capabilities) {
        let hasAllCapabilities = true
        for (const cap of filters.capabilities) {
          switch (cap) {
            case "reasoning":
              if (!model.reasoning) hasAllCapabilities = false
              break
            case "tool_call":
              if (!model.tool_call) hasAllCapabilities = false
              break
            case "temperature":
              if (!model.temperature) hasAllCapabilities = false
              break
            case "attachment":
              if (!model.attachment) hasAllCapabilities = false
              break
          }
        }
        if (!hasAllCapabilities) continue
      }

      models.push({
        provider: providerID,
        model: modelID,
        name: model.name,
        cost: model.cost,
        capabilities: {
          reasoning: model.reasoning,
          tool_call: model.tool_call,
          temperature: model.temperature,
          attachment: model.attachment,
        },
        limits: model.limit,
        release_date: model.release_date,
        experimental: model.experimental,
      })

      if (filters.limit && models.length >= filters.limit) break
    }

    if (filters.limit && models.length >= filters.limit) break
  }

  return models
}

// ==================== OUTPUT FUNCTIONS ====================

function outputModelsTable(models: any[]) {
  if (models.length === 0) {
    console.log("No models found.")
    return
  }

  console.log("Provider/Model".padEnd(40), "Name".padEnd(25), "Cost".padEnd(15), "Capabilities".padEnd(20))
  console.log("-".repeat(100))

  for (const model of models) {
    const modelId = `${model.provider}/${model.model}`.padEnd(40)
    const name = (model.name || model.model).padEnd(25)
    const cost =
      model.cost.input === 0 && model.cost.output === 0
        ? "Free"
        : `$${model.cost.input}/$${model.cost.output}`.padEnd(15)

    const caps: string[] = []
    if (model.capabilities.reasoning) caps.push("R")
    if (model.capabilities.tool_call) caps.push("T")
    if (model.capabilities.temperature) caps.push("Temp")
    if (model.capabilities.attachment) caps.push("Att")
    const capabilities = caps.join(",").padEnd(20)

    console.log(`${modelId}${name}${cost}${capabilities}`)
  }
}

function outputModelsCSV(models: any[]) {
  console.log(
    "provider,model,name,input_cost,output_cost,reasoning,tool_call,temperature,attachment,context_limit,output_limit,release_date,experimental",
  )

  for (const model of models) {
    const row = [
      model.provider,
      model.model,
      model.name || model.model,
      model.cost.input,
      model.cost.output,
      model.capabilities.reasoning,
      model.capabilities.tool_call,
      model.capabilities.temperature,
      model.capabilities.attachment,
      model.limits.context,
      model.limits.output,
      model.release_date,
      model.experimental || false,
    ]
      .map((v) => `"${v}"`)
      .join(",")

    console.log(row)
  }
}

function outputRecommendationsTable(recommendations: ModelRecommendation[]) {
  if (recommendations.length === 0) {
    console.log("No recommendations available.")
    return
  }

  console.log("Model".padEnd(35), "Score".padEnd(8), "Cost".padEnd(10), "Capabilities".padEnd(20))
  console.log("-".repeat(80))
  console.log("Reasoning")
  console.log("-".repeat(80))

  for (const rec of recommendations.sort((a, b) => b.score - a.score)) {
    const modelId = `${rec.provider}/${rec.model}`.padEnd(35)
    const score = `${rec.score}%`.padEnd(8)
    const cost = `$${rec.cost.toFixed(3)}`.padEnd(10)
    const capabilities = rec.capabilities.join(",").padEnd(20)
    console.log(`${modelId}${score}${cost}${capabilities}`)
    console.log(`${rec.reasoning}`)
    console.log()
  }
}

// ==================== PROVIDER MANAGEMENT FUNCTIONS ====================

async function listProviders(argv: any) {
  const providers = await ProviderConfigManager.listConfiguredProviders()

  if (argv.format === "json") {
    console.log(JSON.stringify(providers, null, 2))
  } else {
    console.log("Configured Providers:")
    console.log("ID".padEnd(20), "Name".padEnd(25), "Enabled".padEnd(10), "Models".padEnd(8), "Status")
    console.log("-".repeat(80))

    for (const provider of providers) {
      const status = await ProviderConfigManager.getProviderStatus(provider.id)
      const enabled = status.enabled ? "Yes" : "No"
      const models = status.modelsAvailable.toString()
      const statusText = status.hasCredentials ? "Ready" : "No credentials"

      console.log(
        provider.id.padEnd(20),
        (provider.name || provider.id).padEnd(25),
        enabled.padEnd(10),
        models.padEnd(8),
        statusText,
      )
    }
  }
}

async function manageProvider(argv: any) {
  const subAction = argv._[1] as string
  const providerID = argv._[2] as string

  if (!subAction || !providerID) {
    console.log("Usage: opencode models provider <enable|disable|status|config|reset> <provider-id>")
    exit(1)
  }

  switch (subAction) {
    case "enable":
      await ProviderConfigManager.updateProviderConfig(providerID, { enabled: true })
      console.log(`Provider ${providerID} enabled`)
      break

    case "disable":
      await ProviderConfigManager.updateProviderConfig(providerID, { enabled: false })
      console.log(`Provider ${providerID} disabled`)
      break

    case "status":
      const status = await ProviderConfigManager.getProviderStatus(providerID)
      console.log(`Provider: ${providerID}`)
      console.log(`Configured: ${status.configured ? "Yes" : "No"}`)
      console.log(`Enabled: ${status.enabled ? "Yes" : "No"}`)
      console.log(`Has Credentials: ${status.hasCredentials ? "Yes" : "No"}`)
      console.log(`Models Available: ${status.modelsAvailable}`)
      if (status.validationErrors.length > 0) {
        console.log("Validation Errors:")
        status.validationErrors.forEach((error) => console.log(`  - ${error}`))
      }
      break

    case "config":
      const config = await ProviderConfigManager.getProviderConfig(providerID)
      if (!config) {
        console.log(`Provider ${providerID} not found`)
        exit(1)
      }

      if (argv.format === "json") {
        console.log(JSON.stringify(config, null, 2))
      } else {
        console.log(`Provider Configuration: ${providerID}`)
        console.log(`Name: ${config.name || "N/A"}`)
        console.log(`API: ${config.api || "N/A"}`)
        console.log(`NPM Package: ${config.npm || "N/A"}`)
        console.log(`Environment Variables: ${config.env?.join(", ") || "None"}`)
        console.log(`Enabled: ${config.enabled ? "Yes" : "No"}`)
        console.log(`Custom Models: ${Object.keys(config.models || {}).length}`)
        console.log(`Options: ${JSON.stringify(config.options || {}, null, 2)}`)
      }
      break

    case "reset":
      await ProviderConfigManager.resetProviderToDefault(providerID)
      console.log(`Provider ${providerID} reset to default configuration`)
      break

    default:
      console.log("Available sub-actions: enable, disable, status, config, reset")
      exit(1)
  }
}
