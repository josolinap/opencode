import { test, expect } from "bun:test"
import { loadMinimaxM2Model, ensureMinimaxLoaded } from "../../src/agent/minimax-loader"
import { writeFileSync, unlinkSync, existsSync } from "fs"
import os from "os"
import path from "path"

test("minimax m2 model loads when path exists", async () => {
  const tmpPath = path.join(os.tmpdir(), "minimax-m2-model.bin")
  writeFileSync(tmpPath, "data")
  const oldPath = process.env.MINIMAX_M2_MODEL_PATH
  process.env.MINIMAX_M2_MODEL_PATH = tmpPath
  const loaded = await loadMinimaxM2Model()
  if (existsSync(tmpPath)) {
    unlinkSync(tmpPath)
  }
  process.env.MINIMAX_M2_MODEL_PATH = oldPath
  expect(loaded).toBe(true)
})

test("minimax m2 model does not load when path not set", async () => {
  const oldPath = process.env.MINIMAX_M2_MODEL_PATH
  delete process.env.MINIMAX_M2_MODEL_PATH
  const loaded = await loadMinimaxM2Model()
  process.env.MINIMAX_M2_MODEL_PATH = oldPath
  expect(loaded).toBe(false)
})
