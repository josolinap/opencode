import z from "zod"
import { Tool } from "./tool"
import DESCRIPTION from "./textanalysis.txt"

type Analysis = {
  score: number
  label: "Positive" | "Negative" | "Neutral"
  positive?: string[]
  negative?: string[]
  language?: string
}

const POS = ["good", "great", "awesome", "happy", "fantastic", "love", "excellent", "nice", "amazing", "wonderful"]
const NEG = ["bad", "sad", "terrible", "horrible", "awful", "worst", "hate", "angry", "boring"]

export const TextAnalysisTool = Tool.define("textanalysis", {
  description: DESCRIPTION,
  parameters: z.object({
    text: z.string().describe("Text to analyze for sentiment"),
    language: z.string().optional().describe("Language code (e.g., en, es)"),
  }),
  async execute(params: any, ctx: any) {
    const t = (params.text as string) ?? ""
    const lang = (params.language as string) ?? "en"

    // naive sentiment scoring
    const lower = t.toLowerCase()
    const posCount = POS.filter((w) => lower.includes(w)).length
    const negCount = NEG.filter((w) => lower.includes(w)).length
    const total = Math.max(posCount + negCount, 1)
    const score = (posCount - negCount) / total
    const label = score > 0.15 ? "Positive" : score < -0.15 ? "Negative" : "Neutral"
    const result: Analysis = {
      score,
      label,
      positive: POS.filter((w) => lower.includes(w)),
      negative: NEG.filter((w) => lower.includes(w)),
      language: lang,
    }

    return {
      title: "Text Analysis",
      output: `Sentiment: ${label} (score=${score.toFixed(2)})`,
      metadata: {
        preview: `Sentiment: ${label}`,
        analysis: result,
      },
    }
  },
})
