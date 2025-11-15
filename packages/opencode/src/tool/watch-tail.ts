import path from "path"
import { Tool } from "./tool"
import { Instance } from "../project/instance"
import { promises as fs } from "fs"
import z from "zod"

export const WatchTailTool = Tool.define("watchtail", {
  description: "Watch milestone log tail for progress updates",
  parameters: z.object({
    lines: z.number().optional().describe("Number of lines to show from the end of the watch.log").default(20),
  }),
  async execute(params, ctx) {
    const lines = (params.lines ?? 20) as number
    const logDir = path.resolve(Instance.worktree, ".opencode")
    const logPath = path.join(logDir, "watch.log")

    try {
      const data = await fs.readFile(logPath, { encoding: "utf8" })
      const arr = data.trim().length ? data.trim().split("\n") : []
      const tail = arr.slice(-lines)
      return {
        title: "Watch Log Tail",
        output: tail.join("\n"),
        metadata: { lines: tail.length },
      }
    } catch {
      return {
        title: "Watch Log Tail",
        output: "No watch.log found yet.",
        metadata: { lines: 0 },
      }
    }
  },
})
