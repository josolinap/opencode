# Neo-Clone Enhanced TUI v3.0 (Python Edition) 🚀

A modern, self-hosted AI assistant with an **Enhanced Textual TUI interface**, inspired by Opencode. Built with Python and designed to be completely free and locally runnable.

## ✨ Phase 4 New Features (Opencode Integration)

### 🧩 **Spec-Kit Integration**

- **5 New Skills**: Constitution, specification, planning, task breakdown, and implementation
- **Spec-Driven Development**: Create detailed project specifications and implementation plans
- **Automatic Command Recognition**: `/constitution`, `/specify`, `/plan`, `/tasks`, `/implement`
- **Project Planning**: Generate comprehensive development roadmaps and task breakdowns

### 🤖 **Advanced Model Discovery & Integration**

- **10 AI Providers**: Ollama, HuggingFace, Replicate, Together.ai, OpenAI, Anthropic, Google, DeepSeek, Grok, Cohere
- **36+ Free Models**: Automatically discovered and validated from across the internet
- **Seamless Integration**: Models automatically added to opencode.json configuration
- **Provider Agnostic**: Works with any supported AI provider without code changes

### 🏥 **Model Health Monitoring**

- **Periodic Health Checks**: Automatic monitoring of model availability and performance
- **Automatic Failover**: Unhealthy models are automatically avoided
- **Performance Tracking**: Response times and success rates monitored continuously
- **Health Reports**: Detailed status reports for all integrated models

### 📊 **Model Analytics & Optimization**

- **Usage Analytics**: Track which models perform best for different tasks
- **Automatic Optimization**: AI learns and optimizes model selection based on historical performance
- **Task Pattern Recognition**: Different models automatically selected for different types of tasks
- **Performance Insights**: Detailed analytics on model usage patterns and success rates

## ✨ Phase 3 New Features

### 🎨 **Enhanced User Interface**

- **Dark/Light Theme Toggle** - Beautiful themes for day and night
- **Message Search** - Search through your entire conversation history
- **Enhanced Status Bar** - Real-time information display
- **Keyboard Shortcuts** - Ctrl+T (theme), Ctrl+F (search), Ctrl+P (presets)

### 💾 **Persistent Memory System**

- **Conversation History** - All interactions saved automatically
- **User Preferences** - Theme, settings, and custom commands
- **Export/Import** - Save and share conversation history
- **Usage Analytics** - Track your interaction patterns

### 🧠 **Intelligent LLM Presets**

- **10 Specialized Presets** - Creative, technical, analytical, and more
- **Auto-Selection** - AI automatically chooses the best preset
- **Custom Presets** - Create your own parameter combinations
- **Usage Statistics** - See which presets you use most

### 🛠️ **Expanded Skill Library**

- **8 Total Skills** - Including MiniMax Agent and 3 new powerful capabilities
- **file_manager** - Read, analyze, and manage files and directories
- **web_search** - Search the web, fact-check, and find information
- **planning** - Create project plans, roadmaps, and step-by-step guides
- **Enhanced Analysis** - Better understanding of your requests

### 🧩 **Plugin System**

- **Hot-swappable Modules** - Load/unload plugins without restart
- **Custom Extensions** - Build your own capabilities
- **Plugin Templates** - Easy starting point for development
- **Safe Execution** - Isolated plugin environments

### 📊 **Advanced Analytics**

- **Usage Statistics** - See your assistant usage patterns
- **Performance Metrics** - Response times and success rates
- **Skill Analytics** - Most used capabilities
- **Session Tracking** - Detailed interaction logs

### 🧠 **MiniMax Agent Integration**

- **Dynamic Reasoning Layer** - AI-powered intent analysis and skill generation
- **Smart Intent Classification** - Understand complex user requests with confidence scoring
- **On-Demand Skill Creation** - Generate custom skills based on your requirements
- **Reasoning Transparency** - Detailed trace of decision-making process
- **Seamless Integration** - Works with Neo-Clone's brain and skill systems

## 🚀 Core Features

