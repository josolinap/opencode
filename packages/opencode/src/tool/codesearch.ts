import z from "zod"
import { Tool } from "./tool"
import DESCRIPTION from "./codesearch.txt"
import { Config } from "../config/config"
import { Permission } from "../permission"
import { scheduleNextTask } from "../brain/autopilot"
import { isAutonomyContinueEnabled } from "../storage/feature-flags"

const API_CONFIG = {
  BASE_URL: "https://mcp.exa.ai",
  ENDPOINTS: {
    CONTEXT: "/mcp",
  },
} as const

interface McpCodeRequest {
  jsonrpc: string
  id: number
  method: string
  params: {
    name: string
    arguments: {
      query: string
      tokensNum: number
    }
  }
}

interface McpCodeResponse {
  jsonrpc: string
  result: {
    content: Array<{
      type: string
      text: string
    }>
  }
}

function generateCodeSearchFollowUp(query: string, output: string): string {
  // Generate contextual follow-up task based on code search results
  const lowerQuery = query.toLowerCase()
  const lowerOutput = output.toLowerCase()

  // Check for common code search patterns and suggest follow-ups
  if (lowerQuery.includes("error") || lowerQuery.includes("exception") || lowerQuery.includes("bug")) {
    return "Analyze error patterns and suggest comprehensive error handling improvements"
  }

  if (lowerQuery.includes("test") || lowerQuery.includes("spec") || lowerQuery.includes("unit test")) {
    return "Review test coverage and suggest additional test cases for edge conditions"
  }

  if (lowerQuery.includes("performance") || lowerQuery.includes("optimization") || lowerQuery.includes("speed")) {
    return "Analyze performance bottlenecks and suggest optimization strategies"
  }

  if (lowerQuery.includes("security") || lowerQuery.includes("auth") || lowerQuery.includes("vulnerability")) {
    return "Review security implications and suggest hardening measures"
  }

  if (lowerQuery.includes("refactor") || lowerQuery.includes("clean") || lowerQuery.includes("improve")) {
    return "Identify refactoring opportunities and propose code improvements"
  }

  if (lowerOutput.includes("async") || lowerOutput.includes("promise") || lowerOutput.includes("await")) {
    return "Review asynchronous patterns and suggest concurrency improvements"
  }

  if (lowerOutput.includes("database") || lowerOutput.includes("sql") || lowerOutput.includes("query")) {
    return "Analyze database interactions and suggest query optimizations"
  }

  if (lowerOutput.includes("api") || lowerOutput.includes("endpoint") || lowerOutput.includes("rest")) {
    return "Review API design patterns and suggest interface improvements"
  }

  // Default follow-ups based on code search results
  if (output.length > 1000) {
    return "Review comprehensive code examples and extract best practices"
  }

  if (lowerOutput.includes("function") || lowerOutput.includes("method") || lowerOutput.includes("class")) {
    return "Analyze code structure and suggest design pattern improvements"
  }

  return "Review code examples and identify implementation opportunities"
}

export const CodeSearchTool = Tool.define("codesearch", {
  description: DESCRIPTION,
  parameters: z.object({
    query: z
      .string()
      .describe(
        "Search query to find relevant context for APIs, Libraries, and SDKs. For example, 'React useState hook examples', 'Python pandas dataframe filtering', 'Express.js middleware', 'Next js partial prerendering configuration'",
      ),
    tokensNum: z
      .number()
      .min(1000)
      .max(50000)
      .default(5000)
      .describe(
        "Number of tokens to return (1000-50000). Default is 5000 tokens. Adjust this value based on how much context you need - use lower values for focused queries and higher values for comprehensive documentation.",
      ),
  }),
  async execute(params, ctx) {
    const cfg = await Config.get()
    if (cfg.permission?.webfetch === "ask")
      await Permission.ask({
        type: "codesearch",
        sessionID: ctx.sessionID,
        messageID: ctx.messageID,
        callID: ctx.callID,
        title: "Search code for: " + params.query,
        metadata: {
          query: params.query,
          tokensNum: params.tokensNum,
        },
      })

    const codeRequest: McpCodeRequest = {
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: "get_code_context_exa",
        arguments: {
          query: params.query,
          tokensNum: params.tokensNum || 5000,
        },
      },
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)

    try {
      const headers: Record<string, string> = {
        accept: "application/json, text/event-stream",
        "content-type": "application/json",
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CONTEXT}`, {
        method: "POST",
        headers,
        body: JSON.stringify(codeRequest),
        signal: AbortSignal.any([controller.signal, ctx.abort]),
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Code search error (${response.status}): ${errorText}`)
      }

      const responseText = await response.text()

      // Parse SSE response
      const lines = responseText.split("\n")
      let result
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data: McpCodeResponse = JSON.parse(line.substring(6))
          if (data.result && data.result.content && data.result.content.length > 0) {
            result = {
              output: data.result.content[0].text,
              title: `Code search: ${params.query}`,
              metadata: {},
            }
            break
          }
        }
      }

      if (!result) {
        result = {
          output:
            "No code snippets or documentation found. Please try a different query, be more specific about the library or programming concept, or check the spelling of framework names.",
          title: `Code search: ${params.query}`,
          metadata: {},
        }
      }

      // Autonomous continuation: schedule next task if enabled
      if (isAutonomyContinueEnabled()) {
        try {
          // Non-blocking: schedule next task in background
          setImmediate(async () => {
            try {
              const nextTaskContent = generateCodeSearchFollowUp(params.query, result.output)
              await scheduleNextTask(
                {
                  sessionID: ctx.sessionID,
                  currentTaskId: ctx.callID,
                },
                nextTaskContent,
              )
            } catch (error) {
              // Autonomy failures should not break the main tool execution
              console.warn("CodeSearch autonomy scheduling failed:", error)
            }
          })
        } catch {
          // Ignore autonomy setup failures
        }
      }

      return result
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Code search request timed out")
      }

      throw error
    }
  },
})
