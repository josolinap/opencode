import { describe, expect, test, beforeEach, afterEach, mock } from "bun:test"
import { DataInspectorTool } from "../../src/tool/datainspector"
import { setAutonomyContinueEnabled } from "../../src/storage/feature-flags"
import { Todo } from "../../src/session/todo"
import { telemetry } from "../../src/util/telemetry"

const ctx = {
  sessionID: "test-datainspector-session",
  messageID: "",
  callID: "call-123",
  agent: "build",
  abort: AbortSignal.any([]),
  metadata: () => {},
}

describe("tool.datainspector autopilot integration", () => {
  beforeEach(() => {
    // Reset flags
    setAutonomyContinueEnabled(false)
  })

  afterEach(() => {
    // Clean up
    setAutonomyContinueEnabled(false)
  })

  test("autonomy disabled: data inspector works normally without scheduling", async () => {
    setAutonomyContinueEnabled(false)

    const mockTodoGet = mock(() => Promise.resolve([]))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const csvData = "name,age,city\nJohn,25,NYC\nJane,30,LA\n"
    const result: any = await DataInspectorTool.init().then((tool) => tool.execute({ data: csvData }, ctx))

    expect(result.output).toContain("Rows: 2")
    expect(result.title).toBe("Data Inspector")

    // Should not have attempted to schedule autonomous tasks
    expect(mockTodoGet).not.toHaveBeenCalled()
    expect(mockTodoUpdate).not.toHaveBeenCalled()
  })

  test("autonomy enabled: data inspector schedules next task after analysis", async () => {
    setAutonomyContinueEnabled(true)

    const existingTodos = [{ id: "task-1", content: "Analyze dataset", status: "completed", priority: "high" }]
    const mockTodoGet = mock(() => Promise.resolve(existingTodos))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const csvData = "product,price,rating\nWidget,19.99,4.5\nGadget,29.99,4.2\n"
    const result: any = await DataInspectorTool.init().then((tool) => tool.execute({ data: csvData }, ctx))

    expect(result.output).toContain("Rows: 2")
    expect(result.title).toBe("Data Inspector")

    // Should have checked existing todos
    expect(mockTodoGet).toHaveBeenCalledWith("test-datainspector-session")

    // Should have scheduled autonomous continuation
    expect(mockTodoUpdate).toHaveBeenCalledWith({
      sessionID: "test-datainspector-session",
      todos: expect.arrayContaining([
        ...existingTodos,
        expect.objectContaining({
          content: expect.stringContaining("Explore relationships between key columns"),
          status: "pending",
          priority: "low",
          id: expect.stringMatching(/^auto-\d+$/),
        }),
      ]),
    })
  })

  test("autonomy generates contextual follow-ups based on data analysis", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Test high missing data scenario
    const csvWithMissingData = "col1,col2,col3\nval1,,\n,val2,\n,," // 67% missing
    await DataInspectorTool.init().then((tool) => tool.execute({ data: csvWithMissingData }, ctx))

    // Should suggest data cleaning strategies
    const updateCall = Todo.update.mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("missing data rate")
    expect(scheduledTask.content).toContain("data cleaning strategies")
  })

  test("autonomy handles JSON data analysis", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    const jsonData = '[{"score": 85, "grade": "A"}, {"score": 92, "grade": "A"}, {"score": 78, "grade": "B"}]'
    await DataInspectorTool.init().then((tool) => tool.execute({ data: jsonData, format: "json" }, ctx))

    // Should suggest numeric field analysis
    const updateCall = Todo.update.mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("numeric field distributions")
  })

  test("autonomy handles data parsing errors", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    const invalidData = '{"invalid": json syntax}' // Invalid JSON
    await DataInspectorTool.init().then((tool) => tool.execute({ data: invalidData, format: "json" }, ctx))

    // Should suggest investigating parsing errors
    const updateCall = Todo.update.mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("parsing error")
    expect(scheduledTask.content).toContain("suggest fixes")
  })

  test("autonomy respects session limits to prevent infinite loops", async () => {
    setAutonomyContinueEnabled(true)

    // Mock existing todos at the limit (5 auto tasks)
    const existingTodos = Array(5)
      .fill(null)
      .map((_, i) => ({
        id: `auto-${i}`,
        content: `Auto task ${i}`,
        status: "pending",
        priority: "low",
      }))

    Todo.get = mock(() => Promise.resolve(existingTodos))
    Todo.update = mock(() => Promise.resolve())

    const csvData = "name,value\nTest,123\n"
    const result: any = await DataInspectorTool.init().then((tool) => tool.execute({ data: csvData }, ctx))

    // Data inspection should still succeed
    expect(result.output).toContain("Rows: 1")

    // But autonomy should be blocked due to limit
    expect(Todo.update).not.toHaveBeenCalled()
  })

  test("autonomy telemetry: records data inspector autonomy events", async () => {
    setAutonomyContinueEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    const csvData = "category,sales\nA,100\nB,200\n"
    await DataInspectorTool.init().then((tool) => tool.execute({ data: csvData }, ctx))

    // Should have recorded autonomy telemetry
    const autonomyCalls = mockRecord.mock.calls.filter((call) => call[0].event?.startsWith("autonomy."))

    expect(autonomyCalls.length).toBeGreaterThan(0)

    // Check schedule event
    const scheduleEvent = autonomyCalls.find((e: any) => e.event === "autonomy.schedule_next_task")
    expect(scheduleEvent).toBeDefined()
    expect(scheduleEvent.sessionID).toBe("test-datainspector-session")
    expect(scheduleEvent.currentTaskId).toBe("call-123")
    expect(scheduleEvent.outcome).toBe("scheduled")
    expect(scheduleEvent.autonomyEnabled).toBe(true)
  })

  test("autonomy error handling: data inspection succeeds despite scheduling failures", async () => {
    setAutonomyContinueEnabled(true)

    // Mock Todo operations to fail
    Todo.get = mock(() => {
      throw new Error("Todo system unavailable")
    })
    Todo.update = mock(() => Promise.resolve())

    const csvData = "name,age\nJohn,25\nJane,30\n"
    const result: any = await DataInspectorTool.init().then((tool) => tool.execute({ data: csvData }, ctx))

    // Data inspection should still succeed
    expect(result.output).toContain("Rows: 2")
    expect(result.title).toBe("Data Inspector")

    // Should have attempted autonomy (and failed safely)
    expect(Todo.get).toHaveBeenCalledWith("test-datainspector-session")
  })

  test("privacy protection: no sensitive data in data inspector telemetry", async () => {
    setAutonomyContinueEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Use data that might contain sensitive information
    const sensitiveData = "ssn,name,salary\n123-45-6789,John Doe,75000\n987-65-4321,Jane Smith,80000\n"
    await DataInspectorTool.init().then((tool) => tool.execute({ data: sensitiveData }, ctx))

    // Check all telemetry calls for privacy
    mockRecord.mock.calls.forEach((call) => {
      const event = call[0]

      // Should not contain raw data or sensitive content
      expect(event).not.toHaveProperty("rawData")
      expect(event).not.toHaveProperty("data")
      expect(event).not.toHaveProperty("csvContent")

      // Session ID can be raw for correlation
      if (event.sessionID) {
        expect(event.sessionID).toBe("test-datainspector-session")
      }

      // Autonomy events should have proper structure
      if (event.event?.startsWith("autonomy.")) {
        expect(event).toHaveProperty("autonomyEnabled", true)
        expect(event).toHaveProperty("timestamp")
      }
    })
  })
})
