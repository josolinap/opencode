import z from "zod"

const testSchema = z.object({
  name: z.string(),
})

console.log("Zod test in opencode:", testSchema)
