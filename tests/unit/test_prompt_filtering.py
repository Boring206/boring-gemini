import os
from unittest.mock import MagicMock, patch

from boring.mcp import server, tool_profiles


def test_prompt_filtering_ultra_lite():
    """Verify ULTRA_LITE has 0 prompts."""
    # Reset singleton
    server.instance.mcp = MagicMock()
    server.instance.mcp._prompts = {
        "vibe_start": "demo",
        "quick_fix": "demo",
        "boring_help": "demo",
    }

    with patch.dict(os.environ, {"BORING_MCP_PROFILE": "ultra_lite"}):
        # Force reload profile
        profile = tool_profiles.get_profile("ultra_lite")

        # Simulate server startup logic snippet
        prompts_dict = server.instance.mcp._prompts
        prompts_to_remove = [
            name
            for name in prompts_dict.keys()
            if not tool_profiles.should_register_prompt(name, profile)
        ]
        for name in prompts_to_remove:
            del prompts_dict[name]

        # Assertions
        assert len(prompts_dict) == 0  # Ultra Lite has empty list


def test_prompt_filtering_lite():
    """Verify LITE has specific prompts."""
    server.instance.mcp = MagicMock()
    server.instance.mcp._prompts = {
        "vibe_start": "demo",  # STANDARD only
        "quick_fix": "demo",  # LITE
        "smart_commit": "demo",  # LITE
        "system_status": "demo",  # MINIMAL -> LITE
    }

    with patch.dict(os.environ, {"BORING_MCP_PROFILE": "lite"}):
        profile = tool_profiles.get_profile("lite")

        prompts_dict = server.instance.mcp._prompts
        prompts_to_remove = [
            name
            for name in prompts_dict.keys()
            if not tool_profiles.should_register_prompt(name, profile)
        ]
        for name in prompts_to_remove:
            del prompts_dict[name]

        # Assertions
        assert "quick_fix" in prompts_dict
        assert "smart_commit" in prompts_dict
        assert "system_status" in prompts_dict
        assert "vibe_start" not in prompts_dict  # Should be removed


def test_prompt_filtering_full():
    """Verify FULL has all prompts."""
    server.instance.mcp = MagicMock()
    server.instance.mcp._prompts = {"vibe_start": "demo", "quick_fix": "demo"}

    with patch.dict(os.environ, {"BORING_MCP_PROFILE": "full"}):
        profile = tool_profiles.get_profile("full")

        prompts_dict = server.instance.mcp._prompts
        # Logic for FULL (prompts is None)
        if profile.prompts is not None:
            prompts_to_remove = [
                name
                for name in prompts_dict.keys()
                if not tool_profiles.should_register_prompt(name, profile)
            ]
            for name in prompts_to_remove:
                del prompts_dict[name]

        # Assertions
        assert len(prompts_dict) == 2
