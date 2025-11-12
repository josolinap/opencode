import { Global } from "../global"
import { Log } from "../util/log"
import path from "path"
import z from "zod/v4"
import { data } from "./models-macro" with { type: "macro" }
import { Installation } from "../installation"

export namespace ModelsDev {
  const log = Log.create({ service: "models.dev" })
  const filepath = path.join(Global.Path.cache, "models.json")
  const metadataFile = path.join(Global.Path.cache, "models_metadata.json")

  // Cache metadata to track freshness
  const CacheMetadata = z.object({
    lastFetch: z.number(),
    etag: z.string().optional(),
    lastModified: z.string().optional(),
    version: z.string(),
  })

  export const Model = z
    .object({
      id: z.string(),
      name: z.string(),
      release_date: z.string(),
      attachment: z.boolean(),
      reasoning: z.boolean(),
      temperature: z.boolean(),
      tool_call: z.boolean(),
      cost: z.object({
        input: z.number(),
        output: z.number(),
        cache_read: z.number().optional(),
        cache_write: z.number().optional(),
      }),
      limit: z.object({
        context: z.number(),
        output: z.number(),
      }),
      experimental: z.boolean().optional(),
      options: z.record(z.string(), z.any()),
      provider: z.object({ npm: z.string() }).optional(),
    })
    .meta({
      ref: "Model",
    })
  export type Model = z.infer<typeof Model>

  export const Provider = z
    .object({
      api: z.string().optional(),
      name: z.string(),
      env: z.array(z.string()),
      id: z.string(),
      npm: z.string().optional(),
      models: z.record(z.string(), Model),
    })
    .meta({
      ref: "Provider",
    })

  export type Provider = z.infer<typeof Provider>

  // Cache settings
  const CACHE_DURATION = 60 * 60 * 1000 // 1 hour
  const MAX_CACHE_AGE = 24 * 60 * 60 * 1000 // 24 hours

  export async function get(): Promise<Record<string, Provider>> {
    // Try to get from cache first
    const cached = await getCached()
    if (cached) {
      // Trigger background refresh if cache is stale
      refresh()
      return cached
    }

    // No cache or cache invalid, fetch fresh data
    await refresh()
    const file = Bun.file(filepath)
    const result = await file.json().catch(() => {})
    if (result) return result as Record<string, Provider>

    // Fallback to built-in data
    const json = await data()
    return JSON.parse(json) as Record<string, Provider>
  }

  export async function refresh(): Promise<void> {
    const file = Bun.file(filepath)

    try {
      // Check if we need to refresh
      const metadata = await getCacheMetadata()
      const now = Date.now()

      if (metadata && now - metadata.lastFetch < CACHE_DURATION) {
        log.debug("Cache still fresh, skipping refresh")
        return
      }

      log.info("refreshing models.dev data")

      const headers: Record<string, string> = {
        "User-Agent": Installation.USER_AGENT,
      }

      // Add conditional headers if we have them
      if (metadata?.etag) headers["If-None-Match"] = metadata.etag
      if (metadata?.lastModified) headers["If-Modified-Since"] = metadata.lastModified

      const result = await fetch("https://models.dev/api.json", { headers })

      if (result.status === 304) {
        // Not modified, update last fetch time
        await updateCacheMetadata({ lastFetch: now })
        log.debug("Models.dev data not modified")
        return
      }

      if (!result.ok) {
        throw new Error(`HTTP ${result.status}: ${result.statusText}`)
      }

      const data = await result.text()
      await Bun.write(file, data)

      // Update metadata
      const newMetadata = {
        lastFetch: now,
        etag: result.headers.get("etag") || undefined,
        lastModified: result.headers.get("last-modified") || undefined,
        version: "1.0",
      }
      await updateCacheMetadata(newMetadata)

      log.info("Successfully refreshed models.dev data", {
        size: data.length,
        etag: newMetadata.etag,
      })
    } catch (error) {
      log.error("Failed to refresh models.dev data", { error })

      // If we have cached data and it's not too old, use it
      const metadata = await getCacheMetadata()
      if (metadata && Date.now() - metadata.lastFetch < MAX_CACHE_AGE) {
        log.warn("Using stale cache due to refresh failure")
        return
      }

      throw error
    }
  }

  export async function getCached(): Promise<Record<string, Provider> | null> {
    try {
      const file = Bun.file(filepath)
      const metadata = await getCacheMetadata()

      if (!metadata) return null

      // Check if cache is too old
      if (Date.now() - metadata.lastFetch > MAX_CACHE_AGE) {
        log.debug("Cache too old, will refresh")
        return null
      }

      const result = await file.json().catch(() => null)
      return result as Record<string, Provider> | null
    } catch (error) {
      log.warn("Failed to read cache", { error })
      return null
    }
  }

  export async function clearCache(): Promise<void> {
    try {
      await Bun.write(filepath, "")
      await Bun.write(metadataFile, "")
      log.info("Models cache cleared")
    } catch (error) {
      log.warn("Failed to clear models cache", { error })
    }
  }

  export async function getCacheStats(): Promise<{
    hasCache: boolean
    lastFetch: number | null
    cacheAge: number | null
    size: number | null
  }> {
    const metadata = await getCacheMetadata()
    let size = null

    try {
      const file = Bun.file(filepath)
      const exists = await file.exists()
      if (exists) {
        size = (await file.stat()).size
      }
    } catch {}

    return {
      hasCache: !!metadata,
      lastFetch: metadata?.lastFetch || null,
      cacheAge: metadata ? Date.now() - metadata.lastFetch : null,
      size,
    }
  }

  async function getCacheMetadata(): Promise<z.infer<typeof CacheMetadata> | null> {
    try {
      const file = Bun.file(metadataFile)
      if (!(await file.exists())) return null

      const data = await file.json()
      return CacheMetadata.parse(data)
    } catch {
      return null
    }
  }

  async function updateCacheMetadata(metadata: Partial<z.infer<typeof CacheMetadata>>): Promise<void> {
    try {
      const existing = (await getCacheMetadata()) || {}
      const updated = { ...existing, ...metadata }
      await Bun.write(metadataFile, JSON.stringify(updated))
    } catch (error) {
      log.warn("Failed to update cache metadata", { error })
    }
  }
}

// Background refresh every hour
setInterval(() => ModelsDev.refresh(), 60 * 60 * 1000).unref()
