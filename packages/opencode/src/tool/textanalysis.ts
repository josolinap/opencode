import z from "zod"
import { Tool } from "./tool"
import DESCRIPTION from "./textanalysis.txt"
import { scheduleNextTask } from "../brain/autopilot"
import { isAutonomyContinueEnabled } from "../storage/feature-flags"

type Analysis = {
  score: number
  label: "Positive" | "Negative" | "Neutral"
  confidence: number
  positive?: string[]
  negative?: string[]
  negations?: string[]
  intensifiers?: string[]
  language?: string
  detectedLanguage?: string
  wordCount?: number
  subjectivity?: "Subjective" | "Objective"
}

// Expanded word lists with better coverage
// Simple language detection based on common words
function detectLanguage(text: string): string | null {
  const lower = text.toLowerCase()

  // Spanish indicators
  const spanishWords = ["el", "la", "los", "las", "es", "son", "está", "muy", "pero", "qué", "por", "con"]
  const spanishScore = spanishWords.filter((w) => lower.includes(w)).length

  // French indicators
  const frenchWords = ["le", "la", "les", "est", "et", "en", "un", "une", "dans", "sur", "avec", "pour"]
  const frenchScore = frenchWords.filter((w) => lower.includes(w)).length

  // English indicators
  const englishWords = ["the", "and", "is", "in", "to", "of", "a", "that", "it", "with", "as", "for"]
  const englishScore = englishWords.filter((w) => lower.includes(w)).length

  const maxScore = Math.max(spanishScore, frenchScore, englishScore)
  if (maxScore >= 2) {
    // Require at least 2 matches for confidence
    if (spanishScore === maxScore) return "es"
    if (frenchScore === maxScore) return "fr"
    if (englishScore === maxScore) return "en"
  }

  return null // Default to requested language
}

const WORD_LISTS = {
  en: {
    positive: [
      "good",
      "great",
      "awesome",
      "happy",
      "fantastic",
      "love",
      "excellent",
      "nice",
      "amazing",
      "wonderful",
      "perfect",
      "brilliant",
      "outstanding",
      "superb",
      "marvelous",
      "delightful",
      "pleased",
      "satisfied",
      "thrilled",
      "excited",
      "joyful",
      "cheerful",
      "content",
      "grateful",
      "blessed",
      "fortunate",
      "beautiful",
      "gorgeous",
      "stunning",
      "attractive",
      "charming",
      "elegant",
      "lovely",
      "pretty",
      "best",
      "favorite",
      "preferred",
      "recommended",
      "approved",
      "accepted",
      "welcome",
      "appreciated",
    ],
    negative: [
      "bad",
      "sad",
      "terrible",
      "horrible",
      "awful",
      "worst",
      "hate",
      "angry",
      "boring",
      "disgusting",
      "ugly",
      "hateful",
      "annoying",
      "frustrating",
      "disappointing",
      "terrible",
      "awful",
      "dreadful",
      "miserable",
      "depressed",
      "unhappy",
      "sorrowful",
      "grief",
      "painful",
      "hurtful",
      "offensive",
      "worst",
      "pathetic",
      "lame",
      "stupid",
      "dumb",
      "idiotic",
      "foolish",
      "silly",
      "ridiculous",
      "useless",
      "worthless",
      "garbage",
      "trash",
      "crap",
      "shit",
      "damn",
      "hell",
    ],
    negations: [
      "not",
      "never",
      "no",
      "none",
      "nobody",
      "nothing",
      "nowhere",
      "neither",
      "nor",
      "cannot",
      "can't",
      "won't",
      "don't",
      "doesn't",
      "isn't",
      "aren't",
      "wasn't",
      "weren't",
    ],
    intensifiers: [
      "very",
      "extremely",
      "so",
      "really",
      "quite",
      "absolutely",
      "totally",
      "completely",
      "utterly",
      "highly",
      "incredibly",
      "amazingly",
      "exceptionally",
      "particularly",
      "especially",
    ],
  },
  es: {
    positive: [
      "bueno",
      "genial",
      "fantástico",
      "feliz",
      "amor",
      "excelente",
      "maravilloso",
      "hermoso",
      "perfecto",
      "brillante",
      "asombroso",
      "delicioso",
      "encantado",
      "satisfecho",
      "emocionado",
      "alegre",
      "contento",
      "agradecido",
      "bendecido",
      "afortunado",
      "bello",
      "gorgeoso",
      "estupendo",
      "magnífico",
      "espléndido",
    ],
    negative: [
      "malo",
      "triste",
      "terrible",
      "horrible",
      "odio",
      "enojado",
      "aburrido",
      "feo",
      "odioso",
      "molesto",
      "frustrante",
      "decepcionante",
      "miserable",
      "deprimido",
      "infeliz",
      "doloroso",
      "ofensivo",
      "patético",
      "estúpido",
      "tonto",
      "ridículo",
      "inútil",
      "basura",
      "mierda",
      "maldito",
      "infierno",
    ],
    negations: ["no", "nunca", "nadie", "nada", "ninguno", "tampoco", "ni", "no puede", "no puedo"],
    intensifiers: [
      "muy",
      "extremadamente",
      "tan",
      "realmente",
      "bastante",
      "absolutamente",
      "totalmente",
      "completamente",
      "altamente",
      "increíblemente",
    ],
  },
  fr: {
    positive: [
      "bon",
      "génial",
      "fantastique",
      "heureux",
      "amour",
      "excellent",
      "merveilleux",
      "beau",
      "parfait",
      "brillant",
      "étonnant",
      "délicieux",
      "enchanté",
      "satisfait",
      "excité",
      "joyeux",
      "content",
      "reconnaissant",
      "béni",
      "chanceux",
      "joli",
      "magnifique",
      "superbe",
      "splendide",
      "formidable",
    ],
    negative: [
      "mauvais",
      "triste",
      "terrible",
      "horrible",
      "haine",
      "énervé",
      "ennuyeux",
      "laid",
      "haïssable",
      "agaçant",
      "frustrant",
      "décevant",
      "misérable",
      "déprimé",
      "malheureux",
      "douloureux",
      "offensant",
      "pathétique",
      "stupide",
      "idiot",
      "ridicule",
      "inutile",
      "ordure",
      "merde",
      "maudit",
      "enfer",
    ],
    negations: ["ne", "pas", "jamais", "personne", "rien", "aucun", "ni", "n'est pas", "n'est pas"],
    intensifiers: [
      "très",
      "extrêmement",
      "tellement",
      "vraiment",
      "assez",
      "absolument",
      "totalement",
      "complètement",
      "hautement",
      "incroyablement",
    ],
  },
}

