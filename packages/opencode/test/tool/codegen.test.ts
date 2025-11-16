import { CodeGenTool } from "../../src/tool/codegen"
import { test, expect } from "bun:test"

test("codegen with explanation", async () => {
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await CodeGenTool.init()
  const res = await tool.execute({ prompt: "Make a hello world in JS", language: "JavaScript", explain: true }, ctx)
  expect(res).toBeDefined()
  expect(res.metadata).toBeDefined()
  expect(res.metadata.language).toBe("JavaScript")
  expect(res.metadata.explanation).toBeDefined()
  expect(typeof res.output).toBe("string")
  expect(res.output.length).toBeGreaterThan(0)
})

test("codegen without explanation", async () => {
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await CodeGenTool.init()
  const res = await tool.execute({ prompt: "Make a hello world in Python", language: "Python", explain: false }, ctx)
  expect(res).toBeDefined()
  expect(res.metadata.explanation).toBeUndefined()
})
