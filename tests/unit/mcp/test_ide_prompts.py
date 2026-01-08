import sys

from boring.mcp.prompts import register_prompts


class FakeMCP:
    def __init__(self):
        self.prompts = {}

    def prompt(self, name, description=None):
        def decorator(func):
            self.prompts[name] = func
            return func

        return decorator


def test_setup_ide_prompt():
    fake_mcp = FakeMCP()
    register_prompts(fake_mcp)

    # Run the prompt function
    output = fake_mcp.prompts["setup_ide"]()

    # Check for critical elements
    assert sys.executable in output
    assert "boring.lsp.enabled" in output
    assert "nvim-lspconfig" in output
    assert "Zed" in output
    assert "Detected Python Environment" in output

    # Verify the logic for path replacements (windows backslashes)
    if sys.platform == "win32":
        # Check that we have escaped paths for Zed/Lua

        assert sys.executable.replace("\\", "\\\\") in output