- 🖥️ **Beautiful Enhanced TUI** - Rich, interactive terminal interface with themes
- 🧠 **Modular Brain Engine** - Intelligent intent parsing and skill routing
- 🔧 **Dynamic Skills** - Plugin-based skill system with 7 built-in capabilities
- 💬 **Chat Interface** - Natural conversation with persistent history
- 🎨 **Theme System** - Dark and light themes with instant switching
- 🔍 **Message Search** - Find any conversation from your history
- 🏗️ **Provider Agnostic** - Works with Ollama, Hugging Face, and other providers
- 💻 **Cross-Platform** - Runs on Windows, macOS, and Linux
- 🚀 **CPU-Optimized** - No GPU required, lightweight runtime

## Quick Start

### Prerequisites

- Python 3.8+
- Optional: Ollama for local LLM support

### Installation

```bash
git clone <repository>
cd neo-clone
pip install -r requirements.txt
```

### Running the Application

**Enhanced TUI Mode (Recommended - Default):**

```bash
python main.py --enhanced
# or simply:
python main.py
```

**Classic TUI Mode:**

```bash
python main.py --tui
```

**CLI Mode (Enhanced):**

```bash
python main.py --cli
```

**With Theme Selection:**

```bash
python main.py --enhanced --theme dark
```

**Configuration Options:**

```bash
python main.py --config config.json --theme light --debug
```

### 🤖 Opencode Framework Integration

Neo-Clone TUI is now fully compatible with the Opencode framework! This allows you to use Neo-Clone's enhanced features while taking advantage of Opencode's model selection and management system.

#### Features

- **Seamless Model Switching**: Use Opencode's `/model` commands and TUI dialog
- **Dynamic Model Selection**: Automatically uses Opencode's selected model
- **Drop-in Compatibility**: Copy files directly into your Opencode project
- **Preserved Functionality**: All Phase 3 features remain intact
- **MiniMax Agent**: Enhanced reasoning capabilities work with any model

#### Quick Integration

1. **Copy Opencode-Compatible Files**:

   ```bash
   # Copy the Opencode-compatible modules
   cp config_opencode.py /path/to/opencode/
   cp llm_client_opencode.py /path/to/opencode/
   cp brain_opencode.py /path/to/opencode/
   cp enhanced_tui_opencode.py /path/to/opencode/
   cp -r skills/ /path/to/opencode/
   ```

2. **Configure Opencode Model**:

   ```bash
   # Set your preferred model in Opencode
   opencode config set model "openai/gpt-3.5-turbo"
   # or for local models
   opencode config set model "ollama/llama2"
   ```

3. **Import Integration** (in your Opencode files):
   ```python
   # Replace original imports with Opencode-compatible versions
   from config_opencode import Config, load_config
   from brain_opencode import OpencodeBrain
   from llm_client_opencode import LLMClient
   from enhanced_tui_opencode import NeoCloneApp
   ```

#### Model Selection Commands

Once integrated, you can switch models using:

- **Command Line**: `/model openai/gpt-4`
- **TUI Dialog**: Press `Ctrl+O` to open model selection
- **Code**: Use `brain.switch_model("anthropic/claude-3-sonnet")`

#### Testing the Integration

```bash
# Run the integration demo
python demo_opencode_integration.py

# Run integration tests
python test_opencode_integration_simple.py
```

#### Configuration Precedence

The system uses this priority order:

1. **Opencode Selection**: Current model from `opencode.json`
2. **Local Config**: Traditional Neo-Clone configuration
3. **Environment**: `NEO_*` environment variables
4. **Defaults**: Built-in default values

For complete integration details, see [`OPENCODE_INTEGRATION_CHANGELOG.md`](OPENCODE_INTEGRATION_CHANGELOG.md).

## Usage

### Enhanced TUI Commands

Once in the Enhanced TUI, you can use these commands:

