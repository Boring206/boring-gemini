# ⚡ Prompts & Workflows Reference

This is the **complete reference** for all available MCP Prompts and Workflows in Boring. 

- **Prompts**: Accessed via your IDE's prompt selector (e.g., `Cmd+I` or `✨` button).
- **Workflows**: Accessed via slash commands in Chat (e.g., `/release-prep`).

---

## 🚀 Startup & Planning (專案啟動與規劃)

| Command / Prompt | Type | Description | Best Usage Scenario |
| :--- | :--- | :--- | :--- |
| **`vibe_start`** | Prompt | **One-Click Project Kick-off**. A guided architect workflow that leads you from a vague idea to a structured project plan. | Starting a new project or a major complex feature. |
| **`setup_project`** | Prompt | **Project Initialization**. Guides you through running quickstart, installing hooks, and health checks. | Setting up a fresh repository for the first time. |
| **`/speckit-constitution`** | Workflow | **Establish Principles**. Creates a `constitution.md` to define non-negotiable rules for the project. | First step of any new repository to set coding standards. |
| **`/speckit-clarify`** | Workflow | **Requirement Clarification**. Analyzes your request and asks 3-5 critical questions to clear ambiguity. | When requirements are vague or you're unsure where to start. |
| **`/speckit-plan`** | Workflow | **Technical Planning**. Converts requirements into a detailed technical implementation plan. | After requirements are clear, before writing any code. |
| **`plan_feature`** | Prompt | **Feature Spec Generator**. Generates a detailed implementation plan for a specific new feature. | When adding a single feature to an existing project. |
| **`/speckit-tasks`** | Workflow | **Task Breakdown**. Converts the implementation plan into a checklist in `task.md`. | Ready to start coding? Run this to generate your to-do list. |
| **`roadmap`** | Prompt | **Roadmap Visualizer**. Analyzes `task.md` and generates a Mermaid Gantt/Flowchart of progress. | reviewing project timeline and next major milestones. |
| **`suggest_roadmap`** | Prompt | **Next Steps Suggestion**. AI suggests the next logical features or technical improvements to work on. | When you're stuck or looking for what to build next. |

## 🏗️ Development & Building (開發與建置)

| Command / Prompt | Type | Description | Best Usage Scenario |
| :--- | :--- | :--- | :--- |
| **`full_stack_dev`** | Prompt | **Full Stack Workflow**. Specialized guides for building Frontend + Backend + DB applications. | Building a web application from scratch. |
| **`run_agent`** | Prompt | **Multi-Agent Task**. Orchestrates multiple AI agents (Architect, Coder, Reviewer) to solve a complex task. | Handing off a large, self-contained task to the AI. |
| **`smart_commit`** | Prompt | **Semantic Commit**. Generates a conventional commit message based on your `task.md` progress. | When you are ready to save your changes. |
| **`vibe_check`** | Prompt | **Project Health Check**. Analyzes project structure, docs, and "vibe" (cleanliness), giving a 0-100 score. | When you want a quick sense of the project's state. |
| **`system_status`** | Prompt | **System Status**. Shows current loop status, active background tasks, and general health. | Debugging why the agent seems busy or checking progress. |

## 🛡️ Quality & Verification (品質與驗證)

| Command / Prompt | Type | Description | Best Usage Scenario |
| :--- | :--- | :--- | :--- |
| **`review_code`** | Prompt | **Architect Review**. Deep code review focusing on architecture, security, and performance nuances. | Before merging code or when you finished a module. |
| **`/speckit-checklist`** | Workflow | **Quality Checklist**. Generates a specific checklist to verify if the implementation meets requirements. | Before marking a task as "Done". |
| **`/speckit-analyze`** | Workflow | **Consistency Check**. Ensures that your Code, Plan, and Specs are consistent with each other. | When requirements change or after major refactoring. |
| **`security_scan`** | Prompt | **Security Audit**. Scans for secrets, vulnerabilities (SAST), and bad dependencies. | Before release or periodically during dev. |
| **`evaluate_architecture`** | Prompt | **Hostile Architect**. A strict review that focuses solely on scalability, coupling, and design risks. | Early in the design phase or during major refactors. |
| **`evaluate_code`** | Prompt | **LLM Judge**. Scores code quality based on a specific rubric (Correctness, readability, etc.). | Objective quality assessment. |
| **`compare_implementations`**| Prompt | **A/B Testing**. Compares two different code paths/versions and declares a winner. | Deciding between two refactoring approaches. |
| **`audit_quality`** | Prompt | **Full System Audit**. Runs Health + Security + Verification checks all at once. | Pre-flight check before a major deployment. |

