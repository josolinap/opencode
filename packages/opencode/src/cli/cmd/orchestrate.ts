// Core dependencies
import { Instance } from "../../project/instance"
import { ModelOrchestration, type OrchestrationResult } from "../../provider/orchestration"
import { cmd } from "./cmd"
import { Log } from "../../util/log"
import { exit } from "process"

// Logger for orchestrate command operations
const log = Log.create({ service: "orchestrate-command" })

/**
 * CLI command for executing orchestration workflows
 */
export const OrchestrateCommand = cmd({
  command: "orchestrate <workflow> [input]",
  describe: "Execute orchestration workflows using multiple AI models for complex tasks",
  builder: (yargs) =>
    yargs
      .positional("workflow", {
        describe: "Workflow to execute: code-review, content-creation, data-analysis, or custom workflow ID",
        type: "string",
        demandOption: true,
      })
      .positional("input", {
        describe: "Input data for the workflow (JSON string or file path)",
        type: "string",
      })
      .option("input-file", {
        alias: "f",
        describe: "Read input from file instead of argument",
        type: "string",
      })
      .option("output", {
        alias: "o",
        describe: "Output format: summary, detailed, json",
        type: "string",
        default: "summary",
        choices: ["summary", "detailed", "json"],
      })
      .option("parallel", {
        alias: "p",
        describe: "Maximum number of parallel steps",
        type: "number",
        default: 3,
      })
      .option("timeout", {
        alias: "t",
        describe: "Timeout in milliseconds",
        type: "number",
        default: 300000, // 5 minutes
      })
      .option("list", {
        alias: "l",
        describe: "List available workflows and exit",
        type: "boolean",
        default: false,
      })
      .option("create", {
        alias: "c",
        describe: "Create a new workflow from JSON file",
        type: "string",
      })
      .option("delete", {
        alias: "d",
        describe: "Delete a workflow",
        type: "string",
      }),
  handler: async (argv) => {
    await Instance.provide({
      directory: process.cwd(),
      async fn() {
        const workflowId = argv.workflow as string
        const listOnly = argv.list as boolean
        const createWorkflow = argv.create as string
        const deleteWorkflow = argv.delete as string

        // Handle workflow management commands
        if (listOnly) {
          await listWorkflows(argv)
          return
        }

        if (createWorkflow) {
          await createWorkflowFromFile(createWorkflow)
          return
        }

        if (deleteWorkflow) {
          await deleteWorkflowById(deleteWorkflow)
          return
        }

        // Execute workflow
        if (!workflowId) {
          console.error("Error: Workflow ID is required")
          console.log("Use --list to see available workflows")
          exit(1)
        }

        // Get input data
        let input: any
        try {
          input = await getInputData(argv)
        } catch (error) {
          console.error(`Error reading input: ${(error as Error).message}`)
          exit(1)
        }

        // Execute orchestration
        console.log(`🚀 Executing workflow: ${workflowId}`)
        console.log(
          `📊 Input: ${typeof input === "string" ? input.substring(0, 100) + "..." : JSON.stringify(input).substring(0, 100) + "..."}`,
        )

        try {
          const result = await ModelOrchestration.executeWorkflow(workflowId, input, {
            maxParallelSteps: argv.parallel as number,
            timeout: argv.timeout as number,
            onStepComplete: (stepResult) => {
              const status = stepResult.success ? "✅" : "❌"
              console.log(
                `${status} Step "${stepResult.stepId}" completed in ${stepResult.duration}ms ($${stepResult.cost.toFixed(4)})`,
              )
            },
          })

          // Output results
          outputResults(result, argv.output as string)
        } catch (error) {
          log.error("Workflow execution failed", { error, workflowId })
          console.error(`❌ Workflow execution failed: ${(error as Error).message}`)
          exit(1)
        }
      },
    })
  },
})

// ==================== WORKFLOW MANAGEMENT FUNCTIONS ====================

