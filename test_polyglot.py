
from boring.config import discover_tools, settings
from boring.llm import get_provider


def test_discovery():
    print("=== Boring Tool Discovery Test ===")
    discover_tools()
    print(f"Gemini CLI Path: {settings.GEMINI_CLI_PATH}")
    print(f"Claude CLI Path: {settings.CLAUDE_CLI_PATH}")
    print(f"Default Provider: {settings.LLM_PROVIDER}")

    print("\n=== Provider Factory Test ===")
    # Test Default (Gemini)
    p1 = get_provider()
    print(f"Provider 1: {type(p1).__name__} (Model: {p1.model_name})")
    print(f"Is Available: {p1.is_available}")

    # Test Claude Force
    p2 = get_provider(provider_name="claude-code")
    print(f"Provider 2: {type(p2).__name__} (Model: {p2.model_name})")
    print(f"Is Available: {p2.is_available}")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    test_discovery()
