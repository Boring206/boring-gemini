# Node.js Autonomy

The **Node.js Autonomy** feature ensures that Boring can operate its advanced AI tools even if Node.js is not globally installed on your system.

## Overview

Boring relies on the `gemini-cli` (and other npm-based MCP servers) to provide many of its advanced capabilities. For users who do not have Node.js installed, or are on restricted systems, Boring can now automatically download and manage a **portable** Node.js environment.

## Key Features

- **System-First Strategy**: Boring always prioritizes your existing system Node.js and npm installations.
- **Portable Fallback**: If Node.js is missing or incompatible, Boring offers to download a portable v20 LTS version into `~/.boring/node`.
- **Zero Configuration**: The `boring wizard` handles the detection and installation process automatically.
- **Isolation**: The portable installation is kept separate from your system folders, preventing version conflicts with other projects.
- **One-Click Maintenance**: Health checks will alert you if your environment needs updating and provide a quick fix command.

## How it Works

When you run `boring wizard` or a command that requires Node.js, the `NodeManager` service:
1. Checks for `node` and `npm` in your system PATH.
2. If not found, it checks `~/.boring/node`.
3. If still missing, it prompts for a download (~100MB).
4. Extract the binary and configures the environment for internal use.

## Commands

- `boring wizard`: Run the setup wizard to trigger environment detection.
- `boring health`: Check if Boring is using a **System** or **Portable** Node.js installation.
