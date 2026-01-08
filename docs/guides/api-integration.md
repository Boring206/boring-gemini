# API Integration Guide

> Directly embed Boring's intelligence into your Python scripts and pipelines.

---

## 🛠️ Basic Imports

All of Boring's core logic is accessible via the `boring` package. 

### Core Modules
| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `boring.rag` | Codebase understanding | `RAGRetriever`, `IndexManager` |
| `boring.agents` | Autonomous logic | `StatefulAgentLoop`, `CoderAgent` |
| `boring.security` | Safety intercepts | `ShadowInterceptor` |
| `boring.mcp` | Ecosystem tools | `SpeckitManager`, `McpServer` |

---

## 🚀 Practical Example: Automated Project Summarizer

This script uses the RAG API to scan your project and generate a high-level summary.

### `summarize_project.py`

```python
import os
from boring.rag.retriever import RAGRetriever

def generate_report(project_dir: str):
    # 1. Initialize RAG (Uses existing index or builds one)
    retriever = RAGRetriever(project_path=project_dir)
    
    # 2. Query major components
    print(f"🔍 Analyzing project at: {project_dir}...")
    
    # Ask Boring about the core features
    queries = [
        "What are the main entry points of this application?",
        "What external dependencies are used for networking or database?",
        "How is the authentication logic implemented?"
    ]
    
    report_content = "# Project AI Summary\n\n"
    
    for q in queries:
        report_content += f"### {q}\n"
        results = retriever.search(q, max_results=2)
        
        if not results:
            report_content += "_No specific code found._\n\n"
            continue
            
        for doc in results:
            report_content += f"- **File**: `{doc.file_path}`\n"
            # In a real app, you would pass doc.content to an LLM here for a summary
            report_content += f"  - Context: {doc.content[:150].strip()}...\n\n"

    # 3. Save the report
    with open("PROJECT_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("✅ Report generated: PROJECT_SUMMARY.md")

if __name__ == "__main__":
    generate_report(".")
```

---

## ⚙️ Advanced Integration: Adding Quality Gates to CI

You can use the `Verifier` API to fail a build if codes don't meet your standards.

```python
from boring.core.verifier import ParallelVerifier

verifier = ParallelVerifier(project_path=".")
results = verifier.verify_all()

if not results.passed:
    print(f"❌ Verification Failed: {len(results.issues)} issues found.")
    for issue in results.issues:
        print(f"  - [{issue.category}] {issue.message}")
    exit(1)

print("🚀 All quality gates passed!")
```

---

## 💡 Pro Tips

1.  **Environment Variables**: Many APIs respect variables like `BORING_LOG_LEVEL` or `SHADOW_MODE_LEVEL`.
2.  **Singleton Pattern**: Most managers (like `RAGRetriever`) handle indexing internally, so you don't need to worry about redundant scans.
3.  **Async Support**: For high-performance integrations, look for `async` methods in the `boring.agents` module.
