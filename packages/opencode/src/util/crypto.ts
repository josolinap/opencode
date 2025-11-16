import { createHash } from "node:crypto"

export function sha256Hex(data: string): string {
  const h = createHash("sha256")
  h.update(data)
  return h.digest("hex")
}
