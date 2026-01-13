# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Discovery Registry - The "Renaissance" Bridge (V11.4.1)

This module provides an internal registry for tools that should not
be exposed globally to the LLM context, but are accessible via
the Universal Router or Discovery tools.
"""

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class InternalTool:
    """Metadata for an internal (non-exposed) tool."""
    name: str
    func: Callable
    description: str
    schema: dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    is_core: bool = False
    kwargs: dict[str, Any] = field(default_factory=dict) # Store registration options


class DiscoveryRegistry:
    """
    Acts as a 'Sham MCP' to capture tool registrations without
    immediately exposing them to the FastMCP instance.
    """

    def __init__(self):
        self.tools: dict[str, InternalTool] = {}
        self.categories: dict[str, list[str]] = {}

    def tool(self, description: str = "", category: str = "general", **kwargs):
        """Decorator replacement for @mcp.tool."""
        def wrapper(func: Callable):
            name = func.__name__

            # Simple signature extraction for Renaissance UX
            try:
                sig = inspect.signature(func)
                schema = {
                    "type": "object",
                    "properties": {
                        p.name: {
                            "type": str(p.annotation).replace("<class '", "").replace("'>", ""),
                            "default": p.default if p.default != inspect.Parameter.empty else None
                        }
                        for p in sig.parameters.values()
                    },
                    "required": [
                        p.name for p in sig.parameters.values()
                        if p.default == inspect.Parameter.empty
                    ]
                }
            except Exception:
                schema = {"type": "object", "properties": {}, "note": "Schema extraction failed"}

            tool_obj = InternalTool(
                name=name,
                func=func,
                description=description or func.__doc__ or "No description",
                category=category,
                schema=schema,
                kwargs=kwargs
            )
            self.tools[name] = tool_obj

            if category not in self.categories:
                self.categories[category] = []
            if name not in self.categories[category]:
                self.categories[category].append(name)

            return func
        return wrapper

    def get_tool(self, name: str) -> Optional[InternalTool]:
        """Retrieve a tool by name."""
        return self.tools.get(name)

    def list_all_metadata(self) -> list[dict[str, str]]:
        """Return a list of minimal metadata for all tools."""
        return [
            {"name": t.name, "description": t.description, "category": t.category}
            for t in self.tools.values()
        ]

# Global singleton for internal tools
internal_registry = DiscoveryRegistry()
