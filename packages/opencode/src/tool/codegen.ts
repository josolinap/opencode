import z from "zod"
import { Tool } from "./tool"
import DESCRIPTION from "./codegen.txt"
import { WatchTool } from "./watch"

// Enhanced code generation tool with intelligent template selection
export const CodeGenTool = Tool.define("codegen", {
  description: DESCRIPTION,
  parameters: z.object({
    prompt: z.string().describe("Prompt describing desired code"),
    language: z.string().optional().describe("Target programming language (default: Python)").default("Python"),
    explain: z
      .boolean()
      .optional()
      .describe("Include a brief explanation alongside code (default: true)")
      .default(true),
  }),
  async execute(params: any, ctx: any) {
    const lang = (params.language as string) ?? "Python"
    const prompt = params.prompt.toLowerCase()

    // Determine code type based on prompt keywords
    let codeType = "basic"
    if (prompt.includes("function")) codeType = "function"
    else if (prompt.includes("class")) codeType = "class"
    else if (prompt.includes("loop") || prompt.includes("for") || prompt.includes("while")) codeType = "loop"
    else if (prompt.includes("if") || prompt.includes("condition")) codeType = "conditional"
    else if (prompt.includes("array") || prompt.includes("list")) codeType = "array"

    // Generate code based on language and type
    const code = generateCode(lang, codeType)
    const explanation = params.explain ? generateExplanation(lang, codeType, params.prompt) : undefined

    const output = explanation ? code + "\n" + explanation : code

    const result = {
      title: `Code generation: ${lang} - ${codeType}`,
      output,
      metadata: {
        prompt: params.prompt,
        language: lang,
        codeType,
        explain: !!params.explain,
        explanation: explanation ? explanation : undefined,
      },
    }

    // Log milestone
    try {
      await WatchTool.execute(
        {
          milestone: "CodeGen_end_to_end",
          summary: `CodeGen end-to-end for ${lang} (${codeType})`,
          details: { prompt: params.prompt, language: lang, codeType, explain: !!params.explain },
        },
        ctx,
      )
    } catch {
      // ignore watch failures
    }

    return result
  },
})

// Helper function to generate code based on language and type
function generateCode(lang: string, type: string): string {
  const templates: Record<string, Record<string, string>> = {
    python: {
      basic: `# Generated Python code\nprint('Hello from Python!')\n`,
      function: `def example_function(name):\n    """Example function that greets someone."""\n    return f"Hello, {name}!"\n\n# Usage\nresult = example_function("World")\nprint(result)\n`,
      class: `class ExampleClass:\n    """Example class with basic functionality."""\n    \n    def __init__(self, value):\n        self.value = value\n    \n    def get_value(self):\n        return self.value\n\n# Usage\nobj = ExampleClass(42)\nprint(obj.get_value())\n`,
      loop: `for i in range(5):\n    print(f"Iteration {i}")\n`,
      conditional: `x = 10\nif x > 5:\n    print("x is greater than 5")\nelse:\n    print("x is not greater than 5")\n`,
      array: `my_list = [1, 2, 3, 4, 5]\nfor item in my_list:\n    print(item)\n`,
    },
    javascript: {
      basic: `// Generated JavaScript code\nconsole.log('Hello from JavaScript!');\n`,
      function: `function exampleFunction(name) {\n    // Example function that greets someone\n    return \`Hello, \${name}!\`;\n}\n\n// Usage\nconst result = exampleFunction("World");\nconsole.log(result);\n`,
      class: `class ExampleClass {\n    constructor(value) {\n        this.value = value;\n    }\n    \n    getValue() {\n        return this.value;\n    }\n}\n\n// Usage\nconst obj = new ExampleClass(42);\nconsole.log(obj.getValue());\n`,
      loop: `for (let i = 0; i < 5; i++) {\n    console.log(\`Iteration \${i}\`);\n}`,
      conditional: `const x = 10;\nif (x > 5) {\n    console.log("x is greater than 5");\n} else {\n    console.log("x is not greater than 5");\n}`,
      array: `const myArray = [1, 2, 3, 4, 5];\nmyArray.forEach(item => {\n    console.log(item);\n});\n`,
    },
    java: {
      basic: `// Generated Java code\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello from Java!");\n    }\n}\n`,
      function: `public class Example {\n    public static String exampleFunction(String name) {\n        // Example function that greets someone\n        return "Hello, " + name + "!";\n    }\n    \n    public static void main(String[] args) {\n        String result = exampleFunction("World");\n        System.out.println(result);\n    }\n}\n`,
      class: `public class ExampleClass {\n    private int value;\n    \n    public ExampleClass(int value) {\n        this.value = value;\n    }\n    \n    public int getValue() {\n        return this.value;\n    }\n    \n    public static void main(String[] args) {\n        ExampleClass obj = new ExampleClass(42);\n        System.out.println(obj.getValue());\n    }\n}\n`,
      loop: `for (int i = 0; i < 5; i++) {\n    System.out.println("Iteration " + i);\n}`,
      conditional: `int x = 10;\nif (x > 5) {\n    System.out.println("x is greater than 5");\n} else {\n    System.out.println("x is not greater than 5");\n}`,
      array: `int[] myArray = {1, 2, 3, 4, 5};\nfor (int item : myArray) {\n    System.out.println(item);\n}\n`,
    },
  }

  return templates[lang.toLowerCase()]?.[type] || templates.python[type] || templates.python.basic
}

