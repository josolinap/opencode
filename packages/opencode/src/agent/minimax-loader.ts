import { existsSync } from "fs"

export async function loadMinimaxM2Model(): Promise<boolean> {
  const path = process.env.MINIMAX_M2_MODEL_PATH
  if (!path) return false
  try {
    return existsSync(path)
  } catch {
    return false
  }
}

export async function ensureMinimaxLoaded(): Promise<boolean> {
  return loadMinimaxM2Model()
}

export default { loadMinimaxM2Model, ensureMinimaxLoaded }
