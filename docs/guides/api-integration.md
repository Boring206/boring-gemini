# Python API Integration Guide (V10.26)

> Embed Boring's Intelligence, Judge, and Shadow Mode directly into your Python apps.

Boring-Gemini is not just a CLI tool; it's a modular Python library. You can import its core modules into your own AI applications or automation scripts.

## 📦 Installation

```bash
pip install boring-aicoding
```

## 🧠 Intelligence API (Brain & Memory)

The `boring.intelligence` module provides knowledge management, pattern learning, and vector memory capabilities.

### 1. Knowledge Base Management (BrainManager)

Use `BrainManager` to access or update long-term memory and learned patterns in `.boring/brain`.

```python
from boring.intelligence.brain_manager import BrainManager, LearnedPattern

# Initialize (automatically loads .boring/brain)
brain = BrainManager(project_path="./my_project")

# 1. Query learned patterns (Pattern Mining)
patterns = brain.get_patterns(category="error_handling")
for p in patterns:
    print(f"Pattern [{p.confidence}]: {p.description}")

# 2. Record new knowledge
new_pattern = LearnedPattern(
    trigger="ConnectionError",
    solution="Implement exponential backoff in retry logic",
    confidence=0.9
)
brain.learn_pattern(new_pattern)
```

### 2. Hybrid RAG (RAGRetriever)

Use the high-level `RAGRetriever` for semantic search and dependency expansion.

```python
from boring.rag.rag_retriever import RAGRetriever

retriever = RAGRetriever(project_path=".")

# Semantic Search (RAG)
results = retriever.search("safe file handling", top_k=3)
for res in results:
    print(f"Found in {res['path']}: {res['snippet']}")
```

---

## ⚖️ Judge API (Evaluation & Rubrics)

The `boring.judge` module provides a structured evaluation framework, perfect for controlling LLM output quality.

### Defining Rubrics

You can define your own `Rubric` and apply it to evaluation processes.

```python
from boring.judge.rubrics import Rubric, Criterion

# 1. Define Rubric
security_rubric = Rubric(
    name="API Security",
    criteria=[
        Criterion(name="Auth", description="Standard OIDC/OAuth2 usage", weight=1.0),
        Criterion(name="Validation", description="Input sanitization", weight=0.8),
        Criterion(name="Logging", description="No secrets in logs", weight=1.0),
    ]
)

# 2. Export to Markdown (for LLM context)
print(security_rubric.to_markdown())

# 3. Programmatic scoring usage
# score = evaluator.evaluate(code, security_rubric)
```

---

## 🛡️ Loop API (Workflow & Security)

The `boring.loop` module provides security guards and atomic operations, ideal for building robust automation scripts.

### 1. Shadow Mode Protection (ShadowModeGuard)

Wrap your scripts in Shadow Mode to prevent accidental destructive operations.

```python
from boring.loop.shadow_mode import ShadowModeGuard, OperationSeverity, ShadowModeLevel

# Initialize Guard (Strict Mode)
guard = ShadowModeGuard(level=ShadowModeLevel.STRICT)

# Attempt operation
def delete_database():
    op = guard.create_operation(
        type="delete",
        target="./data.db",
        severity=OperationSeverity.CRITICAL
    )
    
    if guard.allow(op):
        print("Deleting...")
        # os.remove("./data.db")
    else:
        print(f"Operation blocked: {op.reason}")

delete_database()
# Output: Operation blocked: High severity requires approval in STRICT mode
```

### 2. Atomic Transactions (TransactionManager)

Ensure a set of file operations either all succeed or all roll back.

```python
from boring.loop.transactions import TransactionManager

tx = TransactionManager(project_path=".")

with tx.begin() as transaction:
    try:
        # Operations are staged first
        transaction.write("config.py", "DEBUG = False")
        transaction.write("src/main.py", "import config")
        
        # Commit (Atomic Write)
        transaction.commit()
        print("Update successful")
        
    except Exception as e:
        # Auto-rollback (No files modified)
        transaction.rollback()
        print(f"Update failed, rolled back: {e}")
```
