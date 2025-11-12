import z from "zod/v4"

import { ModelRecommendationEngine, type TaskAnalysis } from "./recommendation"
import { Provider } from "./provider"
import { Log } from "../util/log"
import { NamedError } from "../util/error"

const log = Log.create({ service: "model-orchestration" })

/**
 * Defines a complete orchestration workflow for multi-model execution
 */
export interface OrchestrationWorkflow {
  /** Unique identifier for the workflow */
  id: string
  /** Human-readable name */
  name: string
  /** Optional description of the workflow's purpose */
  description?: string
  /** Sequential steps to execute */
  steps: OrchestrationStep[]
  /** How to combine outputs from multiple steps */
  ensemble?: EnsembleMethod
  /** Fallback strategy if workflow fails */
  fallback?: FallbackStrategy
}

/**
 * Defines a single step in an orchestration workflow
 */
export interface OrchestrationStep {
  /** Unique identifier for this step */
  id: string
  /** Human-readable name for the step */
  name: string
  /** Task description for model selection */
  task: string
  /** How to select the appropriate model for this step */
  modelSelector: ModelSelector
  /** How to transform input data for this step */
  inputMapping?: InputMapping
  /** How to process output from this step */
  outputMapping?: OutputMapping
  /** Conditions that must be met to execute this step */
  condition?: ExecutionCondition
  /** Whether this step can run in parallel with others */
  parallel?: boolean
}

/**
 * Defines how to select a model for a workflow step
 */
export interface ModelSelector {
  /** Selection strategy type */
  type: "recommendation" | "specific" | "best_match"
  /** Required capabilities for recommendation-based selection */
  requirements?: TaskAnalysis["requirements"]
  /** Specific model to use (when type is "specific") */
  specificModel?: {
    providerID: string
    modelID: string
  }
  /** Number of models to select (for ensemble methods) */
  count?: number
}

/**
 * Defines how to map input data for a workflow step
 */
export interface InputMapping {
  /** Source of the input data */
  source: "previous" | "original" | "combined"
  /** Specific step ID to get output from (when source is "previous") */
  stepId?: string
  /** Optional transformation function for the input */
  transform?: (input: any) => any
}

/**
 * Defines how to process output from a workflow step
 */
export interface OutputMapping {
  /** Where to send the output */
  target: "next" | "final" | "accumulate"
  /** Key to store output under (for accumulation) */
  key?: string
  /** Optional transformation function for the output */
  transform?: (output: any) => any
}

/**
 * Defines conditions for executing a workflow step
 */
export interface ExecutionCondition {
  /** Type of condition to check */
  type: "success" | "failure" | "threshold"
  /** Threshold value for threshold conditions */
  threshold?: number
  /** Step ID to check condition against */
  stepId?: string
}

/**
 * Defines how to combine outputs from multiple workflow steps
 */
export interface EnsembleMethod {
  /** Ensemble combination strategy */
  type: "majority_vote" | "weighted_average" | "concatenate" | "custom"
  /** Weights for weighted averaging (optional) */
  weights?: Record<string, number>
  /** Custom combination logic (for "custom" type) */
  customLogic?: (outputs: any[]) => any
}

/**
 * Defines fallback strategies when workflow execution fails
 */
export interface FallbackStrategy {
  /** Type of fallback strategy */
  type: "single_model" | "simplified_workflow" | "error"
  /** Single model to use as fallback */
  singleModel?: {
    providerID: string
    modelID: string
  }
  /** Simplified workflow to execute as fallback */
  simplifiedWorkflow?: OrchestrationWorkflow
}

/**
 * Result of executing an orchestration workflow
 */
export interface OrchestrationResult {
  /** ID of the executed workflow */
  workflowId: string
  /** Whether the workflow completed successfully */
  success: boolean
  /** Results from each executed step */
  steps: StepResult[]
  /** Final combined output from the workflow */
  finalOutput: any
  /** Execution metadata and statistics */
  metadata: {
    /** Total number of steps in the workflow */
    totalSteps: number
    /** Number of steps that were actually executed */
    executedSteps: number
    /** Total execution time in milliseconds */
    duration: number
    /** Total cost incurred during execution */
    cost: number
  }
}

/**
 * Result of executing a single workflow step
 */
export interface StepResult {
  /** ID of the executed step */
  stepId: string
  /** Whether the step completed successfully */
  success: boolean
  /** Model that was used for execution */
  model: {
    providerID: string
    modelID: string
  }
  /** Input data provided to the step */
  input: any
  /** Output data produced by the step */
  output: any
  /** Execution time in milliseconds */
  duration: number
  /** Cost incurred during execution */
  cost: number
  /** Error message if the step failed */
  error?: string
}

export namespace ModelOrchestration {
  // ==================== WORKFLOW REGISTRY ====================

