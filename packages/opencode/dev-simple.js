// Simple dev script to bypass package manager issues
import { execSync } from "child_process"
import { existsSync } from "fs"

console.log("Starting OpenCode TUI in simple mode...")

// Check if node_modules exists
if (!existsSync("./node_modules")) {
  console.log("node_modules not found. Installing basic dependencies...")
  try {
    // Try to install just yargs
    execSync("npm install yargs --no-save", { stdio: "inherit" })
  } catch (e) {
    console.log("Failed to install dependencies. Trying to run anyway...")
  }
}

// Try to run the TypeScript file
try {
  execSync("npx tsx ./src/index.ts", { stdio: "inherit" })
} catch (e) {
  console.log("Failed to run with tsx. Trying with ts-node...")
  try {
    execSync("npx ts-node ./src/index.ts", { stdio: "inherit" })
  } catch (e2) {
    console.log("Failed to run TypeScript. Please install dependencies first.")
    console.log("Try: npm install yargs typescript @types/node")
  }
}
