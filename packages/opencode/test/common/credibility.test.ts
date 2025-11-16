import { test, expect } from "bun:test"
import { computeSourceCredibility, computeSourceCredibilityFromInput } from "../../src/common/credibility"

test("credibility should be within [0,1] for sample inputs", () => {
  const samples = [
    { url: "https://example.edu/something", content: "Abstract with references and author", date: "2025-11-01" },
    { url: "https://news.example.com/article", content: "Sponsor content with buy now", date: "2024-01-01" },
    { url: "https://github.com/user/repo", content: "No explicit signals", date: undefined },
  ]
  for (const s of samples) {
    const score = computeSourceCredibility(s.url, s.content, s.date)
    expect(score).toBeGreaterThanOrEqual(0)
    expect(score).toBeLessThanOrEqual(1)
  }
})

test("credibility is deterministic for same inputs", () => {
  const url = "https://example.org/paper"
  const content = "author references citations doi"
  const d = new Date("2025-11-01")
  const a = computeSourceCredibility(url, content, d)
  const b = computeSourceCredibility(url, content, d)
  expect(a).toBeCloseTo(b, 6)
})

test("compute from input helper works", () => {
  const inObj = { url: "https://site.edu", content: "abstract doi", dateInfo: new Date("2025-11-01") }
  const score = computeSourceCredibilityFromInput(inObj)
  expect(score).toBeGreaterThanOrEqual(0)
  expect(score).toBeLessThanOrEqual(1)
})
