const state: {
  inited: boolean
  lsp?: any
} = { inited: false }

async function ensure() {
  if (state.inited) return
  await import(".").then((m) => {
    state.lsp = m.LSP
    state.inited = true
  })
}

export const LSPManager = {
  async touchFile(path: string, force?: boolean) {
    await ensure()
    return state.lsp.touchFile(path, force)
  },
  async diagnostics() {
    await ensure()
    return state.lsp.diagnostics()
  },
  async format(path: string) {
    await ensure()
    return state.lsp.format(path)
  },
}
