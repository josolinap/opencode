import { describe, expect, test, beforeEach, afterEach, mock } from "bun:test"
import { WebSearchTool } from "../../src/tool/websearch"
import { setAutonomyContinueEnabled, setWebSearchMVPEnabled } from "../../src/storage/feature-flags"
import { Todo } from "../../src/session/todo"
import { telemetry } from "../../src/util/telemetry"

const ctx = {
  sessionID: "test-autopilot-session",
  messageID: "",
  toolCallID: "",
  agent: "build",
  abort: AbortSignal.any([]),
  metadata: () => {},
}

// Mock fetch for web search
const mockResponse = {
  ok: true,
  text: async () => 'data: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"mock search result"}]}}',
}

// @ts-ignore
global.fetch = mock(() => Promise.resolve(mockResponse as any))

describe("tool.websearch autopilot integration", () => {
  beforeEach(() => {
    // Reset flags
    setWebSearchMVPEnabled(false)
    setAutonomyContinueEnabled(false)
  })

  afterEach(() => {
    // Clean up
    setWebSearchMVPEnabled(false)
    setAutonomyContinueEnabled(false)
  })

  test("autonomy disabled: web search works normally without scheduling", async () => {
    setAutonomyContinueEnabled(false)
    setWebSearchMVPEnabled(true)

    const mockTodoGet = mock(() => Promise.resolve([]))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const result: any = await WebSearchTool.execute({ query: "test query" }, ctx)

    expect(result.output).toContain("mock")
    expect(result.title).toContain("Web search: test query")

    // Should not have attempted to schedule autonomous tasks
    expect(mockTodoGet).not.toHaveBeenCalled()
    expect(mockTodoUpdate).not.toHaveBeenCalled()
  })

  test("autonomy enabled: web search schedules next task after results", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    const existingTodos = [{ id: "task-1", content: "Initial task", status: "completed", priority: "high" }]
    const mockTodoGet = mock(() => Promise.resolve(existingTodos))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const result: any = await WebSearchTool.execute({ query: "test query" }, ctx)

    expect(result.output).toContain("mock")
    expect(result.title).toContain("Web search: test query")

    // Should have checked existing todos
    expect(mockTodoGet).toHaveBeenCalledWith("test-autopilot-session")

    // Should have scheduled autonomous continuation
    expect(mockTodoUpdate).toHaveBeenCalledWith({
      sessionID: "test-autopilot-session",
      todos: expect.arrayContaining([
        ...existingTodos,
        expect.objectContaining({
          content: expect.stringContaining("Auto continuation"),
          status: "pending",
          priority: "low",
          id: expect.stringMatching(/^auto-\d+$/),
        }),
      ]),
    })
  })

  test("autonomy telemetry: records autonomy events during web search", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    // Mock Todo to avoid actual scheduling
    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    await WebSearchTool.execute({ query: "test query" }, ctx)

    // Should have recorded autonomy telemetry
    const autonomyCalls = mockRecord.mock.calls.filter((call) => call[0].event?.startsWith("autonomy."))

    expect(autonomyCalls.length).toBeGreaterThan(0)

    // Check that autonomy events include required fields
    const autonomyEvent = autonomyCalls[0][0]
    expect(autonomyEvent).toHaveProperty("event")
    expect(autonomyEvent).toHaveProperty("sessionID", "test-autopilot-session")
    expect(autonomyEvent).toHaveProperty("autonomyEnabled", true)
    expect(autonomyEvent).toHaveProperty("timestamp")
  })

  test("autonomy error handling: continues working if scheduling fails", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    // Mock Todo.get to throw error
    Todo.get = mock(() => {
      throw new Error("Todo system unavailable")
    })
    Todo.update = mock(() => Promise.resolve())

    // Web search should still succeed despite autonomy scheduling failure
    const result: any = await WebSearchTool.execute({ query: "test query" }, ctx)

    expect(result.output).toContain("mock")
    expect(result.title).toContain("Web search: test query")

    // Should have attempted to get todos (and failed)
    expect(Todo.get).toHaveBeenCalledWith("test-autopilot-session")
  })

  test("privacy protection: no sensitive data in telemetry", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    await WebSearchTool.execute({ query: "search for confidential data" }, ctx)

    // Check all telemetry calls for privacy
    mockRecord.mock.calls.forEach((call) => {
      const event = call[0]

      // Should not contain raw queries or sensitive content
      expect(event).not.toHaveProperty("rawQuery")
      expect(event).not.toHaveProperty("sensitiveContent")

      // If user/session IDs are present, they should be hashed
      if (event.userId) {
        expect(event.userId).not.toBe("test-autopilot-session") // Should be hashed
      }
      if (event.sessionID) {
        expect(event.sessionID).toBe("test-autopilot-session") // Session ID can be raw for correlation
      }
    })
  })

  test("autonomy context propagation: passes correct context to scheduler", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mockTodoUpdate

    await WebSearchTool.execute({ query: "test query" }, ctx)

    // Check that the scheduled task includes proper context
    const updateCall = mockTodoUpdate.mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))

    expect(scheduledTask).toBeDefined()
    expect(scheduledTask.content).toContain("Auto continuation")
    expect(scheduledTask.status).toBe("pending")
    expect(scheduledTask.priority).toBe("low")
  })
})
