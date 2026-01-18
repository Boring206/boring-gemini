# Boring Pack Format Specification (.boring-pack)

> **Version**: 1.0.0  
> **Status**: Draft  
> **Date**: 2026-01-18

Boring Pack is the standard distribution format for the Boring-Gemini ecosystem. It is not just Python code, but a "Cognitive Container" that includes tools, workflows, prompts, and knowledge.

## 📦 What is a Boring Pack?

A Boring Pack is a standardized directory structure (usually compressed as ZIP) containing:
1. **Tools**: Python implementations of extensions.
2. **Workflows**: Standard Operating Procedures (.md) defining agent behavior.
3. **Prompts**: Expert-level prompt templates.
4. **Knowledge (Brain)**: Pre-indexed domain knowledge.

## 📂 Directory Structure

```text
my-awesome-pack/
├── boring-pack.json       # Manifest (Required)
├── README.md              # Documentation
├── LICENSE                # License file
├── requirements.txt       # Python dependencies
├── tools/                 # Python Plugin Code
│   ├── __init__.py
│   └── my_tool.py
├── workflows/             # Agent Workflows
│   └── deploy_flow.md
├── prompts/               # Prompt Templates
│   └── system_prompt.md
├── brain/                 # Knowledge Base (Optional)
│   └── knowledge.parquet
└── assets/                # Images/Icons
    └── icon.png
```

## 📄 Manifest Schema (boring-pack.json)

```json
{
  "spec_version": "1.0",
  "id": "boring/full-stack-pack",
  "version": "1.0.0",
  "name": "Full Stack Developer Pack",
  "description": "A complete suite for Full Stack development.",
  "author": "Boring Team",
  "license": "Apache-2.0",
  "homepage": "https://github.com/boring/pack",
  
  "min_boring_version": "15.0.0",
  
  "components": {
    "tools": ["tools/"],
    "workflows": ["workflows/"],
    "prompts": ["prompts/"],
    "brain": ["brain/"]
  },
  
  "permissions": [
    "filesystem:read",
    "network:http"
  ]
}
```

## 🛠️ Component Details

### Tools
Standard Boring Plugin syntax using the `@plugin` decorator. The Pack Loader automatically loads all modules under the `tools/` directory.

### Workflows
Markdown format workflow definitions. Once installed, users can execute them via `boring flow run <workflow_name>`.

### Prompts
Text or Markdown format. Once installed, Agents can reference them in conversation, e.g., `@prompt:system_prompt`.

### Brain
Pre-computed vector data. Upon installation, users will be asked whether to merge this into their Global Brain.

## 🚀 Packaging & Distribution

### Packing
Use the `boring pack` command to bundle a directory into a `.boring-pack` (ZIP format).
```bash
boring pack . --output my-pack.boring-pack
```

### Installing
Use the `boring install` command:
```bash
# From GitHub (Source)
boring install https://github.com/user/my-pack

# From Local File (Pack)
boring install ./my-pack.boring-pack
```

### Security
When installing a Pack, the system displays the requested permissions (`permissions` field) and asks for user confirmation.
In Strict Mode, unsigned Packs requesting dangerous permissions may be rejected.
