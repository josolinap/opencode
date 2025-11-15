import z from "zod/v4"
import { exec } from "child_process"
import { Tool } from "./tool"
import { Instance } from "../project/instance"
import { Log } from "../util/log"
import { $ } from "bun"

const log = Log.create({ service: "neo-clone-tool" })

const MAX_OUTPUT_LENGTH = 50_000
const DEFAULT_TIMEOUT = 5 * 60 * 1000 // 5 minutes for AI processing

export const NeoCloneTool = Tool.define("neo-clone", {
  description:
    "Execute queries using the Neo-Clone AI assistant system. Neo-Clone is a Python-based AI assistant with enhanced capabilities including multiple skills, memory system, and intelligent reasoning.",
  parameters: z.object({
    message: z.string().describe("The message or query to send to Neo-Clone"),
    mode: z
      .enum(["tool", "direct"])
      .default("tool")
      .describe(
        "Mode to run Neo-Clone in: 'tool' for single message processing, 'direct' for direct brain integration",
      ),
    timeout: z.number().default(DEFAULT_TIMEOUT).describe("Timeout in milliseconds"),
  }),
  async execute(params, ctx) {
    const neoClonePath = `${Instance.directory}/neo-clone`

    // Find working Python executable
    let pythonCmd = process.platform === "win32" ? "py" : "python3"
    try {
      const candidates = process.platform === "win32" ? ["py", "python"] : ["python3", "python"]
      for (const candidate of candidates) {
        try {
          const result = await $`${candidate} --version`.quiet()
          if (result.exitCode === 0) {
            pythonCmd = candidate
            break
          }
        } catch {
          continue
        }
      }
    } catch (error) {
      // Keep default pythonCmd
    }

    let command: string

    if (params.mode === "direct") {
      // Use direct integration test
      command = `${pythonCmd} test_direct_integration.py`
    } else if (params.mode === "tool") {
      // Use tool mode with input
      command = `${pythonCmd} main.py --tool`
    } else {
      // Legacy cli mode (deprecated)
      command = `${pythonCmd} main.py --cli`
    }

    log.info("Executing Neo-Clone", { command, mode: params.mode, message: params.message })

    try {
      let output = ""
      let errorOutput = ""

      if (params.mode === "tool") {
        // For tool mode, we need to send input and capture output
        const proc = exec(command, {
          cwd: neoClonePath,
          signal: ctx.abort,
          timeout: params.timeout,
        })

        // Send the message to stdin (tool mode reads from stdin)
        proc.stdin?.write(params.message)
        proc.stdin?.end()

        proc.stdout?.on("data", (chunk) => {
          output += chunk.toString()
        })

        proc.stderr?.on("data", (chunk) => {
          errorOutput += chunk.toString()
        })

        await new Promise<void>((resolve, reject) => {
          proc.on("close", (code) => {
            if (code === 0 || code === null) {
              resolve()
            } else {
              reject(new Error(`Neo-Clone process exited with code ${code}: ${errorOutput}`))
            }
          })
          proc.on("error", reject)
        })
      } else {
        // For direct mode, run the test script
        const result = await $`${pythonCmd} test_direct_integration.py`.cwd(neoClonePath).quiet()

        output = result.text()
      }

      // Clean up output (remove emojis that might cause issues)
      output = output.replace(
        /[🤖🛠️📊🎨💻📝📊🤖🔧💬🎨🔍🏗️💻🚀📖📚🔧💬🎨🔍🏗️🚀🔬💻🎯⚡🧠💡📈🔄💾⚙️🎮🛡️🧪📋✅❌⚠️🔴🟡🟢]/g,
        "",
      )

      // Truncate if too long
      if (output.length > MAX_OUTPUT_LENGTH) {
        output = output.slice(0, MAX_OUTPUT_LENGTH) + "\n\n(Output was truncated due to length limit)"
      }

      ctx.metadata({
        metadata: {
          mode: params.mode,
          message: params.message,
          output_length: output.length,
        },
      })

      return {
        title: `Neo-Clone ${params.mode} mode`,
        metadata: {
          mode: params.mode,
          message: params.message,
          output_length: output.length,
        },
        output: output.trim(),
      }
    } catch (error) {
      const err = error as Error
      log.error("Neo-Clone execution failed", { error: err.message, mode: params.mode })
      throw new Error(`Neo-Clone execution failed: ${err.message}`)
    }
  },
})
