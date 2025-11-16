import { DataInspectorTool } from "../../src/tool/datainspector"
import { test, expect } from "bun:test"

test("datainspector CSV basic", async () => {
  const data = "col1,col2\n1,2\n3,4\n"
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const tool = await DataInspectorTool.init()
  const res = await tool.execute({ data, format: "csv" as any, sampleRows: 2 }, ctx)
  expect(res).toBeDefined()
  expect(res.output).toContain("Rows: 2")
  expect(res.metadata).toBeDefined()
  expect(res.metadata.details).toBeDefined()
  // header length check
  expect(res.metadata.details.headers.length).toBeGreaterThan(0)
})

test("datainspector JSON basic", async () => {
  const data = JSON.stringify([
    { a: 1, b: 2 },
    { a: 2, b: 3 },
  ])
  const ctx = { sessionID: "s", messageID: "m", abort: new AbortController().signal } as any
  const res = await (await DataInspectorTool.init()).execute({ data, format: "json" as any }, ctx)
  expect(res).toBeDefined()
  expect(res.output).toContain("Rows: 2")
  expect(res.metadata).toBeDefined()
  expect(res.metadata.details).toBeDefined()
  expect((res.metadata.details as any).numericSummary).toBeDefined()
})
