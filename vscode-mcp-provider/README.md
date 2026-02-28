# VSCode MCP Provider

This extension registers your grandMA2 MCP server for AI assistants in VS Code using the Model Context Protocol (MCP) stdio transport.

## Features
- Registers the MCP server for discovery by compatible AI assistants (Claude, Copilot when supported, etc.)
- Launches the server using `uv run python -m src.server` in your workspace directory

## Usage
1. Open your workspace in VS Code.
2. Build and install this extension.
3. Compatible AI assistants will discover and connect to your MCP server automatically.

## Development
- Main activation code: `src/extension.ts`
- MCP server definition provider registered in `package.json`

## Requirements
- Node.js, npm, and VS Code
- Your Python environment and dependencies set up for the MCP server

---
MIT License