| Command            | Description                 | Example                    |
| ------------------ | --------------------------- | -------------------------- |
| `/help`            | Show enhanced help message  | `/help`                    |
| `/skills`          | List all 7 available skills | `/skills`                  |
| `/config`          | Show current configuration  | `/config`                  |
| `/preset [name]`   | Set LLM preset mode         | `/preset creative_writing` |
| `/theme`           | Toggle dark/light theme     | `/theme`                   |
| `/search [query]`  | Search message history      | `/search python`           |
| `/stats`           | Show usage statistics       | `/stats`                   |
| `/plugins`         | Manage loaded plugins       | `/plugins`                 |
| `/memory`          | Show memory system info     | `/memory`                  |
| `/export [format]` | Export conversation history | `/export json`             |
| `/backup`          | Create data backup          | `/backup`                  |
| `/clear`           | Clear chat history          | `/clear`                   |
| `/quit` or `/exit` | Exit the application        | `/quit`                    |

### Keyboard Shortcuts (Enhanced TUI)

| Shortcut        | Action                    |
| --------------- | ------------------------- |
| `Ctrl+T`        | Toggle theme (Dark/Light) |
| `Ctrl+F`        | Focus search input        |
| `Ctrl+P`        | Show LLM presets          |
| `Ctrl+S`        | Show usage statistics     |
| `Ctrl+L`        | Clear chat history        |
| `Ctrl+C` or `Q` | Quit application          |

### CLI Enhanced Commands

The CLI mode also supports enhanced commands:

| Command    | Description                    |
| ---------- | ------------------------------ |
| `skills`   | List all available skills      |
| `memory`   | Show memory system information |
| `stats`    | Display usage statistics       |
| `presets`  | List available LLM presets     |
| `plugins`  | Show loaded plugins            |
| `help`     | Show help information          |
| `enhanced` | Launch Enhanced TUI            |
| `tui`      | Launch Classic TUI             |

### Available Skills (Phase 4 Enhanced)

The assistant now includes 12 built-in skills:

#### Original Skills

1. **code_generation** 💻 - Generates/explains Python ML code snippets
2. **text_analysis** 📝 - Performs sentiment analysis and text moderation
3. **data_inspector** 📊 - Analyzes CSV/JSON data and provides summaries
4. **ml_training** 🤖 - Provides ML model training guidance and recommendations

#### New Phase 3 Skills

5. **file_manager** 📁 - Read files, analyze content, manage directories
   - Examples: "read /path/to/file.py", "show info about document.txt"
6. **web_search** 🔍 - Search the web, fact-check, and find information
   - Examples: "search for Python tutorials", "find latest AI news"

#### MiniMax Agent Integration

7. **minimax_agent** 🧠 - Dynamic reasoning, intent analysis, and skill generation
   - **Intent Analysis**: Understand complex requests with confidence scoring
   - **Dynamic Skill Generation**: Create custom skills on-demand
   - **Reasoning Traces**: Transparent decision-making process

#### Spec-Kit Skills (Phase 4)

8. **constitution** 📋 - Create project constitutions and foundational documents
   - Examples: "Create a constitution for my web application project"
9. **specification** 📝 - Generate detailed technical specifications
   - Examples: "Specify the requirements for a user authentication system"
10. **planning** 🗓️ - Develop comprehensive implementation plans
    - Examples: "Plan the development of an e-commerce platform"
11. **task_breakdown** 📊 - Break down complex projects into manageable tasks
    - Examples: "Break down the implementation of a machine learning pipeline"
12. **implementation** ⚙️ - Generate executable implementation strategies
    - Examples: "Implement the user registration workflow"

### MiniMax Agent Usage

The MiniMax Agent provides three main modes of operation:

#### 1. Intent Analysis Mode

Analyzes user input to understand intent and suggest appropriate actions:

```
"I need to create a Python script to process CSV files and generate charts"
→ Intent: code_generation + data_analysis
→ Suggested Skills: code_generation, data_inspector
→ Confidence: 0.85
```

#### 2. Dynamic Skill Generation Mode

Creates custom skills based on your requirements:

```
Generate a skill called "csv_processor" that:
- Processes CSV files
- Provides statistical summaries
- Exports results to JSON

→ Creates: skills/generated_csv_processor.py
→ Ready to use: /csv_processor with file_path parameter
```

