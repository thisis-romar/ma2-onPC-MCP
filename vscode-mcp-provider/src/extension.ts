import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    context.subscriptions.push(
        vscode.lm.registerMcpServerDefinitionProvider('gma2-mcp-telnet.mcp-servers', {
            provideMcpServerDefinitions: async () => [
                new vscode.McpStdioServerDefinition(
                    'grandMA2 MCP',
                    'uv',
                    ['run', 'python', '-m', 'src.server'],
                    {}, // Optionally pass .env variables here
                    '1.0.0'
                )
            ]
        })
    );
}

export function deactivate() {}
