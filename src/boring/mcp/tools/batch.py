
import logging
from typing import Annotated, Any

from pydantic import Field

from ...audit import audited
from ...types import BoringResult, create_error_result, create_success_result
from ..instance import MCP_AVAILABLE, mcp

logger = logging.getLogger(__name__)

@audited
def boring_batch(
    steps: Annotated[
        list[dict[str, Any]],
        Field(description="List of tool calls. Each dict must have 'tool' (name) and 'args' (dict).")
    ],
    continue_on_error: Annotated[
        bool,
        Field(description="If True, continue executing remaining steps even if one fails.")
    ] = False,
) -> BoringResult:
    """
    Execute multiple MCP tools in a single batch request to reduce latency.

    Processing:
    - Executes tools sequentially.
    - If a step fails and continue_on_error is False, stops and returns results up to that point.
    - Each internal tool call is subject to its own security/audit checks (Shadow Mode).

    Args:
        steps: List of {"tool": "name", "args": {...}}
        continue_on_error: Whether to proceed after failures.

    Returns:
        Aggregation of all tool results.
    """
    if not MCP_AVAILABLE or mcp is None:
        return create_error_result("MCP server not initialized.")

    results = []
    success_count = 0
    failure_count = 0

    # Access the tool registry robustly
    # FastMCP uses _tools mapping name -> Tool object
    registry = getattr(mcp, "_tools", {})
    if not registry and hasattr(mcp, "_tool_manager"):
         registry = getattr(mcp._tool_manager, "_tools", {})

    for i, step in enumerate(steps):
        tool_name = step.get("tool")
        args = step.get("args", {})

        if not tool_name:
            results.append({
                "step": i,
                "status": "error",
                "message": "Missing 'tool' name in step definition."
            })
            failure_count += 1
            if not continue_on_error:
                break
            continue

        # Look up tool
        tool_def = registry.get(tool_name)
        if not tool_def:
             results.append({
                "step": i,
                "tool": tool_name,
                "status": "error",
                "message": f"Tool '{tool_name}' not found in registry."
            })
             failure_count += 1
             if not continue_on_error:
                 break
             continue

        # Execute
        try:
            # FastMCP Tool object has a .fn callable
            # We call it directly.
            # Note: This bypasses FastMCP's JSON-RPC validation but invokes the python function directly.
            # If the python function is decorated with @audited, that decorator runs.
            # If it's async, we might have an issue if we are sync.
            # Most boring tools are sync defs due to audited decorator.

            func = tool_def.fn

            # Check for async - simple check
            import inspect
            if inspect.iscoroutinefunction(func):
                 results.append({
                    "step": i,
                    "tool": tool_name,
                    "status": "error",
                    "message": f"Async tool '{tool_name}' execution not supported in sync batch."
                })
                 failure_count += 1
                 if not continue_on_error:
                     break
                 continue

            # Call
            # We unpack args. FastMCP usually handles signature binding.
            # Here we try passing as kwargs.
            try:
                # If args is not a dict, this will fail.
                if not isinstance(args, dict):
                     raise ValueError("Args must be a dictionary")

                output = func(**args)

                # Normalize output
                # Tools return BoringResult (dict) or plain value
                results.append({
                    "step": i,
                    "tool": tool_name,
                    "status": "success",
                    "output": output
                })
                success_count += 1

            except Exception as e:
                # Execution error (inside tool)
                 results.append({
                    "step": i,
                    "tool": tool_name,
                    "status": "failure", # Tool ran but threw exception
                    "error": str(e)
                })
                 failure_count += 1
                 if not continue_on_error:
                     break

        except Exception as e:
            # System error
            results.append({
                "step": i,
                "tool": tool_name,
                "status": "system_error",
                "error": str(e)
            })
            failure_count += 1
            if not continue_on_error:
                break

    return create_success_result(
        message=f"Batch execution completed. Success: {success_count}, Failures: {failure_count}",
        data={
            "total_steps": len(steps),
            "executed_steps": len(results),
            "results": results
        }
    )

if MCP_AVAILABLE and mcp is not None:
    mcp.tool(
        description="Execute multiple tools in batch",
        annotations={"readOnlyHint": False, "destructiveHint": True} # Assume risky
    )(boring_batch)
