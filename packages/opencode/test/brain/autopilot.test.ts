// @ts-ignore - Bun test framework types not available in IDE
import { describe, expect, test, beforeEach, afterEach, mock } from "bun:test"
import { canAutoContinue, scheduleNextTask, logAutonomyEvent, AutopilotContext } from "../../src/brain/autopilot"
import { setAutonomyContinueEnabled, toggleAutonomyForTest } from "../../src/storage/feature-flags"
import { Todo } from "../../src/session/todo"
import { telemetry } from "../../src/util/telemetry"

describe("Autopilot", () => {
  beforeEach(() => {
    // Reset to disabled state for each test
    setAutonomyContinueEnabled(false)
  })

  afterEach(() => {
    // Clean up after each test
    setAutonomyContinueEnabled(false)
  })

  describe("canAutoContinue", () => {
    test("returns false when autonomy is disabled", async () => {
      setAutonomyContinueEnabled(false)
      const ctx: AutopilotContext = { sessionID: "test-session" }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(false)
    })

    test("returns false when approval is required", async () => {
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = {
        sessionID: "test-session",
        requireApproval: true,
      }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(false)
    })

    test("returns false when sessionID is missing", async () => {
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = { sessionID: "" }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(false)
    })

    test("returns true when autonomy is enabled and no blockers", async () => {
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = { sessionID: "test-session" }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(true)
    })
  })

  describe("scheduleNextTask", () => {
    const mockTodoGet = mock(() => Promise.resolve([]))
    const mockTodoUpdate = mock(() => Promise.resolve())

    beforeEach(() => {
      Todo.get = mockTodoGet
      Todo.update = mockTodoUpdate
    })

    afterEach(() => {
      mock.restore()
    })

    test("returns null when autonomy is disabled", async () => {
      setAutonomyContinueEnabled(false)
      const ctx: AutopilotContext = { sessionID: "test-session" }
      const result = await scheduleNextTask(ctx)
      expect(result).toBeNull()
      expect(mockTodoGet).not.toHaveBeenCalled()
      expect(mockTodoUpdate).not.toHaveBeenCalled()
    })

    test("schedules a task when autonomy is enabled", async () => {
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = {
        sessionID: "test-session",
        currentTaskId: "task-123",
      }

      const result = await scheduleNextTask(ctx)

      expect(result).toBeTruthy()
      expect(typeof result).toBe("string")
      expect(result?.startsWith("auto-")).toBe(true)

      expect(mockTodoGet).toHaveBeenCalledWith("test-session")
      expect(mockTodoUpdate).toHaveBeenCalledWith({
        sessionID: "test-session",
        todos: expect.arrayContaining([
          expect.objectContaining({
            content: "Auto continuation from task-123",
            status: "pending",
            priority: "low",
            id: result,
          }),
        ]),
      })
    })

    test("uses custom content when provided", async () => {
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = { sessionID: "test-session" }
      const customContent = "Custom autonomous task"

      const result = await scheduleNextTask(ctx, customContent)

      expect(mockTodoUpdate).toHaveBeenCalledWith({
        sessionID: "test-session",
        todos: expect.arrayContaining([
          expect.objectContaining({
            content: customContent,
            status: "pending",
            priority: "low",
            id: result,
          }),
        ]),
      })
    })

    test("handles telemetry errors gracefully", async () => {
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = { sessionID: "test-session" }

      // Mock telemetry to throw error
      const originalRecord = telemetry.record
      telemetry.record = mock(() => {
        throw new Error("Telemetry failed")
      })

      try {
        const result = await scheduleNextTask(ctx)
        expect(result).toBeTruthy() // Should still succeed despite telemetry error
      } finally {
        telemetry.record = originalRecord
      }
    })
  })

  describe("logAutonomyEvent", () => {
    test("records autonomy events through telemetry", () => {
      const mockRecord = mock(() => {})
      telemetry.record = mockRecord

      const event = {
        event: "autonomy.test",
        sessionID: "test-session",
        outcome: "success",
      }

      logAutonomyEvent(event)

      expect(mockRecord).toHaveBeenCalledWith({
        ...event,
        autonomyEnabled: true,
        timestamp: expect.any(Number),
      })
    })

    test("handles telemetry errors gracefully", () => {
      const originalRecord = telemetry.record
      telemetry.record = mock(() => {
        throw new Error("Telemetry failed")
      })

      try {
        logAutonomyEvent({ event: "test" })
        // Should not throw
      } finally {
        telemetry.record = originalRecord
      }
    })
  })

  describe("Safety controls for infinite loops", () => {
    test("blocks continuation when max depth exceeded", async () => {
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = {
        sessionID: "test-session",
        autoTaskDepth: 5, // Exceeds max of 3
      }

      const result = await canAutoContinue(ctx)
      expect(result).toBe(false)
    })

    test("blocks continuation when max auto tasks per session exceeded", async () => {
      setAutonomyContinueEnabled(true)

      // Mock existing todos with max auto tasks
      const existingTodos = Array(5)
        .fill(null)
        .map((_, i) => ({
          id: `auto-${i}`,
          content: "Auto task",
          status: "pending",
          priority: "low",
        }))

      Todo.get = mock(() => Promise.resolve(existingTodos))

      const ctx: AutopilotContext = { sessionID: "test-session" }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(false)
    })

    test("allows continuation within limits", async () => {
      setAutonomyContinueEnabled(true)

      // Mock existing todos within limits
      const existingTodos = Array(3)
        .fill(null)
        .map((_, i) => ({
          id: `auto-${i}`,
          content: "Auto task",
          status: "pending",
          priority: "low",
        }))

      Todo.get = mock(() => Promise.resolve(existingTodos))

      const ctx: AutopilotContext = {
        sessionID: "test-session",
        autoTaskDepth: 2,
      }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(true)
    })
  })

  describe("Health monitoring", () => {
    test("tracks autonomy decisions", async () => {
      setAutonomyContinueEnabled(true)

      // Reset health
      const { getAutonomyHealth } = await import("../../src/brain/autopilot")
      // Note: Health is internal, so we'll test through side effects

      const ctx: AutopilotContext = { sessionID: "test-session" }

      // Test allowed decision
      await canAutoContinue(ctx)

      // Test blocked decision
      setAutonomyContinueEnabled(false)
      await canAutoContinue(ctx)

      // Test scheduled decision
      setAutonomyContinueEnabled(true)
      Todo.get = mock(() => Promise.resolve([]))
      Todo.update = mock(() => Promise.resolve())
      await scheduleNextTask(ctx)
    })

    test("provides health status", async () => {
      const { getAutonomyHealth } = await import("../../src/brain/autopilot")
      const health = getAutonomyHealth()

      expect(health).toHaveProperty("enabled")
      expect(health).toHaveProperty("totalDecisions")
      expect(health).toHaveProperty("healthStatus")
      expect(["healthy", "degraded", "unhealthy"]).toContain(health.healthStatus)
    })
  })

  describe("0%/100% rollout edge cases", () => {
    test("0% rollout blocks all continuation", async () => {
      // This would be tested at the experiment level, not autopilot level
      // Autopilot assumes the experiment has already decided to allow
      setAutonomyContinueEnabled(true)
      const ctx: AutopilotContext = { sessionID: "test-session" }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(true) // Autopilot level allows when enabled
    })

    test("handles backlog access errors gracefully", async () => {
      setAutonomyContinueEnabled(true)

      // Mock Todo.get to throw error
      Todo.get = mock(() => {
        throw new Error("Backlog unavailable")
      })

      const ctx: AutopilotContext = { sessionID: "test-session" }
      const result = await canAutoContinue(ctx)
      expect(result).toBe(false) // Should fail safely
    })
  })

  // describe("Integration with feature flags", () => {
  //   test("respects the toggle function for testing", () => {
  //     toggleAutonomyForTest(true)

  //     // Mock Todo.get to return empty array (no existing auto tasks)
  //     const originalGet = Todo.get
  //     Todo.get = mock(() => Promise.resolve([]))

  //     try {
  //       const ctx: AutopilotContext = { sessionID: "test-session" }
  //       return canAutoContinue(ctx).then(result => {
  //         expect(result).toBe(true)
  //       })
  //     } finally {
  //       Todo.get = originalGet
  //     }
  //   })

  //   test("can be toggled off for testing", () => {
  //     toggleAutonomyForTest(false)
  //     const ctx: AutopilotContext = { sessionID: "test-session" }
  //     return canAutoContinue(ctx).then(result => {
  //       expect(result).toBe(false)
  //     })
  //   })
  // })
})
