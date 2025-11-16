import { TextAnalysisTool } from "../../src/tool/textanalysis"
import { test, expect } from "bun:test"

test("text analysis with positive sentiment", async () => {
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await TextAnalysisTool.init()
  const res = await tool.execute({ text: "This is absolutely amazing and wonderful!", language: "en" }, ctx)
  expect(res).toBeDefined()
  expect(res.metadata).toBeDefined()
  expect(res.metadata.analysis.label).toBe("Positive")
  expect(res.metadata.analysis.confidence).toBeGreaterThan(0)
  expect(res.metadata.analysis.positive).toContain("amazing")
  expect(res.metadata.analysis.intensifiers).toContain("absolutely")
  expect(typeof res.output).toBe("string")
  expect(res.output.length).toBeGreaterThan(0)
})

test("text analysis with negation handling", async () => {
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await TextAnalysisTool.init()
  const res = await tool.execute({ text: "This is not good at all.", language: "en" }, ctx)
  expect(res).toBeDefined()
  expect(res.metadata.analysis.negations).toContain("not")
  expect(res.metadata.analysis.positive).toContain("good") // "good" is positive but negated
  expect(res.metadata.analysis.label).toBe("Negative") // Should be negative due to negation
})

test("text analysis with Spanish text", async () => {
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await TextAnalysisTool.init()
  const res = await tool.execute({ text: "Esto es muy bueno y excelente!", language: "es" }, ctx)
  expect(res).toBeDefined()
  expect(res.metadata.analysis.detectedLanguage).toBe("es")
  expect(res.metadata.analysis.label).toBe("Positive")
})

test("text analysis with neutral text", async () => {
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await TextAnalysisTool.init()
  const res = await tool.execute({ text: "The weather is okay today.", language: "en" }, ctx)
  expect(res).toBeDefined()
  expect(res.metadata.analysis.label).toBe("Neutral")
  expect(res.metadata.analysis.subjectivity).toBe("Objective")
})
