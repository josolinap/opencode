import z from "zod"

console.log("Standalone Zod test successful!")
console.log("z.object available:", typeof z.object)
console.log("z.string available:", typeof z.string)

const testSchema = z.object({
  name: z.string(),
  age: z.number().optional(),
})

console.log("Schema created successfully!")
