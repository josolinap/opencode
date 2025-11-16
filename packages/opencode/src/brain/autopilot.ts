import { isAutonomyContinueEnabled, setAutonomyContinueEnabled } from "../storage/feature-flags"
import { Todo } from "../session/todo"
import { telemetry } from "../util/telemetry"

type AutonomyResult = {
  nextTaskId: string
  scheduled: boolean
}

export interface AutopilotContext {
  sessionID: string
  currentTaskId?: string
  requireApproval?: boolean
  maxAutoTasksPerSession?: number // Prevent infinite loops
  autoTaskDepth?: number // Track recursion depth
}

function getNextTaskContentFromContext(ctx: AutopilotContext): string {
  return `Auto continuation${ctx.currentTaskId ? ` from ${ctx.currentTaskId}` : ""}`
}

export async function canAutoContinue(ctx: AutopilotContext): Promise<boolean> {
  if (!isAutonomyContinueEnabled()) {
    updateAutonomyHealth("blocked")
    return false
  }
  // If approval is required, block by default; this can be relaxed later with overrides
  if (ctx.requireApproval) {
    updateAutonomyHealth("blocked")
    return false
  }
  // Basic guard: ensure we have a session and can access backlog
  if (!ctx.sessionID) {
    updateAutonomyHealth("blocked")
    return false
  }

  // Prevent infinite loops: check auto task depth and count per session
  const maxDepth = ctx.autoTaskDepth ?? 0
  if (maxDepth > 3) {
    // Allow up to 3 levels of auto-continuation
    // logAutonomyEvent({
    //   event: "autonomy.blocked.max_depth",
    //   sessionID: ctx.sessionID,
    //   currentTaskId: ctx.currentTaskId,
    //   autoTaskDepth: maxDepth
    // })
    updateAutonomyHealth("blocked")
    return false
  }

  // Check total auto tasks per session to prevent runaway scheduling
  try {
    const existing = await Todo.get(ctx.sessionID)
    const autoTasks = existing.filter((t) => t.id.startsWith("auto-")).length
    const maxAutoTasks = ctx.maxAutoTasksPerSession ?? 5
    if (autoTasks >= maxAutoTasks) {
      // logAutonomyEvent({
      //   event: "autonomy.blocked.max_tasks",
      //   sessionID: ctx.sessionID,
      //   currentTaskId: ctx.currentTaskId,
      //   autoTaskCount: autoTasks,
      //   maxAutoTasks: maxAutoTasks
      // })
      updateAutonomyHealth("blocked")
      return false
    }
  } catch (error) {
    // If we can't check the backlog, err on the side of caution
    logAutonomyEvent({
      event: "autonomy.blocked.backlog_error",
      sessionID: ctx.sessionID,
      currentTaskId: ctx.currentTaskId,
      error: error instanceof Error ? error.message : String(error),
    })
    updateAutonomyHealth("error")
    return false
  }

  updateAutonomyHealth("allowed")
  return true
}

export async function scheduleNextTask(ctx: AutopilotContext, nextContent?: string): Promise<string | null> {
  const can = await canAutoContinue(ctx)
  if (!can) return null

  try {
    // Load existing backlog
    const existing = await Todo.get(ctx.sessionID)
    const id = `auto-${Date.now()}`
    const todo: Todo.Info = {
      content: nextContent ?? getNextTaskContentFromContext(ctx),
      status: "pending",
      priority: "low",
      id,
    }
    const updated = [...existing, todo]
    await Todo.update({ sessionID: ctx.sessionID, todos: updated })

    // Update health metrics
    updateAutonomyHealth("scheduled")

    // Telemetry about autonomous continuation decision
    logAutonomyEvent({
      event: "autonomy.schedule_next_task",
      sessionID: ctx.sessionID,
      currentTaskId: ctx.currentTaskId,
      autoTaskId: id,
      variantName: process.env.CREDIBILITY_POLICY_VARIANT ?? "default",
      policyVersion: process.env.CREDIBILITY_POLICY_VERSION ?? "default",
      outcome: "scheduled",
    } as any)

    return id
  } catch (error) {
    // Track scheduling errors
    updateAutonomyHealth("error")
    logAutonomyEvent({
      event: "autonomy.schedule_error",
      sessionID: ctx.sessionID,
      currentTaskId: ctx.currentTaskId,
      error: error instanceof Error ? error.message : String(error),
    })
    return null
  }
}

export function logAutonomyEvent(event: any) {
  // Lightweight wrapper to align with existing telemetry API
  // We reuse TelemetryCollector, but keep payload minimal to avoid PII leakage

  const payload: any = {
    autonomyEnabled: true,
    timestamp: Date.now(),
  }
  // Only include defined values to avoid schema errors
  for (const [key, value] of Object.entries(event)) {
    if (value !== undefined) {
      payload[key] = value
    }
  }
  // Deliver through the same telemetry sink, letting it apply policy/version when possible
  // The TelemetryCollector will also add its own timestamp; avoid duplication by overwriting
  try {
    telemetry.record(payload)
  } catch (error) {
    // Silently ignore telemetry errors to prevent breaking autonomy flow
    console.warn("Autonomy telemetry failed:", error)
  }
}

// Health monitoring for autopilot status
export interface AutonomyHealth {
  enabled: boolean
  lastDecisionTime?: number
  totalDecisions: number
  blockedDecisions: number
  scheduledTasks: number
  errorCount: number
  healthStatus: "healthy" | "degraded" | "unhealthy"
}

let autonomyHealth: AutonomyHealth = {
  enabled: false,
  totalDecisions: 0,
  blockedDecisions: 0,
  scheduledTasks: 0,
  errorCount: 0,
  healthStatus: "healthy",
}

export function getAutonomyHealth(): AutonomyHealth {
  return { ...autonomyHealth, enabled: isAutonomyContinueEnabled() }
}

export function updateAutonomyHealth(decision: "allowed" | "blocked" | "scheduled" | "error") {
  autonomyHealth.lastDecisionTime = Date.now()
  autonomyHealth.totalDecisions++

  switch (decision) {
    case "blocked":
      autonomyHealth.blockedDecisions++
      break
    case "scheduled":
      autonomyHealth.scheduledTasks++
      break
    case "error":
      autonomyHealth.errorCount++
      break
  }

  // Update health status based on error rate
  const errorRate = autonomyHealth.errorCount / Math.max(autonomyHealth.totalDecisions, 1)
  if (errorRate > 0.1) {
    // >10% error rate
    autonomyHealth.healthStatus = "unhealthy"
  } else if (errorRate > 0.05) {
    // >5% error rate
    autonomyHealth.healthStatus = "degraded"
  } else {
    autonomyHealth.healthStatus = "healthy"
  }
}

// Simple bootstrap for environments where autopilot should be engaged in tests
export async function initAutonomyBootstrap() {
  // Hook for future canary bootstrap: enable by config/env in a safe way
  // For now, do nothing
}

export default {
  canAutoContinue,
  scheduleNextTask,
  logAutonomyEvent,
  initAutonomyBootstrap,
}
