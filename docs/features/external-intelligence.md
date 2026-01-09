# 🧠 External Intelligence

> Make Boring not just code, but possess "Real-time Knowledge" and "Deep Thinking" capabilities.

Boring integrates the most powerful MCP tools by default, giving your AI Agent superpowers.

---

## 📚 Context7: Your Real-time Documentation Library

**Pain Point**: AI models have training data cutoffs and don't know the latest API changes (e.g., Next.js 14, Stripe API updates).
**Solution**: Context7 is a real-time RAG service specifically for technical documentation.

### ✨ Key Features
- **Real-time Queries**: `context7_query_docs` fetches the latest library usage.
- **Precise Parsing**: Automatically finds the most relevant Code Snippets.
- **Seamless Integration**: Boring's `boring-route` determines when external docs are needed.

### 💡 Use Case
When you ask: "How to use the latest LangChain v0.2 LCEL?"
1. Agent detects training data might be stale.
2. Automatically calls `context7` to query LangChain v0.2 docs.
3. Generates correct code based on the latest docs, not old patterns.

---

## 🤔 Thinking Tools: Deep Thinking Engine

Boring integrates two powerful thinking modes, forcing the Agent to "think clearly" before coding.

### 1. Sequential Thinking
**Use Case**: Complex refactoring, architecture design, multi-step tasks.

It forces the Agent into a "Chain of Thought":
- Step 1: Analyze status
- Step 2: Formulate hypothesis
- Step 3: Verify hypothesis...
- Only starts coding after thinking is complete.

### 2. Critical Thinking
**Use Case**: Code Review, bug hunting, security audit.

It teaches the Agent "Self-Doubt":
- "Does this solution have side effects?"
- "Is there a more efficient way?"
- "Are edge cases considered?"

---

## 🛠️ Zero Config: One-Click Integration

**You DO NOT need to manually download or install these external tools!**

Boring uses an "All-in-One" design. Core features are built-in, and external intelligence is managed via a one-click extension mechanism.

### How to Enable?

1.  **Initialize Extensions** (Run once):
    ```bash
    # In CLI
    boring setup-extensions
    ```
    Or ask the Agent in chat:
    > "Help me setup extensions"
    > (Agent will call `boring_setup_extensions()` tool)

2.  **Auto-Configuration**:
    Boring will automatically:
    - Download necessary MCP Servers (`context7`, `criticalthink`, `sequential-thinking`)
    - Configure API Keys and environment variables
    - Update configuration to enable them

3.  **Ready to Use**:
    Once setup, these tools appear automatically in the Agent's toolbox.
    You can ask directly in chat:
    > "Please use **Sequential Thinking** to plan this refactor."
    > "Please use **Context7** to check the new React 19 Hooks."

This way, you get not just code, but high-quality output that has been "thought through" and "verified".
