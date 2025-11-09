"""
enhanced_tui.py - Enhanced TUI interface for Neo-Clone with Phase 3 features

Implements:
- Dark/Light theme toggle
- Message search functionality  
- Integration with memory, logging, presets, and plugin systems
- Enhanced command handling
- Backward compatibility with existing features
"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Set
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Input, Label, RichLog, Button, Switch
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

from config import Config, load_config
from skills import SkillRegistry
from brain import Brain
from memory import get_memory
from logging_system import get_logger, SkillExecutionContext
from llm_presets import get_preset_manager
from plugin_system import get_plugin_manager

logger = logging.getLogger(__name__)

class MessageData:
    """Data class to store message information with metadata"""
    def __init__(self, role: str, content: str, timestamp: str = None, 
                 intent: str = None, skill_used: str = None, 
                 preset_used: str = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.intent = intent
        self.skill_used = skill_used
        self.preset_used = preset_used

class SearchResultWidget(Container):
    """Widget to display search results"""
    
    def __init__(self, matches: List[MessageData], query: str):
        super().__init__()
        self.matches = matches
        self.query = query
    
    def compose(self) -> ComposeResult:
        if not self.matches:
            yield Label(f"No matches found for '{self.query}'")
            return
        
        yield Label(f"Found {len(self.matches)} matches for '{self.query}':", style="bold")
        
        for i, match in enumerate(self.matches, 1):
            preview = match.content[:100] + "..." if len(match.content) > 100 else match.content
            yield Label(
                f"{i}. [{match.timestamp}] {match.role}: {preview}",
                style="link" if match.role == "user" else "info"
            )

class ThemeManager:
    """Manages dark/light theme switching"""
    
    # CSS for light theme
    LIGHT_CSS = """
    Screen {
        background: $surface;
    }
    
    .chat-container {
        height: 1fr;
        padding: 1;
    }
    
    .messages {
        height: 1fr;
        border: solid $primary;
    }
    
    .input-container {
        height: 3;
        padding: 1;
        border: solid $secondary;
        background: $surface;
    }
    
    .input-widget {
        width: 100%;
    }
    
    .status-bar {
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
    }
    
    .toolbar {
        height: 2;
        background: $panel;
        border: solid $primary;
        padding: 0 1;
    }
    
    .search-container {
        height: 3;
        background: $panel;
        border: solid $warning;
    }
    """
    
    # CSS for dark theme
    DARK_CSS = """
    Screen {
        background: #1e1e1e;
    }
    
    .chat-container {
        height: 1fr;
        padding: 1;
    }
    
    .messages {
        height: 1fr;
        border: solid #569cd6;
    }
    
    .input-container {
        height: 3;
        padding: 1;
        border: solid #4ec9b0;
        background: #2d2d2d;
    }
    
    .input-widget {
        width: 100%;
    }
    
    .status-bar {
        height: 1;
        background: #569cd6;
        color: #ffffff;
        text-align: center;
    }
    
    .toolbar {
        height: 2;
        background: #2d2d2d;
        border: solid #569cd6;
        padding: 0 1;
    }
    
    .search-container {
        height: 3;
        background: #2d2d2d;
        border: solid #ce9178;
    }
    """
    
    def __init__(self, app: App, initial_theme: str = "light"):
        self.app = app
        self.current_theme = initial_theme
        self.apply_theme(initial_theme)
    
    def apply_theme(self, theme: str):
        """Apply theme to the app"""
        self.current_theme = theme
        if theme == "dark":
            self.app.css = self.DARK_CSS
        else:
            self.app.css = self.LIGHT_CSS
        
        logger.info(f"Applied {theme} theme")
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme)
        return new_theme

class EnhancedNeoTUI(App):
    """Enhanced TUI application for Neo-Clone with Phase 3 features."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear Chat"),
        Binding("ctrl+f", "focus_search", "Search"),
        Binding("ctrl+t", "toggle_theme", "Toggle Theme"),
        Binding("ctrl+p", "show_presets", "LLM Presets"),
        Binding("ctrl+s", "show_stats", "Statistics"),
    ]
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or load_config()
        self.skills = SkillRegistry()
        self.brain = Brain(self.config, self.skills)
        self.console = Console()
        
        # Phase 3 integrations
        self.memory = get_memory()
        self.logger = get_logger()
        self.preset_manager = get_preset_manager()
        self.plugin_manager = get_plugin_manager()
        
        # UI state
        self.is_processing = False
        self.message_history: List[MessageData] = []
        self.current_preset = "conversational"
        
        # Theme management
        initial_theme = self.memory.preferences.theme if hasattr(self.memory, 'preferences') else "light"
        self.theme_manager = ThemeManager(self, initial_theme)
        
        # Setup logging
        self.logger.log_system_event("tui_startup", f"Started TUI with {initial_theme} theme")
    
    def compose(self) -> ComposeResult:
        """Create the enhanced TUI layout."""
        with Container(classes="chat-container"):
            # Toolbar with controls
            with Container(classes="toolbar"):
                with Horizontal():
                    yield Button("💡", id="theme-btn", tooltip="Toggle Theme")
                    yield Button("🔍", id="search-btn", tooltip="Search Messages")
                    yield Button("⚙️", id="presets-btn", tooltip="LLM Presets")
                    yield Button("📊", id="stats-btn", tooltip="Usage Statistics")
                    yield Button("🧩", id="plugins-btn", tooltip="Plugin Manager")
            
            yield RichLog(classes="messages", id="messages", auto_scroll=True)
            
            # Search container (hidden by default)
            yield Container(
                Input(placeholder="Search messages... (Ctrl+F to focus)", 
                      classes="input-widget", id="search-input"),
                classes="search-container",
                id="search-container"
            )
            
            yield Container(
                Input(placeholder="Type your message... (/help for enhanced commands)", 
                      classes="input-widget", id="input"),
                classes="input-container"
            )
        
        status_text = f"Neo-Clone v3.0 | Theme: {self.theme_manager.current_theme.title()} | Preset: {self.current_preset}"
        yield Label(status_text, classes="status-bar")
    
    async def on_mount(self) -> None:
        """Mount the TUI and show enhanced welcome message."""
        self.title = "Neo-Clone Enhanced TUI Assistant"
        await self.show_enhanced_welcome()
    
    async def show_enhanced_welcome(self):
        """Display enhanced welcome message with new features."""
        welcome_text = """
# Welcome to Neo-Clone Enhanced TUI v3.0! 🚀

## New Features in Phase 3:
- 🎨 **Dark/Light Themes** - Toggle with Ctrl+T
- 🔍 **Message Search** - Search with Ctrl+F
- ⚙️ **LLM Presets** - Choose AI modes with Ctrl+P
- 📊 **Usage Statistics** - View with Ctrl+S
- 🧩 **Plugin System** - Extend with custom plugins
- 💾 **Persistent Memory** - Conversations are saved automatically

## Enhanced Commands:
### Core Commands
- `/help` - Show this help message
- `/skills` - List available skills (now includes file_manager, web_search)
- `/config` - Show current configuration
- `/preset [name]` - Set LLM preset (creative, technical, analytical, etc.)
- `/theme` - Toggle between dark and light themes
- `/search [query]` - Search message history
- `/stats` - Show usage statistics
- `/plugins` - Manage plugins
- `/clear` - Clear chat history
- `/quit` or `/exit` - Exit the application

### Memory & Analytics
- `/memory` - Show memory usage and settings
- `/export` - Export conversation history
- `/backup` - Create data backup

## Quick Start:
1. Try `/skills` to see the new capabilities
2. Use `/preset creative` for writing tasks
3. Try `search for file operations` to see new skills in action
4. Press Ctrl+F to search through your conversation history
        """
        
        messages_log = self.query_one("#messages", RichLog)
        await messages_log.write(Markdown(welcome_text))
        
        # Log startup
        self.logger.log_system_event("tui_welcome_shown", "Enhanced welcome message displayed")
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission with enhanced processing."""
        if self.is_processing:
            return
        
        # Check if search input was focused
        if hasattr(self, '_search_focused') and self._search_focused:
            await self.handle_search_input(event.value)
            return
        
        user_input = event.value.strip()
        if not user_input:
            return
        
        # Clear input
        self.query_one("#input", Input).value = ""
        
        # Log user message
        self.logger.log_user_message(user_input)
        
        # Add to memory
        self.memory.add_conversation(user_input, "", intent="user_input")
        
        # Add user message to chat
        await self.add_message("user", user_input)
        
        # Process the message
        await self.process_message(user_input)
    
    async def handle_search_input(self, query: str):
        """Handle search input submission."""
        if not query.strip():
            await self.hide_search()
            return
        
        # Search through memory
        search_results = self.memory.search_conversations(query)
        
        # Add search results to chat
        if search_results:
            results_text = f"# Search Results for '{query}'\n\n"
            for i, result in enumerate(search_results[:10], 1):
                preview = result.user_message[:100] + "..." if len(result.user_message) > 100 else result.user_message
                results_text += f"**{i}.** [{result.timestamp}] You: {preview}\n\n"
            
            await self.add_message("system", results_text)
        else:
            await self.add_message("system", f"No search results found for '{query}'")
        
        await self.hide_search()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle toolbar button presses."""
        button_id = event.button.id
        
        if button_id == "theme-btn":
            await self.toggle_theme()
        elif button_id == "search-btn":
            await self.show_search()
        elif button_id == "presets-btn":
            await self.show_presets()
        elif button_id == "stats-btn":
            await self.show_statistics()
        elif button_id == "plugins-btn":
            await self.show_plugins()
    
    async def toggle_theme(self):
        """Toggle between dark and light themes."""
        new_theme = self.theme_manager.toggle_theme()
        
        # Update status bar
        status_bar = self.query_one(".status-bar")
        new_status = f"Neo-Clone v3.0 | Theme: {new_theme.title()} | Preset: {self.current_preset}"
        status_bar.update(new_status)
        
        # Save preference
        if hasattr(self.memory, 'preferences'):
            self.memory.preferences.theme = new_theme
            self.memory.save_preferences()
        
        await self.add_message("system", f"Switched to {new_theme} theme 🌙" if new_theme == "dark" else f"Switched to {new_theme} theme ☀️")
    
    async def show_search(self):
        """Show the search interface."""
        search_container = self.query_one("#search-container")
        search_input = self.query_one("#search-input")
        
        search_container.display = "block"
        search_input.focus()
        self._search_focused = True
        
        await self.add_message("system", "Search mode active. Type your search query above.")
    
    async def hide_search(self):
        """Hide the search interface."""
        search_container = self.query_one("#search-container")
        search_input = self.query_one("#search-input")
        
        search_container.display = "none"
        search_input.value = ""
        self._search_focused = False
        
        # Return focus to main input
        main_input = self.query_one("#input")
        main_input.focus()
    
    async def show_presets(self):
        """Show available LLM presets."""
        presets = self.preset_manager.list_presets()
        
        presets_text = "# Available LLM Presets\n\n"
        for name, preset in presets.items():
            icon = {"creative": "🎨", "technical": "💻", "analytical": "🔬", "conversational": "💬"}.get(preset.category, "📝")
            presets_text += f"## {icon} {name}\n"
            presets_text += f"**Category:** {preset.category.title()}\n"
            presets_text += f"**Description:** {preset.description}\n"
            presets_text += f"**Use Cases:** {', '.join(preset.use_cases[:3])}\n\n"
        
        presets_text += """
**Usage:** Use `/preset <name>` to switch to a specific preset.
Example: `/preset creative_writing` for creative tasks.
        """
        
        await self.add_message("assistant", presets_text)
    
    async def show_statistics(self):
        """Show usage statistics."""
        # Get statistics from various sources
        memory_stats = self.memory.get_statistics()
        preset_stats = self.preset_manager.get_usage_analytics()
        skill_stats = self.logger.get_skill_statistics()
        
        stats_text = "# Usage Statistics\n\n"
        
        # Memory stats
        stats_text += "## 💾 Memory & Conversations\n"
        stats_text += f"- **Total Conversations:** {memory_stats.get('total_conversations', 0)}\n"
        stats_text += f"- **Current Session:** {memory_stats.get('session_id', 'N/A')}\n"
        stats_text += f"- **Max History:** {memory_stats.get('preferences', {}).get('max_history', 'N/A')}\n\n"
        
        # Preset usage
        stats_text += "## ⚙️ LLM Presets\n"
        if preset_stats.get('most_used_presets'):
            for preset, count in preset_stats['most_used_presets'][:3]:
                stats_text += f"- **{preset}:** {count} uses\n"
        else:
            stats_text += "- No preset usage data yet\n"
        stats_text += f"- **Total Interactions:** {preset_stats.get('total_interactions', 0)}\n\n"
        
        # Skill usage
        stats_text += "## 🛠️ Skills Usage\n"
        if skill_stats:
            for skill, stats in list(skill_stats.items())[:3]:
                success_rate = (stats['successful_calls'] / stats['total_calls'] * 100) if stats['total_calls'] > 0 else 0
                stats_text += f"- **{skill}:** {stats['total_calls']} calls ({success_rate:.1f}% success)\n"
        else:
            stats_text += "- No skill usage data yet\n"
        
        await self.add_message("assistant", stats_text)
    
    async def show_plugins(self):
        """Show loaded plugins."""
        plugins = self.plugin_manager.list_all_plugins()
        
        if not plugins:
            await self.add_message("system", "No plugins loaded. Check the plugins/ directory.")
            return
        
        plugins_text = "# Loaded Plugins\n\n"
        for name, info in plugins.items():
            status_icon = "✅" if info['loaded'] else "❌"
            plugins_text += f"## {status_icon} {name}\n"
            if info['metadata']:
                plugins_text += f"**Version:** {info['metadata'].get('version', 'Unknown')}\n"
                plugins_text += f"**Description:** {info['metadata'].get('description', 'No description')}\n"
                plugins_text += f"**Author:** {info['metadata'].get('author', 'Unknown')}\n"
            plugins_text += f"**Status:** {'Loaded' if info['loaded'] else 'Not loaded'}\n\n"
        
        await self.add_message("assistant", plugins_text)
    
    async def add_message(self, role: str, content: str, **kwargs):
        """Add a message to the chat log."""
        messages_log = self.query_one("#messages", RichLog)
        
        # Create message data
        message_data = MessageData(role=role, content=content, **kwargs)
        self.message_history.append(message_data)
        
        # Format message
        if role == "user":
            role_text = "You"
            role_color = "cyan"
        elif role == "system":
            role_text = "System"
            role_color = "blue"
        else:
            role_text = "Neo"
            role_color = "green"
        
        # Add metadata to display if present
        display_content = content
        if hasattr(self, '_show_metadata') and self._show_metadata:
            metadata_parts = []
            if message_data.skill_used:
                metadata_parts.append(f"Skill: {message_data.skill_used}")
            if message_data.preset_used:
                metadata_parts.append(f"Preset: {message_data.preset_used}")
            if message_data.timestamp:
                metadata_parts.append(f"Time: {message_data.timestamp}")
            
            if metadata_parts:
                display_content = f"[dim]{' | '.join(metadata_parts)}[/dim]\n\n{content}"
        
        await messages_log.write(Panel(
            display_content,
            title=f"[bold {role_color}]{role_text}[/bold {role_color}]",
            border_style=role_color
        ))
    
    async def process_message(self, message: str):
        """Process a user message with enhanced capabilities."""
        self.is_processing = True
        
        try:
            # Check for commands
            if message.startswith("/"):
                await self.handle_enhanced_command(message)
            else:
                # Regular message - use enhanced brain processing
                await self.process_with_enhanced_brain(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.logger.log_error("message_processing", str(e), message)
            await self.add_message("assistant", f"[Error] {str(e)}")
        finally:
            self.is_processing = False
    
    async def handle_enhanced_command(self, command: str):
        """Handle enhanced slash commands."""
        cmd_parts = command[1:].split()  # Remove leading /
        cmd = cmd_parts[0].lower() if cmd_parts else ""
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        if cmd in ["help", "h"]:
            await self.show_enhanced_help()
        elif cmd in ["skills", "skill"]:
            await self.show_enhanced_skills()
        elif cmd in ["config", "cfg"]:
            await self.show_config()
        elif cmd in ["preset", "presets"]:
            await self.handle_preset_command(args)
        elif cmd == "theme":
            await self.toggle_theme()
        elif cmd in ["search"]:
            await self.handle_search_command(args)
        elif cmd in ["stats", "statistics"]:
            await self.show_statistics()
        elif cmd in ["plugins", "plugin"]:
            await self.show_plugins()
        elif cmd in ["memory"]:
            await self.show_memory_info()
        elif cmd in ["export"]:
            await self.handle_export_command(args)
        elif cmd in ["backup"]:
            await self.handle_backup_command()
        elif cmd in ["clear", "c"]:
            await self.clear_chat()
        elif cmd in ["quit", "exit", "q"]:
            await self.quit_app()
        else:
            await self.add_message("system", f"Unknown command: /{cmd}. Type /help for available commands.", style="red")
    
    async def handle_preset_command(self, args: List[str]):
        """Handle preset selection command."""
        if not args:
            await self.show_presets()
            return
        
        preset_name = args[0]
        preset = self.preset_manager.get_preset(preset_name)
        
        if not preset:
            await self.add_message("system", f"Preset '{preset_name}' not found. Use /preset to see available presets.")
            return
        
        # Apply preset (in a real implementation, this would update the brain's LLM parameters)
        self.current_preset = preset_name
        
        # Update status bar
        status_bar = self.query_one(".status-bar")
        new_status = f"Neo-Clone v3.0 | Theme: {self.theme_manager.current_theme.title()} | Preset: {self.current_preset}"
        status_bar.update(new_status)
        
        await self.add_message("system", f"Applied preset: {preset_name} 🎯\n{preset.description}")
        self.logger.log_system_event("preset_applied", f"Applied {preset_name} preset", {"preset_name": preset_name})
    
    async def handle_search_command(self, args: List[str]):
        """Handle search command with arguments."""
        if not args:
            await self.show_search()
            return
        
        query = " ".join(args)
        search_results = self.memory.search_conversations(query)
        
        if search_results:
            results_text = f"# Search Results for '{query}'\n\n"
            for i, result in enumerate(search_results[:5], 1):
                preview = result.user_message[:100] + "..." if len(result.user_message) > 100 else result.user_message
                results_text += f"**{i}.** [{result.timestamp}] You: {preview}\n\n"
            
            await self.add_message("assistant", results_text)
        else:
            await self.add_message("system", f"No search results found for '{query}'")
    
    async def show_enhanced_help(self):
        """Show enhanced help information."""
        help_text = """
# Enhanced Commands

## Core Commands
- `/help` or `/h` - Show this help message
- `/skills` - List available skills
- `/config` or `/cfg` - Show current configuration
- `/clear` or `/c` - Clear chat history
- `/quit`, `/exit`, or `/q` - Exit the application

## Phase 3 Features
- `/preset [name]` - Set LLM preset (creative, technical, analytical, etc.)
- `/theme` - Toggle between dark and light themes
- `/search [query]` - Search message history
- `/stats` - Show usage statistics
- `/plugins` - Manage plugins
- `/memory` - Show memory information
- `/export [format]` - Export conversation history
- `/backup` - Create data backup

## Keyboard Shortcuts
- `Ctrl+T` - Toggle theme
- `Ctrl+F` - Focus search
- `Ctrl+P` - Show presets
- `Ctrl+S` - Show statistics

## New Skills Available
- **file_manager** - Read files, analyze content, manage directories
- **web_search** - Search the web, fact-check, news lookup

## LLM Presets
- `creative_writing` - For creative content
- `code_generation` - For programming tasks
- `data_analysis` - For analytical work
- `fact_checking` - For verification
- `conversational` - For natural chat
        """
        
        await self.add_message("assistant", help_text)
    
    async def show_enhanced_skills(self):
        """Show enhanced skills list including new ones."""
        skills_list = self.skills.list_skills()
        
        if not skills_list:
            await self.add_message("assistant", "No skills available.")
            return
        
        skills_text = "# Available Skills (Enhanced)\n\n"
        
        # Group skills by category
        skill_categories = {
            "original": ["code_generation", "data_inspector", "ml_training", "text_analysis"],
            "new": ["file_manager", "web_search"]
        }
        
        for category, skills in skill_categories.items():
            skills_text += f"## {category.title()} Skills\n"
            for skill_name in skills:
                if skill_name in skills_list:
                    try:
                        skill = self.skills.get(skill_name)
                        icon = {"code_generation": "💻", "data_inspector": "📊", "ml_training": "🤖", 
                               "text_analysis": "📝", "file_manager": "📁", "web_search": "🔍"}.get(skill_name, "🛠️")
                        skills_text += f"### {icon} {skill_name}\n"
                        skills_text += f"**Description:** {skill.description}\n"
                        skills_text += f"**Example:** {skill.example_usage}\n\n"
                    except Exception as e:
                        logger.error(f"Error getting skill {skill_name}: {e}")
        
        skills_text += "## Usage Tips\n"
        skills_text += "- Skills are automatically triggered by keywords in your message\n"
        skills_text += "- New skills: Try 'search for Python tutorials' or 'read /path/to/file'\n"
        skills_text += "- Use `/search` to find previous skill usages in your history\n"
        
        await self.add_message("assistant", skills_text)
    
    async def process_with_enhanced_brain(self, message: str):
        """Process message using enhanced brain with presets and logging."""
        # Auto-select preset
        auto_preset = self.preset_manager.auto_select_preset(message)
        if auto_preset and auto_preset != self.current_preset:
            await self.add_message("system", f"Auto-selected preset: {auto_preset}")
            self.current_preset = auto_preset
        
        # Add thinking indicator
        await self.add_message("system", f"🤔 Thinking with {self.current_preset} preset...", style="yellow")
        
        try:
            with SkillExecutionContext(self.logger, "brain_processing", message):
                # Call brain with enhanced processing
                response = self.brain.send_message(message)
                
                # Update the last message with preset info
                if self.message_history:
                    self.message_history[-1].preset_used = self.current_preset
                
                # Add assistant response
                await self.add_message("assistant", response, preset_used=self.current_preset)
                
                # Store in memory with response
                if self.message_history:
                    self.memory.add_conversation(
                        self.message_history[-1].content,
                        response,
                        intent="chat",
                        metadata={"preset": self.current_preset}
                    )
                
        except Exception as e:
            logger.error(f"Brain error: {e}")
            self.logger.log_error("brain_processing", str(e), message)
            await self.add_message("assistant", f"Sorry, I encountered an error: {e}")
    
    async def show_memory_info(self):
        """Show memory system information."""
        memory_stats = self.memory.get_statistics()
        
        memory_text = "# Memory System Information\n\n"
        memory_text += f"## 💾 Current Status\n"
        memory_text += f"- **Total Conversations:** {memory_stats.get('total_conversations', 0)}\n"
        memory_text += f"- **Current Session:** {memory_stats.get('session_id', 'N/A')}\n"
        memory_text += f"- **Memory Directory:** {memory_stats.get('memory_dir', 'N/A')}\n\n"
        
        if 'preferences' in memory_stats:
            prefs = memory_stats['preferences']
            memory_text += f"## ⚙️ Preferences\n"
            memory_text += f"- **Theme:** {prefs.get('theme', 'light')}\n"
            memory_text += f"- **Max History:** {prefs.get('max_history', 50)}\n"
            memory_text += f"- **Auto Save:** {prefs.get('auto_save', True)}\n\n"
        
        memory_text += f"## 📁 Data Files\n"
        memory_text += f"- Conversations are automatically saved\n"
        memory_text += f"- User preferences are persisted\n"
        memory_text += f"- Usage statistics are tracked\n"
        memory_text += f"- Automatic backups can be created with `/backup`\n"
        
        await self.add_message("assistant", memory_text)
    
    async def handle_export_command(self, args: List[str]):
        """Handle export command."""
        format_type = args[0] if args else "json"
        
        try:
            export_file = f"conversations_export_{self.memory.session_id}.{format_type}"
            self.memory.export_conversations(export_file, format_type)
            await self.add_message("system", f"Exported conversation history to {export_file} 📤")
            self.logger.log_system_event("export", f"Exported conversations to {export_file}")
        except Exception as e:
            await self.add_message("system", f"Export failed: {e} ❌")
    
    async def handle_backup_command(self):
        """Handle backup command."""
        try:
            backup_name = self.memory.create_backup()
            if backup_name:
                await self.add_message("system", f"Created backup: {backup_name} 💾")
                self.logger.log_system_event("backup", f"Created backup: {backup_name}")
            else:
                await self.add_message("system", "Backup failed ❌")
        except Exception as e:
            await self.add_message("system", f"Backup error: {e} ❌")
    
    async def clear_chat(self):
        """Clear the chat history."""
        messages_log = self.query_one("#messages", RichLog)
        await messages_log.clear()
        self.message_history.clear()
        self.brain.clear_history()
        await self.add_message("system", "Chat history cleared. 💫", style="green")
        self.logger.log_system_event("clear_chat", "Chat history cleared by user")
    
    async def quit_app(self):
        """Exit the application."""
        await self.add_message("system", "Goodbye! Thanks for using Neo-Clone Enhanced TUI! 👋", style="green")
        
        # Final save
        self.memory.save_all()
        self.logger.log_system_event("tui_shutdown", "TUI shutdown initiated")
        
        # Delay a bit to show the goodbye message
        await asyncio.sleep(0.5)
        await self.action_quit()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    # Action bindings
    def action_toggle_theme(self) -> None:
        """Action to toggle theme."""
        self.run_worker(self.toggle_theme())
    
    def action_focus_search(self) -> None:
        """Action to focus search."""
        self.run_worker(self.show_search())
    
    def action_show_presets(self) -> None:
        """Action to show presets."""
        self.run_worker(self.show_presets())
    
    def action_show_stats(self) -> None:
        """Action to show statistics."""
        self.run_worker(self.show_statistics())


def main():
    """Main entry point for enhanced TUI mode."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo-Clone Enhanced TUI Assistant")
    parser.add_argument("--config", help="Path to config file", default=None)
    parser.add_argument("--debug", help="Enable debug logging", action="store_true")
    parser.add_argument("--theme", choices=["light", "dark"], help="Initial theme", default=None)
    
    args = parser.parse_args()
    
    # Setup logging
    from utils import setup_logging
    setup_logging(debug=args.debug)
    
    # Load config
    config = load_config(args.config)
    
    # Create and configure app
    app = EnhancedNeoTUI(config)
    
    # Set initial theme if specified
    if args.theme:
        app.theme_manager.apply_theme(args.theme)
    
    # Run TUI
    app.run()


if __name__ == "__main__":
    main()