## 🔧 Maintenance & Refactoring (維護與重構)

| Command / Prompt | Type | Description | Best Usage Scenario |
| :--- | :--- | :--- | :--- |
| **`quick_fix`** | Prompt | **Auto-Fixer**. Automatically diagnosis and fixes lint errors, format issues, and simple bugs. | When you have red squiggly lines or failing lint checks. |
| **`debug_error`** | Prompt | **Root Cause Analysis**. Analyzes an error message/stack trace to find the root cause and suggest logic fixes. | When you hit a bug or crash. |
| **`refactor_code`** | Prompt | **Refactoring**. Suggests improvements for code clarity, performance, and structure. | When code works but looks messy ("Code Smell"). |
| **`/release-prep`** | Workflow | **Release Protocol**. Handle version bumping, changelog updates, and release checks. | When you are ready to publish a new version. |
| **`safe_refactor`** | Prompt | **Transactional Refactor**. Performs changes in a "Sandbox" that can be auto-rolled back if verification fails. | Execution risky changes where you want a safety net. |
| **`rollback`** | Prompt | **Undo Changes**. Reverts the codebase to the last safe state (requires Transaction usage). | When a `safe_refactor` attempt goes wrong. |
| **`verify_work`** | Prompt | **Manual Verification**. Explicitly triggers the verification workflow (Tests + Linting). | When you want to double-check everything is green. |

## 🧠 Knowledge & Context (知識與上下文)

| Command / Prompt | Type | Description | Best Usage Scenario |
| :--- | :--- | :--- | :--- |
| **`explain_code`** | Prompt | **Code Tutor**. Explains how a specific file or function works in plain language. | Onboarding to a new codebase. |
| **`visualize`** | Prompt | **Diagram Gen**. Generates Mermaid.js diagrams (Class, Sequence, Flow) for code. | Visualizing complex dependencies. |
| **`visualize_architecture`**| Prompt | **Arch Visualization**. Generates high-level module dependency diagrams. | Understanding the big picture of the system. |
| **`semantic_search`** | Prompt | **Deep Search**. Uses RAG to find code based on meaning, not just keywords. | "Where is the auth logic?" |
| **`project_brain`** | Prompt | **Knowledge Base**. Summarizes what the AI has learned about this project (patterns, rules). | Checking what the AI knows about your project context. |
| **`manage_memory`** | Prompt | **Memory Management**. Consolidates learned patterns and updates evaluation rubrics. | After a long coding session to "save" learnings. |

## ⚙️ Workspace & Session Management (工作區與會話)

| Command / Prompt | Type | Description | Best Usage Scenario |
| :--- | :--- | :--- | :--- |
| **`save_session`** | Prompt | **Save Context**. Saves your current working files and conversation state to a named slot. | Switching context or taking a break. |
| **`load_session`** | Prompt | **Load Context**. Restores a previously saved session. | Resuming work on a specific feature. |
| **`switch_project`** | Prompt | **Switch Project**. Changes the active Boring workspace to another registered project. | Working on multi-repo setups. |
| **`add_project`** | Prompt | **Register Project**. Adds a new directory to the Boring workspace registry. | Importing an existing project into Boring. |
| **`shadow_review`** | Prompt | **Shadow Mode Admin**. Review/Approve/Reject pending high-risk operations. | When Shadow Mode blocks an action you need to perform. |

## 🧩 Advanced / Plugins

| Command / Prompt | Type | Description | Best Usage Scenario |
| :--- | :--- | :--- | :--- |
| **`run_plugin`** | Prompt | **Execute Plugin**. Runs a specific installed Boring plugin. | Using 3rd party extensions. |
| **`create_plugin`** | Prompt | **Plugin Scaffolding**. Generates template code for a new Boring plugin. | Extending Boring's capabilities. |
| **`background_verify`** | Prompt | **Async Verify**. Runs verification in the background (returns a Task ID). | Validating huge codebases without blocking the chat. |
| **`background_test`** | Prompt | **Async Test**. Runs tests in the background. | Running long test suites. |
