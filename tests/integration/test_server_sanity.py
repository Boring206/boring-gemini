from boring.mcp.server import get_server_instance


def test_server_tools_registration_sanity():
    """
    Integration sanity check to ensure all modular tools are registered correctly.
    This verifies that our refactoring of server.py and tool modules didn't break import/registration.
    """
    # 1. Get server instance (simulates startup)
    mcp = get_server_instance()

    # 2. Extract tools safely
    tools = {}
    if hasattr(mcp, "_tool_manager"):
        if hasattr(mcp._tool_manager, "_tools"):
            tools = mcp._tool_manager._tools
        elif hasattr(mcp._tool_manager, "tools"):
            tools = mcp._tool_manager.tools

    if not tools:
        if hasattr(mcp, "_tools"):
            tools = mcp._tools
        elif hasattr(mcp, "tools"):
            tools = mcp.tools

    tool_names = list(tools.keys())
    print(f"DEBUG: Found tools: {tool_names}")

    # 3. Assert Core Modular Tools are present
    assert "boring_suggest_next" in tool_names, "Missing intelligence tool: boring_suggest_next"
    assert "boring_prompt_fix" in tool_names, "Missing intelligence tool: boring_prompt_fix"

    # 4. Assert Workspace Tools
    assert "boring_workspace_add" in tool_names, "Missing workspace tool: boring_workspace_add"

    # 5. Assert Plugin Tools
    assert "boring_list_plugins" in tool_names, "Missing plugin tool: boring_list_plugins"

    # 6. Assert Knowledge Tools (Action 3)
    assert "boring_brain_status" in tool_names, "Missing knowledge tool: boring_brain_status"
    assert "boring_learn" in tool_names, "Missing knowledge tool: boring_learn"

    print(f"\n✅ Server Sanity Check Passed! {len(tool_names)} tools registered.")
    print(f"   Context tools: {[t for t in tool_names if 'brain' in t or 'learn' in t]}")


if __name__ == "__main__":
    # Allow running as a script
    try:
        test_server_tools_registration_sanity()
    except AssertionError as e:
        print(f"❌ Sanity Check Failed: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        exit(1)
