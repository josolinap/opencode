import { describe, expect, test } from "bun:test"
import { WebSearchTool } from "../../src/tool/websearch"
import { setWebSearchMVPEnabled } from "../../src/storage/feature-flags"
import { WebSearchCache } from "../../src/storage/cache/web_search_cache"

const ctx = {
  sessionID: "test",
  messageID: "",
  toolCallID: "",
  agent: "build",
  abort: AbortSignal.any([]),
  metadata: () => {},
}

// Simple mock for global fetch to simulate API responses
let fetchCalls = 0
const mockResponse = {
  ok: true,
  text: async () => 'data: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"mock result"}]}}',
}

// @ts-ignore
global.fetch = async () => {
  fetchCalls += 1
  return mockResponse as any
}

describe("tool.websearch (MVP) stability and enrichment", () => {
  test("MVP disabled: no MVP fields and no cache", async () => {
    setWebSearchMVPEnabled(false)
    WebSearchCache.clear?.()

    const res: any = await WebSearchTool.execute({ query: "test query" }, ctx)

    expect(res.output).toContain("mock")
    expect(res.title).toContain("Web search: test query")
    expect(res.metadata).not.toHaveProperty("mvp")
    // ensure a fetch occurred to get the data
    expect(fetchCalls).toBeGreaterThan(0)
  })

  test("MVP enabled: enrich with MVP payload and caching", async () => {
    fetchCalls = 0
    setWebSearchMVPEnabled(true)
    WebSearchCache.clear?.()

    const res1: any = await WebSearchTool.execute({ query: "test query" }, ctx)
    expect(res1.metadata).toHaveProperty("mvp")
    const mvp1 = res1.metadata.mvp
    expect(mvp1).toHaveProperty("credibility_score")

    // ensure cache has stored the result
    const res2: any = await WebSearchTool.execute({ query: "test query" }, ctx)
    // Second call should come from cache, so fetch should not be called again
    expect(fetchCalls).toBe(0) // since cache hit, no new fetch
    expect(res2.metadata).toHaveProperty("mvp")
  })
})
