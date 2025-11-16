// Lightweight in-memory feature flags for MVPed capabilities.
// This module provides a minimal, non-breaking mechanism to gate new features
// behind a runtime flag. By default, features are disabled to ensure stability.

type FlagValue = boolean

const flags: Record<string, FlagValue> = {
  // MVP flag for the Web Search enhancements (structured results, credibility, caching, etc.)
  // Default to false to preserve existing behavior unless explicitly enabled.
  "web_search_mvp.enabled": false,
  // Autonomous continuation (ATC) flag for brain-driven task progression
  "autonomy.continue.enabled": false,
}

export function isWebSearchMVPEnabled(): boolean {
  return !!flags["web_search_mvp.enabled"]
}

export function setWebSearchMVPEnabled(value: boolean): void {
  flags["web_search_mvp.enabled"] = value
}

// Expose a tiny API to toggle for tests or scripted canary runs
export function toggleWebSearchMVPForTest(enable: boolean): void {
  setWebSearchMVPEnabled(enable)
}

export function isAutonomyContinueEnabled(): boolean {
  return !!flags["autonomy.continue.enabled"]
}

export function setAutonomyContinueEnabled(value: boolean): void {
  flags["autonomy.continue.enabled"] = value
}

export function toggleAutonomyForTest(enable: boolean): void {
  setAutonomyContinueEnabled(enable)
}
