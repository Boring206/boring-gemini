from boring.core.dependencies import DependencyManager

# Create MCP server instance lazily or via guard
if DependencyManager.check_mcp():
    import functools

    from fastmcp import FastMCP

    from .registry import internal_registry
    from .tool_profiles import get_profile, should_register_tool

    _raw_mcp = FastMCP(name="Boring AI Development Agent")

    def _create_tracking_wrapper(func, tool_name: str):
        """Create a wrapper that tracks tool usage and detects anomalies."""
        @functools.wraps(func)
        def tracking_wrapper(*args, **kwargs):
            try:
                from ..intelligence.usage_tracker import AnomalyDetectedError, get_tracker
                get_tracker().track(tool_name, tool_args=(args, kwargs))
            except AnomalyDetectedError as e:
                return f"⛔ **ANOMALY DETECTED**: You have called `{tool_name}` {e.count} times consecutively with IDENTICAL arguments. Please STOP and rethink your approach."
            except Exception:
                pass
            return func(*args, **kwargs)
        return tracking_wrapper

    class SmartMCP:
        """
        The Renaissance Wrapper: Selectively révèle tools to the context
        while keeping all tools accessible via internal execution.
        """
        def __init__(self, raw_mcp):
            object.__setattr__(self, "_raw_mcp", raw_mcp)
            object.__setattr__(self, "_exposed_tools", set())

        def tool(self, **kwargs):
            def wrapper(func):
                name = func.__name__
                profile = get_profile()

                # Renaissance V2: Infer category for Skill-based Partitioning
                module_name = func.__module__.lower()
                category = "general"
                if "speckit" in module_name:
                    category = "Architect"
                elif "git" in module_name or "checkpoint" in module_name:
                    category = "Watcher"
                elif "rag" in module_name or "search" in module_name:
                    category = "Surveyor"
                elif "brain" in module_name:
                    category = "Sage"
                elif "fix" in module_name or "patch" in module_name or "lint" in module_name or "metrics" in module_name:
                    category = "Healer"

                # Renaissance V2: Always register in internal registry for discovery/router hydration
                internal_registry.tool(category=category, **kwargs)(func)

                if should_register_tool(name, profile):
                    self._exposed_tools.add(name)

                    # P3+P5: Usage Tracking & Anomaly Detection
                    wrapped_func = _create_tracking_wrapper(func, name)
                    return self._raw_mcp.tool(**kwargs)(wrapped_func)

                return func
            return wrapper

        def inject_tool(self, tool_name: str) -> bool:
            """Dynamically register an internal tool with the main MCP instance."""
            if tool_name in self._exposed_tools:
                return True

            tool = internal_registry.get_tool(tool_name)
            if tool:
                # P3+P5: Usage Tracking & Anomaly Detection
                wrapped_func = _create_tracking_wrapper(tool.func, tool_name)
                self._raw_mcp.tool(**tool.kwargs)(wrapped_func)
                self._exposed_tools.add(tool_name)
                return True
            return False

        def reset_injected_tools(self) -> int:
            """Clear all dynamically injected tools from the active profile."""
            count = len(self._exposed_tools)
            self._exposed_tools.clear()
            return count

        def __getattr__(self, name):
            return getattr(self._raw_mcp, name)

        def __setattr__(self, name, value):
            setattr(self._raw_mcp, name, value)

    mcp = SmartMCP(_raw_mcp)
    MCP_AVAILABLE = True
else:
    mcp = None
    MCP_AVAILABLE = False
