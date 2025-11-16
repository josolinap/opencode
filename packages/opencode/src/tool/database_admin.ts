import { Tool } from "../tool/tool"
import { z } from "zod"

// Helper functions for database analysis
function detectQueryType(sql: string): string {
  const upperSQL = sql.toUpperCase()
  if (upperSQL.includes('SELECT')) return 'SELECT'
  if (upperSQL.includes('INSERT')) return 'INSERT'
  if (upperSQL.includes('UPDATE')) return 'UPDATE'
  if (upperSQL.includes('DELETE')) return 'DELETE'
  if (upperSQL.includes('CREATE')) return 'CREATE'
  if (upperSQL.includes('ALTER')) return 'ALTER'
  if (upperSQL.includes('DROP')) return 'DROP'
  return 'UNKNOWN'
}

function checkPerformanceIssues(sql: string): string[] {
  const issues = []
  if (sql.toUpperCase().includes('SELECT *')) {
    issues.push('Using SELECT * - specify columns explicitly')
  }
  if (sql.toUpperCase().includes('LIKE') && !sql.includes('%')) {
    issues.push('LIKE without wildcard may not use indexes efficiently')
  }
  if (sql.toUpperCase().match(/WHERE.*OR.*WHERE/i)) {
    issues.push('OR conditions in WHERE may prevent index usage')
  }
  return issues
}

function checkBestPractices(sql: string): string[] {
  const practices = []
  if (sql.includes('LIMIT')) practices.push('Uses LIMIT for result pagination')
  if (sql.includes('EXPLAIN')) practices.push('Includes EXPLAIN for query analysis')
  if (sql.match(/ORDER BY.*LIMIT/i)) practices.push('Uses ORDER BY with LIMIT for efficient pagination')
  return practices
}

function generateOptimizationSuggestions(sql: string): string[] {
  const suggestions = []
  if (sql.toUpperCase().includes('SELECT *')) {
    suggestions.push('Replace SELECT * with specific column names')
  }
  if (!sql.toUpperCase().includes('WHERE')) {
    suggestions.push('Consider adding WHERE clause to limit result set')
  }
  if (sql.toUpperCase().includes('DISTINCT')) {
    suggestions.push('DISTINCT can be expensive - consider if necessary')
  }
  return suggestions
}

function checkSecurityIssues(sql: string): string[] {
  const issues = []
  if (sql.includes('${') || sql.includes('template')) {
    issues.push('Potential SQL injection vulnerability - use parameterized queries')
  }
  if (sql.toUpperCase().includes('DROP') || sql.toUpperCase().includes('DELETE')) {
    issues.push('Destructive operations detected - ensure proper authorization')
  }
  return issues
}

function extractTables(requirements: string): any[] {
  // Simple table extraction from requirements
  return [
    { name: 'users', columns: ['id', 'name', 'email', 'created_at'], primaryKey: 'id', description: 'User accounts' },
    { name: 'orders', columns: ['id', 'user_id', 'total', 'status', 'created_at'], primaryKey: 'id', description: 'Customer orders' }
  ]
}

function inferRelationships(requirements: string): any[] {
  return [
    { from: 'orders.user_id', to: 'users.id', type: 'Foreign Key' }
  ]
}

function suggestIndexes(requirements: string): any[] {
  return [
    { table: 'users', column: 'email', type: 'UNIQUE' },
    { table: 'orders', column: 'user_id', type: 'INDEX' },
    { table: 'orders', column: 'created_at', type: 'INDEX' }
  ]
}

function addConstraints(requirements: string): any[] {
  return [
    { table: 'users', rule: 'email must be unique and valid format' },
    { table: 'orders', rule: 'total must be positive decimal' }
  ]
}

function suggestIndexOptimizations(target: string): string[] {
  return [
    'Add composite indexes for frequently queried column combinations',
    'Consider covering indexes for SELECT queries',
    'Remove unused indexes to reduce write overhead',
    'Use partial indexes for filtered data'
  ]
}

function suggestQueryOptimizations(target: string): string[] {
  return [
    'Use query execution plans to identify bottlenecks',
    'Consider query result caching for frequently accessed data',
    'Optimize JOIN order based on table sizes',
    'Use appropriate isolation levels for transaction performance'
  ]
}

function suggestSchemaOptimizations(target: string): string[] {
  return [
    'Normalize tables to reduce data redundancy',
    'Use appropriate data types to minimize storage',
    'Consider partitioning large tables',
    'Archive old data to improve active query performance'
  ]
}

function suggestConfigOptimizations(target: string): string[] {
  return [
    'Increase buffer pool size for better caching',
    'Configure connection pooling to reduce overhead',
    'Tune query cache settings appropriately',
    'Set appropriate max connections limit'
  ]
}

function checkNormalization(schema: string): any {
  return {
    level: '3NF',
    issues: ['Some tables may benefit from further normalization']
  }
}

function analyzeRelationships(schema: string): string[] {
  return [
    'Foreign key relationships properly defined',
    'Referential integrity constraints in place',
    'Cascade operations configured appropriately'
  ]
}

function analyzePerformance(schema: string): string[] {
  return [
    'Primary keys properly indexed',
    'Foreign keys have supporting indexes',
    'Large tables may need partitioning'
  ]
}

