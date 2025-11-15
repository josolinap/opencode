import path from "path"
import { Tool } from "./tool"
import { Instance } from "../project/instance"
import { promises as fs } from "fs"
import z from "zod"

function getInstanceId(): string {
  const v = process?.env?.OPENCODE_INSTANCE
  if (v) return String(v)
  try {
    return "pid-" + process.pid
  } catch {}
  return "default"
}

export const WatchTool = Tool.define("watch", {
  description: "Milestone watcher for autonomous progress updates",
  parameters: z.object({
    milestone: z.string(),
    summary: z.string().optional(),
    details: z.any().optional(),
  }),
  async execute(params, ctx) {
    const milestone = params.milestone as string
    const summary = params.summary ?? ""
    const details = params.details ?? {}

    const instanceId = getInstanceId()
    const logDir = path.resolve(Instance.worktree, ".opencode")
    const instanceLogDir = path.join(logDir, `watch-${instanceId}`)
    try {
      await fs.mkdir(instanceLogDir, { recursive: true })
    } catch {}
    const logPath = path.join(instanceLogDir, "watch.log")
    const entry = {
      ts: new Date().toISOString(),
      milestone,
      summary,
      details,
    }
    try {
      await fs.appendFile(logPath, JSON.stringify(entry) + "\n")
    } catch {}
    return {
      title: "Watcher",
      output: "Logged milestone: " + milestone,
      metadata: {},
    }
  },
})
