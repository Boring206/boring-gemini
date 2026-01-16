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

from boring.flow.detector import FlowDetector
from boring.flow.engine import FlowEngine
from boring.flow.events import FlowEvent, FlowEventBus
from boring.flow.graph import FlowGraph
from boring.flow.nodes.architect import ArchitectNode

# Node classes
from boring.flow.nodes.base import (
    BaseNode,
    FlowContext,
    NodeResult,
    NodeResultStatus,
)
from boring.flow.nodes.builder import BuilderNode
from boring.flow.nodes.evolver import EvolverNode
from boring.flow.nodes.healer import HealerNode
from boring.flow.nodes.polish import PolishNode
from boring.flow.parallel import ParallelExecutor
from boring.flow.skills_advisor import SkillsAdvisor
from boring.flow.states import (
    STAGE_PROGRESS,
    STAGE_SKILL_MAPPING,
    FlowStage,
    FlowState,
    get_progress_bar,
)
from boring.flow.vibe_interface import VibeInterface

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