// Helper function to generate explanation
function generateExplanation(lang: string, type: string, originalPrompt: string): string {
  const explanations: Record<string, Record<string, string>> = {
    python: {
      basic: `# This is a basic ${lang} code snippet. It demonstrates a simple print statement.`,
      function: `# This ${lang} code defines a function that takes a name parameter and returns a greeting.\n# Functions in ${lang} are defined using 'def' and can include docstrings for documentation.`,
      class: `# This ${lang} code defines a class with an initializer and a method.\n# Classes in ${lang} use 'class' keyword and 'self' parameter for instance methods.`,
      loop: `# This is a for loop in ${lang} that iterates over a range of numbers.\n# ${lang} uses 'for' with 'in' to iterate over sequences.`,
      conditional: `# This demonstrates conditional logic in ${lang} using if-else statements.\n# ${lang} uses indentation to define code blocks.`,
      array: `# This shows how to work with lists (arrays) in ${lang}.\n# Lists are mutable sequences that can contain mixed types.`,
    },
    javascript: {
      basic: `# This is a basic ${lang} code snippet using console.log for output.`,
      function: `# This ${lang} code defines a function using modern arrow function syntax.\n# Functions can use template literals (\`\`) for string interpolation.`,
      class: `# This ${lang} code uses ES6 class syntax with constructor and methods.\n# Classes provide a cleaner way to create objects and inheritance.`,
      loop: `# This is a for loop in ${lang} using let for block-scoped variables.\n# Template literals allow embedding expressions in strings.`,
      conditional: `# This demonstrates conditional logic in ${lang} using if-else statements.\n# ${lang} uses curly braces {} to define code blocks.`,
      array: `# This shows array methods in ${lang}, specifically forEach for iteration.\n# Arrays can contain mixed types and have many built-in methods.`,
    },
    java: {
      basic: `# This is a basic ${lang} program with a main method.\n# ${lang} requires a class with a main method as the entry point.`,
      function: `# This ${lang} code defines a static method within a class.\n# Static methods can be called without creating an instance of the class.`,
      class: `# This ${lang} code defines a class with private fields and public methods.\n# ${lang} uses access modifiers (public, private) to control visibility.`,
      loop: `# This is an enhanced for loop in ${lang} for iterating over arrays.\n# ${lang} provides different loop types for various scenarios.`,
      conditional: `# This demonstrates conditional logic in ${lang} using if-else.\n# ${lang} uses curly braces {} and requires explicit type declarations.`,
      array: `# This shows array declaration and iteration in ${lang}.\n# Arrays have fixed size and contain elements of the same type.`,
    },
  }

  return explanations[lang.toLowerCase()]?.[type] || `# Generated ${lang} code for: ${originalPrompt}`
}
