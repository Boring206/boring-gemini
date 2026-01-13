import json
import warnings

from ...audit import audited
from ..registry import internal_registry
from ..tool_profiles import get_profile
from ..tool_router import get_tool_router


@audited
def boring(request: str) -> str:
    """
    🎯 Universal Router - Natural Language Tool Interface

    Instead of remembering 98+ tool names, just describe what you want:
    - "search for authentication code" → boring_rag_search
    - "review my code for security" → boring_security_scan
    - "generate tests for user.py" → boring_test_gen

    Args:
        request: Natural language description of what you want to do

    Returns:
        Routing result with matched tool and suggested parameters
    """
    router = get_tool_router()
    result = router.route(request)

    # P1: Low Confidence Handling
    if result.confidence < 0.7:
        # Low Confidence Path
        response = f"❓ **Ambiguous Request** (Confidence: {result.confidence:.0%})\n\n"
        response += f"Did you mean: `{result.matched_tool}`?\n"

        if result.alternatives:
            response += "\n🔄 **Alternatives:**\n"
            for alt in result.alternatives:
                response += f"- `{alt}`\n"

        response += "\n💡 **Tip:** Be more specific, e.g., 'check project health' instead of 'check'."
        return response

    # High Confidence Path
    tool_name = result.matched_tool

    tool = internal_registry.get_tool(tool_name)
    extra_info = ""

    if tool:
        # --- Renaissance V2: Auto-Injection for High Confidence ---
        auto_injected = False
        if result.confidence >= 0.95:
            # Use instance.mcp (SmartMCP) to inject
            # Note: instance variable reference might be tricky here if not imported correctly
            # But we imported 'mcp' from ..instance which is the SmartMCP instance
            from ..instance import mcp as smart_mcp
            if smart_mcp.inject_tool(tool.name):
                auto_injected = True

        # If it's an internal tool, provide the schema
        extra_info = (
            f"\n\n🛠️ **Internal Tool Schema for `{tool.name}`:**\n"
            f"```json\n{json.dumps(tool.schema, indent=2)}\n```\n"
        )

        if auto_injected:
            extra_info += f"✅ **Auto-Injected:** `{tool.name}` is now available in your tool list for direct use."
        else:
            extra_info += f"💡 Use `boring_call(tool_name=\"{tool.name}\", arguments={{...}})` to execute."
    else:
        # It's either real MCP or missing
        extra_info = f"\n💡 Call `{tool_name}` directly with the suggested parameters."

    return (
        f"🎯 **Routed to:** `{tool_name}`\n"
        f"📊 **Confidence:** {result.confidence:.0%}\n"
        f"📁 **Category:** {result.category}\n"
        f"📝 **Suggested params:** {json.dumps(result.suggested_params)}\n"
        + extra_info
    )


@audited
def boring_help() -> str:
    """Get help on available Boring tools and categories."""
    warnings.warn(
        "boring_help is deprecated. Use `boring help` instead.",
        DeprecationWarning,
        stacklevel=2
    )
    router = get_tool_router()
    summary = router.get_categories_summary()
    profile = get_profile()

    # Renaissance V2: Show Skills
    skill_info = "\n## 🎨 Role-based Skills (Activate via `boring_active_skill`)\n"
    if internal_registry.categories:
        for cat, tools in sorted(internal_registry.categories.items()):
            skill_info += f"- **{cat}**: {len(tools)} tools available\n"
    else:
        skill_info += "- No skills registered yet.\n"

    profile_info = (
        f"\n## 🎛️ Current Profile: **{profile.name}** ({len(profile.tools) if profile.tools else 'all'} tools)\n"
    )
    return summary + skill_info + profile_info


@audited
def boring_discover(tool_name: str) -> str:
    """
    Progressive Disclosure: Get full schema for a specific tool.

    Use this in ULTRA_LITE mode to fetch tool details on-demand,
    saving ~97% token overhead compared to loading all schemas upfront.

    Args:
        tool_name: Name of the tool to discover (e.g., 'boring_rag_search')

    Returns:
        Full JSON schema for the tool, or error if not found
    """
    warnings.warn(
        "boring_discover is deprecated. Use `boring discover <tool_name>` instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # 1. Start with registered tools
    # Access internal tools from mcp instance if available
    from ..instance import mcp as smart_mcp

    all_tools = {}

    # Use cached tools if available (UNFILTERED list for progressive disclosure)
    tools_source = getattr(smart_mcp, "_all_tools_cache", None)

    # Fallback to current tools (likely filtered)
    if not tools_source and hasattr(smart_mcp, "_tools"):
        tools_source = smart_mcp._tools

    if tools_source:
        for name, tool in tools_source.items():
            all_tools[name] = {
                "description": getattr(tool, "description", ""),
                "schema": getattr(tool, "inputSchema", {})
            }

    # 2. Merge with internal tools
    for name, tool in internal_registry.tools.items():
        if name not in all_tools:
            all_tools[name] = {
                "description": tool.description,
                "schema": tool.schema
            }

    if tool_name not in all_tools:
        # Try to find similar tools
        similar = [t for t in all_tools.keys() if tool_name.lower() in t.lower()]
        if similar:
            return f"❌ Tool `{tool_name}` not found. Did you mean: {', '.join(similar[:5])}?"
        return (
            f"❌ Tool `{tool_name}` not found. Use `boring_help` to see available categories."
        )

    tool_data = all_tools[tool_name]
    # Extract schema information
    schema_info = {
        "name": tool_name,
        "description": tool_data["description"],
    }

    # Try to get input schema if available
    if "schema" in tool_data:
        schema_info["input_schema"] = tool_data["schema"]
    elif "parameters" in tool_data:
        schema_info["parameters"] = tool_data["parameters"]

    return (
        f"## 🔍 Tool: `{tool_name}`\n\n"
        f"**Description:** {schema_info.get('description', 'N/A')}\n\n"
        f"<!-- CACHEABLE_CONTENT_START -->\n"
        f"**Schema:**\n```json\n{json.dumps(schema_info, indent=2, default=str)}\n```\n"
        f"<!-- CACHEABLE_CONTENT_END -->\n\n"
        f"💡 You can now call `{tool_name}` with the parameters above.\n"
        f"ℹ️  This schema is stable and can be cached for the session."
    )


def register_router_tools(mcp_instance):
    """Register router-related tools."""
    if not mcp_instance:
        return

    from ..tool_router import create_router_tool_description

    mcp_instance.tool(
        description=create_router_tool_description(),
        annotations={"readOnlyHint": True, "openWorldHint": True},
    )(boring)

    mcp_instance.tool(
        description="Show all available tool categories, Skills, and help.",
        annotations={"readOnlyHint": True},
    )(boring_help)

    mcp_instance.tool(
        description="Get full schema for a tool (progressive disclosure).",
        annotations={"readOnlyHint": True},
    )(boring_discover)
