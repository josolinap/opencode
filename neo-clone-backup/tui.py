"""
tui.py - Textual TUI interface for Neo-Clone assistant.

Implements:
- Chat-style interface with message history
- Input field for user messages
- Support for /commands (/skills, /config, /quit, /clear)
- Integration with brain.py reasoning engine
- Error handling and display
"""

import logging
import asyncio
from typing import Dict, List, Optional
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Input, Label, RichLog
from textual.binding import Binding
from textual.reactive import reactive
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel
from rich.align import Align
from rich.console import Console
from rich.syntax import Syntax

from config import Config, load_config
from skills import SkillRegistry
from brain import Brain

logger = logging.getLogger(__name__)

class MessageWidget(Container):
    """Widget to display a single message in the chat."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        super().__init__()
        self.role = role
        self.content = content
        self.timestamp = timestamp
    
    def compose(self) -> ComposeResult:
        # Format the message based on role
        if self.role == "user":
            role_text = "You"
            role_color = "cyan"
        else:
            role_text = "Neo"
            role_color = "green"
        
        # Create panel content
        content = f"[bold {role_color}]{role_text}:[/bold {role_color}]\n{self.content}"
        
        # Try to detect if content is markdown or code
        if self.content.strip().startswith("```") or "```" in self.content:
            # Extract code block
            lines = self.content.split("\n")
            in_code = False
            code_lines = []
            language = ""
            
            for line in lines:
                if line.strip().startswith("```"):
                    if not in_code:
                        language = line.strip()[3:].strip()
                        in_code = True
                    else:
                        in_code = False
                elif in_code:
                    code_lines.append(line)
            
            if code_lines:
                # Display as syntax highlighted code
                code_content = "\n".join(code_lines)
                try:
                    code_widget = Syntax(
                        code_content,
                        language if language else "python",
                        theme="monokai",
                        line_numbers=True
                    )
                    yield Panel(
                        Align.center(code_widget),
                        title=f"[bold {role_color}]{role_text}[/bold {role_color}]",
                        border_style=role_color
                    )
                    return
                except:
                    pass
        
        # Check if content looks like markdown
        if any(marker in self.content for marker in ["#", "*", "-", "**", "`"]):
            try:
                md_widget = Markdown(self.content)
                yield Panel(
                    md_widget,
                    title=f"[bold {role_color}]{role_text}[/bold {role_color}]",
                    border_style=role_color
                )
                return
            except:
                pass
        
        # Default text display
        yield Panel(
            content,
            title=f"[bold {role_color}]{role_text}[/bold {role_color}]",
            border_style=role_color
        )


class NeoTUI(App):
    """Main TUI application for Neo-Clone."""
    
    CSS = """
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
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear Chat"),
    ]
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or load_config()
        self.skills = SkillRegistry()
        self.brain = Brain(self.config, self.skills)
        self.console = Console()
        self.is_processing = False
    
    def compose(self) -> ComposeResult:
        """Create the TUI layout."""
        with Container(classes="chat-container"):
            yield RichLog(classes="messages", id="messages", auto_scroll=True)
            yield Container(
                Input(placeholder="Type your message... (/help for commands)", 
                      classes="input-widget", id="input"),
                classes="input-container"
            )
        yield Label("Press Ctrl+C or 'q' to quit | /help for commands", classes="status-bar")
    
    async def on_mount(self) -> None:
        """Mount the TUI and show welcome message."""
        self.title = "Neo-Clone TUI Assistant"
        await self.show_welcome()
    
    async def show_welcome(self):
        """Display welcome message and system info."""
        welcome_text = """
# Welcome to Neo-Clone TUI

## Available Commands:
- `/help` - Show this help message
- `/skills` - List available skills
- `/config` - Show current configuration
- `/clear` - Clear chat history
- `/quit` or `/exit` - Exit the application

## How to use:
Simply type your message and press Enter. The assistant will:
1. Parse your intent
2. Use the most appropriate skill if needed
3. Otherwise, use the LLM for general conversation
        """
        
        messages_log = self.query_one("#messages", RichLog)
        await messages_log.write(Markdown(welcome_text))
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if self.is_processing:
            return
        
        user_input = event.value.strip()
        if not user_input:
            return
        
        # Clear input
        self.query_one("#input", Input).value = ""
        
        # Add user message to chat
        await self.add_message("user", user_input)
        
        # Process the message
        await self.process_message(user_input)
    
    async def add_message(self, role: str, content: str):
        """Add a message to the chat log."""
        messages_log = self.query_one("#messages", RichLog)
        
        # Create message widget
        message_widget = MessageWidget(role=role, content=content)
        await messages_log.write(Panel(
            content,
            title=f"[bold {'cyan' if role == 'user' else 'green'}]{'You' if role == 'user' else 'Neo'}[/bold {'cyan' if role == 'user' else 'green'}]",
            border_style={'cyan' if role == 'user' else 'green'}
        ))
    
    async def add_system_message(self, content: str, style: str = "blue"):
        """Add a system message to the chat."""
        messages_log = self.query_one("#messages", RichLog)
        
        message_text = Text(content, style=f"bold {style}")
        await messages_log.write(message_text)
    
    async def process_message(self, message: str):
        """Process a user message."""
        self.is_processing = True
        
        try:
            # Check for commands
            if message.startswith("/"):
                await self.handle_command(message)
            else:
                # Regular message - use brain
                await self.process_with_brain(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.add_message("assistant", f"[Error] {str(e)}")
        finally:
            self.is_processing = False
    
    async def process_with_brain(self, message: str):
        """Process message using the brain engine."""
        # Add thinking indicator
        await self.add_system_message("🤔 Thinking...", style="yellow")
        
        try:
            # Call brain
            response = self.brain.send_message(message)
            
            # Add assistant response
            await self.add_message("assistant", response)
            
        except Exception as e:
            logger.error(f"Brain error: {e}")
            await self.add_message("assistant", f"Sorry, I encountered an error: {e}")
    
    async def handle_command(self, command: str):
        """Handle slash commands."""
        cmd_parts = command[1:].split()  # Remove leading /
        cmd = cmd_parts[0].lower() if cmd_parts else ""
        
        if cmd in ["help", "h"]:
            await self.show_help()
        elif cmd in ["skills", "skill"]:
            await self.show_skills()
        elif cmd in ["config", "cfg"]:
            await self.show_config()
        elif cmd in ["clear", "c"]:
            await self.clear_chat()
        elif cmd in ["quit", "exit", "q"]:
            await self.quit_app()
        else:
            await self.add_system_message(f"Unknown command: /{cmd}. Type /help for available commands.", style="red")
    
    async def show_help(self):
        """Show help information."""
        help_text = """
# Available Commands

## Chat Commands
- `/help` or `/h` - Show this help message
- `/skills` - List available skills
- `/config` or `/cfg` - Show current configuration
- `/clear` or `/c` - Clear chat history
- `/quit` or `/exit` - Exit the application

## General Tips
- The assistant automatically detects intent and uses appropriate skills
- Skills are triggered by keywords in your message
- You can have a natural conversation with the assistant
        """
        
        await self.add_message("assistant", help_text)
    
    async def show_skills(self):
        """Show available skills."""
        skills_list = self.skills.list_skills()
        
        if not skills_list:
            await self.add_message("assistant", "No skills available.")
            return
        
        skills_text = "# Available Skills\n\n"
        for skill_name in skills_list:
            try:
                skill = self.skills.get(skill_name)
                skills_text += f"## {skill_name}\n"
                skills_text += f"**Description:** {skill.description}\n"
                skills_text += f"**Example:** {skill.example_usage}\n\n"
            except Exception as e:
                logger.error(f"Error getting skill {skill_name}: {e}")
        
        await self.add_message("assistant", skills_text)
    
    async def show_config(self):
        """Show current configuration."""
        config_text = "# Current Configuration\n\n"
        config_text += f"**Provider:** {self.config.provider}\n"
        config_text += f"**Model:** {self.config.model_name}\n"
        config_text += f"**API Endpoint:** {self.config.api_endpoint}\n"
        config_text += f"**Max Tokens:** {self.config.max_tokens}\n"
        config_text += f"**Temperature:** {self.config.temperature}\n"
        
        await self.add_message("assistant", config_text)
    
    async def clear_chat(self):
        """Clear the chat history."""
        messages_log = self.query_one("#messages", RichLog)
        await messages_log.clear()
        self.brain.clear_history()
        await self.add_system_message("Chat history cleared.", style="green")
    
    async def quit_app(self):
        """Exit the application."""
        await self.add_system_message("Goodbye! 👋", style="green")
        # Delay a bit to show the goodbye message
        await asyncio.sleep(0.5)
        await self.action_quit()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def main():
    """Main entry point for TUI mode."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo-Clone TUI Assistant")
    parser.add_argument("--config", help="Path to config file", default=None)
    parser.add_argument("--debug", help="Enable debug logging", action="store_true")
    
    args = parser.parse_args()
    
    # Setup logging
    from utils import setup_logging
    setup_logging(debug=args.debug)
    
    # Load config
    config = load_config(args.config)
    
    # Run TUI
    app = NeoTUI(config)
    app.run()


if __name__ == "__main__":
    main()