// Webview script for OpenCode VSCode extension

class OpenCodeWebview {
  constructor() {
    this.port = window.OPENCODE_PORT;
    this.messages = [];
    this.sessionId = null;
    this.init();
  }

  init() {
    this.setupElements();
    this.setupEventListeners();
    this.connectToServer();
    this.notifyReady();
  }

  setupElements() {
    this.header = document.getElementById("header");
    this.status = document.querySelector(".status");
    this.messagesContainer = document.getElementById("messages");
    this.messageInput = document.getElementById("message-input");
    this.sendButton = document.getElementById("send-button");
    this.clearBtn = document.getElementById("clear-btn");
    this.helpBtn = document.getElementById("help-btn");
    this.settingsBtn = document.getElementById("settings-btn");
  }

  setupEventListeners() {
    this.sendButton.addEventListener("click", () => this.sendMessage());
    this.messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
    this.clearBtn.addEventListener("click", () => this.clearConversation());
    this.helpBtn.addEventListener("click", () => this.showHelp());
    this.settingsBtn.addEventListener("click", () => this.showSettings());

    // Listen for messages from extension
    window.addEventListener("message", (event) => {
      this.handleExtensionMessage(event.data);
    });
  }

  async connectToServer() {
    try {
      console.log(`Connecting to OpenCode server on port ${this.port}...`);
      const response = await fetch(`http://localhost:${this.port}/health`);
      if (response.ok) {
        this.updateStatus("Connected", "connected");
        console.log("Successfully connected to OpenCode server");
      } else {
        this.updateStatus("Server Error", "error");
        console.error("Server responded with error:", response.status);
      }
    } catch (error) {
      this.updateStatus("Connection Failed", "error");
      console.error("Failed to connect to OpenCode server:", error);
      // Notify extension of connection failure
      vscode.postMessage({ type: "error", error: error.message });
    }
  }

  notifyReady() {
    // Notify extension that webview is ready
    vscode.postMessage({ type: "ready" });
  }

  handleExtensionMessage(message) {
    switch (message.type) {
      case "context":
        this.updateContext(message.file);
        break;
      case "response":
        this.addMessage("assistant", message.content);
        break;
    }
  }

  updateStatus(text, className) {
    this.status.textContent = text;
    this.status.className = `status ${className}`;
  }

  updateContext(file) {
    // Update context display
    const contextElement = document.createElement("div");
    contextElement.className = "context-info";
    contextElement.textContent = `Working on: ${file}`;
    this.header.appendChild(contextElement);
  }