#### 3. Reasoning Mode

Provides detailed reasoning and recommendations for complex queries:

```
"What's the best approach for building a data pipeline?"
→ Detailed reasoning about pipeline design
→ Best practices and considerations
→ Implementation recommendations
```

#### MiniMax Agent Examples

**Intent Analysis:**

```
User: "I need to build a web scraper for e-commerce data"
MiniMax Response:
- Primary Intent: web_operations (confidence: 0.92)
- Detected Technologies: web, scraping
- Suggested Skills: web_search, text_analysis
- Complexity Score: 0.7
```

**Skill Generation:**

```
Request: Create a skill for analyzing log files
Result:
- Generated: skills/generated_log_analyzer.py
- Parameters: file_path, log_format, analysis_type
- Lines of Code: 45
- Ready for immediate use!
```

**Reasoning with Traces:**

```
Query: "Optimize my machine learning workflow"
Reasoning Steps:
1. [0.001s] Intent Analysis: Analyzed query → skill_creation (confidence: 0.88)
2. [0.002s] Context Analysis: Analyzed 3 context items, found 2 relevant
3. [0.003s] Skill Generation: Generated skill 'ml_optimizer' with 3 parameters
```

### Usage Examples

#### Basic Conversation

```
Hello, how are you today?
What can you help me with?
Tell me a joke about programming
```

#### Skill Examples (Original)

```
Generate a scikit-learn classifier code
Analyze the sentiment: "I love this product!"
Show me a data summary of my CSV file
Train a recommendation model
```

#### New Phase 3 Skills

```
Read /path/to/main.py
Show me information about this file
search for Python tutorials
Find information about machine learning
search for latest AI developments
```

#### Spec-Kit Skills (Phase 4)

```
/constitution Create a constitution for my mobile app project
/specify Define the technical specifications for a REST API
/plan Develop an implementation plan for a data analytics dashboard
/tasks Break down the development of a user management system
/implement Create an execution strategy for deploying to production
```

#### Enhanced TUI Features

```
/preset creative_writing     # Switch to creative mode
/theme                       # Toggle dark/light theme
/search python               # Search conversation history
/stats                       # View usage statistics
/memory                      # Show memory system info
```

#### Auto-Preset Selection Examples

The assistant automatically selects the best preset based on your input:

```
Write a creative story           # → Creative Writing preset
Generate Python code            # → Code Generation preset
Analyze this data               # → Data Analysis preset
Verify this fact                # → Fact Checking preset
How do I train a model?         # → Technical preset
```

#### Plugin System Examples

```
/plugins                      # View loaded plugins
# Create custom plugin in plugins/ directory
# Hot-reload plugins without restart
```

## LLM Presets (Phase 3 Feature)

Neo-Clone v3.0 includes 10 specialized LLM presets for different use cases:

### Creative Presets

- **🎨 creative_writing** - For storytelling, brainstorming, and creative content
- **📜 poetry_mode** - Specialized for poetry, rhyming, and artistic expression

### Technical Presets

- **💻 code_generation** - Optimized for programming and code explanation
- **📈 data_analysis** - Focused on data analysis and statistical reasoning

### Analytical Presets

- **🔍 fact_checking** - Designed for fact verification and accurate information retrieval
- **🧠 analytical_reasoning** - Optimized for logical reasoning and problem-solving

### Conversational Presets

- **💬 conversational** - Natural conversation with friendly, helpful responses
- **📚 tutorial_mode** - Patient, educational responses perfect for learning

### Specialized Presets

- **🔬 research_mode** - Academic and research-focused with citations
- **⚡ quick_responses** - Fast, concise responses for quick interactions

### Auto-Selection

The AI automatically selects the most appropriate preset based on your input keywords and context.

### Manual Selection

```
/preset creative_writing    # Switch to creative mode
/preset code_generation     # Switch to programming mode
/preset fact_checking       # Switch to verification mode
```

## Memory System (Phase 3 Feature)

### Persistent Storage

