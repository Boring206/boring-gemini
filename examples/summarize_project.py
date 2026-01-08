import asyncio
from pathlib import Path
from boring.rag.retriever import RAGRetriever
from boring.mcp.utils import find_project_root
from boring.agents.orchestrator import AgentOrchestrator

async def main():
    # 1. Automatically find project root
    root = find_project_root(Path.cwd())
    print(f"Project Root: {root}")

    # 2. Search codebase for "core architecture"
    print("Searching codebase...")
    retriever = RAGRetriever(root)
    results = await retriever.search("Summarize the core architecture of this project")
    
    context_chunks = [r.content for r in results]
    print(f"Found {len(context_chunks)} relevant chunks.")

    # 3. Use an Agent to generate a report
    print("Generating report...")
    agent = AgentOrchestrator(root)
    prompt = f"Based on these code snippets:\n\n{''.join(context_chunks[:5])}\n\nWrite a concise architectural summary."
    
    response = await agent.run_task(prompt)
    
    print("\n--- Project Summary ---")
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
