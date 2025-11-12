// Core dependencies
import z from "zod/v4"
import { Tool } from "./tool"
import { ModelOrchestration, type OrchestrationWorkflow } from "../provider/orchestration"
import { Log } from "../util/log"

// Logger for orchestration tool operations
const log = Log.create({ service: "orchestration-tool" })

/**
 * General-purpose orchestration tool for executing any workflow
 */
export const OrchestrationTool = Tool.define("orchestration", {
  description: "Execute complex multi-model workflows and orchestration pipelines for advanced AI tasks",
  parameters: z.object({
    workflowId: z
      .string()
      .describe("ID of the workflow to execute (e.g., 'code-review', 'content-creation', 'data-analysis')"),
    input: z.any().describe("Input data for the workflow"),
    options: z
      .object({
        maxParallelSteps: z.number().optional().describe("Maximum number of parallel steps to execute"),
        timeout: z.number().optional().describe("Timeout in milliseconds"),
      })
      .optional()
      .describe("Execution options"),
  }),
  async execute(params, ctx): Promise<{ title: string; metadata: any; output: any }> {
    try {
      log.info("Executing orchestration workflow", { workflowId: params.workflowId })

      const result = await ModelOrchestration.executeWorkflow(params.workflowId, params.input, {
        maxParallelSteps: params.options?.maxParallelSteps,
        timeout: params.options?.timeout,
        onStepComplete: (stepResult) => {
          log.info("Step completed", {
            stepId: stepResult.stepId,
            success: stepResult.success,
            duration: stepResult.duration,
            cost: stepResult.cost,
          })
        },
      })

      ctx.metadata({
        metadata: {
          workflowId: result.workflowId,
          success: result.success,
          totalSteps: result.metadata.totalSteps,
          executedSteps: result.metadata.executedSteps,
          duration: result.metadata.duration,
          cost: result.metadata.cost,
          steps: result.steps.map((s) => ({
            id: s.stepId,
            success: s.success,
            model: s.model,
            duration: s.duration,
            cost: s.cost,
          })),
        },
      })

      return {
        title: `Orchestration: ${result.workflowId}`,
        metadata: {
          workflowId: result.workflowId,
          success: result.success,
          duration: result.metadata.duration,
          cost: result.metadata.cost,
        },
        output: result.finalOutput,
      }
    } catch (error) {
      log.error("Orchestration execution failed", { error, workflowId: params.workflowId })
      throw new Error(`Orchestration failed: ${(error as Error).message}`)
    }
  },
})

// ==================== SPECIALIZED ORCHESTRATION TOOLS ====================

/**
 * Specialized tool for executing code review workflows
 */
export const CodeReviewOrchestrationTool = Tool.define("code-review-orchestration", {
  description: "Execute comprehensive code review using multiple specialized models",
  parameters: z.object({
    code: z.string().describe("The code to review"),
    language: z.string().optional().describe("Programming language for context"),
    focus: z.array(z.string()).optional().describe("Specific areas to focus on (security, performance, logic, etc.)"),
  }),
  async execute(params): Promise<{ title: string; metadata: any; output: any }> {
    const input = {
      code: params.code,
      language: params.language || "unknown",
      focus: params.focus || ["general"],
    }

    const result = await ModelOrchestration.executeWorkflow("code-review", input)
    return {
      title: `Code Review Results`,
      metadata: result.metadata,
      output: result.finalOutput,
    }
  },
})

/**
 * Specialized tool for executing content creation workflows
 */
export const ContentCreationOrchestrationTool = Tool.define("content-creation-orchestration", {
  description: "Create high-quality content using multi-step ideation, drafting, and refinement",
  parameters: z.object({
    topic: z.string().describe("Content topic or brief"),
    type: z.enum(["article", "blog", "tutorial", "documentation", "creative"]).describe("Type of content"),
    length: z.enum(["short", "medium", "long"]).optional().describe("Desired content length"),
    audience: z.string().optional().describe("Target audience"),
  }),
  async execute(params): Promise<{ title: string; metadata: any; output: any }> {
    const input = {
      topic: params.topic,
      type: params.type,
      length: params.length || "medium",
      audience: params.audience || "general",
    }

    const result = await ModelOrchestration.executeWorkflow("content-creation", input)
    return {
      title: `Content Creation Results`,
      metadata: result.metadata,
      output: result.finalOutput,
    }
  },
})

/**
 * Specialized tool for executing data analysis workflows
 */
export const DataAnalysisOrchestrationTool = Tool.define("data-analysis-orchestration", {
  description: "Perform comprehensive data analysis using multiple models for different perspectives",
  parameters: z.object({
    data: z.any().describe("The data to analyze (can be JSON, CSV string, or structured data)"),
    analysisType: z.array(z.string()).optional().describe("Types of analysis to perform"),
    questions: z.array(z.string()).optional().describe("Specific questions to answer"),
  }),
  async execute(params): Promise<{ title: string; metadata: any; output: any }> {
    const input = {
      data: params.data,
      analysisType: params.analysisType || ["statistical", "patterns", "insights"],
      questions: params.questions || [],
    }

    const result = await ModelOrchestration.executeWorkflow("data-analysis", input)
    return {
      title: `Data Analysis Results`,
      metadata: result.metadata,
      output: result.finalOutput,
    }
  },
})

/**
 * Tool for managing orchestration workflows (list, create, modify, delete)
 */
export const WorkflowManagementTool = Tool.define("workflow-management", {
  description: "Manage orchestration workflows - list, create, modify, and delete workflows",
  parameters: z.object({
    action: z.enum(["list", "get", "create", "update", "delete"]).describe("Action to perform"),
    workflowId: z.string().optional().describe("Workflow ID for get/update/delete actions"),
    workflow: z.any().optional().describe("Workflow definition for create/update actions"),
  }),
  async execute(params): Promise<{ title: string; metadata: any; output: any }> {
    try {
      switch (params.action) {
        case "list":
          const workflows = ModelOrchestration.listWorkflows()
          return {
            title: "Available Workflows",
            metadata: { count: workflows.length },
            output: workflows.map((w) => ({
              id: w.id,
              name: w.name,
              description: w.description,
              steps: w.steps.length,
            })),
          }

        case "get":
          if (!params.workflowId) {
            throw new Error("workflowId required for get action")
          }
          const workflow = ModelOrchestration.getWorkflow(params.workflowId)
          if (!workflow) {
            throw new Error(`Workflow ${params.workflowId} not found`)
          }
          return {
            title: `Workflow: ${workflow.name}`,
            metadata: { id: workflow.id },
            output: workflow,
          }

        case "create":
        case "update":
          if (!params.workflow) {
            throw new Error("workflow definition required for create/update action")
          }
          ModelOrchestration.registerWorkflow(params.workflow as OrchestrationWorkflow)
          return {
            title: `Workflow ${params.action}d`,
            metadata: { id: params.workflow.id },
            output: `Successfully ${params.action}d workflow: ${params.workflow.name}`,
          }

        case "delete":
          if (!params.workflowId) {
            throw new Error("workflowId required for delete action")
          }
          const deleted = ModelOrchestration.unregisterWorkflow(params.workflowId)
          return {
            title: "Workflow Deleted",
            metadata: { id: params.workflowId, deleted },
            output: deleted ? `Workflow ${params.workflowId} deleted` : `Workflow ${params.workflowId} not found`,
          }

        default:
          throw new Error(`Unknown action: ${params.action}`)
      }
    } catch (error) {
      log.error("Workflow management failed", { error, action: params.action })
      throw new Error(`Workflow management failed: ${(error as Error).message}`)
    }
  },
})
