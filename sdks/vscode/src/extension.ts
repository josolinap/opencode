// This method is called when your extension is deactivated
export function deactivate() {}

import * as vscode from "vscode";

const TERMINAL_NAME = "opencode";

export function activate(context: vscode.ExtensionContext) {
  let openNewTerminalDisposable = vscode.commands.registerCommand("opencode.openNewTerminal", async () => {
    await openTerminal();
  });

  let openTerminalDisposable = vscode.commands.registerCommand("opencode.openTerminal", async () => {
    // An opencode terminal already exists => focus it
    const existingTerminal = vscode.window.terminals.find((t: vscode.Terminal) => t.name === TERMINAL_NAME);
    if (existingTerminal) {
      existingTerminal.show();
      return;
    }

    await openTerminal();
  });

  // New GUI Panel Command
  let openGuiPanelDisposable = vscode.commands.registerCommand("opencode.openGuiPanel", async () => {
    await openGuiPanel(context);
  });

  let addFilepathDisposable = vscode.commands.registerCommand("opencode.addFilepathToTerminal", async () => {
    const fileRef = getActiveFile();
    if (!fileRef) {return;}

    const terminal = vscode.window.activeTerminal;
    if (!terminal) {return;}

    if (terminal.name === TERMINAL_NAME) {
      // @ts-ignore
      const port = terminal.creationOptions.env?.["_EXTENSION_OPENCODE_PORT"];
      port ? await appendPrompt(parseInt(port), fileRef) : terminal.sendText(fileRef);
      terminal.show();
    }
  });

  // Traycer commands
  let planDisposable = vscode.commands.registerCommand("opencode.plan", async () => {
    const description = await vscode.window.showInputBox({ prompt: "Enter feature description for planning" });
    if (!description) {return;}
    runTraycerCommand(`plan "${description}"`);
  });

  let reviewDisposable = vscode.commands.registerCommand("opencode.review", async () => {
    const file = getActiveFile();
    if (!file) {return;}
    runTraycerCommand(`review ${file}`);
  });

  let traycerDisposable = vscode.commands.registerCommand("opencode.traycer", async () => {
    const description = await vscode.window.showInputBox({
      prompt: "Enter feature description for full Traycer workflow",
    });
    if (!description) {return;}
    runTraycerCommand(`traycer "${description}"`);
  });

  // Auto-review on save
  const autoReviewDisposable = vscode.workspace.onDidSaveTextDocument(async (document: vscode.TextDocument) => {
    const config = vscode.workspace.getConfiguration("opencode");
    if (!config.get("autoReview", false)) {return;}

    const file = vscode.workspace.asRelativePath(document.uri);
    const output = await runTraycerCommand(`review ${file}`, false);
    if (output !== null) {
      vscode.window.showInformationMessage(`Review completed for ${file}`);
      // Optionally show in output channel
      const channel = vscode.window.createOutputChannel("Opencode Review");
      if (typeof output === "string") { channel.appendLine(output); }
      channel.show();
    }
  });

  context.subscriptions.push(
    openTerminalDisposable,
    openGuiPanelDisposable,
    addFilepathDisposable,
    planDisposable,
    reviewDisposable,
    traycerDisposable,
    autoReviewDisposable,
  );

  async function openTerminal() {
    // Create a new terminal in split screen
    const port = Math.floor(Math.random() * (65535 - 16384 + 1)) + 16384;
    const terminal = vscode.window.createTerminal({
      name: TERMINAL_NAME,
      iconPath: {
        light: vscode.Uri.file(context.asAbsolutePath("images/button-dark.svg")),
        dark: vscode.Uri.file(context.asAbsolutePath("images/button-light.svg")),
      },
      location: {
        viewColumn: vscode.ViewColumn.Beside,
        preserveFocus: false,
      },
      env: {
        _EXTENSION_OPENCODE_PORT: port.toString(),
        OPENCODE_CALLER: "vscode",
      },
    });

    terminal.show();
    terminal.sendText(`opencode --port ${port}`);

    const fileRef = getActiveFile();
    if (!fileRef) {return;}

    // Wait for the terminal to be ready
    let tries = 10;
    let connected = false;
    do {
      await new Promise((resolve) => setTimeout(resolve, 200));
      try {
        await fetch(`http://localhost:${port}/app`);
        connected = true;
        break;
      } catch (e) {}

      tries--;
    } while (tries > 0);

    // If connected, append the prompt to the terminal
    if (connected) {
      await appendPrompt(port, `In ${fileRef}`);
      terminal.show();
    }
  }

  async function openGuiPanel(context: vscode.ExtensionContext) {
    // Check if panel already exists (webview panels are tracked differently)
    // For now, we'll allow multiple panels or implement proper tracking later

    // Start OpenCode server
    const port = Math.floor(Math.random() * (65535 - 16384 + 1)) + 16384;

    // Create webview panel
    const panel = vscode.window.createWebviewPanel(
      "opencodeGui",
      "OpenCode AI",
      {
        viewColumn: vscode.ViewColumn.Beside,
        preserveFocus: false,
      },
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [vscode.Uri.file(context.extensionPath)],
      },
    );

    // Set panel icon
    panel.iconPath = {
      light: vscode.Uri.file(context.asAbsolutePath("images/icon.png")),
      dark: vscode.Uri.file(context.asAbsolutePath("images/icon.png")),
    };

    // Start OpenCode server in background
    const terminal = vscode.window.createTerminal({
      name: "opencode-server",
      env: {
        OPENCODE_CALLER: "vscode-gui",
      },
    });

    terminal.sendText(`opencode serve --port ${port}`);
    context.subscriptions.push(terminal);

    // Clean up terminal when extension deactivates
    context.subscriptions.push({
      dispose: () => {
        terminal.dispose();
      },
    });

    // Wait for server to be ready
    let tries = 15;
    let connected = false;
    do {
      await new Promise((resolve) => setTimeout(resolve, 500));
      try {
        const response = await fetch(`http://localhost:${port}/health`);
        if (response.ok) {
          connected = true;
          break;
        }
      } catch (e) {}

      tries--;
    } while (tries > 0);

    if (!connected) {
      vscode.window.showErrorMessage("Failed to start OpenCode server");
      panel.dispose();
      return;
    }

    // Set up webview content
    const webviewContent = getWebviewContent(panel.webview, context.extensionUri, port);
    panel.webview.html = webviewContent;

    // Handle messages from webview
    panel.webview.onDidReceiveMessage(
      async (message: { type: string; error?: string }) => {
        switch (message.type) {
          case "ready":
            // Send initial context
            const fileRef = getActiveFile();
            if (fileRef) {
              panel.webview.postMessage({
                type: "context",
                file: fileRef,
              });
            }
            break;
          case "command":
            // Handle commands from GUI
            break;
        }
      },
      undefined,
      context.subscriptions,
    );

    // Handle panel disposal
    panel.onDidDispose(
      () => {
        try {
          terminal.dispose();
        } catch (error) {
          // Error disposing terminal
        }
      },
      null,
      context.subscriptions,
    );

    // Handle webview errors
    panel.webview.onDidReceiveMessage(
      (message: { type: string; error?: string }) => {
        if (message.type === "error") {
          vscode.window.showErrorMessage(`OpenCode GUI Error: ${message.error}`);
        }
      },
      undefined,
      context.subscriptions,
    );

    // Listen for active editor changes
    const editorChangeDisposable = vscode.window.onDidChangeActiveTextEditor(
      (editor: vscode.TextEditor | undefined) => {
        if (editor && panel.visible) {
          const fileRef = getActiveFile();
          if (fileRef) {
            panel.webview.postMessage({
              type: "context",
              file: fileRef,
            });
          }
        }
      },
    );

    context.subscriptions.push(editorChangeDisposable);
  }

  async function appendPrompt(port: number, text: string) {
    await fetch(`http://localhost:${port}/tui/append-prompt`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });
  }

  async function runTraycerCommand(command: string, showTerminal = true) {
    const terminal = vscode.window.activeTerminal;
    if (!terminal || terminal.name !== TERMINAL_NAME) {
      vscode.window.showErrorMessage("Opencode terminal not active. Run 'Opencode: Open Terminal' first.");
      return;
    }

    terminal.sendText(`opencode ${command}`);
    if (showTerminal) {terminal.show();}
  }

  function getWebviewContent(webview: vscode.Webview, extensionUri: vscode.Uri, port: number) {
    const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, "src", "webview.js"));
    const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, "src", "webview.css"));

    // Use a nonce to only allow specific scripts to run
    const nonce = getNonce();

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}'; connect-src http://localhost:${port};">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenCode AI</title>
    <link href="${styleUri}" rel="stylesheet">
