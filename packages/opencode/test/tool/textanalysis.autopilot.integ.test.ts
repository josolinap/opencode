import { describe, expect, test, beforeEach, afterEach, mock } from "bun:test"
import { TextAnalysisTool } from "../../src/tool/textanalysis"
import { setAutonomyContinueEnabled } from "../../src/storage/feature-flags"
import { Todo } from "../../src/session/todo"
import { telemetry } from "../../src/util/telemetry"

const ctx = {
  sessionID: "test-textanalysis-session",
  messageID: "",
  callID: "call-123",
  agent: "build",
  abort: AbortSignal.any([]),
  metadata: () => {},
}

describe("tool.textanalysis autopilot integration", () => {
  beforeEach(() => {
    // Reset state
    setAutonomyContinueEnabled(false)

    // Clear any existing telemetry
    telemetry.clear?.()
  })

  afterEach(() => {
    // Clean up
    setAutonomyContinueEnabled(false)
  })

  test("autonomy disabled: text analysis works normally without scheduling", async () => {
    setAutonomyContinueEnabled(false)

    const mockTodoGet = mock(() => Promise.resolve([]))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const positiveText = "This is absolutely amazing and wonderful! I love it so much."
    const result: any = await TextAnalysisTool.init().then((tool) => tool.execute({ text: positiveText }, ctx))

    expect(result.output).toContain("Sentiment: Positive")
    expect(result.title).toBe("Enhanced Text Analysis")
    expect(result.metadata.analysis.label).toBe("Positive")

    // Should not have attempted to schedule autonomous tasks
    expect(mockTodoGet).not.toHaveBeenCalled()
    expect(mockTodoUpdate).not.toHaveBeenCalled()
  })

  test("autonomy enabled: text analysis schedules next task after analysis", async () => {
    setAutonomyContinueEnabled(true)

    const existingTodos = [
      { id: "task-1", content: "Analyze customer feedback", status: "completed", priority: "high" },
    ]
    const mockTodoGet = mock(() => Promise.resolve(existingTodos))
    const mockTodoUpdate = mock(() => Promise.resolve())
    Todo.get = mockTodoGet
    Todo.update = mockTodoUpdate

    const positiveText = "This product is absolutely fantastic and amazing! I love it so much."
    const result: any = await TextAnalysisTool.init().then((tool) => tool.execute({ text: positiveText }, ctx))

    expect(result.output).toContain("Sentiment: Positive")
    expect(result.title).toBe("Enhanced Text Analysis")

    // Should have checked existing todos
    expect(mockTodoGet).toHaveBeenCalledWith("test-textanalysis-session")

    // Should have scheduled autonomous continuation
    expect(mockTodoUpdate).toHaveBeenCalledWith({
      sessionID: "test-textanalysis-session",
      todos: expect.arrayContaining([
        ...existingTodos,
        expect.objectContaining({
          content: expect.stringContaining("highly positive"),
          status: "pending",
          priority: "low",
          id: expect.stringMatching(/^auto-\d+$/),
        }),
      ]),
    })
  })

  test("autonomy generates contextual follow-ups based on sentiment analysis", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Test negative sentiment
    const negativeText = "This is absolutely terrible and horrible. I hate it so much."
    await TextAnalysisTool.init().then((tool) => tool.execute({ text: negativeText }, ctx))

    // Should suggest mitigation strategies
    const updateCall = (Todo.update as any).mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("strong negative sentiment")
    expect(scheduledTask.content).toContain("mitigation strategies")
  })

  test("autonomy generates contextual follow-ups for neutral content", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Test neutral/objective content
    const neutralText =
      "The product specifications are as follows: dimensions 10x5x2 inches, weight 1.5 pounds, color options include red, blue, and green."
    await TextAnalysisTool.init().then((tool) => tool.execute({ text: neutralText }, ctx))

    // Should suggest making content more engaging
    const updateCall = (Todo.update as any).mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("objective content")
    expect(scheduledTask.content).toContain("more engaging")
  })

  test("autonomy generates contextual follow-ups for long-form content", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Test long-form content (over 500 words)
    const longText =
      "This is a very long piece of content. ".repeat(150) +
      "It contains many words and should trigger long-form analysis suggestions."
    await TextAnalysisTool.init().then((tool) => tool.execute({ text: longText }, ctx))

    // Should suggest content organization improvements
    const updateCall = (Todo.update as any).mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("long-form content structure")
    expect(scheduledTask.content).toContain("organization improvements")
  })

  test("autonomy generates contextual follow-ups for multilingual content", async () => {
    setAutonomyContinueEnabled(true)

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Test Spanish content
    const spanishText = "Este producto es muy bueno y excelente. Me encanta mucho."
    await TextAnalysisTool.init().then((tool) => tool.execute({ text: spanishText }, ctx))

    // Should suggest localization strategies
    const updateCall = (Todo.update as any).mock.calls[0][0]
    const scheduledTask = updateCall.todos.find((t: any) => t.id.startsWith("auto-"))
    expect(scheduledTask.content).toContain("multilingual content")
    expect(scheduledTask.content).toContain("localization or translation strategies")
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

    const positiveText = "This is amazing and wonderful!"
    const result: any = await TextAnalysisTool.init().then((tool) => tool.execute({ text: positiveText }, ctx))

    // Text analysis should still succeed
    expect(result.output).toContain("Sentiment: Positive")

    // But autonomy should be blocked due to limit
    expect(Todo.update).not.toHaveBeenCalled()
  })

  test("autonomy telemetry: records text analysis autonomy events", async () => {
    setAutonomyContinueEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    const positiveText = "This is absolutely fantastic and amazing!"
    await TextAnalysisTool.init().then((tool) => tool.execute({ text: positiveText }, ctx))

    // Should have recorded autonomy telemetry
    const autonomyCalls = mockRecord.mock.calls.filter((call) => call[0].event?.startsWith("autonomy."))

    expect(autonomyCalls.length).toBeGreaterThan(0)

    // Check schedule event
    const scheduleEvent = autonomyCalls.find((e: any) => e.event === "autonomy.schedule_next_task")
    expect(scheduleEvent).toBeDefined()
    expect(scheduleEvent.sessionID).toBe("test-textanalysis-session")
    expect(scheduleEvent.currentTaskId).toBe("call-123")
    expect(scheduleEvent.outcome).toBe("scheduled")
    expect(scheduleEvent.autonomyEnabled).toBe(true)
  })

  test("autonomy error handling: text analysis succeeds despite scheduling failures", async () => {
    setAutonomyContinueEnabled(true)

    // Mock Todo operations to fail
    Todo.get = mock(() => {
      throw new Error("Todo system unavailable")
    })
    Todo.update = mock(() => Promise.resolve())

    const positiveText = "This is amazing and wonderful!"
    const result: any = await TextAnalysisTool.init().then((tool) => tool.execute({ text: positiveText }, ctx))

    // Text analysis should still succeed
    expect(result.output).toContain("Sentiment: Positive")

    // Should have attempted autonomy (and failed safely)
    expect(Todo.get).toHaveBeenCalledWith("test-textanalysis-session")
  })

  test("privacy protection: no sensitive data in text analysis telemetry", async () => {
    setAutonomyContinueEnabled(true)

    const mockRecord = mock(() => {})
    telemetry.record = mockRecord

    Todo.get = mock(() => Promise.resolve([]))
    Todo.update = mock(() => Promise.resolve())

    // Execute analysis with potentially sensitive content
    const sensitiveText =
      "This customer service is absolutely terrible and frustrating. I hate dealing with this company."
    await TextAnalysisTool.init().then((tool) => tool.execute({ text: sensitiveText }, ctx))

    // Check all telemetry calls for privacy
    mockRecord.mock.calls.forEach((call: any) => {
      const event = call[0]

      // Should not contain raw text or sensitive content
      expect(event).not.toHaveProperty("rawText")
      expect(event).not.toHaveProperty("text")
      expect(event).not.toHaveProperty("content")

      // Session ID can be raw for correlation
      if (event.sessionID) {
        expect(event.sessionID).toBe("test-textanalysis-session")
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

    const positiveText = "This is fantastic and amazing!"
    await TextAnalysisTool.init().then((tool) => tool.execute({ text: positiveText }, ctx))

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
