import { cmd } from "@/cli/cmd/cmd"
import { Instance } from "@/project/instance"
import path from "path"
import { Server } from "@/server/server"
import { upgrade } from "@/cli/upgrade"

export const TuiSpawnCommand = cmd({
  command: "spawn [project]",
  builder: (yargs: any) =>
    yargs
      .positional("project", {
        type: "string",
        describe: "path to start opencode in",
      })
      .option("port", {
        type: "number",
        describe: "port to listen on",
        default: 0,
      })
      .option("hostname", {
        type: "string",
        describe: "hostname to listen on",
        default: "127.0.0.1",
      }),
  handler: async (args: any) => {
    upgrade()
    const server = await Server.listen({
      port: args.port,
      hostname: "127.0.0.1",
    })

    const bin = process.execPath
    const cmd = []
    let cwd = process.cwd()

    // Run the CLI directly with the attach command
    const scriptPath = path.resolve(process.cwd(), "src/index.ts")
    cmd.push(bin, scriptPath, "attach", server.url, "--dir", args.project ? path.resolve(args.project) : process.cwd())

    if (bin.endsWith("bun")) {
      cmd.unshift("run")
    }
    const proc = Bun.spawn({
      cmd,
      cwd,
      stdout: "inherit",
      stderr: "inherit",
      stdin: "inherit",
      env: {
        ...process.env,
        BUN_OPTIONS: "",
      },
    })
    await proc.exited
    await Instance.disposeAll()
    await server.stop(true)
  },
})
