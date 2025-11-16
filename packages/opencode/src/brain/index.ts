/**
 * Brain namespace for Neo-Clone autonomous capabilities.
 * Central hub for AI-driven features like task continuation and decision making.
 */

// Core autonomy functionality
export * from "./autopilot"

// Policy and configuration management
export { getPolicyVersion, getPolicyVariant, getPolicyName } from "../config/policy"

// Telemetry helpers for brain operations
export { logAutonomyEvent } from "../util/telemetry"

// Health monitoring
export { getAutonomyHealth, updateAutonomyHealth } from "./autopilot"

// Future brain modules can be added here:
// export * from "./reasoning"
// export * from "./planning"
// export * from "./learning"
