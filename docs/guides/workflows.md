# Agentic Workflows (Slash Commands)

> Automate complex multi-step processes with pre-defined AI recipes.

---

## 🤖 What are Agentic Workflows?

Agentic Workflows are specialized markdown files located in your `.agent/workflows/` directory. They act as **Standard Operating Procedures (SOPs)** for the AI agent. Instead of giving long, repetitive instructions, you can simply trigger a workflow.

### Key Benefits
- **Consistency**: Every release or feature follow the exact same steps.
- **Automation**: Workflows can include shell commands that the AI executes for you.
- **Organization**: Complex checklists are managed separately from your code.

---

## ⚡ How to Trigger a Workflow

You can activate any workflow by using a **Slash Command** in your chat. 

For example, if you have `release-prep.md` in `.agent/workflows/`:
1.  In the chat, type: `/release-prep`
2.  Boring will detect the command, load the file, and start working through the checklist.

---

## 📂 The `release-prep.md` Example

This is a built-in workflow designed to prepare your project for a new version tag.

### What it does:
1.  **Version Bump**: Prompts to update `pyproject.toml` and init files.
2.  **Doc Sync**: Reminds to update changelogs and README badges.
3.  **Verification**: Automatically runs `boring verify` to ensure the release is stable.
4.  **Git Ops**: Prepares the staging and tagging commands.

---

## 🛠️ Creating Your Own Workflow

Simply create a new `.md` file in `.agent/workflows/`.

### Template: `my-task.md`
```markdown
---
description: Short description of the command
---

# My Custom Task

Detailed instructions for the AI to follow...

1.  [ ] Check file A
2.  [ ] Run `npm test`
3.  [ ] Report results
```

Now you can run it by typing `/my-task`.

---

## 💡 Best Practices

- **Use Checkboxes**: `[ ]` helps the AI track state across multiple steps.
- **Include Commands**: If a step requires `run_command`, explicitly write it out.
- **Bilingual Support**: If your team is international, you can have `my-task_zh.md` as well.
