import { existsSync } from "fs"

export function getPolicyVersion(): string {
  // Read from environment or default
  return process.env.CREDIBILITY_POLICY_VERSION ?? "default"
}

export function getPolicyVariant(): string {
  return process.env.CREDIBILITY_POLICY_VARIANT ?? "default"
}

// Additional policy metadata: name for experiments and governance
export function getPolicyName(): string {
  return process.env.CREDIBILITY_POLICY_NAME ?? "default"
}
