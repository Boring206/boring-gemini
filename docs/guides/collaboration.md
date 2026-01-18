# Serverless Collaboration Guide

> **Philosophy**: Zero Infrastructure, Infinite Scaling.
> Boring-Gemini uses Git as the universal backend for code, state, and knowledge.

## 1. Plugin Ecosystem (The "App Store")

In Boring, the "App Store" is just GitHub. You don't need a central server to publish or install extensions.

### Installing Plugins
Install any plugin directly from a Git URL:
```bash
boring install https://github.com/boring/security-scanner
# Or short syntax
boring install boring/security-scanner
```

### Creating & Sharing Packs
Bundle your tools, prompts, and workflows into a single `.boring-pack` file:

1. **Initialize**: `boring pack init --name my-awesome-pack`
2. **Build**: `cd my-awesome-pack && boring pack build`
3. **Share**: Upload the `.boring-pack` file to GitHub Releases, or push the repo directly.

## 2. Knowledge Sharing (The "Brain")

Your agent learns as it works. You can transfer this learning to your teammates.

### Exporting Knowledge
Export your Vector Database (ChromaDB) to a portable file:
```bash
boring brain export --output team-knowledge.boring-brain
```

### Importing Knowledge
Your teammate can import this knowledge. It will **merge** with their existing brain, not overwrite it.
```bash
boring brain import team-knowledge.boring-brain
```

## 3. Team Synchronization (GitOps)

Collaborate on the same project without conflicts using `boring sync`. This command handles the complex dance of synchronizing SQLite state via Git.

### How it Works
1. **Export**: Boring dumps its internal SQLite state (tasks, milestones) to `.boring/sync/state.json`.
2. **Git**: It commits this JSON file and pulls changes from your team.
3. **Merge**: It intelligently merges your team's state into your local SQLite.
4. **Push**: It pushes your updates.

### Usage
Simply run this command frequently:
```bash
boring sync
```

You can also add a message:
```bash
boring sync -m "Completed the auth module"
```

## Summary

| Feature | Command | Backend |
|---------|---------|---------|
| **Code** | `git push/pull` | Git |
| **State** | `boring sync` | Git + JSON |
| **Plugins** | `boring install` | Git / HTTP |
| **Knowledge** | `boring brain` | Zip / File |

This architecture ensures you own your data, and rely on $0 external infrastructure.
