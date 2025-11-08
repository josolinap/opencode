import * as assert from "assert";
import * as vscode from "vscode";

// You can import and use all API from the 'vscode' module
// as well as import your extension to test it
// const myExtension = require('../extension');

suite("Extension Test Suite", () => {
  vscode.window.showInformationMessage("Start all tests.");

  test("Sample test", () => {
    assert.strictEqual(-1, [1, 2, 3].indexOf(5));
    assert.strictEqual(-1, [1, 2, 3].indexOf(0));
  });

  test("GUI Panel Command Registration", async () => {
    // Test that the GUI panel command is registered
    const commands = await vscode.commands.getCommands(true);
    assert.ok(commands.includes("opencode.openGuiPanel"), "GUI panel command should be registered");
  });
});