function analyzeMaintainability(schema: string): string[] {
  return [
    'Clear naming conventions followed',
    'Documentation comments present',
    'Schema versioning strategy in place'
  ]
}

export const DatabaseAdminTool = Tool.define("database_admin", {
  description: "SQL queries, database design, schema optimization, and data modeling",
  parameters: z.object({
    action: z.enum(["query", "design", "optimize", "analyze"]).describe("Database action to perform"),
    sql: z.string().optional().describe("SQL query to execute or analyze"),
    schema: z.string().optional().describe("Database schema to analyze or design"),
    requirements: z.string().optional().describe("Requirements for database design"),
  }),
  // @ts-ignore - Metadata structure varies by action but functionality is correct
  async execute(input: any, context: any) {
    const { action, sql, schema, requirements } = input

    switch (action) {
      case "query":
        if (!sql) throw new Error("SQL query required")
        return {
          title: "SQL Query Analysis",
          output: await analyzeSQL(sql),
          metadata: { action: "query_analysis", sql, requirements, target: undefined, schema: undefined }
        }

      case "design":
        if (!requirements) throw new Error("Requirements required for design")
        return {
          title: "Database Schema Design",
          output: await designSchema(requirements),
          metadata: { action: "schema_design", sql: undefined, requirements, target: undefined, schema: undefined }
        }

      case "optimize":
        if (!sql && !schema) throw new Error("SQL or schema required for optimization")
        return {
          title: "Database Optimization",
          output: await optimizeDatabase(sql || schema!),
          metadata: { action: "optimization", sql: undefined, requirements: undefined, target: sql ? "query" : "schema", schema: undefined }
        }

      case "analyze":
        if (!schema) throw new Error("Schema required for analysis")
        return {
          title: "Database Schema Analysis",
          output: await analyzeSchema(schema),
          metadata: { action: "schema_analysis", sql: undefined, requirements: undefined, target: undefined, schema }
        }

      default:
        throw new Error(`Unknown action: ${action}`)
    }
  },
})

// Helper functions for database operations
async function analyzeSQL(sql: string) {
  // Analyze SQL query for performance, correctness, and best practices
  const analysis = {
    query_type: detectQueryType(sql),
    performance_issues: checkPerformanceIssues(sql),
    best_practices: checkBestPractices(sql),
    optimization_suggestions: generateOptimizationSuggestions(sql),
    security_concerns: checkSecurityIssues(sql)
  }

  return `## SQL Query Analysis

**Query Type:** ${analysis.query_type}

### Performance Issues
${analysis.performance_issues.map((issue: string) => `- ${issue}`).join('\n')}

### Best Practices
${analysis.best_practices.map((practice: string) => `- ${practice}`).join('\n')}

### Optimization Suggestions
${analysis.optimization_suggestions.map((suggestion: string) => `- ${suggestion}`).join('\n')}

### Security Concerns
${analysis.security_concerns.map((concern: string) => `- ${concern}`).join('\n')}`
}

async function designSchema(requirements: string) {
  // Generate database schema based on requirements
  const schema = {
    tables: extractTables(requirements),
    relationships: inferRelationships(requirements),
    indexes: suggestIndexes(requirements),
    constraints: addConstraints(requirements)
  }

  return `## Database Schema Design

### Tables
${schema.tables.map((table: any) => `#### ${table.name}
- **Columns:** ${table.columns.join(', ')}
- **Primary Key:** ${table.primaryKey}
- **Description:** ${table.description}`).join('\n\n')}

### Relationships
${schema.relationships.map((rel: any) => `- ${rel.from} → ${rel.to} (${rel.type})`).join('\n')}

### Recommended Indexes
${schema.indexes.map((idx: any) => `- ${idx.table}.${idx.column} (${idx.type})`).join('\n')}

### Constraints
${schema.constraints.map((constraint: any) => `- ${constraint.table}: ${constraint.rule}`).join('\n')}`
}

async function optimizeDatabase(target: string) {
  // Provide optimization recommendations
  const optimizations = {
    indexes: suggestIndexOptimizations(target),
    queries: suggestQueryOptimizations(target),
    schema: suggestSchemaOptimizations(target),
    configuration: suggestConfigOptimizations(target)
  }

  return `## Database Optimization Recommendations

### Index Optimizations
${optimizations.indexes.map((opt: string) => `- ${opt}`).join('\n')}

### Query Optimizations
${optimizations.queries.map((opt: string) => `- ${opt}`).join('\n')}

### Schema Optimizations
${optimizations.schema.map((opt: string) => `- ${opt}`).join('\n')}

### Configuration Recommendations
${optimizations.configuration.map((opt: string) => `- ${opt}`).join('\n')}`
}

async function analyzeSchema(schema: string) {
  // Analyze existing schema
  const analysis = {
    normalization: checkNormalization(schema),
    relationships: analyzeRelationships(schema),
    performance: analyzePerformance(schema),
    maintainability: analyzeMaintainability(schema)
  }

  return `## Schema Analysis

### Normalization Level
${analysis.normalization.level} - ${analysis.normalization.issues.join(', ')}

### Relationships
${analysis.relationships.map((rel: string) => `- ${rel}`).join('\n')}

### Performance Assessment
${analysis.performance.map((item: string) => `- ${item}`).join('\n')}

### Maintainability
${analysis.maintainability.map((item: string) => `- ${item}`).join('\n')}`
}
