// Lightweight shared credibility scoring utility
export function computeSourceCredibility(url: string, content: string, dateInfo?: Date | string): number {
  // Domain reputation base score
  let domainScore = 0.5
  try {
    const host = new URL(url || "http://neutral").hostname.toLowerCase()
    if (host.endsWith(".edu") || host.endsWith(".gov")) {
      domainScore = 0.9
    } else if (host.endsWith(".org")) {
      domainScore = 0.7
    } else if (host.includes("wikipedia.org") || host.includes("github.com") || host.includes("arxiv.org")) {
      domainScore = 0.9
    } else if (host.endsWith(".com")) {
      domainScore = 0.5
    } else {
      domainScore = 0.4
    }
  } catch {
    // if URL parsing fails, keep default domain score
  }

  // Content quality indicators (simple heuristics)
  let contentBonus = 0
  const text = (content ?? "").toLowerCase()
  if (text.includes("author") || text.includes("references") || text.includes("citations") || text.includes("doi")) {
    contentBonus += 0.1
  }
  if (text.includes("methodology") || text.includes("abstract")) {
    contentBonus += 0.1
  }
  if (text.includes("sponsored") || text.includes("buy now")) {
    contentBonus -= 0.1
  }

  // Recency bonuses
  let recencyBonus = 0
  let days = 30
  if (dateInfo) {
    const dt = dateInfo instanceof Date ? dateInfo : new Date(dateInfo)
    if (!isNaN(dt.getTime())) {
      const diff = (Date.now() - dt.getTime()) / (1000 * 60 * 60 * 24)
      days = Math.max(0, diff)
      if (days <= 1) recencyBonus = 0.1
      else if (days <= 7) recencyBonus = 0.08
      else if (days <= 30) recencyBonus = 0.05
      else if (days <= 365) recencyBonus = 0.02
    } else {
      // invalid date; keep zero bonus
    }
  } else {
    // no date info; give modest default recency bonus
    days = 30
  }

  let score = domainScore + contentBonus + recencyBonus
  if (score < 0) score = 0
  if (score > 1) score = 1

  return score
}

export type CredibilityInput = {
  url: string
  content: string
  dateInfo?: Date | string
}

export function computeSourceCredibilityFromInput(input: CredibilityInput): number {
  return computeSourceCredibility(input.url, input.content, input.dateInfo)
}
