import z from "zod"
import { Tool } from "./tool"
import DESCRIPTION from "./datainspector.txt"
import { WatchTool } from "./watch"
import { scheduleNextTask } from "../brain/autopilot"
import { isAutonomyContinueEnabled } from "../storage/feature-flags"

type DataFormat = "csv" | "json"

// Simple in-memory cache for demonstration
const cache = new Map<string, any>()

function isJsonString(str: string): boolean {
  try {
    JSON.parse(str)
    return true
  } catch {
    return false
  }
}

function generateDataInspectorFollowUp(details: any, format: DataFormat): string {
  // Generate contextual follow-up task based on data inspection results
  if (details.error) {
    return "Investigate data parsing error and suggest fixes"
  }

  if (format === "csv") {
    const { rowsCount, cols, missingAvg, headers } = details

    if (missingAvg > 0.5) {
      return `Address high missing data rate (${(missingAvg * 100).toFixed(1)}%) - consider data cleaning strategies`
    }

    if (rowsCount > 1000) {
      return "Analyze large dataset patterns and consider sampling strategies"
    }

    if (headers?.length > 0) {
      return `Explore relationships between key columns: ${headers.slice(0, 3).join(", ")}`
    }
  } else {
    // JSON format
    const { numericSummary } = details
    const numericFields = Object.keys(numericSummary || {})

    if (numericFields.length > 0) {
      return `Analyze numeric field distributions and correlations: ${numericFields.slice(0, 3).join(", ")}`
    }
  }

  return "Review data quality and suggest next analysis steps"
}

export const DataInspectorTool = Tool.define("datainspector", {
  description: DESCRIPTION,
  parameters: z.object({
    data: z.string().describe("Data payload in CSV or JSON"),
    format: z
      .enum(["csv", "json"])
      .optional()
      .describe("Data format (csv or json). If omitted, a best-effort guess is used."),
    sampleRows: z.number().optional().describe("Number of rows to sample for summary (default: 100)"),
  }),
  async execute(params, ctx) {
    const raw = params.data ?? ""
    const inferredFormat: DataFormat =
      (params.format as DataFormat) ?? (isJsonString(raw) || raw.trim().startsWith("[") ? "json" : "csv")

    const cacheKey = raw + "|" + inferredFormat + "|" + (params.sampleRows ?? 100)
    if (cache.has(cacheKey)) return cache.get(cacheKey)

    let summary = ""
    let details: any = {}

    try {
      if (inferredFormat === "csv") {
        const rows = raw.split(/\r?\n/).filter((r) => r.trim() !== "")
        const hasHeader = rows.length > 0 && rows[0].includes(",")
        const headers = hasHeader ? rows[0].split(",") : []
        const dataRows = hasHeader ? rows.slice(1) : rows
        const cols = headers.length || (dataRows[0]?.split(",").length ?? 0)
        const sampleCount = Math.max(0, Math.min(params.sampleRows ?? 100, dataRows.length))
        let missingPerRow = 0
        const numericStats: { [key: string]: { min?: number; max?: number; sum?: number; count?: number } } = {}
        // Track missing per column (per header index)
        const missingPerColumn: number[] = headers.map(() => 0)

        for (let i = 0; i < sampleCount; i++) {
          const row = dataRows[i]
          const colsInRow = row.split(",")
          for (let c = 0; c < colsInRow.length; c++) {
            const val = colsInRow[c]
            if (val === "" || val === undefined) {
              missingPerRow++
              missingPerColumn[c] = (missingPerColumn[c] ?? 0) + 1
            }
            const key = headers[c] ?? `col${c}`
            const v = Number(val)
            if (!Number.isNaN(v)) {
              if (!numericStats[key]) numericStats[key] = { min: v, max: v, sum: v, count: 1 }
              else {
                numericStats[key].min = Math.min(numericStats[key].min ?? v, v)
                numericStats[key].max = Math.max(numericStats[key].max ?? v, v)
                numericStats[key].sum = (numericStats[key].sum ?? 0) + v
                numericStats[key].count = (numericStats[key].count ?? 0) + 1
              }
            }
          }
        }

        const rowsCount = dataRows.length
        const missingAvg = sampleCount > 0 ? missingPerRow / sampleCount : 0
        const numericSummary: any = {}
        for (const key of Object.keys(numericStats)) {
          const s = numericStats[key]
          const count = s.count ?? 1
          const mean = (s.sum ?? 0) / count
          numericSummary[key] = { min: s.min, max: s.max, mean }
        }
        const missingPerColumnSummary: any = {}
        headers.forEach((h, idx) => {
          missingPerColumnSummary[h] = missingPerColumn[idx] ?? 0
        })
        summary = `Rows: ${rowsCount}, Cols: ${cols}, MissingPerRowAvg: ${missingAvg.toFixed(2)}, Numeric: ${
          Object.keys(numericSummary).length > 0
            ? Object.entries(numericSummary)
                .map(([k, v]) => `${k}:${v.mean}`)
                .join(",")
            : "none"
        }`
        details = {
          headers,
          rowsCount,
          cols,
          missingAvg,
          missingPerColumn: missingPerColumn,
          missingPerColumnSummary,
          numericSummary,
        }
      } else {
        // JSON
        const parsed = JSON.parse(raw)
        let rowsCount = 0
        const numericSummary: any = {}
        if (Array.isArray(parsed)) {
          rowsCount = parsed.length
          const first = parsed[0]
          if (first && typeof first === "object") {
            for (const key of Object.keys(first)) {
              let min = Number.POSITIVE_INFINITY
              let max = Number.NEGATIVE_INFINITY
              let sum = 0
              let count = 0
              for (const item of parsed) {
                const val = item[key]
                if (typeof val === "number" && Number.isFinite(val)) {
                  min = Math.min(min, val)
                  max = Math.max(max, val)
                  sum += val
                  count++
                }
              }
              if (count > 0) numericSummary[key] = { min, max, mean: sum / count }
            }
          }
        } else {
          rowsCount = 1
        }
        summary = `Rows: ${rowsCount}, NumericFields: ${Object.keys(numericSummary).length}`
        details = { numericSummary }
      }
    } catch (e) {
      summary = `Data length: ${params.data.length}`
      details = { error: (e as Error).message }
    }

    const result = {
      title: "Data Inspector",
      output: summary,
      metadata: {
        preview: summary,
        details,
      },
    }

    // Log milestone to watch log
    try {
      const watchResult = await WatchTool.init()
      await watchResult.execute({ milestone: "DataInspector_end_to_end", summary, details }, ctx)
    } catch {
      // ignore watch logging failures
    }

    // Autonomous continuation: schedule next task if enabled
    if (isAutonomyContinueEnabled()) {
      try {
        // Non-blocking: schedule next task in background
        setImmediate(async () => {
          try {
            const nextTaskContent = generateDataInspectorFollowUp(details, inferredFormat)
            await scheduleNextTask({
              sessionID: ctx.sessionID,
              currentTaskId: ctx.callID,
            }, nextTaskContent)
          } catch (error) {
            // Autonomy failures should not break the main tool execution
            console.warn("DataInspector autonomy scheduling failed:", error)
          }
        })
      } catch {
        // Ignore autonomy setup failures
      }
    }

    cache.set(cacheKey, result)
    return result
  },
})
