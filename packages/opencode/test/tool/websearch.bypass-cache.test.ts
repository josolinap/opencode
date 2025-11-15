import { WebSearchTool } from "../../src/tool/websearch"
import { WebSearchCache } from "../../src/storage/cache/web_search_cache"
import { test, expect } from "bun:test"

test("websearch bypassCache uses live fetch when bypassCache is true", async () => {
  WebSearchCache.clear()
  // seed cache with a value to verify bypass works
  WebSearchCache.set(
    "cached-query",
    {
      output: "Cached result",
      title: "Web search: cached-query",
      metadata: {},
      results: ["Cached result"],
    },
    60 * 1000,
  )

  let fetchCalled = false
  ;(globalThis as any).fetch = async () => {
    fetchCalled = true
    return {
      ok: true,
      text: async () => 'data: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"Live result"}]}}',
    } as any
  }

  const ctx = { sessionID: "s", messageID: "m", callID: "c", abort: new AbortController().signal } as any
  const res = await WebSearchTool.execute({ query: "cached-query", bypassCache: true, type: "auto" } as any, ctx)

  // cleanup
  ;(globalThis as any).fetch = undefined

  expect(fetchCalled).toBe(true)
  expect(res).toBeDefined()
  expect(res.output).toBe("Live result")
  expect(Array.isArray((res as any).results)).toBe(true)
  expect((res as any).results[0]).toBe("Live result")
})

test("websearch bypassCache uses cache when bypassCache is false", async () => {
  WebSearchCache.clear()
  WebSearchCache.set(
    "cached-query-2",
    {
      output: "Cached 2",
      title: "Web search: cached-query-2",
      metadata: {},
      results: ["Cached 2"],
    },
    60 * 1000,
  )

  let fetchCalled = false
  ;(globalThis as any).fetch = async () => {
    fetchCalled = true
    return {
      ok: true,
      text: async () => 'data: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"Live"}]}}',
    } as any
  }

  const ctx = { sessionID: "s", messageID: "m", callID: "c", abort: new AbortController().signal } as any
  const res = await WebSearchTool.execute({ query: "cached-query-2", bypassCache: false, type: "auto" } as any, ctx)

  // cleanup
  ;(globalThis as any).fetch = undefined

  expect(fetchCalled).toBe(false)
  expect(res.output).toBe("Cached 2")
  expect(Array.isArray((res as any).results)).toBe(true)
  expect((res as any).results[0]).toBe("Cached 2")
})
