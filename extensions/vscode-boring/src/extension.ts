import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as cp from 'child_process';

let statusBarItem: vscode.StatusBarItem;
let agentProcess: cp.ChildProcess | null = null;
let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
    console.log('Boring for Gemini is now active!');
    outputChannel = vscode.window.createOutputChannel("Boring AI");

    // Commands
    let startCmd = vscode.commands.registerCommand('boring.start', startAgent);
    let stopCmd = vscode.commands.registerCommand('boring.stop', stopAgent);
    let dashCmd = vscode.commands.registerCommand('boring.dashboard', openDashboard);

    context.subscriptions.push(startCmd, stopCmd, dashCmd);

    // Status Bar
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'boring.dashboard';
    context.subscriptions.push(statusBarItem);

    updateStatus('Idle', false);

    // Sidebar Provider
    const statusProvider = new BoringStatusProvider();
    vscode.window.registerTreeDataProvider('boring-status', statusProvider);
}

export function deactivate() {
    stopAgent();
}

function updateStatus(text: string, isActive: boolean) {
    statusBarItem.text = `$(hubot) Boring: ${text}`;
    if (isActive) {
        statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        statusBarItem.tooltip = "Agent is running";
        statusBarItem.show();
    } else {
        statusBarItem.backgroundColor = undefined;
        statusBarItem.tooltip = "Agent is idle";
        statusBarItem.show();
    }
}

function startAgent() {
    if (agentProcess) {
        vscode.window.showInformationMessage("Boring Agent is already running.");
        return;
    }

    const config = vscode.workspace.getConfiguration('boring');
    const pythonPath = config.get<string>('pythonPath') || 'python';
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;

    if (!workspaceRoot) {
        vscode.window.showErrorMessage("Please open a workspace folder first.");
        return;
    }

    outputChannel.show();
    outputChannel.appendLine(`Starting Boring Agent in ${workspaceRoot}...`);

    // Launch process
    agentProcess = cp.spawn(pythonPath, ['-m', 'boring', 'start'], {
        cwd: workspaceRoot,
        shell: true
    });

    agentProcess.stdout?.on('data', (data) => {
        outputChannel.append(data.toString());
    });

    agentProcess.stderr?.on('data', (data) => {
        outputChannel.append(data.toString());
    });

    agentProcess.on('close', (code) => {
        outputChannel.appendLine(`Agent exited with code ${code}`);
        agentProcess = null;
        updateStatus('Idle', false);
    });

    updateStatus('Running', true);
    vscode.window.showInformationMessage("Boring Agent started 🚀");
}

function stopAgent() {
    if (agentProcess) {
        agentProcess.kill();
        agentProcess = null;
        updateStatus('Stopped', false);
        vscode.window.showInformationMessage("Boring Agent stopped.");
    }
}

function openDashboard() {
    const config = vscode.workspace.getConfiguration('boring');
    const pythonPath = config.get<string>('pythonPath') || 'python';

    const term = vscode.window.createTerminal("Boring Dashboard");
    term.show();
    term.sendText(`${pythonPath} -m boring dashboard`);
}

// Tree Data Provider for Side Bar
class BoringStatusProvider implements vscode.TreeDataProvider<BoringItem> {
    getTreeItem(element: BoringItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: BoringItem): Thenable<BoringItem[]> {
        if (!element) {
            return Promise.resolve([
                new BoringItem('Status', vscode.TreeItemCollapsibleState.None, 'Idle', 'circle-outline'),
                new BoringItem('Circuit Breaker', vscode.TreeItemCollapsibleState.None, 'Closed', 'shield'),
                new BoringItem('Loops', vscode.TreeItemCollapsibleState.None, '0', 'sync'),
            ]);
        }
        return Promise.resolve([]);
    }
}

class BoringItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly description: string,
        iconName: string
    ) {
        super(label, collapsibleState);
        this.iconPath = new vscode.ThemeIcon(iconName);
    }
}
