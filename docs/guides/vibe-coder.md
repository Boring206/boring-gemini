# Vibe Coder Guide

> **For developers who code by describing.** No command-line expertise needed. Just tell Boring what you want.

---

## 🎨 What is Vibe Coding?

Vibe Coding is a development style where you:
1. **Describe** what you want in natural language
2. **Let AI** generate the implementation
3. **Review** and refine the output

**You focus on the "what", AI handles the "how".**

---

## 🚀 Your First Vibe Session

### Step 1: Start with /vibe_start

```
You: /vibe_start I want to build a personal blog with a dark theme

# OR using boring-route CLI
$ boring-route "I want to build a personal blog with a dark theme"

```

### Step 2: Answer the Questions

```
Boring: Great idea! Let me understand your vision:
        
        1. Static site or with a backend?
        2. Features needed? (comments, search, tags)
        3. Design style? (minimal, magazine, tech)
        4. Target platform? (desktop, mobile-first)

You: 1. Static site is fine
     2. Tags and search
     3. Minimal and clean
     4. Mobile-first
```

### Step 3: Watch Your Blog Come to Life

```
Boring: Perfect! Here's what I'll create:
        
        📁 blog/
        ├── index.html       (Home page)
        ├── posts/           (Blog posts)
        ├── styles/          (Dark theme CSS)
        ├── js/              (Search functionality)
        └── tags/            (Tag pages)
        
        Starting implementation...
        ✅ Created base structure
        ✅ Implemented dark theme
        ✅ Added search feature
        ✅ Created sample posts
        
        Your blog is ready! Open index.html to see it.
```

---

## 💡 Quick Prompts for Vibe Coders

| What You Want | Just Say |
|---------------|----------|
| Build something new | `/vibe_start [describe your idea]` |
| Fix any error | `/quick_fix` or `boring-route "fix it"` |
| Commit changes | `/smart_commit` or `boring-route "commit this"` |
| Full-stack app | `/full_stack_dev` or `boring-route "build app..."` |

### Examples

```
/vibe_start Create a weather dashboard with city search

/vibe_start Build a task manager with drag-and-drop

/vibe_start Make a portfolio site for a photographer

/full_stack_dev my-store "Next.js + Stripe + Supabase"
```

---

## 🎯 Vibe Coding Patterns

### Pattern 1: Describe the Experience

❌ **Don't say this:**
```
Create a React component with useState for form handling
```

✅ **Say this:**
```
I want a sign-up form that feels smooth and shows validation 
errors as the user types
```

### Pattern 2: Focus on the User

❌ **Don't say this:**
```
Implement JWT authentication with refresh tokens
```

✅ **Say this:**
```
Users should be able to stay logged in for a week without 
having to re-enter their password
```

### Pattern 3: Show, Don't Tell

❌ **Don't say this:**
```
Add error handling
```

✅ **Say this:**
```
When something goes wrong, show a friendly message that 
explains what happened and what the user can do about it
```

---

## 🔄 The Vibe Workflow

```
┌─────────────────────────────────────────────────────────┐
│                   VIBE WORKFLOW                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   1. DESCRIBE        2. REVIEW        3. REFINE        │
│   ───────────        ──────────       ─────────        │
│   Tell AI what       Look at the      "Make the        │
│   you envision       result           button bigger"   │
│                                                         │
│        ↓                 ↓                 ↓            │
│                                                         │
│   "I want a         "Looks good,     AI adjusts       │
│   landing page      but needs        and you're       │
│   that pops"        more color"      done! 🎉         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🛡️ Safety First (Even for Vibe Coders)

### Shadow Mode Protects You

Even if you're not a command-line expert, Boring protects you:

```
Boring: I want to delete the old cache files.
        
        ⚠️ This operation requires your approval:
        - Delete: cache/*.json (15 files)
        
        [Approve] [Reject] [Show Details]
```

**You're always in control.** Dangerous operations need your OK.

---

## 📱 For Mobile/Web Developers

### Build a Mobile App

```
/vibe_start Create a React Native expense tracker with:
- Beautiful pie charts
- Easy receipt scanning
- Monthly budgets
```

### Build a Web App

```
/vibe_start I want a SaaS dashboard for project management
that looks like Linear but simpler
```

### Build an API

```
/vibe_start Build a REST API for a recipe sharing platform
with user accounts and recipe ratings
```

---

## 🎮 For Game Developers

```
/vibe_start Create a 2D platformer game with:
- A cute robot character
- 5 levels with increasing difficulty
- Coin collection and high scores
```

---

## 🤖 For AI/ML Developers

```
/vibe_start Build a sentiment analysis web app that:
- Takes user reviews as input
- Shows positive/negative/neutral with confidence
- Has a beautiful visualization
```

---

## 💬 Common Phrases

| Phrase | What Happens |
|--------|-------------|
| "Make it better" | AI improves code quality |
| "Add tests" | AI writes test cases |
| "Make it faster" | AI optimizes performance |
| "Make it prettier" | AI improves UI/design |
| "Explain this" | AI documents the code |
| "Fix this" | AI debugs the issue |

---

## 🆘 When You're Stuck

### Ask for Help
```
I'm confused about how the authentication works. 
Can you explain it like I'm 5?
```

### Start Over
```
Let's start fresh. I want to take a different approach.
```

### Get Specific
```
The button doesn't look right on mobile. 
Can you make it full-width on small screens?
```

---

## See Also

- [Quick Tutorials](./quick-tutorials.md) - Step-by-step guides
- [Cookbook](./cookbook.md) - Ready-made recipes
- [Pro Tips](./pro-tips.md) - Level up your skills
