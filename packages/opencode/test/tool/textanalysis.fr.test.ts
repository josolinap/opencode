import { TextAnalysisTool } from "../../src/tool/textanalysis"
import { test, expect } from "bun:test"

test("text analysis with French sentence", async () => {
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await TextAnalysisTool.init()
  const res = await tool.execute({ text: "C'est très bon et fantastique!", language: "fr" }, ctx)
  expect(res).toBeDefined()
  expect(res.metadata).toBeDefined()
  expect(res.metadata.analysis.detectedLanguage).toBe("fr")
  expect(res.metadata.analysis.label).toBe("Positive")
})
