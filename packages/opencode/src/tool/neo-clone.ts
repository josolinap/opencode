import z from "zod/v4"
import { Tool } from "./tool"
import { $ } from "bun"
import path from "path"
import { Instance } from "../project/instance"

export const NeoCloneTool = Tool.define("neo_clone_brain", {
  description: "Neo-Clone enhanced AI brain with MiniMax reasoning, skills, memory, and model selection",
  parameters: z.object({
    input: z.string().describe("The user input to process through Neo-Clone's brain"),
    context: z.string().optional().describe("Additional context for processing"),
    model: z.string().optional().describe("The model to use in provider/model format"),
  }),
  async execute(params, ctx) {
    try {
      // Get the neo-clone directory
      const neoCloneDir = path.join(Instance.worktree, "neo-clone")

      // Create a temporary input file
      const inputFile = path.join(neoCloneDir, "temp_input.json")
      const outputFile = path.join(neoCloneDir, "temp_output.json")

      const inputData = {
        input: params.input,
        context: params.context || "",
        session_id: ctx.sessionID,
        model: params.model, // Pass the current model
      }

      // Write input to file
      await Bun.write(inputFile, JSON.stringify(inputData))

      // Call Neo-Clone brain
      const script = `
import sys
import json
import os
sys.path.insert(0, '.')

from config_opencode import load_config, translate_opencode_model_to_neo
from brain_opencode import OpencodeBrain
from skills import SkillRegistry

def main():
    with open('temp_input.json', 'r') as f:
        data = json.load(f)

    config = load_config()

    # Override model if provided
    if data.get('model'):
        provider, model_name = translate_opencode_model_to_neo(data['model'])
        config.provider = provider
        config.model_name = model_name
        config.opencode_model = data['model']

    skills = SkillRegistry()
    brain = OpencodeBrain(config, skills)

    response = brain.send_message(data['input'])

    result = {
        'response': response,
        'status': 'success',
        'model_used': f"{config.provider}/{config.model_name}"
    }

    with open('temp_output.json', 'w') as f:
        json.dump(result, f)

if __name__ == "__main__":
    main()
`

      const scriptFile = path.join(neoCloneDir, "temp_script.py")
      await Bun.write(scriptFile, script)

      // Run the Python script
      const result = await $`cd ${neoCloneDir} && py temp_script.py`.nothrow()

      if (result.exitCode !== 0) {
        throw new Error(`Neo-Clone brain failed: ${result.stderr}`)
      }

      // Read output
      const outputData = JSON.parse(await Bun.file(outputFile).text())

      // Clean up temp files
      await Bun.write(inputFile, "")
      await Bun.write(outputFile, "")
      await Bun.write(scriptFile, "")

      return {
        title: "Neo-Clone Response",
        output: outputData.response,
        metadata: {
          status: outputData.status,
          brain: "neo-clone",
          model_used: outputData.model_used,
          error: false,
        },
      }
    } catch (error) {
      return {
        title: "Neo-Clone Error",
        output: `Error calling Neo-Clone brain: ${error}`,
        metadata: {
          status: "error",
          brain: "neo-clone",
          model_used: "unknown",
          error: true,
        },
      }
    }
  },
})
