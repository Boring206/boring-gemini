# Appendix C: Architect Prompt Design Philosophy

> **Core Principle**: Boring is not a code generator—it's a **Senior Architect Mentor** that prevents technical debt before it happens.

---

## The Problem with Traditional AI Coding

Most AI coding assistants follow this pattern:

```
User: "Write a function to fetch users"
AI: *writes code*
User: "It's slow"
AI: *patches the symptom*
```

**Result**: Accumulated technical debt, band-aid fixes, no learning.

---

## The Architect-First Approach

Boring inverts this pattern:

```
User: "Write a function to fetch users"
Architect: "Before I write code, let me ask:
  - How many users? (10? 10M?)
  - Real-time or cached?
  - What's your consistency requirement?"
  
*After understanding context*

Architect: "I recommend:
  1. Paginated queries (not SELECT *)
  2. Redis cache with TTL
  3. Circuit breaker for DB failures
  
Here's the implementation..."
```

**Result**: Production-ready code from day one.

---

## Prompt Engineering Principles

### 1. Persona-Based Prompts

Each prompt defines a **strong persona** that shapes behavior:

```python
# Instead of:
"Please help debug this error"

# We use:
"You are a Senior Architect helping debug an issue.
Your Analysis Must Include:
1. Root Cause
2. Likely Culprits
3. Suggested Fix
4. 🏛️ Architecture Lesson:
   - Why did this happen? (Design flaw?)
   - How to prevent this class of errors permanently?"
```

The persona creates **consistency** and **depth**.

---

### 2. Proactive Guidance Rules

Prompts include explicit instructions to be proactive:

```python
"**Proactive Advice Rule**:
If you see a naive implementation (e.g., using a list for lookups), 
DON'T just say 'fix it'.

Say: '⚠️ **Architecture Risk**: This is O(N). In production, this will 
kill the CPU. **Mandatory Refactor**: Use a Set or HashMap (O(1)).'

Be direct. Be strict. Save the user from future pain."
```

This prevents the AI from being too polite or passive.

---

### 3. Structured Output Requirements

Every prompt defines what the output MUST include:

```python
"完成後提供摘要報告，包含：
- 已實作功能清單
- 🏛️ 架構決策記錄 (ADR)
- 潛在改進建議"
```

This ensures **actionable, complete responses**.

---

### 4. Checkpoint Architecture

Complex workflows have explicit checkpoints:

```python
"**Phase 2: 架構規劃 (Architect Checkpoint ✅)**
3. 使用 `speckit_plan` 根據需求生成實作計畫
4. 🏛️ **架構審查**：我會檢查計畫中的潛在設計問題（如過度耦合、缺少抽象層）"
```

Checkpoints force **reflection before action**.

---

## The Four Architect Personas

### 1. Chief Architect (Code Review)

**Used in**: `review_code` prompt

**Traits**:
- Looks for Architecture Smells, not just bugs
- Identifies God classes, tight coupling
- Suggests patterns (Circuit Breaker, DI)

**Example Output**:
```
⚠️ **Architecture Risk**: Synchronous API call in loop.
This will timeout under load. Use async/batch processing.
```

---

### 2. Senior Architect (Debugging)

**Used in**: `debug_error` prompt

**Traits**:
- Finds root cause, not just symptoms
- Provides Architecture Lesson
- Teaches prevention strategies

**Example Output**:
```
🏛️ Architecture Lesson:
This error happens because you're not using Dependency Injection.
The DB connection is hardcoded, making it impossible to mock.
Refactor to inject the connection via constructor.
```

---

### 3. Principal Architect (Evaluation)

**Used in**: `evaluate_architecture` prompt

**Traits**:
- Hostile/Critical stance
- Focuses on production concerns (10k RPS, failure modes)
- Ignores style issues, focuses on scalability

**Example Output**:
```
⚠️ **Scalability Bottleneck**: This HashMap is not thread-safe.
At 10k RPS, you'll see data corruption.
**Mandatory Refactor**: Use ConcurrentHashMap or add synchronization.
```

---

### 4. Mentor Architect (Vibe Coding)

**Used in**: `vibe_start` prompt

**Traits**:
- Guides through full workflow
- Inserts checkpoints for human review
- Produces Architecture Decision Records (ADR)

**Example Output**:
```
🏛️ 架構決策記錄 (ADR):
- Decision: 使用 PostgreSQL 而非 MongoDB
- Rationale: 需要 ACID transactions, 關聯查詢
- Consequences: 需要管理 schema migrations
```

---

## Key Design Patterns

### Pattern 1: "Don't Just Say Fix It"

```
❌ "This function is slow. Consider optimizing."
✅ "⚠️ This function is O(N²). At 10k users, this takes 100M operations.
   **Mandatory Refactor**: Pre-sort the list and use binary search (O(N log N))."
```

---

### Pattern 2: Architecture Lesson Block

Every debugging response includes:

```
🏛️ Architecture Lesson:
- Why did this happen? [Design flaw explanation]
- How to prevent permanently? [Pattern/abstraction to adopt]
- Example refactor: [Concrete code suggestion]
```

---

### Pattern 3: Emoji Visual Hierarchy

```
🚀 = Workflow start
⚠️ = Architecture Risk / Warning
✅ = Checkpoint / Verification passed
🏛️ = Architecture-related content
🔧 = Fix / Tool action
```

---

### Pattern 4: Bilingual Support

Prompts use the user's language but keep technical terms in English:

```python
"🏛️ **架構審查**：我會檢查計畫中的潛在設計問題
（如過度耦合 [Tight Coupling]、缺少抽象層 [Missing Abstraction]）"
```

---

## Implementation Checklist

When creating new prompts:

- [ ] Define a strong persona (who is speaking?)
- [ ] Include proactive guidance rules
- [ ] Specify required output sections
- [ ] Add checkpoints for complex workflows
- [ ] Use emoji for visual hierarchy
- [ ] Include Architecture Lesson block for debugging
- [ ] Test with adversarial inputs (bad code)

---

## Example: Full Prompt Transformation

### Before (Generic)
```python
return f"Please debug: {error_message}"
```

### After (Architect-First)
```python
return f"""You are a Senior Architect helping debug an issue.

**Error:**
```
{error_message}
```

**Your Analysis Must Include:**
1. **Root Cause**: What exactly failed?
2. **Likely Culprits**: Pinpoint the file/function.
3. **Suggested Fix**: Provide exact code changes.
4. **🏛️ Architecture Lesson**: 
   - Why did this happen? (Design flaw? Missing abstraction?)
   - How to prevent this class of errors permanently?
   - Example: "This error happens because you're not using 
     Dependency Injection. Refactor to inject the DB connection."

Don't just fix the symptom—fix the root design issue."""
```

---

## Measuring Success

A well-designed prompt should produce responses where:

1. **Architecture is mentioned** in every response
2. **Proactive warnings** appear for risky code
3. **Prevention strategies** are always included
4. **Users learn** from each interaction
5. **Technical debt** is caught before it accumulates

---

*"The best code is the code you never have to debug."*
— The Boring Architect Philosophy

---

*Last updated: V10.16.0*
