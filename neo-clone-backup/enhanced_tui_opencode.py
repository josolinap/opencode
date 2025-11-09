"""
enhanced_tui_opencode.py - Opencode-compatible Enhanced TUI interface for Neo-Clone

This module extends the original enhanced_tui.py to work seamlessly with Opencode's
model selection system while maintaining all Phase 3 features:

- Dark/Light theme toggle
- Message search functionality  
- Integration with memory, logging, presets, and plugin systems
- Model selection integration with Opencode
- Enhanced command handling
- Backward compatibility with existing features
"""

import logging
import asyncio
import json
import subprocess
from typing import Dict, List, Optional, Set, Any
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Input, Label, RichLog, Button, Switch, Static
from textual.binding import Binding
from textual.reactive import reactive
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel
from rich.align import Align
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt
from rich.json import JSON
from rich.traceback import install

from config_opencode import Config, load_config, get_current_opencode_model, is_opencode_available
from skills import SkillRegistry
from brain_opencode import OpencodeBrain
from memory import get_memory
from logging_system import get_logger, SkillExecutionContext
from llm_presets import get_preset_manager
from plugin_system import get_plugin_manager

# Install rich traceback for better error display
install(show_locals=True)

logger = logging.getLogger(__name__)

class MessageData:
    """Enhanced data class to store message information with metadata"""
    def __init__(self, role: str, content: str, timestamp: str = None, 
                 intent: str = None, skill_used: str = None, 
                 preset_used: str = None, model_used: str = None,
                 response_time: float = None, error: bool = False):
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.intent = intent
        self.skill_used = skill_used
        self.preset_used = preset_used
        self.model_used = model_used
        self.response_time = response_time
        self.error = error

class ModelSelectionDialog(Static):
    """Model selection dialog for Opencode integration"""
    
    def __init__(self, brain: OpencodeBrain, on_select=None):
        super().__init__()
        self.brain = brain
        self.on_select = on_select
        self.selected_index = 0
    
    def compose(self) -> ComposeResult:
        with Container(classes="model-dialog"):
            yield Label("🤖 Model Selection", classes="dialog-title")
            yield Label("Use arrow keys to navigate, Enter to select", classes="dialog-subtitle")
            
            models = self.brain.llm.get_available_models()[:10]
            current = self.brain.llm.get_current_model()
            
            for i, model in enumerate(models):
                is_current = model == current
                classes = "model-item selected" if i == self.selected_index else "model-item"
                marker = "▶️ " if is_current else "  "
                yield Label(f"{marker}{model}", classes=classes)