function generateTextAnalysisFollowUp(analysis: Analysis, text: string): string {
  // Generate contextual follow-up task based on text analysis results
  const { label, confidence, subjectivity, detectedLanguage, wordCount } = analysis

  // Base follow-ups based on sentiment
  if (label === "Positive") {
    if (confidence > 0.7) {
      return "Analyze what makes this text highly positive and identify key success factors"
    }
    return "Explore positive sentiment patterns and suggest ways to amplify them"
  }

  if (label === "Negative") {
    if (confidence > 0.7) {
      return "Investigate strong negative sentiment and develop mitigation strategies"
    }
    return "Address negative sentiment and suggest improvement approaches"
  }

  // Neutral sentiment - focus on other aspects
  if (subjectivity === "Objective") {
    return "Review objective content and suggest ways to make it more engaging"
  }

  if (wordCount && wordCount > 500) {
    return "Analyze long-form content structure and suggest content organization improvements"
  }

  if (detectedLanguage && detectedLanguage !== "en") {
    return `Review multilingual content and suggest localization or translation strategies for ${detectedLanguage}`
  }

  return "Analyze text characteristics and suggest content optimization strategies"
}

export const TextAnalysisTool = Tool.define("textanalysis", {
  description: DESCRIPTION,
  parameters: z.object({
    text: z.string().describe("Text to analyze for sentiment"),
    language: z.string().optional().describe("Language code (e.g., en, es)"),
  }),
  async execute(params: any, ctx: any) {
    const t = (params.text as string) ?? ""
    const requestedLang = (params.language as string) ?? "en"

    // Detect language if not specified or auto-detect
    const detectedLang = detectLanguage(t) || requestedLang
    const wordList = WORD_LISTS[detectedLang as keyof typeof WORD_LISTS] || WORD_LISTS.en

    const lower = t.toLowerCase()
    const words = lower.split(/\s+/).filter((w) => w.length > 0)
    const wordCount = words.length

    // Find sentiment words
    const positiveWords = wordList.positive.filter((w) => lower.includes(w))
    const negativeWords = wordList.negative.filter((w) => lower.includes(w))
    const negations = wordList.negations.filter((w) => lower.includes(w))
    const intensifiers = wordList.intensifiers.filter((w) => lower.includes(w))

    // Calculate sentiment with enhancements
    let posScore = positiveWords.length
    let negScore = negativeWords.length

    // Apply intensifiers (boost score by 50% if intensifier nearby)
    const boostScore = (baseScore: number, wordList: string[]) => {
      let boosted = baseScore
      for (const word of wordList) {
        const index = words.indexOf(word)
        if (index >= 0) {
          // Check for nearby intensifiers
          const start = Math.max(0, index - 2)
          const end = Math.min(words.length, index + 3)
          const nearbyWords = words.slice(start, end)
          if (nearbyWords.some((w) => intensifiers.includes(w))) {
            boosted += 0.5
          }
        }
      }
      return boosted
    }

    posScore = boostScore(posScore, positiveWords)
    negScore = boostScore(negScore, negativeWords)

    // Apply negations (flip sentiment for negated phrases)
    const applyNegations = (text: string, posWords: string[], negWords: string[]) => {
      let adjustedPos = posScore
      let adjustedNeg = negScore

      for (const neg of negations) {
        const negIndex = words.indexOf(neg)
        if (negIndex >= 0) {
          // Check for sentiment words within 3 words of negation
          const start = Math.max(0, negIndex - 3)
          const end = Math.min(words.length, negIndex + 4)
          const nearbyWords = words.slice(start, end)

          const nearbyPos = positiveWords.filter((w) => nearbyWords.includes(w))
          const nearbyNeg = negativeWords.filter((w) => nearbyWords.includes(w))

          // Flip the sentiment for nearby words
          adjustedPos -= nearbyPos.length * 0.8
          adjustedNeg += nearbyPos.length * 0.8
          adjustedPos += nearbyNeg.length * 0.8
          adjustedNeg -= nearbyNeg.length * 0.8
        }
      }

      return { adjustedPos: Math.max(0, adjustedPos), adjustedNeg: Math.max(0, adjustedNeg) }
    }

    const { adjustedPos, adjustedNeg } = applyNegations(t, positiveWords, negativeWords)

    // Calculate final score and confidence
    const totalSentimentWords = adjustedPos + adjustedNeg
    const score = totalSentimentWords > 0 ? (adjustedPos - adjustedNeg) / totalSentimentWords : 0
    const confidence = Math.min(totalSentimentWords / Math.max(wordCount * 0.1, 1), 1)

    const label = score > 0.2 ? "Positive" : score < -0.2 ? "Negative" : "Neutral"
    const subjectivity = totalSentimentWords > wordCount * 0.05 ? "Subjective" : "Objective"

    const analysis: Analysis = {
      score,
      label,
      confidence,
      positive: positiveWords,
      negative: negativeWords,
      negations,
      intensifiers,
      language: requestedLang,
      detectedLanguage: detectedLang,
      wordCount,
      subjectivity,
    }

    const output =
      `Sentiment: ${label} (score=${score.toFixed(2)}, confidence=${(confidence * 100).toFixed(0)}%)\n` +
      `Language: ${detectedLang} (${subjectivity})\n` +
      `Words: ${wordCount} total, ${positiveWords.length} positive, ${negativeWords.length} negative`

    const toolResult = {
      title: "Enhanced Text Analysis",
      output,
      metadata: {
        preview: `${label} (${(confidence * 100).toFixed(0)}% confidence)`,
        analysis,
      },
    }

    // Autonomous continuation: schedule next task if enabled
    if (isAutonomyContinueEnabled()) {
      try {
        // Non-blocking: schedule next task in background
        setImmediate(async () => {
          try {
            const nextTaskContent = generateTextAnalysisFollowUp(analysis, params.text)
            await scheduleNextTask(
              {
                sessionID: ctx.sessionID,
                currentTaskId: ctx.callID,
              },
              nextTaskContent,
            )
          } catch (error) {
            // Autonomy failures should not break the main tool execution
            console.warn("TextAnalysis autonomy scheduling failed:", error)
          }
        })
      } catch {
        // Ignore autonomy setup failures
      }
    }

    return toolResult
  },
})
