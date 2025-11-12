## IMPORTANT

- Try to keep things in one function unless composable or reusable
- DO NOT do unnecessary destructuring of variables
- DO NOT use `else` statements unless necessary
- DO NOT use `try`/`catch` if it can be avoided
- AVOID `try`/`catch` where possible
- AVOID `else` statements
- AVOID using `any` type
- AVOID `let` statements
- PREFER single word variable names where possible
- Use as many bun apis as possible like Bun.file()

## Neo-Clone Integration

opencode now includes seamless integration with the Neo-Clone AI assistant system. Neo-Clone capabilities are automatically available through the general agent - no manual agent selection required.

### What Neo-Clone Provides

Neo-Clone is a Python-based AI assistant with specialized capabilities:

- **Code Generation**: Generate Python code, explain algorithms, create ML models
- **Text Analysis**: Sentiment analysis, text processing, content moderation
- **Data Inspection**: Analyze CSV/JSON data, provide insights and summaries
- **ML Training**: Guidance on machine learning workflows and model training
- **File Management**: Read files, analyze content, manage directories
- **Web Search**: Search the internet, fact-check information, find resources
- **Advanced Reasoning**: Complex problem-solving with the MiniMax agent

### Seamless Usage

The general opencode agent automatically uses Neo-Clone capabilities when appropriate:

- **Code tasks**: "Generate Python code for a neural network"
- **Data analysis**: "Analyze this CSV file"
- **Text processing**: "Analyze the sentiment of this text"
- **ML/AI tasks**: "Create a classifier for..."
- **File operations**: "Read and analyze this file"
- **Research**: "Search for tutorials on..."
- **Complex reasoning**: Multi-step analytical tasks

### Configuration

Neo-Clone is configured as a default tool available to all agents. The general agent (`.opencode/agent/general.md`) includes instructions to automatically use Neo-Clone for appropriate tasks. A dedicated neo-clone agent is also available at `.opencode/agent/neo-clone.md` for specialized usage.

## Debugging

- To test opencode in the `packages/opencode` directory you can run `bun dev`
