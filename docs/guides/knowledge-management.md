# Knowledge & Brain Management Guide

> How to manage, backup, and share Boring's intelligence.

---

## 🧠 What is the "Brain"?

Boring stores its persistent intelligence in a dedicated directory called `.boring/brain` (usually located in `~/.boring/brain`). This directory contains:

1.  **Learnings (`patterns/`)**: Captured error-solution patterns.
2.  **Rubrics (`rubrics/`)**: Project-specific quality criteria.
3.  **Shadow Config**: Global Shadow Mode settings.

---

## 💾 Backup & Migration

### Sharing Progress with a Team
To allow a team member to benefit from what Boring has already learned:
1.  **Export patterns**: Use `boring_global_export` to share specific patterns.
2.  **Import**: The colleague can use `boring_global_import`.

### Migrating across Projects
Starting in V10.31, **Active Recall** automatically handles cross-project knowledge retrieval from the global brain.

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

- **Periodic Backups**: Knowledge in `~/.boring/brain/` is global. Keep it safe!
- **Selective Learning**: Use the `boring_learn_pattern` tool explicitly if you find a very clever fix that you want the agent to remember forever.
