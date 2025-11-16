// Type declarations for .txt file imports
declare module "*.txt" {
  const content: string
  export default content
}

// Type declarations for .md file imports
declare module "*.md" {
  const content: string
  export default content
}

// Global Bun types
declare global {
  namespace Bun {
    function file(path: string | URL): any
  }
  const $: any
  function fileURLToPath(url: string | URL): string
}

// Ensure Bun globals are available
declare const Bun: typeof globalThis.Bun
declare const $: any
declare const fileURLToPath: (url: string | URL) => string