- **Conversations**: All interactions saved automatically
- **User Preferences**: Theme, settings, and custom commands
- **Usage Analytics**: Statistics and interaction patterns
- **Cross-Session**: Resume conversations across restarts

### Data Location

```
data/
├── memory/
│   ├── conversations.json     # Conversation history
│   ├── preferences.json       # User settings
│   └── usage_stats.json       # Analytics data
├── logs/
│   ├── interactions.jsonl     # Detailed logs
│   ├── skills.log            # Skill execution logs
│   └── errors.log            # Error tracking
└── presets/
    ├── presets.json          # Built-in presets
    ├── custom_presets.json   # User-created presets
    └── usage_stats.json      # Preset usage analytics
```

### Export and Backup

```bash
/export json                 # Export to JSON format
/export txt                  # Export to text format
/backup                      # Create timestamped backup
```

## Plugin System (Phase 3 Feature)

### Built-in Plugin Support

Neo-Clone includes a powerful plugin system for extensibility:

```bash
/plugins                     # List loaded plugins
# Plugins are auto-discovered from plugins/ directory
# Hot-swappable - load/unload without restart
```

### Creating Custom Plugins

1. Create a file in `plugins/my_plugin.py`
2. Inherit from `BasePlugin` class
3. Implement required methods
4. Plugin auto-loads on next startup

### Plugin Template

```python
from plugin_system import BasePlugin

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "my_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "My custom plugin"

    def initialize(self, config: Dict[str, Any]) -> bool:
        # Add your initialization code here
        return True

    def shutdown(self):
        # Add your cleanup code here
        pass

    def example_method(self) -> str:
        """Example method that can be called"""
        return f"Hello from {self.name} plugin!"

# Plugin metadata
PLUGIN_METADATA = {{
    "name": "{plugin_name}",
    "version": "1.0.0",
    "description": "Example plugin for Neo-Clone",
    "author": "Your Name",
    "dependencies": []
}}

# Create plugin instance
plugin = MyPlugin()
```

## Configuration

Configuration can be set via environment variables or a JSON file:

### Environment Variables

```bash
export NEO_PROVIDER="ollama"
export NEO_MODEL="ggml-neural-chat"
export NEO_API_ENDPOINT="http://localhost:11434"
export NEO_TEMPERATURE="0.2"
```

### JSON Configuration File

Create a `config.json` file:

```json
{
  "provider": "ollama",
  "model_name": "ggml-neural-chat",
  "api_endpoint": "http://localhost:11434",
  "max_tokens": 1024,
  "temperature": 0.2
}
```

Then run:

```bash
python main.py --config config.json
```

## Architecture

The project follows a modular architecture with Phase 3 enhancements:

