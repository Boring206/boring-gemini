# Hidden Gems & Power User Tips

> Unlock the full potential of Boring with these advanced features and lesser-known tricks.

---

## 🛠️ Deep Debugging with Profiles

You might know about `lite` vs `full` profiles, but did you know you can customize them?

### Why `boring_debug_code` Vanished?
If you are in `lite` mode (default), advanced debugging tools are hidden to save context. To get them back:

```bash
# Temporarily enable full toolkit for a session
export BORING_MCP_PROFILE=full
boring start
```

### Custom Profiles
Create `custom_profile.toml` to mix-and-match:

```toml
[profiles.my_debug]
include = ["boring_read_file", "boring_debug_code", "boring_security_scan"]
exclude = ["boring_commit"]
```

---

## 🧠 Brain Surgery

Your AI learns from mistakes (`~/.boring_brain`), but sometimes it learns the *wrong* thing.

### View Your Brain
Check what patterns are currently stored:

```bash
cat ~/.boring_brain/patterns.json
```

### Force Unlearning
If Boring keeps making a mistake it "learned" to do, you can manually edit this file or use the `boring_learn` tool explicitly:

```bash
boring-route "Forget the pattern about checking for requirements.txt"
```

---

## 🕵️ Mastering the Router

The `boring()` router uses semantic scoring, not just keywords.

### Triggering Analysis
To force a "Sequential Thinking" session, use keywords like:

*   "Think about..."
*   "Analyze deeply..."
*   "Reason through..."

```python
# Triggers sequentialthinking tool
boring("Think about the race condition in the auth module")
```

### External Knowledge (Context7)
You don't need to leave your IDE to check documentation.

```python
# Queries external docs via Context7
boring("How do I use the new React useActionState hook?")
```

**Pro Tip**: Be specific with library names. "Query PyTorch docs" works better than "Query ML docs".

---

## 🛡️ Shadow Mode Tricks

### Strict Mode for Code Review
You can use Shadow Mode as a forced code review tool, even for safe operations.

```bash
export SHADOW_MODE_LEVEL=STRICT
boring-route "Refactor the login page"
```

Now, **every single file write** will pop up a diff for you to approve. It's like an interactive PR review.

---

## 🔍 HyDE Search Secrets

Boring uses **HyDE (Hypothetical Document Embeddings)** for search.

*   **Bad Query**: "auth error"
*   **Good Query**: "Why does the login function return a 401 error when the token is valid?"

**Why?** HyDE generates a fake "perfect answer" and searches for code that looks like *that*. Phrasing as a question helps it hallucinate a better search target.
