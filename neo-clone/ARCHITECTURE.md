ARCHITECTURE - Neo-Clone (Python TUI)

Data Flow (high-level)
- User input -> main.py (TUI/CLI) -> Brain.send_message()
- Brain maintains ConversationHistory, decides intent
- If skill intent: SkillRegistry executes the selected skill
- Otherwise Brain forwards conversation to LLM via LLMClient
- Response returned to TUI/CLI and displayed

Core Components
- main.py: entry point, TUI/CLI orchestration
- config.py: pydantic-based configuration loader
- brain.py: conversation/context management and LLM client
- skills/: modular skill implementations and registry
- utils.py: logging, helpers

Extensibility
- Add skills by creating a new .py under skills/ that defines a BaseSkill subclass.
- Swap LLM provider by changing provider and api_endpoint in config or environment.

Notes
- The project intentionally keeps LLM calls and heavy deps optional so tools like `python -m py_compile` work in environments without textual/torch installed.
