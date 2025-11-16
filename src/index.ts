#!/usr/bin/env bun
import { spawn } from "child_process"

// Delegate to the actual opencode CLI in packages/opencode
const proc = spawn(process.execPath, ["run", "--cwd", "packages/opencode", "src/index.ts", ...process.argv.slice(2)], {
  stdio: "inherit",
  cwd: process.cwd(),
})

proc.on("exit", (code) => {
  process.exit(code)
})

proc.on("error", (err) => {
  console.error("Failed to start opencode:", err)
  process.exit(1)
})
