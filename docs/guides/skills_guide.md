# Agent Skills Guide (Universal System)

## Overview

Boring V12.3 introduces the **Universal Skills System (BUSS)**. This system unifies skill management across multiple AI platforms, allowing you to use the same skills in **Gemini CLI**, **Claude Code**, **Antigravity**, and **Boring Flow**.

### Key Features

1.  **Write Once, Run Anywhere**: Skills written in standard Markdown (`SKILL.md`) work across all supported platforms.
2.  **Local "Brain"**: Skills are stored locally in your project, giving the agent persistent, project-specific expertise.
3.  **Auto-Sync**: Skills created or downloaded via Boring are automatically synchronized to `.gemini/skills` and `.claude/skills` directories.
4.  **Flow Integration**: The Boring Flow Engine automatically discovers and uses these skills during autonomous execution.

---

## Universal Skill Structure

A Universal Skill is simply a directory containing a `SKILL.md` file with a YAML frontmatter header.

**File Path**: `.boring/skills/my-skill/SKILL.md`

```markdown
---
name: my-skill
description: A clear description of what this skill does. The Agent uses this to activate it.
---

# My Skill Title

## Instructions
1. Step one...
2. Step two...

## Rules
- Always do X...
- Never do Y...
```markdown
---
name: my-skill
description: A clear description of what this skill does. The Agent uses this to activate it.
---

# My Skill Title

## Instructions
1. Step one...
2. Step two...

## Rules
- Always do X...
- Never do Y...
```

### Advanced Directory Structure (OpenAI Codex / SkillsMP Compatible)

For more complex skills, you can use the standard directory structure which Boring automatically detects:

```text
my-skill/
├── SKILL.md        (Required: Instructions & Metadata)
├── scripts/        (Optional: Executable Python/Bash scripts)
├── references/     (Optional: PDF/Text documentation)
└── assets/         (Optional: Templates, Images, Resources)
```

**Boring automatically exposes:**
- Scripts in `scripts/` are listed in the activation prompt.
- Documents in `references/` are listed as available context.


---

## Managing Skills

### 1. Discovering Skills
Boring automatically scans the following directories for skills:
- `.boring/skills/` (Primary Hub)
- `.antigravity/skills/`
- `.gemini/skills/`
- `.claude/skills/`

Use the command (or let the Agent use it):
```python
boring_skill_discover()
```

### 2. Creating a Skill
You can ask the Agent to create a skill for you:
> "Create a skill for reviewing python code security"

Or manually create one using the template above.

### 3. Downloading Skills (The "App Store")
You can download verified skills from trusted community repositories:

```python
boring_skill_download(url="https://github.com/boring-stack/skill-python-expert")
```

This will:
1. Download the skill to `.boring/skills/python-expert`
2. **Auto-Sync**: Copy it to `.gemini/skills/` and `.claude/skills/` so your other tools can use it too!

### 4. Direct Activation
The Agent can activate a skill dynamically based on need:

```python
boring_skill_activate(skill_name="code-reviewer")
```

---

## Best Practices

- **Descriptive Names**: Use hyphen-case (e.g., `api-designer`, `bug-hunter`).
- **Clear Descriptions**: The `description` field in the frontmatter is the **most important** part. It's what the AI "sees" before loading the full skill. Make it precise.
- **Atomic Expertise**: Keep skills focused on a single domain or task.

## Legacy Catalog
The old `Boring Skills Catalog` (`boring_skills_install`) is still available for backward compatibility and for discovering external tool-based extensions.
