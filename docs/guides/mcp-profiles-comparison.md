# 🎛️ MCP Profiles Deep Dive: Choosing the Right Mode

> **Deep Thinking Analysis**: MCP Profiles are not just about "hiding" tools; they are about **Context Budget Management**. 
> LLMs have fixed attention spans. Feeding 100+ tools (~10k tokens) to a model distracts it. 
> Profiles allow you to match the **Tool Density** to the **Task Complexity** and **Model Capability**.

This guide provides a detailed breakdown of each profile, its ideal usage points, and trade-offs.

---

## 📊 Quick Comparison

| Profile | Tools | Use Case | Ideal Model Tier | Token Cost |
| :--- | :--- | :--- | :--- | :--- |
| **`ultra_lite`** | 3 | **Gateway** / Chat-heavy | Low (e.g., Llama 3 8B) | 🟢 Extremely Low |
| **`minimal`** | 8 | **Safety Ops** / CI | Medium | 🟢 Low |
| **`lite`** | 20 | **Daily Coding** (Recommended) | High (Claude 3.5, Gemini 1.5) | 🟡 Balanced |
| **`standard`** | 50 | **Architecture** / Management | Very High | 🟠 High |
| **`full`** | All | **Unified Intelligence** / Debug | Ultra (Gemini 1.5 Pro, Opus) | 🔴 Very High |

---

## 🛠️ Deep Dive by Profile

### 1. `ultra_lite` (The Gateway)
**Concept**: "Progressive Disclosure".
The agent knows *nothing* initially except how to discover tools. It asks for tool definitions only when it needs them.

*   **✅ Usage Point**: 
    *   **Cost Optimization**: When you are paying per input token and want to minimize prompt size.
    *   **Small Models**: Using local 7B/8B models that get confused by large tool definitions.
    *   **Chat Focus**: When the session is 90% discussion and only 10% action.
*   **❌ Limitations**: 
    *   **High Latency**: Every tool use requires 2 steps (Discover -> Execute).
    *   **No Spontaneity**: The agent won't "accidentally" use a helpful tool it doesn't know exists.

### 2. `minimal` (The Guard)
**Concept**: "Read-Only / Safety First".
Provides enough tools to *see* and *verify* the project, but limits generative capabilities.

*   **✅ Usage Point**:
    *   **Project Auditing**: "Read the code and tell me if it's safe."
    *   **CI/CD Pipelines**: Automated checks where you don't want the agent getting creative.
    *   **Quick Fixes**: Simple git commits or vibe checks.
*   **❌ Limitations**:
    *   Cannot review code (no `code_review`).
    *   Cannot write tests (no `test_gen`).

### 3. `lite` (The Daily Driver) 🌟
**Concept**: "The Pareto Optimal".
Contains the 20 tools that do 80% of the work. Designed to fit comfortably in a 128k context window while leaving space for files.

*   **✅ Usage Point**:
    *   **Feature Development**: "Add a login page." (Uses `write_file`, `rag_context`, `code_review`).
    *   **Refactoring**: "Clean up this class."
    *   **TDD**: "Write tests for this function."
    *   **Default Choice**: Start here. Only switch if you hit a limit.
*   **❌ Limitations**:
    *   Lacks administrative tools (workspace management, git hooks).
    *   Lacks multi-agent simulation.

### 4. `standard` (The Architect)
**Concept**: "Project Manager".
Expands scope to include repository management, security administration, and deeper analysis.

*   **✅ Usage Point**:
    *   **Repository Setup**: Installing Git hooks, configuring Shadow Mode.
    *   **Deep Research**: Using full RAG expansion (`rag_expand`) to understand complex dependencies.
    *   **Multi-Agent Flows**: Running `boring_multi_agent` to simulate user behaviors.
    *   **Spec Writing**: Using `speckit_*` tools to clarify requirements.
*   **❌ Limitations**:
    *   Significantly higher token usage.

### 5. `full` (God Mode)
**Concept**: "Raw Unfiltered Access".
Exposes **EVERY** registered tool in the system, including experimental, legacy, and debugging tools. nothing is hidden.

*   **✅ Usage Point**:
    *   **Maximum Context Models**: When using **Gemini 1.5 Pro (2M)** or **Claude 3 Opus** where 50k tokens of system prompt is negligible.
    *   **Plugin Development**: When you are developing *new* Boring tools and want to test them immediately without configuring a profile.
    *   **Experimental Features**: Accessing bleeding-edge tools that haven't graduated to `Standard` yet.
    *   **"I Can't Find It"**: When you know a tool exists but isn't in your profile, switch to Full to find it.
*   **⚠️ Critical Warning**:
    *   **Hallucinations**: 100+ tools increase the chance of the LLM picking the wrong one (e.g., confusing `verify` with `verify_file`).
    *   **Cost**: Extremely expensive on per-token billing models.
    *   **Performance**: Slower "Thinking" (preprocessing large tool definitions).

---

## ⚙️ Configuration

### Switching Profiles
You can switch profiles dynamically based on your current task's needs.

#### 1. Environment Variable (Global)
```bash
export BORING_MCP_PROFILE=lite
```

#### 2. Project Config (`.boring.toml`)
```toml
[boring]
# Persist the setting for this project
profile = "standard"
```

#### 3. Runtime Switch (VS Code / Cursor)
1. Open User Settings (JSON).
2. Find `"mcpServers"`.
3. Edit the `env` section for `boring`.
4. **Restart** the MCP server (Developer: Reload Window).

---

## 💡 Recommendation
Start with **`lite`**.
- If you find the model "hallucinating" tools that don't exist -> Switch to **`standard`**.
- If you find the model is "slow" or "expensive" -> Switch to **`minimal`** or **`ultra_lite`**.
- If you are doing deep R&D or using Gemini 1.5 Pro -> Switch to **`full`**.