  /** Registry of available orchestration workflows */
  const workflows = new Map<string, OrchestrationWorkflow>()

  // ==================== BUILT-IN WORKFLOWS ====================

  /** Pre-defined orchestration workflows */
  const BUILT_IN_WORKFLOWS: Record<string, OrchestrationWorkflow> = {
    "code-review": {
      id: "code-review",
      name: "Code Review Pipeline",
      description: "Multi-step code review using specialized models",
      steps: [
        {
          id: "syntax-check",
          name: "Syntax and Basic Analysis",
          task: "Check code syntax and basic structure",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: false,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 8000,
              cost: "free",
            },
          },
        },
        {
          id: "logic-review",
          name: "Logic and Algorithm Review",
          task: "Analyze code logic and algorithms",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 16000,
              cost: "budget",
            },
          },
          inputMapping: {
            source: "previous",
            transform: (input) => `Review the logic in this code:\n${input}`,
          },
        },
        {
          id: "security-check",
          name: "Security Analysis",
          task: "Check for security vulnerabilities",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 12000,
              cost: "budget",
            },
          },
          inputMapping: {
            source: "previous",
            transform: (input) => `Perform security analysis on this code:\n${input}`,
          },
          parallel: true,
        },
        {
          id: "performance-review",
          name: "Performance Optimization",
          task: "Suggest performance improvements",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 12000,
              cost: "budget",
            },
          },
          inputMapping: {
            source: "previous",
            transform: (input) => `Analyze performance of this code:\n${input}`,
          },
          parallel: true,
        },
      ],
      ensemble: {
        type: "concatenate",
        customLogic: (outputs: any[]) => {
          return outputs
            .map(
              (output, i) =>
                `## ${["Syntax Check", "Logic Review", "Security Analysis", "Performance Review"][i]}\n${output}\n`,
            )
            .join("\n")
        },
      },
    },

    "content-creation": {
      id: "content-creation",
      name: "Content Creation Pipeline",
      description: "Multi-step content creation with ideation, drafting, and refinement",
      steps: [
        {
          id: "brainstorm",
          name: "Idea Generation",
          task: "Generate creative ideas and outline",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: true,
              attachment: false,
              contextLength: 8000,
              cost: "free",
            },
          },
        },
        {
          id: "draft",
          name: "First Draft",
          task: "Create initial content draft",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: false,
              toolCalling: false,
              temperature: true,
              attachment: false,
              contextLength: 12000,
              cost: "budget",
            },
          },
          inputMapping: {
            source: "previous",
            transform: (input) => `Based on this outline, create a draft:\n${input}`,
          },
        },
        {
          id: "refine",
          name: "Content Refinement",
          task: "Polish and improve the content",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 12000,
              cost: "budget",
            },
          },
          inputMapping: {
            source: "previous",
            transform: (input) => `Refine and improve this content:\n${input}`,
          },
        },
      ],
      ensemble: {
        type: "custom",
        customLogic: (outputs: any[]) => outputs[outputs.length - 1], // Return final refined version
      },
    },

    "data-analysis": {
      id: "data-analysis",
      name: "Data Analysis Ensemble",
      description: "Multiple models analyzing data from different perspectives",
      steps: [
        {
          id: "statistical-analysis",
          name: "Statistical Analysis",
          task: "Perform statistical analysis on the data",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 12000,
              cost: "budget",
            },
          },
        },
        {
          id: "pattern-recognition",
          name: "Pattern Recognition",
          task: "Identify patterns and trends in the data",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 24000,
              cost: "budget",
            },
          },
          parallel: true,
        },
        {
          id: "insight-generation",
          name: "Insight Generation",
          task: "Generate actionable insights from analysis",
          modelSelector: {
            type: "recommendation",
            requirements: {
              reasoning: true,
              toolCalling: false,
              temperature: false,
              attachment: false,
              contextLength: 20000,
              cost: "premium",
            },
          },
          parallel: true,
        },
      ],
      ensemble: {
        type: "concatenate",
        customLogic: (outputs: any[]) => {
          return `## Statistical Analysis\n${outputs[0]}\n\n## Pattern Recognition\n${outputs[1]}\n\n## Key Insights\n${outputs[2]}`
        },
      },
    },
  }

  // Initialize built-in workflows
  for (const [id, workflow] of Object.entries(BUILT_IN_WORKFLOWS)) {
    workflows.set(id, workflow)
  }

  // ==================== WORKFLOW EXECUTION ====================

  /**
   * Execute an orchestration workflow with the given input
   * @param workflowId - ID of the workflow to execute
   * @param input - Input data for the workflow
   * @param options - Execution options
   * @returns Promise resolving to the orchestration result
   */
  export async function executeWorkflow(
    workflowId: string,
    input: any,
    options: {
      maxParallelSteps?: number
      timeout?: number
      onStepComplete?: (stepResult: StepResult) => void
    } = {},
  ): Promise<OrchestrationResult> {
    const startTime = Date.now()
    const workflow = workflows.get(workflowId)

    if (!workflow) {
      throw new WorkflowNotFoundError({ workflowId })
    }

    log.info("Executing orchestration workflow", { workflowId, stepCount: workflow.steps.length })

    const results: StepResult[] = []
    const stepOutputs = new Map<string, any>()
    let totalCost = 0

    try {
      // Execute steps in order, handling parallel execution
      for (let i = 0; i < workflow.steps.length; i++) {
        const step = workflow.steps[i]
        const parallelSteps: OrchestrationStep[] = []

        // Collect parallel steps
        parallelSteps.push(step)
        while (i + 1 < workflow.steps.length && workflow.steps[i + 1].parallel) {
          i++
          parallelSteps.push(workflow.steps[i])
        }

        // Execute parallel steps
        const stepPromises = parallelSteps.map(async (parallelStep) => {
          return executeStep(parallelStep, input, stepOutputs)
        })

        const stepResults = await Promise.all(stepPromises)

        // Process results
        for (const result of stepResults) {
          results.push(result)
          totalCost += result.cost

          if (result.success) {
            stepOutputs.set(result.stepId, result.output)
          }

          options.onStepComplete?.(result)
        }

        // Check if we should continue based on conditions
        const failedSteps = stepResults.filter((r) => !r.success)
        if (failedSteps.length > 0 && workflow.fallback) {
          return handleFallback(workflow.fallback, input, failedSteps, startTime)
        }
      }

      // Apply ensemble method if specified
      const finalOutput = workflow.ensemble
        ? applyEnsemble(
            workflow.ensemble,
            results.filter((r) => r.success),
          )
        : stepOutputs.get(results[results.length - 1]?.stepId)

      const duration = Date.now() - startTime

      return {
        workflowId,
        success: true,
        steps: results,
        finalOutput,
        metadata: {
          totalSteps: workflow.steps.length,
          executedSteps: results.length,
          duration,
          cost: totalCost,
        },
      }
    } catch (error) {
      log.error("Workflow execution failed", { workflowId, error })

      if (workflow.fallback) {
        return handleFallback(workflow.fallback, input, [], startTime)
      }

      return {
        workflowId,
        success: false,
        steps: results,
        finalOutput: null,
        metadata: {
          totalSteps: workflow.steps.length,
          executedSteps: results.length,
          duration: Date.now() - startTime,
          cost: totalCost,
        },
      }
    }
  }

  async function executeStep(
    step: OrchestrationStep,
    originalInput: any,
    stepOutputs: Map<string, any>,
  ): Promise<StepResult> {
    const startTime = Date.now()

    try {
      // Prepare input
      let input = originalInput
      if (step.inputMapping) {
        input = prepareStepInput(step.inputMapping, originalInput, stepOutputs)
      }

      // Select model
      const modelSelection = await selectModelForStep(step.modelSelector, step.task)

      // Execute with selected model
      const result = await executeWithModel(modelSelection, step.task, input)

      const duration = Date.now() - startTime

      return {
        stepId: step.id,
        success: true,
        model: modelSelection,
        input,
        output: result.output,
        duration,
        cost: result.cost,
      }
    } catch (error) {
      const duration = Date.now() - startTime

      return {
        stepId: step.id,
        success: false,
        model: { providerID: "unknown", modelID: "unknown" },
        input: null,
        output: null,
        duration,
        cost: 0,
        error: (error as Error).message,
      }
    }
  }

  async function selectModelForStep(
    selector: ModelSelector,
    task: string,
  ): Promise<{ providerID: string; modelID: string }> {
    switch (selector.type) {
      case "specific":
        if (!selector.specificModel) {
          throw new Error("Specific model not defined")
        }
        return selector.specificModel

      case "recommendation":
        const recommendations = await ModelRecommendationEngine.recommendForTask(task)
        const best = recommendations[0]
        if (!best) {
          throw new Error("No suitable model found")
        }
        return { providerID: best.provider, modelID: best.model }

      case "best_match":
        // Use the existing model selection logic
        const defaultModel = await Provider.defaultModel()
        return defaultModel

      default:
        throw new Error(`Unknown selector type: ${selector.type}`)
    }
  }

  async function executeWithModel(
    modelSelection: { providerID: string; modelID: string },
    task: string,
    input: any,
  ): Promise<{ output: any; cost: number }> {
    // This would integrate with the actual model execution
    // For now, return mock results
    const model = await Provider.getModel(modelSelection.providerID, modelSelection.modelID)

    // Mock execution - in real implementation, this would call the model
    const output = `Mock output for task: ${task} with input: ${JSON.stringify(input)}`
    const cost = (model.info.cost.input + model.info.cost.output) * 0.001 // Mock cost calculation

    return { output, cost }
  }

  function prepareStepInput(mapping: InputMapping, originalInput: any, stepOutputs: Map<string, any>): any {
    let input: any

    switch (mapping.source) {
      case "original":
        input = originalInput
        break
      case "previous":
        input = mapping.stepId ? stepOutputs.get(mapping.stepId) : originalInput
        break
      case "combined":
        input = {
          original: originalInput,
          previous: Object.fromEntries(stepOutputs),
        }
        break
    }

    return mapping.transform ? mapping.transform(input) : input
  }

  function applyEnsemble(method: EnsembleMethod, results: StepResult[]): any {
    switch (method.type) {
      case "majority_vote":
        // Simple majority vote for classification tasks
        return results[0]?.output // Placeholder

      case "weighted_average":
        // Weighted average for numerical outputs
        return results[0]?.output // Placeholder

      case "concatenate":
        return results.map((r) => r.output).join("\n\n")

      case "custom":
        return method.customLogic?.(results.map((r) => r.output)) || results[0]?.output

      default:
        return results[0]?.output
    }
  }

  async function handleFallback(
    fallback: FallbackStrategy,
    input: any,
    failedSteps: StepResult[],
    startTime: number,
  ): Promise<OrchestrationResult> {
    log.warn("Applying fallback strategy", { type: fallback.type })

    switch (fallback.type) {
      case "single_model":
        if (!fallback.singleModel) {
          throw new Error("Single model fallback not configured")
        }

        const result = await executeWithModel(fallback.singleModel, "Fallback execution", input)
        return {
          workflowId: "fallback",
          success: true,
          steps: [
            {
              stepId: "fallback",
              success: true,
              model: fallback.singleModel,
              input,
              output: result.output,
              duration: Date.now() - startTime,
              cost: result.cost,
            },
          ],
          finalOutput: result.output,
          metadata: {
            totalSteps: 1,
            executedSteps: 1,
            duration: Date.now() - startTime,
            cost: result.cost,
          },
        }

      case "simplified_workflow":
        if (!fallback.simplifiedWorkflow) {
          throw new Error("Simplified workflow fallback not configured")
        }
        return executeWorkflow(fallback.simplifiedWorkflow.id, input)

      case "error":
      default:
        throw new Error(`Workflow failed at steps: ${failedSteps.map((s) => s.stepId).join(", ")}`)
    }
  }

  // ==================== WORKFLOW MANAGEMENT ====================

  /**
   * Register a new orchestration workflow
   * @param workflow - The workflow definition to register
   */
  export function registerWorkflow(workflow: OrchestrationWorkflow): void {
    workflows.set(workflow.id, workflow)
    log.info("Workflow registered", { workflowId: workflow.id })
  }

  /**
   * Get a registered workflow by ID
   * @param workflowId - ID of the workflow to retrieve
   * @returns The workflow definition or undefined if not found
   */
  export function getWorkflow(workflowId: string): OrchestrationWorkflow | undefined {
    return workflows.get(workflowId)
  }

  /**
   * List all registered workflows
   * @returns Array of all registered workflow definitions
   */
  export function listWorkflows(): OrchestrationWorkflow[] {
    return Array.from(workflows.values())
  }

  /**
   * Remove a workflow from the registry
   * @param workflowId - ID of the workflow to remove
   * @returns True if the workflow was removed, false if it wasn't found
   */
  export function unregisterWorkflow(workflowId: string): boolean {
    return workflows.delete(workflowId)
  }

  // ==================== CONVENIENCE METHODS ====================

  /**
   * Execute the built-in code review workflow
   * @param code - The code to review
   * @returns Promise resolving to the orchestration result
   */
  export async function executeCodeReview(code: string): Promise<OrchestrationResult> {
    return executeWorkflow("code-review", code)
  }

  /**
   * Execute the built-in content creation workflow
   * @param topic - The topic or brief for content creation
   * @returns Promise resolving to the orchestration result
   */
  export async function executeContentCreation(topic: string): Promise<OrchestrationResult> {
    return executeWorkflow("content-creation", topic)
  }

  /**
   * Execute the built-in data analysis workflow
   * @param data - The data to analyze
   * @returns Promise resolving to the orchestration result
   */
  export async function executeDataAnalysis(data: any): Promise<OrchestrationResult> {
    return executeWorkflow("data-analysis", data)
  }

  // ==================== ERROR CLASSES ====================

  /** Error thrown when a requested workflow is not found */
  export const WorkflowNotFoundError = NamedError.create(
    "WorkflowNotFoundError",
    z.object({
      workflowId: z.string(),
    }),
  )

  /** Error thrown when a workflow step fails to execute */
  export const StepExecutionError = NamedError.create(
    "StepExecutionError",
    z.object({
      stepId: z.string(),
      error: z.string(),
    }),
  )
}
