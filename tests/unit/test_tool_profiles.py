# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from boring.mcp.tool_profiles import get_profile, should_register_tool


def test_lite_profile_contains_session_tools():
    """Verify that the LITE profile includes boring_session_start and related tools."""
    profile = get_profile("lite")

    expected_tools = [
        "boring_session_start",
        "boring_session_confirm",
        "boring_session_status",
        "boring_session_load",
        "boring_session_pause",
        "boring_session_auto",
    ]

    for tool_name in expected_tools:
        assert tool_name in profile.tools, f"{tool_name} should be in LITE profile"
        assert should_register_tool(tool_name, profile), f"{tool_name} should be registered in LITE profile"

def test_full_profile_contains_session_tools():
    """Verify that the FULL profile includes session tools (implicit check)."""
    profile = get_profile("full")
    assert profile.tools is None # All tools

    # should_register_tool returns True for any tool name if tools is None
    assert should_register_tool("boring_session_start", profile)

