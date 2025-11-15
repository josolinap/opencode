import z from "zod"
import { Tool } from "./tool"
import DESCRIPTION from "./websearch.txt"
import { Config } from "../config/config"
import { Permission } from "../permission"
import { isWebSearchMVPEnabled } from "../storage/feature-flags"
import { WebSearchCache } from "../storage/cache/web_search_cache"

const API_CONFIG = {
  BASE_URL: "https://mcp.exa.ai",
  ENDPOINTS: {
    SEARCH: "/mcp",
  },
  DEFAULT_NUM_RESULTS: 8,
} as const

interface McpSearchRequest {
  jsonrpc: string
  id: number
  method: string
  params: {
    name: string
    arguments: {
      query: string
      numResults?: number
      livecrawl?: "fallback" | "preferred"
      type?: "auto" | "fast" | "deep"
      contextMaxCharacters?: number
    }
  }
}

interface McpSearchResponse {
  jsonrpc: string
  result: {
    content: Array<{
      type: string
      text: string
    }>
  }
}

export const WebSearchTool = Tool.define("websearch", {
  description: DESCRIPTION,
  parameters: z.object({
    query: z.string().describe("Websearch query"),
    numResults: z.number().optional().describe("Number of search results to return (default: 8)"),
    livecrawl: z
      .enum(["fallback", "preferred"])
      .optional()
      .describe(
        "Live crawl mode - 'fallback': use live crawling as backup if cached content unavailable, 'preferred': prioritize live crawling (default: 'fallback')",
      ),
    type: z
      .enum(["auto", "fast", "deep"])
      .optional()
      .describe("Search type - 'auto': balanced search (default), 'fast': quick results, 'deep': comprehensive search"),
    contextMaxCharacters: z
      .number()
      .optional()
      .describe("Maximum characters for context string optimized for LLMs (default: 10000)"),
    bypassCache: z.boolean().optional().describe("Bypass web search cache and perform live search"),
    ttlMs: z.number().optional().describe("Cache TTL in milliseconds for results"),
    summarize: z.boolean().optional().describe("Summarize top results and include a short summary in the response"),
    summaryCount: z.number().optional().describe("Number of results to summarize (default: 3)"),
  }),
  async execute(params, ctx) {
    const cfg = await Config.get()
    if (cfg.permission?.webfetch === "ask")
      await Permission.ask({
        type: "websearch",
        sessionID: ctx.sessionID,
        messageID: ctx.messageID,
        callID: ctx.callID,
        title: "Search web for: " + params.query,
        metadata: {
          query: params.query,
          numResults: params.numResults,
          livecrawl: params.livecrawl,
          type: params.type,
          contextMaxCharacters: params.contextMaxCharacters,
        },
      })

    const searchRequest: McpSearchRequest = {
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: "web_search_exa",
        arguments: {
          query: params.query,
          type: params.type || "auto",
          numResults: params.numResults || API_CONFIG.DEFAULT_NUM_RESULTS,
          livecrawl: params.livecrawl || "fallback",
          contextMaxCharacters: params.contextMaxCharacters,
        },
      },
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)

    // Cache lookup (optional)
    const bypassCache = params.bypassCache ?? false
    if (!bypassCache) {
      const cached = WebSearchCache.get(params.query)
      if (cached) {
        clearTimeout(timeoutId)
        return cached
      }
    }

    try {
      const headers: Record<string, string> = {
        "User-Agent": "Opencode-WebSearch/1.0",
        accept: "application/json, text/event-stream",
        "content-type": "application/json",
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.SEARCH}`, {
        method: "POST",
        headers,
        body: JSON.stringify(searchRequest),
        signal: AbortSignal.any([controller.signal, ctx.abort]),
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Search error (${response.status}): ${errorText}`)
      }

      const responseText = await response.text()

      // Parse SSE response
      const lines = responseText.split("\n")
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data: McpSearchResponse = JSON.parse(line.substring(6))
          if (data.result && data.result.content && data.result.content.length > 0) {
            const results = data.result.content.map((c) => c.text)
            const summarizeEnabled = params.summarize ?? true
            const summaryCount = params.summaryCount ?? 3
            const summaryText =
              summarizeEnabled && results.length > 0
                ? results.slice(0, Math.min(summaryCount, results.length)).join(" ")
                : ""

            const base = {
              output: results[0] ?? "",
              title: `Web search: ${params.query}`,
              metadata: {},
            }

            if (isWebSearchMVPEnabled()) {
              const mvpPayload = {
                credibility_score: 0.5,
                quotes: [],
                source_type: "Tier2" as const,
                source_id: "exa-web-01",
                corroboration_count: 0,
                sourceMap: {
                  claim_key: params.query,
                  sources: [],
                },
              }
              const finalMetadata = { ...base.metadata, mvp: mvpPayload }
              const finalResult = { ...base, metadata: finalMetadata, results, summary: summaryText }
              WebSearchCache.set(params.query, finalResult, params.ttlMs)
              return finalResult
            }

            const finalResult = { ...base, results, summary: summaryText }
            WebSearchCache.set(params.query, finalResult, params.ttlMs)
            return finalResult
          }
        }
      }

      return {
        output: "No search results found. Please try a different query.",
        title: `Web search: ${params.query}`,
        metadata: {},
      }
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Search request timed out")
      }

      throw error
    }
  },
})
