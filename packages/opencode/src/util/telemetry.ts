import { Log } from "../util/log"
import { sha256Hex } from "./crypto"
import { getPolicyVariant, getPolicyVersion } from "../config/policy"

const log = Log.create({ service: "telemetry" })

export interface TelemetryEvent {
  skill?: string
  prompt?: string
  latencyMs?: number
  success?: boolean
  error?: string
  timestamp: number
  policyVersion?: string
  variantName?: string
  urlDomainHash?: string
  userIdHash?: string
  promptHash?: string
  autonomyEnabled?: boolean
  autopilotVariant?: string
  autoTaskId?: string
  autoOutcome?: string
}

class TelemetryCollector {
  private events: TelemetryEvent[] = []
  private maxEvents = 1000

  record(event: TelemetryEvent) {
    this.events.push(event)
    if (this.events.length > this.maxEvents) {
      this.events.shift()
    }
    log.info("telemetry", event)
  }

  getEvents(): TelemetryEvent[] {
    return [...this.events]
  }

  clear() {
    this.events = []
  }
}

export const telemetry = new TelemetryCollector()

// Helper to wrap skill execution with telemetry
export function withTelemetry<T>(skillName: string, prompt: string, fn: () => Promise<T>): Promise<T> {
  const start = Date.now()
  return fn()
    .then((result) => {
      telemetry.record({
        skill: skillName,
        prompt,
        latencyMs: Date.now() - start,
        success: true,
        timestamp: Date.now(),
        policyVersion: getPolicyVersion(),
        variantName: getPolicyVariant(),
      })
      return result
    })
    .catch((error) => {
      telemetry.record({
        skill: skillName,
        prompt,
        latencyMs: Date.now() - start,
        success: false,
        error: error instanceof Error ? error.message : String(error),
        timestamp: Date.now(),
        policyVersion: getPolicyVersion(),
        variantName: getPolicyVariant(),
      })
      throw error
    })
}

export function logAutonomyEvent(event: TelemetryEvent) {
  telemetry.record({ ...event, timestamp: Date.now() })
}
