# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Unified Environment Settings for Boring V14.0

Centralizes all environment variable checks and provides a single source
of truth for runtime configuration.

Features:
- BORING_OFFLINE_MODE: Enable fully offline operation
- BORING_ENABLE_*: Control external MCP extension availability
- BORING_LOCAL_*: Local LLM configuration
"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class BoringEnvironment:
    """Unified environment settings for Boring."""

    # Offline Mode
    offline_mode: bool = False

    # Local LLM
    local_llm_model: str | None = None
    local_llm_context_size: int = 4096
    model_dir: str | None = None

    # External MCP Extensions (V14.0)
    enable_sequential_thinking: bool = True
    enable_critical_thinking: bool = True
    enable_context7: bool = True

    # MCP Mode
    mcp_mode: bool = False
    mcp_profile: str = "lite"
    mcp_debug: bool = False

    # Feature Flags
    lazy_mode: bool = False
    startup_profile: bool = False


@lru_cache(maxsize=1)
def get_environment() -> BoringEnvironment:
    """
    Get the unified environment settings.

    This function is cached and only reads environment variables once.
    Call `clear_environment_cache()` to force re-reading.

    Returns:
        BoringEnvironment with all settings
    """

    def _bool(key: str, default: bool = False) -> bool:
        val = os.environ.get(key, "").lower()
        if val in ("true", "1", "yes", "on"):
            return True
        if val in ("false", "0", "no", "off"):
            return False
        return default

    def _get_settings_profile() -> str:
        try:
            from boring.core.config import settings

            return settings.MCP_PROFILE
        except Exception:
            return "lite"

    return BoringEnvironment(
        # Offline Mode
        offline_mode=_bool("BORING_OFFLINE_MODE", False),
        # Local LLM
        local_llm_model=os.environ.get("BORING_LOCAL_LLM_MODEL"),
        local_llm_context_size=int(os.environ.get("BORING_LOCAL_LLM_CONTEXT_SIZE", "4096")),
        model_dir=os.environ.get("BORING_MODEL_DIR"),
        # External MCP Extensions
        enable_sequential_thinking=_bool("BORING_ENABLE_SEQUENTIAL", True),
        enable_critical_thinking=_bool("BORING_ENABLE_CRITICAL", True),
        enable_context7=_bool("BORING_ENABLE_CONTEXT7", True),
        # MCP Mode
        mcp_mode=_bool("BORING_MCP_MODE", False),
        mcp_profile=os.environ.get("BORING_MCP_PROFILE") or _get_settings_profile(),
        mcp_debug=_bool("BORING_MCP_DEBUG", False),
        # Feature Flags
        lazy_mode=_bool("BORING_LAZY_MODE", False),
        startup_profile=_bool("BORING_STARTUP_PROFILE", False),
    )


def clear_environment_cache():
    """Clear the environment cache to force re-reading variables."""
    get_environment.cache_clear()


def is_offline_mode() -> bool:
    """Check if offline mode is enabled."""
    return get_environment().offline_mode


def is_extension_enabled(extension: str) -> bool:
    """
    Check if an external MCP extension is enabled.

    Args:
        extension: Extension name (sequential, critical, context7)

    Returns:
        True if extension is enabled
    """
    env = get_environment()
    mapping = {
        "sequential": env.enable_sequential_thinking,
        "sequential_thinking": env.enable_sequential_thinking,
        "critical": env.enable_critical_thinking,
        "critical_thinking": env.enable_critical_thinking,
        "context7": env.enable_context7,
    }
    return mapping.get(extension.lower(), True)


def get_available_extensions() -> list[str]:
    """
    Get list of enabled external MCP extensions.

    Returns:
        List of enabled extension names
    """
    env = get_environment()
    extensions = []

    if env.enable_sequential_thinking:
        extensions.append("sequential_thinking")
    if env.enable_critical_thinking:
        extensions.append("critical_thinking")
    if env.enable_context7:
        extensions.append("context7")

    return extensions


# Convenience exports
def get_mcp_profile() -> str:
    """Get the current MCP tool profile."""
    return get_environment().mcp_profile


def is_mcp_mode() -> bool:
    """Check if running as MCP server."""
    return get_environment().mcp_mode
