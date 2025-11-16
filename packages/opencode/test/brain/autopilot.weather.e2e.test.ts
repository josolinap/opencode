import { describe, expect, test, beforeEach, afterEach, mock } from "bun:test"
import { WebSearchTool } from "../../src/tool/websearch"
import { setAutonomyContinueEnabled, setWebSearchMVPEnabled } from "../../src/storage/feature-flags"
import { Todo } from "../../src/session/todo"
import { telemetry } from "../../src/util/telemetry"

const ctx = {
  sessionID: "weather-test-session",
  messageID: "",
  toolCallID: "",
  agent: "build",
  abort: AbortSignal.any([]),
  metadata: () => {},
}

// Mock external weather API calls
const mockWeatherResponse = {
  ok: true,
  text: async () =>
    'data: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"Weather: Sunny, 72°F, 10% chance of rain"}]}}',
}

// Mock web search for weather queries
let searchCalls = 0
// @ts-ignore
global.fetch = mock(() => {
  searchCalls++
  return mockWeatherResponse
})

describe.skip("Autopilot Weather End-to-End Flow", () => {
  beforeEach(() => {
    // Reset state
    setWebSearchMVPEnabled(false)
    setAutonomyContinueEnabled(false)
    searchCalls = 0

    // Clear any existing telemetry
    telemetry.clear?.()
  })

  afterEach(() => {
    // Clean up
    setWebSearchMVPEnabled(false)
    setAutonomyContinueEnabled(false)
  })

  test("Weather query with autonomy OFF: single search, no continuation", async () => {
    setAutonomyContinueEnabled(false)
    setWebSearchMVPEnabled(true)

    // Mock empty backlog
    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Execute weather search
    const result: any = await WebSearchTool.execute({ query: "weather in Seattle today" }, ctx)

    // Verify search succeeded
    expect(result.output).toContain("Sunny")
    expect(result.title).toContain("Web search: weather in Seattle today")
    expect(searchCalls).toBe(1)

    // Verify no autonomy actions
    expect(Todo.get).not.toHaveBeenCalled()
    expect(Todo.update).not.toHaveBeenCalled()

    // Verify no autonomy telemetry
    const events = telemetry.getEvents?.() || []
    const autonomyEvents = events.filter((e: any) => e.event?.startsWith("autonomy."))
    expect(autonomyEvents.length).toBe(0)
  })

  test("Weather query with autonomy ON: search + autonomous continuation", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    // Mock existing backlog with one completed task
    const existingBacklog = [{ id: "task-1", content: "Check weather", status: "completed", priority: "high" }]
    Todo.get = mock(() => Promise.resolve(existingBacklog))
    Todo.update = mock(() => Promise.resolve())

    // Execute weather search
    const result: any = await WebSearchTool.execute({ query: "weather in Seattle today" }, ctx)

    // Verify search succeeded
    expect(result.output).toContain("Sunny")
    expect(result.title).toContain("Web search: weather in Seattle today")
    expect(searchCalls).toBe(1)

    // Verify autonomy was triggered
    expect(Todo.get).toHaveBeenCalledWith("weather-test-session")

    // Verify autonomous task was scheduled
    expect(Todo.update).toHaveBeenCalledWith({
      sessionID: "weather-test-session",
      todos: expect.arrayContaining([
        ...existingBacklog,
        expect.objectContaining({
          content: expect.stringContaining("Auto continuation"),
          status: "pending",
          priority: "low",
          id: expect.stringMatching(/^auto-\d+$/),
        }),
      ]),
    })

    // Verify autonomy telemetry was recorded
    const events = telemetry.getEvents?.() || []
    const autonomyEvents = events.filter((e: any) => e.event?.startsWith("autonomy."))

    expect(autonomyEvents.length).toBeGreaterThan(0)

    // Check for schedule event
    const scheduleEvent = autonomyEvents.find((e: any) => e.event === "autonomy.schedule_next_task")
    expect(scheduleEvent).toBeDefined()
    expect(scheduleEvent.sessionID).toBe("weather-test-session")
    expect(scheduleEvent.outcome).toBe("scheduled")
    expect(scheduleEvent.autonomyEnabled).toBe(true)
  })

  test("Weather query with autonomy blocked: search succeeds, continuation blocked", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    // Mock backlog with max auto tasks already
    const maxAutoTasks = Array(5)
      .fill(null)
      .map((_, i) => ({
        id: `auto-${i}`,
        content: "Previous auto task",
        status: "pending",
        priority: "low",
      }))
    Todo.get = mock(() => Promise.resolve(maxAutoTasks))
    Todo.update = mock(() => Promise.resolve())

    // Execute weather search
    const result: any = await WebSearchTool.execute({ query: "weather in Seattle today" }, ctx)

    // Verify search still succeeded
    expect(result.output).toContain("Sunny")
    expect(searchCalls).toBe(1)

    // Verify autonomy was checked but blocked
    expect(Todo.get).toHaveBeenCalledWith("weather-test-session")

    // Verify no new task was scheduled (would exceed limit)
    expect(Todo.update).not.toHaveBeenCalled()

    // Verify blocking telemetry
    const events = telemetry.getEvents?.() || []
    const blockEvent = events.find((e: any) => e.event === "autonomy.blocked.max_tasks")
    expect(blockEvent).toBeDefined()
    expect(blockEvent.sessionID).toBe("weather-test-session")
    expect(blockEvent.autoTaskCount).toBe(5)
  })

  test("Weather query autonomy error handling: search succeeds despite telemetry failure", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    // Mock successful backlog operations
    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Mock telemetry to fail
    const originalRecord = telemetry.record
    telemetry.record = mock(() => {
      throw new Error("Telemetry service down")
    })

    try {
      // Execute weather search
      const result: any = await WebSearchTool.execute({ query: "weather in Seattle today" }, ctx)

      // Verify search still succeeded despite telemetry failure
      expect(result.output).toContain("Sunny")
      expect(searchCalls).toBe(1)

      // Verify autonomy still worked (scheduling succeeded)
      expect(Todo.update).toHaveBeenCalled()
    } finally {
      // Restore telemetry
      telemetry.record = originalRecord
    }
  })

  test("Weather query privacy validation: no sensitive data in telemetry", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Execute search with potentially sensitive query
    await WebSearchTool.execute({ query: "weather at my home address 123 Main St" }, ctx)

    // Verify telemetry contains no raw sensitive data
    const events = telemetry.getEvents?.() || []

    events.forEach((event: any) => {
      // Should not contain raw addresses or sensitive location data
      expect(event).not.toHaveProperty("rawQuery")
      expect(event).not.toHaveProperty("address")
      expect(event).not.toHaveProperty("location")

      // If user/session IDs are present, they should be appropriate for correlation
      if (event.sessionID) {
        expect(event.sessionID).toBe("weather-test-session") // Expected session ID
      }

      // Autonomy events should have proper structure
      if (event.event?.startsWith("autonomy.")) {
        expect(event).toHaveProperty("autonomyEnabled", true)
        expect(event).toHaveProperty("timestamp")
      }
    })
  })

  test("Weather query multiple searches: autonomy respects session limits", async () => {
    setAutonomyContinueEnabled(true)
    setWebSearchMVPEnabled(true)

    // Start with 3 auto tasks (under limit of 5)
    let callCount = 0
    Todo.get = mock(() => {
      callCount++
      const baseTasks = [{ id: "task-1", content: "Weather search 1", status: "completed", priority: "high" }]
      const autoTasks = Array(Math.min(callCount + 2, 5))
        .fill(null)
        .map((_, i) => ({
          id: `auto-${i}`,
          content: `Auto task ${i}`,
          status: "pending",
          priority: "low",
        }))
      return Promise.resolve([...baseTasks, ...autoTasks])
    })

    Todo.update = mock(() => Promise.resolve())

    // First search should succeed with autonomy
    const result1: any = await WebSearchTool.execute({ query: "weather Seattle" }, ctx)
    expect(result1.output).toContain("Sunny")

    // Second search should also succeed (still under limit)
    const result2: any = await WebSearchTool.execute({ query: "weather Portland" }, ctx)
    expect(result2.output).toContain("Sunny")

    // Third search should be blocked (would exceed limit)
    const result3: any = await WebSearchTool.execute({ query: "weather San Francisco" }, ctx)
    expect(result3.output).toContain("Sunny") // Search still works

    // Verify blocking occurred on third call
    const events = telemetry.getEvents?.() || []
    const blockEvents = events.filter((e: any) => e.event === "autonomy.blocked.max_tasks")
    expect(blockEvents.length).toBeGreaterThan(0)
  })
})