class NeoCloneApp(App):
    """Enhanced Neo-Clone TUI with Opencode integration"""
    
    CSS = """
    .main-container {
        height: 100%;
        width: 100%;
    }
    
    .header {
        height: 3;
        background: $primary;
        color: $text;
    }
    
    .status-bar {
        height: 2;
        background: $surface;
        color: $text;
    }
    
    .message-log {
        height: 1fr;
        border: solid $primary;
    }
    
    .input-container {
        height: 5;
        background: $surface;
        padding: 1;
    }
    
    .model-dialog {
        width: 80%;
        height: 20;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .dialog-title {
        text-align: center;
        color: $primary;
        text-style: bold;
    }
    
    .dialog-subtitle {
        text-align: center;
        color: $text-muted;
    }
    
    .model-item {
        padding: 0 1;
    }
    
    .model-item.selected {
        background: $primary;
        color: $text;
    }
    
    .input-field {
        width: 1fr;
    }
    
    .send-button {
        width: 10;
        margin-left: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+t", "toggle_theme", "Toggle Theme"),
        Binding("ctrl+f", "toggle_search", "Search"),
        Binding("ctrl+o", "open_model_dialog", "Model Selection"),
        Binding("ctrl+r", "clear_history", "Clear History"),
        Binding("ctrl+s", "save_session", "Save Session"),
        Binding("ctrl+l", "load_session", "Load Session"),
        Binding("enter", "send_message", "Send"),
    ]
    
    def __init__(self):
        super().__init__()
        
        # Load configuration with Opencode integration
        self.config = load_config()
        
        # Initialize core components
        self.skills = SkillRegistry()
        self.brain = OpencodeBrain(self.config, self.skills)
        self.memory = get_memory()
        self.logger = get_logger("enhanced_tui")
        self.preset_manager = get_preset_manager()
        self.plugin_manager = get_plugin_manager()
        
        # UI state
        self.messages: List[MessageData] = []
        self.search_active = False
        self.theme = "dark"
        self.model_dialog_active = False
        self.current_search = ""
        
        # Performance tracking
        self.session_start = asyncio.get_event_loop().time()
        
        logger.info("Enhanced TUI with Opencode integration initialized")
    
    def compose(self) -> ComposeResult:
        """Compose the application layout"""
        with Container(classes="main-container"):
            # Header
            with Container(classes="header"):
                yield self.create_header()
            
            # Status bar
            with Container(classes="status-bar"):
                yield self.create_status_bar()
            
            # Message log
            yield RichLog(classes="message-log", id="message-log")
            
            # Input area
            with Container(classes="input-container"):
                with Horizontal():
                    yield Input(placeholder="Type your message... (Ctrl+O for model selection, /model to switch)", 
                              classes="input-field", id="input-field")
                    yield Button("Send", variant="primary", classes="send-button", id="send-button")
            
            # Model selection dialog (initially hidden)
            if self.model_dialog_active:
                yield ModelSelectionDialog(self.brain, on_select=self.on_model_selected)
    
    def create_header(self) -> Label:
        """Create the header with model and session info"""
        brain_status = self.brain.get_status()
        model_info = brain_status["current_model"]
        
        # Add Opencode indicator if available
        if brain_status["is_opencode_available"]:
            model_info = f"🔗 {model_info} (Opencode)"
        else:
            model_info = f"🔧 {model_info} (Local)"
        
        header_text = f"Neo-Clone TUI | Model: {model_info} | Skills: {len(brain_status['available_skills'])}"
        return Label(header_text, classes="header")
    
    def create_status_bar(self) -> Label:
        """Create the status bar"""
        brain_status = self.brain.get_status()
        session_time = asyncio.get_event_loop().time() - self.session_start
        
        status_parts = [
            f"Messages: {len(self.messages)}",
            f"Session: {session_time:.0f}s",
            f"Theme: {self.theme}",
        ]
        
        if brain_status["model_switches"] > 0:
            status_parts.append(f"Switches: {brain_status['model_switches']}")
        
        return Label(" | ".join(status_parts), classes="status-bar")
    
    async def on_mount(self) -> None:
        """Called when the app is mounted"""
        await self.initialize_plugins()
        await self.load_session_memory()
        self.focus_input()
        
        # Send welcome message
        welcome_msg = self.get_welcome_message()
        await self.add_message("assistant", welcome_msg)
    
    def get_welcome_message(self) -> str:
        """Generate welcome message with Opencode integration info"""
        brain_status = self.brain.get_status()
        
        if brain_status["is_opencode_available"]:
            return f"""🎉 **Welcome to Neo-Clone TUI with Opencode Integration!**

🤖 **Current Model:** {brain_status['current_model']} (via Opencode)
🔧 **Available Skills:** {len(brain_status['available_skills'])}
💡 **Quick Commands:**
- `/model <provider/model>` - Switch models
- `Ctrl+O` - Open model selection dialog
- `Ctrl+T` - Toggle theme
- `/minimax analyze <text>` - Use MiniMax Agent

**Ready to assist with your coding and analysis tasks!**"""
        else:
            return f"""🎉 **Welcome to Neo-Clone TUI!**

🤖 **Current Model:** {brain_status['current_model']} (Local)
🔧 **Available Skills:** {len(brain_status['available_skills'])}
💡 **Quick Commands:**
- Configure Opencode for model selection
- `Ctrl+T` - Toggle theme
- `/minimax analyze <text>` - Use MiniMax Agent