  async sendMessage() {
    const text = this.messageInput.value.trim();
    if (!text) {return;}

    this.addMessage("user", text);
    this.messageInput.value = "";

    try {
      console.log("Sending message:", text);

      // First, ensure we have a session
      if (!this.sessionId) {
        console.log("Creating new session...");
        await this.createSession();
        console.log("Session created:", this.sessionId);
      }

      // Send message to the session
      console.log("Sending message to session:", this.sessionId);
      const response = await fetch(`http://localhost:${this.port}/session/${this.sessionId}/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          parts: [
            {
              type: "text",
              text: text,
            },
          ],
          model: {
            providerID: "anthropic",
            modelID: "claude-3-5-sonnet-20241022",
          },
          agent: "general",
        }),
      });

      console.log("Response status:", response.status);
      if (response.ok) {
        const data = await response.json();
        console.log("Response data:", data);
        // The response contains message info, we need to get the actual response
        this.addMessage("assistant", "Processing your request...");
        // Poll for the response or use SSE to get real-time updates
        this.pollForResponse();
      } else {
        const error = await response.text();
        console.error("API Error:", error);
        this.addMessage("assistant", `Error: ${error}`);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      this.addMessage("assistant", "Failed to send message. Please check your connection.");
      // Notify extension of message sending failure
      vscode.postMessage({ type: "error", error: `Failed to send message: ${error.message}` });
    }
  }

  async createSession() {
    try {
      const response = await fetch(`http://localhost:${this.port}/session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "VSCode GUI Session",
        }),
      });

      if (response.ok) {
        const session = await response.json();
        this.sessionId = session.id;
      } else {
        throw new Error("Failed to create session");
      }
    } catch (error) {
      console.error("Error creating session:", error);
      throw error;
    }
  }

  async pollForResponse() {
    let initialMessageCount = 0;

    // Get initial message count
    try {
      const response = await fetch(`http://localhost:${this.port}/session/${this.sessionId}/message`);
      if (response.ok) {
        const messages = await response.json();
        initialMessageCount = messages.length;
      }
    } catch (error) {
      console.error("Error getting initial message count:", error);
      return;
    }

    // Poll for new messages
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:${this.port}/session/${this.sessionId}/message`);
        if (response.ok) {
          const messages = await response.json();
          if (messages.length > initialMessageCount) {
            // Find the newest assistant message
            const newMessages = messages.slice(initialMessageCount);
            const assistantMessage = newMessages.find((msg) => msg.info.role === "assistant");

            if (assistantMessage) {
              // Update the "Processing..." message with the actual response
              const lastMessageElement = this.messagesContainer.lastElementChild;
              if (lastMessageElement && lastMessageElement.classList.contains("assistant")) {
                const contentElement = lastMessageElement.querySelector(".content");
                if (contentElement && contentElement.textContent === "Processing your request...") {
                  // Get the text content from the message parts
                  const textParts = assistantMessage.parts.filter((part) => part.type === "text");
                  const responseText = textParts.map((part) => part.text).join("\n");
                  contentElement.innerHTML = this.formatContent(responseText);
                  clearInterval(pollInterval);
                }
              }
            }
          }
        }
      } catch (error) {
        console.error("Error polling for response:", error);
      }
    }, 1000);

    // Stop polling after 30 seconds
    setTimeout(() => {
      clearInterval(pollInterval);
      // If still processing, show timeout message
      const lastMessageElement = this.messagesContainer.lastElementChild;
      if (lastMessageElement && lastMessageElement.classList.contains("assistant")) {
        const contentElement = lastMessageElement.querySelector(".content");
        if (contentElement && contentElement.textContent === "Processing your request...") {
          contentElement.innerHTML = this.formatContent(
            "Response timeout. The assistant may still be processing your request.",
          );
        }
      }
    }, 30000);
  }

  addMessage(role, content) {
    const messageElement = document.createElement("div");
    messageElement.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "👤" : "🤖";

    const contentElement = document.createElement("div");
    contentElement.className = "content";
    contentElement.innerHTML = this.formatContent(content);

    messageElement.appendChild(avatar);
    messageElement.appendChild(contentElement);

    this.messagesContainer.appendChild(messageElement);
    this.scrollToBottom();
  }

  formatContent(content) {
    // Basic markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/`(.*?)`/g, "<code>$1</code>")
      .replace(/\n/g, "<br>");
  }

  getCurrentContext() {
    // Get current file context from VSCode
    const contextElements = document.querySelectorAll(".context-info");
    return contextElements.length > 0 ? contextElements[0].textContent : "";
  }

  clearConversation() {
    this.messagesContainer.innerHTML = "";
    this.messages = [];
  }

  showHelp() {
    const helpText = `
OpenCode AI Help:

• Type your questions about code in the input field
• Use @filename to reference specific files
• Use #L1-10 to reference line ranges
• Press Enter to send, Shift+Enter for new line
• Click 🗑️ to clear conversation
• Click ⚙️ for settings

Commands:
• /help - Show this help
• /clear - Clear conversation
• /plan - Plan a feature
• /review - Review current file
    `;
    this.addMessage("assistant", helpText);
  }

  showSettings() {
    // TODO: Implement settings panel
    this.addMessage("assistant", "Settings panel coming soon!");
  }

  scrollToBottom() {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new OpenCodeWebview();
});

// VSCode API
const vscode = acquireVsCodeApi();