```
neo-clone/
├── main.py              # Entry point with enhanced mode selection
├── enhanced_tui.py      # Enhanced TUI with themes, search, Phase 3 features
├── tui.py               # Classic TUI interface (backward compatibility)
├── brain.py             # Core reasoning engine with analytics integration
├── config.py            # Configuration management
├── utils.py             # Utility functions
├── memory.py            # Persistent memory system (Phase 3)
├── logging_system.py    # Advanced logging and analytics (Phase 3)
├── llm_presets.py       # LLM parameter presets system (Phase 3)
├── plugin_system.py     # Plugin management system (Phase 3)
├── model_discovery.py   # AI model discovery and integration (Phase 4)
├── model_validator.py   # Model validation and testing (Phase 4)
├── model_integrator.py  # Model integration orchestration (Phase 4)
├── model_monitor.py     # Health monitoring system (Phase 4)
├── model_analytics.py   # Usage analytics and optimization (Phase 4)
├── skills/              # Dynamic skill discovery and execution
│   ├── __init__.py      # Skill registry and BaseSkill class
│   ├── code_generation.py
│   ├── text_analysis.py
│   ├── data_inspector.py
│   ├── ml_training.py
│   ├── file_manager.py  # New: File operations (Phase 3)
│   ├── web_search.py    # New: Web search capability (Phase 3)
│   ├── constitution.py  # New: Project constitution creation (Phase 4)
│   ├── specification.py # New: Technical specification generation (Phase 4)
│   ├── planning.py      # New: Implementation planning (Phase 4)
│   ├── task_breakdown.py # New: Task breakdown and organization (Phase 4)
│   └── implementation.py # New: Implementation strategy (Phase 4)
├── plugins/             # Plugin directory (Phase 3)
│   ├── # Add your custom plugins here
│   └── # Plugin templates
├── data/                # Persistent data storage (Phase 3)
│   ├── memory/          # Conversation history and preferences
│   ├── logs/            # Detailed interaction logs
│   └── presets/         # LLM preset configurations
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

### Core Components (Enhanced)

#### Phase 1 Original Components

- **Brain Engine** (`brain.py`): Processes messages, parses intent, routes to skills
- **TUI Interface** (`tui.py`): Classic terminal interface with chat history
- **Skill Registry** (`skills/`): Dynamic discovery and execution of capabilities
- **Configuration** (`config.py`): Provider-agnostic settings management

#### Phase 3 New Components

- **Enhanced TUI** (`enhanced_tui.py`): Modern interface with themes, search, analytics
- **Persistent Memory** (`memory.py`): Cross-session conversation history and preferences
- **Logging System** (`logging_system.py`): Detailed analytics and performance tracking
- **LLM Presets** (`llm_presets.py`): Specialized parameter configurations for different use cases
- **Plugin System** (`plugin_system.py`): Hot-swappable module system for extensibility
- **New Skills** (file_manager, web_search): Extended capability set

#### Phase 4 New Components

- **Model Discovery** (`model_discovery.py`): Automatic discovery of AI models from 10+ providers
- **Model Validation** (`model_validator.py`): Comprehensive testing and validation of discovered models
- **Model Integration** (`model_integrator.py`): Seamless integration of validated models into the system
- **Model Monitoring** (`model_monitor.py`): Continuous health monitoring and automatic failover
- **Model Analytics** (`model_analytics.py`): Usage tracking and performance optimization
- **Spec-Kit Skills** (constitution, specification, planning, task_breakdown, implementation): Project planning and specification tools

### System Integration

The enhanced architecture maintains full backward compatibility:

- **CLI Mode**: Enhanced with Phase 3 features
- **Classic TUI**: Preserved for users who prefer original interface
- **Enhanced TUI**: Full Phase 3 experience with all new features
- **Plugin System**: Optional extension without core dependencies
- **Memory System**: Transparent operation with fallbacks

## Development

### Running Tests

```bash
# Run enhanced TUI test suite
python test_tui.py

# Run interactive demo
python demo_tui.py

# Test CLI with Phase 3 features
python main.py --cli

# Run MiniMax Agent demonstration
python demo_minimax_agent.py
```

### Phase 4 Testing

```bash
# Test model discovery
python -c "from model_discovery import ModelDiscovery; d = ModelDiscovery(); models = d.scan_all_sources(); print(f'Discovered {len(models)} models')"

# Test model health monitoring
python model_monitor.py --config ../opencode.json --report

# Test model analytics
python test_analytics.py

# Test Spec-Kit skills
python -c "from skills import SkillRegistry; s = SkillRegistry(); print([skill for skill in s._skills.keys() if 'spec' in skill or 'plan' in skill or 'task' in skill or 'implement' in skill or 'constitution' in skill])"
```

### Phase 3 Testing

```bash
# Test memory system
python -c "from memory import get_memory; print(get_memory().get_statistics())"

# Test LLM presets
python -c "from llm_presets import get_preset_manager; print(get_preset_manager().list_presets())"

# Test plugin system
python -c "from plugin_system import get_plugin_manager; print(get_plugin_manager().list_all_plugins())"
```

### Adding New Skills

1. Create a new file in the `skills/` directory
2. Implement a class that inherits from `BaseSkill`
3. The skill will be automatically discovered and registered
4. Available in both Classic and Enhanced TUI modes

Example skill (Phase 3 enhanced):

```python
from skills import BaseSkill

