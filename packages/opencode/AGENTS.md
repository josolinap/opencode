# opencode agent guidelines

## Neo-Clone Integration

Neo-Clone is seamlessly integrated into opencode as a default capability available to all agents.

### Seamless Integration

Neo-Clone capabilities are automatically available through the general agent without requiring manual agent selection. The system automatically routes appropriate tasks to Neo-Clone's specialized skills.

### Available Skills

Neo-Clone provides 7 built-in skills that are automatically triggered based on task type:

1. **Code Generation** 💻 - Generates/explains Python ML code snippets
2. **Text Analysis** 📝 - Performs sentiment analysis and text moderation
3. **Data Inspector** 📊 - Analyzes CSV/JSON data and provides summaries
4. **ML Training** 🤖 - Provides ML model training guidance and recommendations
5. **File Manager** 📁 - Read files, analyze content, manage directories
6. **Web Search** 🔍 - Search the web, fact-check, and find information
7. **MiniMax Agent** 🧠 - Dynamic reasoning, intent analysis, and skill generation

### Automatic Usage

The general agent automatically uses Neo-Clone for:

- Code generation and explanation tasks
- Data analysis and visualization
- Text processing and sentiment analysis
- Machine learning guidance
- File operations and content analysis
- Web research and fact-checking
- Complex reasoning and problem-solving

### Dedicated Agent

A dedicated `neo-clone` agent is also available at `.opencode/agent/neo-clone.md` for specialized Neo-Clone usage when needed.

### Skill Routing (Phase 3)

Prompts are automatically routed to the most appropriate Neo-Clone skill using a priority-based registry system. The registry defines skills with descriptions, keywords, and priorities for deterministic matching. Includes override support for testing/debugging and comprehensive edge case handling.

#### How It Works

- **Keyword Matching**: Prompts are scanned for skill-specific keywords (single words or phrases)
- **Priority Ordering**: Skills are checked in priority order (highest first) for deterministic routing
- **Phrase Handling**: Multi-word keywords require all words to be present (e.g., "read file" matches "read this file")
- **Fallback**: Unmatched prompts default to `web_search` for general questions

#### Examples

- "Generate Python code for a neural network" → `code_generation`
- "Analyze the sentiment of this review" → `text_analysis`
- "Train a model using this dataset" → `ml_training` (prioritized over `data_inspector`)
- "Plan a multi-step workflow" → `minimax_agent`
- "Read this file and summarize" → `file_manager`
- "What is the weather?" → `web_search` (fallback)

#### Maintenance Guide

- **Adding Skills**: Edit `SKILL_REGISTRY` in `src/agent/skill-registry.ts` with name, description, keywords, and priority
- **Adjusting Priorities**: Higher numbers = higher priority; reorder if conflicts arise
- **Keyword Tuning**: Use specific terms to avoid false positives; test with `bun test test/skill-routing.test.ts`
- **Override for Testing**: Use `routePromptToSkill(prompt, "desired_skill")` in code for manual routing

- **Registry Location**: `src/agent/skill-registry.ts`
- **Routing Logic**: `src/agent/skill-router.ts` uses the registry for keyword-based matching
- **Override**: Optional `overrideSkill` parameter for forced routing; or set `OPENCODE_FORCE_SKILL` env var
- **Fallback**: Generic prompts default to `web_search`
- **Safety**: Handles empty/null prompts, multiple cues (highest priority wins)

### Tool Parameters

- `message`: The query or message to send to Neo-Clone
- `mode`: "cli" (default) for interactive mode, "direct" for direct brain integration
- `timeout`: Timeout in milliseconds (default: 5 minutes)

## Build/Test Commands

- **Install**: `bun install`
- **Run**: `bun run index.ts`
- **Typecheck**: `bun run typecheck` (npm run typecheck)
- **Test**: `bun test` (runs all tests)
- **Single test**: `bun test test/tool/tool.test.ts` (specific test file)

## Code Style

- **Runtime**: Bun with TypeScript ESM modules
- **Imports**: Use relative imports for local modules, named imports preferred
- **Types**: Zod schemas for validation, TypeScript interfaces for structure
- **Naming**: camelCase for variables/functions, PascalCase for classes/namespaces
- **Error handling**: Use Result patterns, avoid throwing exceptions in tools
- **File structure**: Namespace-based organization (e.g., `Tool.define()`, `Session.create()`)

## Architecture

- **Tools**: Implement `Tool.Info` interface with `execute()` method
- **Context**: Pass `sessionID` in tool context, use `App.provide()` for DI
- **Validation**: All inputs validated with Zod schemas
- - **Logging**: Use `Log.create({ service: "name" })` pattern
- - **Storage**: Use `Storage` namespace for persistence
- - **API Client**: Go TUI communicates with TypeScript server via stainless SDK. When adding/modifying server endpoints in `packages/opencode/src/server/server.ts`, ask the user to generate a new client SDK to proceed with client-side changes.

* **_ Note: The following is a test note; the rest of the file would be extended accordingly._**