</head>
<body>
    <div id="app">
        <div id="header">
            <div class="logo">🚀 OpenCode AI</div>
            <div class="status">Connecting...</div>
        </div>

        <div id="chat-container">
            <div id="messages"></div>
            <div id="input-container">
                <textarea id="message-input" placeholder="Ask me anything about your code..."></textarea>
                <button id="send-button">Send</button>
            </div>
        </div>

        <div id="toolbar">
            <button id="clear-btn" title="Clear conversation">🗑️</button>
            <button id="help-btn" title="Help">❓</button>
            <button id="settings-btn" title="Settings">⚙️</button>
        </div>
    </div>

    <script nonce="${nonce}" src="${scriptUri}"></script>
    <script nonce="${nonce}">
        // Initialize with server port
        window.OPENCODE_PORT = ${port};
    </script>
</body>
</html>`;
  }

  function getNonce() {
    let text = "";
    const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for (let i = 0; i < 32; i++) {
      text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
  }

  function getActiveFile() {
    const activeEditor = vscode.window.activeTextEditor;
    if (!activeEditor) {return;}

    const document = activeEditor.document;
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (!workspaceFolder) {return;}

    // Get the relative path from workspace root
    const relativePath = vscode.workspace.asRelativePath(document.uri);
    let filepathWithAt = `@${relativePath}`;

    // Check if there's a selection and add line numbers
    const selection = activeEditor.selection;
    if (!selection.isEmpty) {
      // Convert to 1-based line numbers
      const startLine = selection.start.line + 1;
      const endLine = selection.end.line + 1;

      if (startLine === endLine) {
        // Single line selection
        filepathWithAt += `#L${startLine}`;
      } else {
        // Multi-line selection
        filepathWithAt += `#L${startLine}-${endLine}`;
      }
    }

    return filepathWithAt;
  }
}