class MyCustomSkill(BaseSkill):
    @property
    def name(self):
        return "my_custom_skill"

    @property
    def description(self):
        return "Description of what this skill does"

    @property
    def example_usage(self):
        return "How to use this skill"

    def execute(self, params):
        return {"result": "Skill output"}
```

### Using MiniMax Agent in Development

The MiniMax Agent can be used programmatically to add intelligent capabilities:

```python
from skills.minimax_agent import MiniMaxAgent

# Initialize the agent
agent = MiniMaxAgent()

# Analyze user intent
result = agent.analyze_user_input(
    "I need to create a data visualization tool",
    context=["user likes python", "works with pandas"]
)

print(f"Intent: {result['primary_intent']}")
print(f"Confidence: {result['confidence']}")
print(f"Suggested skills: {result['suggested_skills']}")

# Generate a custom skill
skill_result = agent.generate_dynamic_skill(
    skill_name="chart_generator",
    description="Generate matplotlib charts from data",
    parameters={"data": "pandas DataFrame", "chart_type": "string"}
)

# Save the generated skill
save_result = agent.save_generated_skill(skill_result['skill_code'])
print(f"Skill saved: {save_result}")
```

#### MiniMax Agent Integration Patterns

**1. Brain System Integration:**

```python
from brain import Brain
from skills import SkillRegistry
from skills.minimax_agent import MiniMaxAgent

# Add MiniMax Agent to skill registry
skills = SkillRegistry()
minimax = MiniMaxAgent()
skills.register(minimax)

# Brain will automatically use it for complex requests
brain = Brain(config, skills)
response = brain.send_message("Create a custom skill for my workflow")
```

**2. Intent Analysis Only:**

```python
# Use just the intent analysis without skill generation
result = agent.analyze_user_input("process this data file")
if result['confidence'] > 0.8:
    # High confidence - proceed with suggested skills
    suggested_skills = result['suggested_skills']
```

**3. Custom Reasoning Traces:**

```python
# Enable detailed reasoning for debugging
result = agent.analyze_user_input(
    "complex query requiring deep analysis",
    context=["additional context"]
)

trace = result['reasoning_trace']
for step in trace['steps']:
    print(f"{step['step']}: {step['details']} (confidence: {step['confidence']})")
```

### Creating Plugins (Phase 3)

1. Create a new file in the `plugins/` directory
2. Inherit from `BasePlugin` class
3. Implement required methods
4. Plugins can provide skills, commands, or custom functionality

Example plugin:

```python
from plugin_system import BasePlugin

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "my_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "My custom plugin"

    def initialize(self, config: Dict[str, Any]) -> bool:
        # Add your initialization code here
        return True

    def shutdown(self):
        # Add your cleanup code here
        pass

    def custom_functionality(self):
        return "Plugin executed!"
```

### Using Presets in Development

```python
from llm_presets import get_preset_manager

preset_manager = get_preset_manager()

# Get specific preset
creative_preset = preset_manager.get_preset("creative_writing")

# Auto-select based on input
auto_preset = preset_manager.auto_select_preset("Write a creative story")

# Create custom preset
from llm_presets import LLMParameters
custom_params = LLMParameters(temperature=0.7, max_tokens=1000)
preset_manager.create_custom_preset(
    "my_preset", "My custom preset", "creative",
    custom_params, ["writing", "creative"], ["story", "creative"]
)
```

### Memory System in Development

```python
from memory import get_memory

memory = get_memory()

# Add conversation
memory.add_conversation("user message", "assistant response")

# Search history
results = memory.search_conversations("python")

# Get statistics
stats = memory.get_statistics()

# Export conversations
memory.export_conversations("backup.json", "json")
```

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## Development Notes

### Phase 3 Testing

```bash
# Test memory system
python -c "from memory import get_memory; print(get_memory().get_statistics())"

# Test LLM presets
python -c "from llm_presets import get_preset_manager; print(get_preset_manager().list_presets())"

