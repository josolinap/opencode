import { describe, expect, test, beforeEach, afterEach, mock } from "bun:test"
import { CodeSearchTool } from "../../src/tool/codesearch"
import { setAutonomyContinueEnabled } from "../../src/storage/feature-flags"
import { Todo } from "../../src/session/todo"
import { telemetry } from "../../src/util/telemetry"

const ctx = {
  sessionID: "test-codesearch-session",
  messageID: "",
  callID: "call-123",
  agent: "build",
  abort: AbortSignal.any([]),
  metadata: () => {},
}

// Mock external code search API
const mockCodeResponse = {
  ok: true,
  text: async () =>
    'data: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"Sample React useState code example"}]}}',
}

// Mock fetch for code search
let searchCalls = 0
// @ts-ignore
global.fetch = mock(() => {
  searchCalls++
  return mockCodeResponse
})

describe("tool.codesearch autopilot integration", () => {
  beforeEach(() => {
    // Reset state
    setAutonomyContinueEnabled(false)
    searchCalls = 0

    // Clear any existing telemetry
    telemetry.clear?.()
  })

  afterEach(() => {
    // Clean up
    setAutonomyContinueEnabled(false)
  })

  test("autonomy disabled: code search works normally without scheduling", async () => {
    setAutonomyContinueEnabled(false)

    const mockTodoGet = mock(() => Promise.resolve([]))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const result: any = await CodeSearchTool.init().then((tool) =>
      tool.execute({ query: "React useState examples", tokensNum: 5000 }, ctx),
    )

    expect(result.output).toContain("Sample React useState code")
    expect(result.title).toContain("Code search: React useState examples")
    expect(searchCalls).toBe(1)

    // Should not have attempted to schedule autonomous tasks
    expect(mockTodoGet).not.toHaveBeenCalled()
    expect(mockTodoUpdate).not.toHaveBeenCalled()
  })

  test("autonomy enabled: code search schedules next task after analysis", async () => {
    setAutonomyContinueEnabled(true)

    const existingTodos = [
      { id: "task-1", content: "Search for React patterns", status: "completed", priority: "high" },
    ]
    const mockTodoGet = mock(() => Promise.resolve(existingTodos))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const result: any = await CodeSearchTool.init().then((tool) =>
      tool.execute({ query: "React useState examples", tokensNum: 5000 }, ctx),
    )

    expect(result.output).toContain("Sample React useState code")
    expect(result.title).toContain("Code search: React useState examples")
    expect(searchCalls).toBe(1)

    // Should have checked existing todos
    expect(mockTodoGet).toHaveBeenCalledWith("test-codesearch-session")

    // Should have scheduled autonomous continuation
    expect(mockTodoUpdate).toHaveBeenCalledWith({
      sessionID: "test-codesearch-session",
      todos: expect.arrayContaining([
        ...existingTodos,
        expect.objectContaining({
          content: expect.stringContaining("design pattern improvements"),
          status: "pending",
          priority: "low",
          id: expect.stringMatching(/^auto-\d+$/),
        }),
      ]),
    })
  })

  test("autonomy generates contextual follow-ups based on code search query", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Test error handling query
    await CodeSearchTool.init().then((tool) => tool.execute({ query: "error handling patterns", tokensNum: 5000 }, ctx))

    // Should suggest error handling improvements
    const updateCall = (Todo.update as any).mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("error patterns")
    expect(scheduledTask.content).toContain("error handling improvements")
  })

  test("autonomy generates contextual follow-ups based on code content", async () => {
    setAutonomyContinueEnabled(true)

    // Mock response with async/await patterns
    const asyncMockResponse = {
      ok: true,
      text: async () =>
        'data: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"async function example() { await fetchData(); }"}]}}',
    }

    // @ts-ignore
    global.fetch = mock(() => asyncMockResponse)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    await CodeSearchTool.init().then((tool) => tool.execute({ query: "async patterns", tokensNum: 5000 }, ctx))

    // Should suggest concurrency improvements
    const updateCall = (Todo.update as any).mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("asynchronous patterns")
    expect(scheduledTask.content).toContain("concurrency improvements")
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

    const result: any = await CodeSearchTool.init().then((tool) =>
      tool.execute({ query: "test query", tokensNum: 5000 }, ctx),
    )

    // Code search should still succeed
    expect(result.output).toContain("Sample React useState code")
    expect(searchCalls).toBe(1)

    // But autonomy should be blocked due to limit
    expect(Todo.update).not.toHaveBeenCalled()
  })

  test("autonomy telemetry: records code search autonomy events", async () => {
    setAutonomyContinueEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    await CodeSearchTool.init().then((tool) => tool.execute({ query: "React patterns", tokensNum: 5000 }, ctx))

    // Should have recorded autonomy telemetry
    const autonomyCalls = mockRecord.mock.calls.filter((call) => call[0].event?.startsWith("autonomy."))

    expect(autonomyCalls.length).toBeGreaterThan(0)

    // Check schedule event
    const scheduleEvent = autonomyCalls.find((e: any) => e.event === "autonomy.schedule_next_task")
    expect(scheduleEvent).toBeDefined()
    expect(scheduleEvent.sessionID).toBe("test-codesearch-session")
    expect(scheduleEvent.currentTaskId).toBe("call-123")
    expect(scheduleEvent.outcome).toBe("scheduled")
    expect(scheduleEvent.autonomyEnabled).toBe(true)
  })

  test("autonomy error handling: code search succeeds despite scheduling failures", async () => {
    setAutonomyContinueEnabled(true)

    // Mock Todo operations to fail
    Todo.get = mock(() => {
      throw new Error("Todo system unavailable")
    })
    Todo.update = mock(() => Promise.resolve())

    const result: any = await CodeSearchTool.init().then((tool) =>
      tool.execute({ query: "test query", tokensNum: 5000 }, ctx),
    )

    // Code search should still succeed
    expect(result.output).toContain("Sample React useState code")
    expect(searchCalls).toBe(1)

    // Should have attempted autonomy (and failed safely)
    expect(Todo.get).toHaveBeenCalledWith("test-codesearch-session")
  })

  test("privacy protection: no sensitive data in code search telemetry", async () => {
    setAutonomyContinueEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Execute search with potentially sensitive query
    await CodeSearchTool.init().then((tool) =>
      tool.execute({ query: "private API key handling", tokensNum: 5000 }, ctx),
    )

    // Check all telemetry calls for privacy
    mockRecord.mock.calls.forEach((call: any) => {
      const event = call[0]

      // Should not contain raw queries or sensitive content
      expect(event).not.toHaveProperty("rawQuery")
      expect(event).not.toHaveProperty("query")
      expect(event).not.toHaveProperty("codeContent")

      // Session ID can be raw for correlation
      if (event.sessionID) {
        expect(event.sessionID).toBe("test-codesearch-session")
      }

      // Autonomy events should have proper structure
      if (event.event?.startsWith("autonomy.")) {
        expect(event).toHaveProperty("autonomyEnabled", true)
        expect(event).toHaveProperty("timestamp")
      }
    })
  })

  test("autonomy context propagation: passes correct context to scheduler", async () => {
    setAutonomyContinueEnabled(true)

    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mockTodoUpdate

    await CodeSearchTool.init().then((tool) => tool.execute({ query: "test query", tokensNum: 5000 }, ctx))

    // Check that the scheduled task includes proper context
    const updateCall = mockTodoUpdate.mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))

    expect(scheduledTask).toBeDefined()
    expect(scheduledTask.content).toBeTruthy()
    expect(typeof scheduledTask.content).toBe("string")
    expect(scheduledTask.status).toBe("pending")
    expect(scheduledTask.priority).toBe("low")
  })
})