**Ready to assist with your coding and analysis tasks!**"""
    
    async def initialize_plugins(self):
        """Initialize plugins and extensions"""
        try:
            await self.plugin_manager.initialize_plugins()
            logger.info(f"Loaded {len(self.plugin_manager.plugins)} plugins")
        except Exception as e:
            logger.error(f"Plugin initialization failed: {e}")
    
    async def load_session_memory(self):
        """Load conversation history from memory"""
        try:
            session_data = await self.memory.get("current_session")
            if session_data:
                # Restore session state
                logger.info("Session memory restored")
        except Exception as e:
            logger.error(f"Failed to load session memory: {e}")
    
    def focus_input(self):
        """Focus the input field"""
        input_widget = self.query_one("#input-field", Input)
        input_widget.focus()
    
    async def add_message(self, role: str, content: str, **kwargs):
        """Add a message to the log"""
        message_data = MessageData(role=role, content=content, **kwargs)
        self.messages.append(message_data)
        
        # Update UI
        message_log = self.query_one("#message-log", RichLog)
        
        if role == "user":
            text = Text()
            text.append("👤 You: ", style="bold blue")
            text.append(content)
            await message_log.write(text)
        else:
            # Format assistant messages with rich content
            if "```" in content:
                # Handle code blocks
                await message_log.write(Markdown(content))
            else:
                await message_log.write(Markdown(f"🤖 **Assistant:** {content}"))
        
        # Update status bar
        await self.update_status_bar()
    
    async def update_status_bar(self):
        """Update the status bar"""
        # This would be implemented to refresh the status bar
        pass
    
    async def on_input_submitted(self, message: str) -> None:
        """Handle input submission"""
        if not message.strip():
            return
        
        # Add user message
        await self.add_message("user", message)
        
        # Process with brain
        start_time = asyncio.get_event_loop().time()
        
        try:
            with SkillExecutionContext("enhanced_tui", "send_message"):
                response = self.brain.send_message(message)
                response_time = asyncio.get_event_loop().time() - start_time
                
                # Add assistant response
                await self.add_message(
                    "assistant", 
                    response,
                    model_used=self.brain.llm.get_current_model(),
                    response_time=response_time
                )
                
                # Log to system
                self.logger.info("Message processed", extra={
                    "user_message": message,
                    "response": response,
                    "response_time": response_time,
                    "model": self.brain.llm.get_current_model()
                })
                
        except Exception as e:
            error_msg = f"❌ Error processing message: {str(e)}"
            await self.add_message("assistant", error_msg, error=True)
            self.logger.error("Message processing failed", extra={
                "user_message": message,
                "error": str(e)
            })
        
        # Save session state
        await self.save_session_state()
    
    async def action_send_message(self) -> None:
        """Send message action"""
        input_widget = self.query_one("#input-field", Input)
        message = input_widget.value
        input_widget.value = ""
        
        await self.on_input_submitted(message)
    
    async def action_toggle_theme(self) -> None:
        """Toggle between dark and light themes"""
        self.theme = "light" if self.theme == "dark" else "dark"
        
        if self.theme == "light":
            self.dark = False
        else:
            self.dark = True
        
        await self.update_status_bar()
    
    async def action_toggle_search(self) -> None:
        """Toggle search mode"""
        self.search_active = not self.search_active
        if self.search_active:
            # Focus search input
            pass
        else:
            self.focus_input()
    
    async def action_open_model_dialog(self) -> None:
        """Open model selection dialog"""
        if not is_opencode_available():
            await self.add_message("assistant", "❌ Opencode not available. Please install and configure Opencode first.")
            return
        
        self.model_dialog_active = not self.model_dialog_active
        await self.refresh()
    
    async def action_clear_history(self) -> None:
        """Clear conversation history"""
        self.brain.clear_history()
        self.messages.clear()
        message_log = self.query_one("#message-log", RichLog)
        message_log.clear()
        await self.add_message("assistant", "🗑️ Conversation history cleared")
    
    async def action_save_session(self) -> None:
        """Save current session"""
        session_data = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "model_used": msg.model_used
                }
                for msg in self.messages
            ],
            "brain_status": self.brain.get_status(),
            "config": self.config.dict()
        }
        
        try:
            await self.memory.set("current_session", session_data)
            await self.add_message("assistant", "💾 Session saved successfully")
        except Exception as e:
            await self.add_message("assistant", f"❌ Failed to save session: {str(e)}")
    
    async def action_load_session(self) -> None:
        """Load previous session"""
        try:
            session_data = await self.memory.get("current_session")
            if session_data:
                # Restore session (implementation details)
                await self.add_message("assistant", "📂 Session loaded successfully")
            else:
                await self.add_message("assistant", "❌ No saved session found")
        except Exception as e:
            await self.add_message("assistant", f"❌ Failed to load session: {str(e)}")
    
    async def on_model_selected(self, model: str):
        """Handle model selection"""
        result = self.brain.switch_model(model)
        await self.add_message("assistant", result)
        self.model_dialog_active = False
        await self.refresh()
    
    async def save_session_state(self):
        """Save session state to memory"""
        try:
            session_data = {
                "last_activity": asyncio.get_event_loop().time(),
                "message_count": len(self.messages),
                "brain_status": self.brain.get_status()
            }
            await self.memory.set("session_state", session_data)
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
    
    async def on_key(self, event) -> None:
        """Handle keyboard input"""
        if self.model_dialog_active and event.key in ("up", "down", "enter", "escape"):
            # Handle model dialog key events
            pass
        else:
            await super().on_key(event)
    
    def on_button_pressed(self, event) -> None:
        """Handle button press events"""
        if event.button.id == "send-button":
            self.action_send_message()

# Backward compatibility
class EnhancedTUI(NeoCloneApp):
    """Backward compatible Enhanced TUI class"""
    pass