async function listWorkflows(argv: any) {
  const workflows = ModelOrchestration.listWorkflows()

  if (argv.format === "json") {
    console.log(JSON.stringify(workflows, null, 2))
  } else {
    console.log("Available Orchestration Workflows:")
    console.log("=".repeat(50))

    for (const workflow of workflows) {
      console.log(`📋 ${workflow.id}`)
      console.log(`   ${workflow.name}`)
      if (workflow.description) {
        console.log(`   ${workflow.description}`)
      }
      console.log(`   Steps: ${workflow.steps.length}`)
      if (workflow.ensemble) {
        console.log(`   Ensemble: ${workflow.ensemble.type}`)
      }
      console.log()
    }

    console.log("Built-in workflows:")
    console.log("  code-review     - Multi-step code review pipeline")
    console.log("  content-creation - Content creation with ideation and refinement")
    console.log("  data-analysis   - Multi-perspective data analysis")
    console.log()
    console.log("Usage examples:")
    console.log("  opencode orchestrate code-review 'def hello(): pass'")
    console.log("  opencode orchestrate content-creation 'Write about AI ethics'")
    console.log("  opencode orchestrate data-analysis --input-file data.json")
  }
}

async function createWorkflowFromFile(filePath: string) {
  try {
    const content = await Bun.file(filePath).text()
    const workflow = JSON.parse(content)

    ModelOrchestration.registerWorkflow(workflow)
    console.log(`✅ Workflow "${workflow.name}" created successfully`)
    console.log(`   ID: ${workflow.id}`)
    console.log(`   Steps: ${workflow.steps.length}`)
  } catch (error) {
    console.error(`❌ Failed to create workflow: ${(error as Error).message}`)
    exit(1)
  }
}

async function deleteWorkflowById(workflowId: string) {
  const deleted = ModelOrchestration.unregisterWorkflow(workflowId)
  if (deleted) {
    console.log(`✅ Workflow "${workflowId}" deleted successfully`)
  } else {
    console.error(`❌ Workflow "${workflowId}" not found`)
    exit(1)
  }
}

// ==================== UTILITY FUNCTIONS ====================

async function getInputData(argv: any): Promise<any> {
  const inputArg = argv.input as string
  const inputFile = argv["input-file"] as string

  if (inputFile) {
    // Read from file
    const content = await Bun.file(inputFile).text()
    try {
      return JSON.parse(content)
    } catch {
      // If not JSON, return as string
      return content
    }
  }

  if (inputArg) {
    // Try to parse as JSON, otherwise treat as string
    try {
      return JSON.parse(inputArg)
    } catch {
      return inputArg
    }
  }

  // No input provided - use empty object
  return {}
}

// ==================== OUTPUT FUNCTIONS ====================

function outputResults(result: OrchestrationResult, format: string) {
  console.log(`\n🎯 Workflow Execution Complete`)
  console.log(`📊 Workflow: ${result.workflowId}`)
  console.log(`⏱️  Duration: ${result.metadata.duration}ms`)
  console.log(`💰 Cost: $${result.metadata.cost.toFixed(4)}`)
  console.log(`✅ Success: ${result.success}`)
  console.log(`📈 Steps: ${result.metadata.executedSteps}/${result.metadata.totalSteps}`)

  if (format === "json") {
    console.log(JSON.stringify(result, null, 2))
    return
  }

  if (format === "detailed") {
    console.log("\n📝 Step Details:")
    console.log("-".repeat(80))

    for (const step of result.steps) {
      const status = step.success ? "✅" : "❌"
      console.log(`${status} ${step.stepId}`)
      console.log(`   Model: ${step.model.providerID}/${step.model.modelID}`)
      console.log(`   Duration: ${step.duration}ms`)
      console.log(`   Cost: $${step.cost.toFixed(4)}`)
      if (step.error) {
        console.log(`   Error: ${step.error}`)
      }
      console.log()
    }
  }

  console.log("\n📄 Final Output:")
  console.log("-".repeat(50))
  if (typeof result.finalOutput === "string") {
    console.log(result.finalOutput)
  } else {
    console.log(JSON.stringify(result.finalOutput, null, 2))
  }
}