# Test plugin system
python -c "from plugin_system import get_plugin_manager; print(get_plugin_manager().list_all_plugins())"
```

### Adding New Skills

1. Create a new file in the `skills/` directory
2. Implement a class that inherits from `BaseSkill`
3. The skill will be automatically discovered and registered
4. Available in both Classic and Enhanced TUI modes

Example skill (Phase 3 enhanced):

```python
from skills import BaseSkill

class MyCustomSkill(BaseSkill):
    @property
    def name(self):
        return "my_custom_skill"

    @property
    def description(self):
        return "Description of what this skill does"

    @property
    def example_usage(self):
        return "How to use this skill"

    def execute(self, params):
        return {"result": "Skill output"}
```

### Using MiniMax Agent in Development

The MiniMax Agent can be used programmatically to add intelligent capabilities:

```python
from skills.minimax_agent import MiniMaxAgent

# Initialize the agent
agent = MiniMaxAgent()

# Analyze user intent
result = agent.analyze_user_input(
    "I need to create a data visualization tool",
    context=["user likes python", "works with pandas"]
)

print(f"Intent: {result['primary_intent']}")
print(f"Confidence: {result['confidence']}")
print(f"Suggested skills: {result['suggested_skills']}")

# Generate a custom skill
skill_result = agent.generate_dynamic_skill(
    skill_name="chart_generator",
    description="Generate matplotlib charts from data",
    parameters={"data": "pandas DataFrame", "chart_type": "string"}
)

# Save the generated skill
save_result = agent.save_generated_skill(skill_result['skill_code'])
print(f"Skill saved: {save_result}")
```

#### MiniMax Agent Integration Patterns

**1. Brain System Integration:**

```python
from brain import Brain
from skills import SkillRegistry
from skills.minimax_agent import MiniMaxAgent

# Add MiniMax Agent to skill registry
skills = SkillRegistry()
minimax = MiniMaxAgent()
skills.register(minimax)

# Brain will automatically use it for complex requests
brain = Brain(config, skills)
response = brain.send_message("Create a custom skill for my workflow")
```

**2. Intent Analysis Only:**

```python
# Use just the intent analysis without skill generation
result = agent.analyze_user_input("process this data file")
if result['confidence'] > 0.8:
    # High confidence - proceed with suggested skills
    suggested_skills = result['suggested_skills']
```

**3. Custom Reasoning Traces:**

```python
# Enable detailed reasoning for debugging
result = agent.analyze_user_input(
    "complex query requiring deep analysis",
    context=["additional context"]
)

trace = result['reasoning_trace']
for step in trace['steps']:
    print(f"{step['step']}: {step['details']} (confidence: {step['confidence']})")
```

### Creating Plugins (Phase 3)

1. Create a new file in the `plugins/` directory
2. Inherit from `BasePlugin` class
3. Implement required methods
4. Plugins can provide skills, commands, or custom functionality

Example plugin:

```python
from plugin_system import BasePlugin

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "my_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "My custom plugin"

    def initialize(self, config: Dict[str, Any]) -> bool:
        # Add your initialization code here
        return True

    def shutdown(self):
        # Add your cleanup code here
        pass

    def custom_functionality(self):
        return "Plugin executed!"
```

### Using Presets in Development

```python
from llm_presets import get_preset_manager

preset_manager = get_preset_manager()

# Get specific preset
creative_preset = preset_manager.get_preset("creative_writing")

# Auto-select based on input
auto_preset = preset_manager.auto_select_preset("Write a creative story")

# Create custom preset
from llm_presets import LLMParameters
custom_params = LLMParameters(temperature=0.7, max_tokens=1000)
preset_manager.create_custom_preset(
    "my_preset", "My custom preset", "creative",
    custom_params, ["writing", "creative"], ["story", "creative"]
)
```

### Memory System in Development

```python
from memory import get_memory

memory = get_memory()

# Add conversation
memory.add_conversation("user message", "assistant response")

# Search history
results = memory.search_conversations("python")

# Get statistics
stats = memory.get_statistics()

# Export conversations
memory.export_conversations("backup.json", "json")
```

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.
