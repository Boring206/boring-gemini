# Knowledge & Brain Management Guide

> How to manage, backup, and share Boring's intelligence.

---

## 🧠 What is the "Brain"?

Boring stores its persistent intelligence in a dedicated directory called `.boring/brain` (usually located in your project root or user home). This directory contains:

1.  **Learnings (`learnings.json`)**: Captured error-solution patterns.
2.  **RAG Index (ChromaDB)**: Vector metadata of your codebase.
3.  **Context**: History of your plans and progress.

---

## 💾 Backup & Migration

### Sharing Progress with a Team
To allow a team member to benefit from what Boring has already learned:
1.  **Copy metadata**: Share the `.boring/brain/learnings.json` file.
2.  **Import**: The colleague can place this file in their local `.boring/brain/` directory.

### Migrating across Projects
If you start a new project similar to an old one, you can bootstrap it by copying the `learnings.json`.

---

## 🔄 RAG Index Management

The RAG index ensures Boring "knows" where everything is. If your codebase changes significantly and Boring seems confused:

### Reconstruction
```bash
boring rag-reindex --force
```
This will delete the old vector storage and perform a fresh scan.

---

## 🧹 Resetting the Brain

If you want Boring to start with a clean slate (forgetting all previous errors and fixes):
1.  **Stop Boring**.
2.  **Delete the directory**: `rm -rf .boring/brain`
3.  **Restart**: Boring will re-initialize a fresh "infant" brain.

---

## 💡 Best Practices

- **Periodic Backups**: Commit your `.boring/brain/learnings.json` (if small) to Git if you want to track how the project's knowledge evolves.
- **Selective Learning**: Use the `boring_learn` tool explicitly if you find a very clever fix that you want the agent to remember forever.
