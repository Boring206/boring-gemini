"""
Example: Using Vector Memory

This example demonstrates how to use the vector memory system
for semantic search over past experiences.
"""
from pathlib import Path

from boring.vector_memory import VectorMemory, create_vector_memory


def main():
    """Demonstrate vector memory usage."""

    # Create vector memory (requires chromadb)
    memory = create_vector_memory(
        project_root=Path.cwd(),
        log_dir=Path("logs")
    )

    if not memory.enabled:
        print("Vector memory not available. Install with:")
        print("  pip install boring-gemini[vector]")
        return

    # Add some experiences
    memory.add_experience(
        error_type="ImportError",
        error_message="No module named 'requests'",
        solution="pip install requests",
        context="web_client.py"
    )

    memory.add_experience(
        error_type="TypeError",
        error_message="'NoneType' object is not subscriptable",
        solution="Check if result is None before accessing: if result: value = result['key']",
        context="data_parser.py"
    )

    # Query for similar errors
    print("\n--- Searching for similar errors ---\n")

    results = memory.retrieve_similar(
        "module not found error",
        n_results=2
    )

    for result in results:
        print(f"Error: {result['error_type']}")
        print(f"Solution: {result['solution']}")
        print(f"Similarity: {result['similarity']:.2%}")
        print()

    # Get context injection for prompts
    context = memory.generate_context_injection("TypeError: NoneType")
    print("--- Context Injection ---")
    print(context)


if __name__ == "__main__":
    main()
