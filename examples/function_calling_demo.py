"""
Example: Function Calling with Gemini

This example demonstrates how to use the Function Calling feature
for structured AI responses.
"""
from pathlib import Path

from boring.gemini_client import BORING_TOOLS, GeminiClient


def main():
    """Demonstrate function calling usage."""

    # Create client
    client = GeminiClient(
        model_name="models/gemini-2.0-flash-exp",
        log_dir=Path("logs")
    )

    if not client.use_function_calling:
        print("Function calling not available for this model")
        return

    # Generate with tools
    prompt = """
    Create a simple Python hello world script.
    Use the write_file function to create it at src/hello.py
    """

    text, function_calls, success = client.generate_with_tools(
        prompt=prompt,
        context="Creating a new Python project"
    )

    print(f"Response text: {text[:200]}...")
    print(f"Function calls: {len(function_calls)}")

    for fc in function_calls:
        print(f"  - {fc['name']}: {list(fc['args'].keys())}")

    # Process the function calls
    if function_calls:
        project_root = Path.cwd()
        results = client.process_function_calls(function_calls, project_root)

        print("\nResults:")
        print(f"  Files written: {results['files_written']}")
        print(f"  Search/replaces: {results['search_replaces']}")
        print(f"  Status: {results['status']}")
        print(f"  Errors: {results['errors']}")


if __name__ == "__main__":
    main()
