import { Config } from "../config/config"
import { Provider } from "./provider"
import { ModelsDev } from "./models"
import { Log } from "../util/log"
import { NamedError } from "../util/error"
import z from "zod/v4"

const log = Log.create({ service: "provider-config" })

export interface ProviderConfig {
  id: string
  name?: string
  api?: string
  npm?: string
  env?: string[]
  options?: Record<string, any>
  models?: Record<string, ModelsDev.Model>
  enabled?: boolean
}

export namespace ProviderConfigManager {
  export async function listConfiguredProviders(): Promise<ProviderConfig[]> {
    const cfg = await Config.get()
    const providers: ProviderConfig[] = []

    // Get all available providers from ModelsDev
    const allProviders = await ModelsDev.get()

    for (const [providerID, providerInfo] of Object.entries(allProviders)) {
      const config = cfg.provider?.[providerID]
      const isEnabled = !cfg.disabled_providers?.includes(providerID)

      providers.push({
        id: providerID,
        name: config?.name || providerInfo.name,
        api: config?.api || providerInfo.api,
        npm: config?.npm || providerInfo.npm,
        env: config?.env || providerInfo.env,
        options: config?.options || {},
        models: (config?.models as Record<string, ModelsDev.Model>) || {},
        enabled: isEnabled,
      })
    }

    return providers
  }

  export async function getProviderConfig(providerID: string): Promise<ProviderConfig | null> {
    const providers = await listConfiguredProviders()
    return providers.find((p) => p.id === providerID) || null
  }

  export async function updateProviderConfig(providerID: string, updates: Partial<ProviderConfig>): Promise<void> {
    const cfg = await Config.get()

    if (!cfg.provider) cfg.provider = {}
    if (!cfg.provider[providerID]) cfg.provider[providerID] = {}

    const existing = cfg.provider[providerID]

    // Update configuration
    if (updates.name !== undefined) existing.name = updates.name
    if (updates.api !== undefined) existing.api = updates.api
    if (updates.npm !== undefined) existing.npm = updates.npm
    if (updates.env !== undefined) existing.env = updates.env
    if (updates.options !== undefined) existing.options = { ...existing.options, ...updates.options }
    if (updates.models !== undefined) existing.models = { ...existing.models, ...updates.models }

    // Handle enabled/disabled status
    if (updates.enabled !== undefined) {
      if (!cfg.disabled_providers) cfg.disabled_providers = []

      if (updates.enabled) {
        cfg.disabled_providers = cfg.disabled_providers.filter((id) => id !== providerID)
      } else {
        if (!cfg.disabled_providers.includes(providerID)) {
          cfg.disabled_providers.push(providerID)
        }
      }
    }

    await Config.update(cfg)
    log.info("Provider configuration updated", { providerID, updates })
  }

  export async function addCustomProvider(config: ProviderConfig): Promise<void> {
    const cfg = await Config.get()

    if (!cfg.provider) cfg.provider = {}
    if (cfg.provider[config.id]) {
      throw new ProviderAlreadyExistsError({ providerID: config.id })
    }

    cfg.provider[config.id] = {
      name: config.name,
      api: config.api,
      npm: config.npm,
      env: config.env,
      options: config.options || {},
      models: (config.models as Record<string, ModelsDev.Model>) || {},
    }

    await Config.update(cfg)
    log.info("Custom provider added", { providerID: config.id })
  }

  export async function removeProvider(providerID: string): Promise<void> {
    const cfg = await Config.get()

    if (cfg.provider?.[providerID]) {
      delete cfg.provider[providerID]
      await Config.update(cfg)
      log.info("Provider removed", { providerID })
    }

    // Also remove from disabled list if present
    if (cfg.disabled_providers) {
      cfg.disabled_providers = cfg.disabled_providers.filter((id) => id !== providerID)
      await Config.update(cfg)
    }
  }

  export async function validateProviderConfig(providerID: string): Promise<{ valid: boolean; errors: string[] }> {
    const config = await getProviderConfig(providerID)
    if (!config) {
      return { valid: false, errors: [`Provider ${providerID} not found`] }
    }

    const errors: string[] = []

    // Check if provider exists in ModelsDev
    const allProviders = await ModelsDev.get()
    if (!allProviders[providerID]) {
      errors.push(`Provider ${providerID} not found in Models.dev database`)
    }

    // Check environment variables
    if (config.env) {
      for (const envVar of config.env) {
        if (!process.env[envVar]) {
          errors.push(`Environment variable ${envVar} is not set`)
        }
      }
    }

    // Check API configuration
    if (config.api && !config.api.startsWith("http")) {
      errors.push(`API URL must start with http/https`)
    }

    return {
      valid: errors.length === 0,
      errors,
    }
  }

  export async function getProviderStatus(providerID: string): Promise<{
    configured: boolean
    enabled: boolean
    hasCredentials: boolean
    modelsAvailable: number
    validationErrors: string[]
  }> {
    const config = await getProviderConfig(providerID)
    const validation = await validateProviderConfig(providerID)

    let hasCredentials = false
    let modelsAvailable = 0

    if (config) {
      // Check if credentials are available
      hasCredentials = !config.env || config.env.some((envVar) => process.env[envVar])

      // Count available models
      try {
        const provider = await Provider.getProvider(providerID)
        if (provider) {
          modelsAvailable = Object.keys(provider.info.models).length
        }
      } catch (error) {
        // Provider not available
      }
    }

    return {
      configured: !!config,
      enabled: config?.enabled ?? false,
      hasCredentials,
      modelsAvailable,
      validationErrors: validation.errors,
    }
  }

  export async function resetProviderToDefault(providerID: string): Promise<void> {
    const cfg = await Config.get()

    if (cfg.provider?.[providerID]) {
      delete cfg.provider[providerID]
      await Config.update(cfg)
      log.info("Provider reset to default", { providerID })
    }
  }

  export async function exportProviderConfig(): Promise<string> {
    const providers = await listConfiguredProviders()
    return JSON.stringify(providers, null, 2)
  }

  export async function importProviderConfig(jsonConfig: string): Promise<void> {
    try {
      const providers = JSON.parse(jsonConfig) as ProviderConfig[]
      const cfg = await Config.get()

      if (!cfg.provider) cfg.provider = {}

      for (const provider of providers) {
        cfg.provider[provider.id] = {
          name: provider.name,
          api: provider.api,
          npm: provider.npm,
          env: provider.env,
          options: provider.options || {},
          models: provider.models || {},
        }
      }

      await Config.update(cfg)
      log.info("Provider configuration imported", { count: providers.length })
    } catch (error) {
      throw new InvalidConfigError({ reason: (error as Error).message })
    }
  }

  export const ProviderAlreadyExistsError = NamedError.create(
    "ProviderAlreadyExistsError",
    z.object({
      providerID: z.string(),
    }),
  )

  export const InvalidConfigError = NamedError.create(
    "InvalidProviderConfigError",
    z.object({
      reason: z.string(),
    }),
  )
}
