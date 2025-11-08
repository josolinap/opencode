import path from "path"
import { Ripgrep } from "../file/ripgrep"

export const FileIndex = (() => {
  const files = new Map<string, number>()
  async function build(dir: string) {
    for await (const f of Ripgrep.files({ cwd: dir, glob: ["**/*.*"] })) {
      const full = path.isAbsolute(f) ? f : path.resolve(dir, f)
      await Bun.file(full)
        .stat()
        .then((s) => files.set(full, s.mtime.getTime()))
        .catch(() => {})
    }
  }

  function search(q: string, limit = 50) {
    const s = q.toLowerCase()
    return Array.from(files.keys())
      .filter((p) => p.toLowerCase().includes(s))
      .slice(0, limit)
  }

  function size() {
    return files.size
  }

  return {
    build,
    search,
    size,
  }
})()
