// storage/user/preferences.ts
// Minimal per-session user preferences for the web research MVP.

export type OutputFormat = "brief" | "memo" | "table"

export interface UserPreferences {
  domainsWhitelist: string[]
  domainsBlacklist: string[]
  dateWindowMonths: number
  language: string | null
  outputFormat: OutputFormat
  citationStyle: string
}

const DEFAULT: UserPreferences = {
  domainsWhitelist: [],
  domainsBlacklist: [],
  dateWindowMonths: 12,
  language: null,
  outputFormat: "brief",
  citationStyle: "APA",
}

// Simple in-memory map keyed by sessionID. In a real system this would be backed by a persistent store.
const prefsStore = new Map<string, UserPreferences>()

export function getUserPreferences(sessionID: string): UserPreferences {
  return prefsStore.get(sessionID) ?? DEFAULT
}

export function setUserPreferences(sessionID: string, next: Partial<UserPreferences>): void {
  const current = getUserPreferences(sessionID)
  const updated = { ...current, ...next }
  prefsStore.set(sessionID, updated)
}

export function resetUserPreferences(sessionID: string): void {
  prefsStore.delete(sessionID)
}
