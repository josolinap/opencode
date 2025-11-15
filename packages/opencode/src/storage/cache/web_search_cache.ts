// storage/cache/web_search_cache.ts
// Simple TTL-based in-memory cache for Web Search MVP results.

type CacheEntry = {
  data: any
  timestamp: number
  ttlMs: number
}

const cache = new Map<string, CacheEntry>()
const DEFAULT_TTL_MS = 24 * 60 * 60 * 1000 // 24 hours

export const WebSearchCache = {
  get(query: string): any | undefined {
    const key = String(query)
    const entry = cache.get(key)
    if (!entry) return undefined
    const now = Date.now()
    if (now - entry.timestamp > entry.ttlMs) {
      cache.delete(key)
      return undefined
    }
    return entry.data
  },
  set(query: string, data: any, ttlMs?: number): void {
    cache.set(String(query), {
      data,
      timestamp: Date.now(),
      ttlMs: ttlMs ?? DEFAULT_TTL_MS,
    })
  },
  clear(): void {
    cache.clear()
  },
}
