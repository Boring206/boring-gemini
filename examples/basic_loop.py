"""
Example: Basic Boring Loop

This example shows how to programmatically control the Boring development loop.
"""
from pathlib import Path
from boring.loop import AgentLoop
from boring.config import settings

def main():
    """Run a basic development loop."""
    
    # Option 1: Use defaults (reads PROMPT.md from current directory)
    loop = AgentLoop(
        model_name="models/gemini-2.0-flash-exp",
        verification_level="STANDARD",
        verbose=True
    )
    
    # Run the loop
    loop.run()


def custom_prompt():
    """Run with a custom prompt file."""
    
    loop = AgentLoop(
        prompt_file=Path("MY_INSTRUCTIONS.md"),
        context_file=Path("PROJECT_CONTEXT.md"),
        verification_level="FULL",  # Include pytest
    )
    
    loop.run()


if __name__ == "__main__":
    main()
