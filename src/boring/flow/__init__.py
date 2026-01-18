# Boring Flow - The One Dragon Architecture
# This package implements the unified workflow engine.

"""
Boring Flow Package

The One Dragon Architecture implementation providing:
- FlowEngine: Main entry point for running flows
- FlowGraph: State machine for workflow execution
- FlowDetector: Project state detection
- Nodes: Architect, Builder, Healer, Polish, Evolver
- Events: Event bus for decoupled automation
"""

from typing import Any

# Light submodules can be imported at top level if they don't pull heavy dependencies
from boring.flow.states import (
    STAGE_PROGRESS,
    STAGE_SKILL_MAPPING,
    FlowStage,
    FlowState,
    get_progress_bar,
)

# We use __getattr__ (PEP 562) to lazily load heavy components
_LAZY_MAPPING = {
    "FlowDetector": "boring.flow.detector",
    "FlowEngine": "boring.flow.engine",
    "FlowEvent": "boring.flow.events",
    "FlowEventBus": "boring.flow.events",
    "FlowGraph": "boring.flow.graph",
    "ArchitectNode": "boring.flow.nodes.architect",
    "BaseNode": "boring.flow.nodes.base",
    "FlowContext": "boring.flow.nodes.base",
    "NodeResult": "boring.flow.nodes.base",
    "NodeResultStatus": "boring.flow.nodes.base",
    "BuilderNode": "boring.flow.nodes.builder",
    "EvolverNode": "boring.flow.nodes.evolver",
    "HealerNode": "boring.flow.nodes.healer",
    "PolishNode": "boring.flow.nodes.polish",
    "ParallelExecutor": "boring.flow.parallel",
    "SkillsAdvisor": "boring.flow.skills_advisor",
    "VibeInterface": "boring.flow.vibe_interface",
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_MAPPING:
        import importlib

        module_path = _LAZY_MAPPING[name]
        module = importlib.import_module(module_path)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_MAPPING.keys()))


__all__ = [
    # Engine
    "FlowEngine",
    "FlowGraph",
    "FlowDetector",
    # Events
    "FlowEvent",
    "FlowEventBus",
    # States
    "FlowStage",
    "FlowState",
    "STAGE_PROGRESS",
    "STAGE_SKILL_MAPPING",
    "get_progress_bar",
    # Parallel
    "ParallelExecutor",
    # Interfaces
    "VibeInterface",
    "SkillsAdvisor",
    # Node Base
    "BaseNode",
    "FlowContext",
    "NodeResult",
    "NodeResultStatus",
    # Nodes
    "ArchitectNode",
    "BuilderNode",
    "EvolverNode",
    "HealerNode",
    "PolishNode",
]
