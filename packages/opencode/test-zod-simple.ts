import z from "zod"

console.log("Zod imported successfully!")
console.log("z.string:", typeof z.string)
console.log("z.object:", typeof z.object)

const testSchema = z.object({
  name: z.string(),
})

console.log("Test schema created:", testSchema ? "SUCCESS" : "FAILED")
