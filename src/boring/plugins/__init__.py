# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Boring Plugin System - Extensible tool registration.

Allows users to create custom MCP tools and register them
with the Boring server at runtime.
"""

from .loader import BoringPlugin, PluginLoader, plugin

__all__ = ["PluginLoader", "BoringPlugin", "plugin"]
