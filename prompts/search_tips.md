# Search Tips

This prompt optimizes code search and RAG retrieval.

## Effective Search Queries

1. **Be Specific**: Instead of "auth", use "JWT token validation"
2. **Use Technical Terms**: "middleware authentication" not "login check"
3. **Include Context**: "FastAPI dependency injection for auth"

## RAG Search Strategies

### Finding Function Definitions
- Query: "function definition <function_name>"
- Tip: Include the expected return type if known

### Finding Usage Examples
- Query: "calls to <function_name>" or "<function_name> usage"
- Filter by file type if needed

### Tracing Dependencies
- Query: "imports <module_name>"
- Use `boring_rag_expand` to see related files

## When Results Are Poor

1. Try synonyms (e.g., "authenticate" vs "login" vs "verify user")
2. Broaden the scope (search parent directories)
3. Use file path filters to narrow down
4. Try the dependency graph: `boring_rag_graph`
