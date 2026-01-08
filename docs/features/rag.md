# 🕵️ Hybrid RAG Architecture

> **Intelligence Maximization Component**
> "Stop searching for keywords. Start finding answers."

Boring-Gemini uses a **Hybrid RAG (Retrieval-Augmented Generation)** system designed specifically for codebases. It moves beyond simple vector similarity to understand the *structure* and *intent* of your code.

## 🚀 Key Technologies

### 1. HyDE (Hypothetical Document Embeddings)
Traditional RAG fails when your query (e.g., "how does auth work?") looks nothing like the code (e.g., `class AuthenticationManager`).
**HyDE** generates a hypothetical code snippet based on your query, then searches for that.
*   **Result**: 20-30% higher semantic accuracy.

### 2. Cross-Encoder Reranking
Vector search is fast but imprecise. We use a **Cross-Encoder** to deeply analyze the top results and re-rank them based on true relevance to your specific query.
*   **Result**: The code you actually need is at the top.

### 3. Dependency Graph Expansion (GraphRAG)
Code doesn't exist in isolation. When we find a relevant function, we also pull in its **callers** (who uses it?) and **callees** (what does it use?) using a static analysis graph.
*   **Result**: The LLM understands the *context*, not just the text.

## 🧠 Vibe Coder Integration

You don't need to configure any of this. Just use the Router:

```bash
# 1. "Keyword Search" (Old School)
boring-route "search for login"

# 2. "Semantic Question" (HyDE + RAG)
boring-route "how do we handle token expiration?"
# RAG will: 
#   -> Generating hypothetical token logic...
#   -> Searching vectors...
#   -> Reranking results...
#   -> Expanding context...
#   -> "Here is the TokenRefreshService class..."
```

## 📊 Performance

| Metric | Traditional RAG | Boring Hybrid RAG |
|--------|-----------------|-------------------|
| **Recall** | ~40% | **~85%** |
| **Context Noise** | High | **Low (Reranked)** |
| **Structure Awareness** | None | **High (Graph)** |

## 🛠️ Tools

*   `boring_rag_search`: The main entry point (Hybrid search).
*   `boring_rag_context`: Get deep context for a specific file/symbol.
*   `boring_rag_index`: Force a re-index of the codebase.
