"""
Boring for Gemini - AI Coding Assistant

V11.5.0 "Intelligent Adaptability Update":
- **Usage Analytics**: New `boring_usage_stats` and Usage Dashboard (CLI/Web) for self-aware insights.
- **Safety Net**: Anomaly Detection prevents infinite loops and stuck states.
- **Adaptive Intelligence**: Smart Prompt Injection dynamically loads relevant guides (Testing, Standards) based on usage context.
- **Code Quality**: Enhanced thread safety, logging, and rigorous type checking.

V11.4.2 "Renaissance Hardening":
- **Universal Semantic Gating**: Intelligent tool filtering based on project capabilities.


V11.1.0 "Turbo Mode & Wizard Upgrade":

V11.0.0 "The Resilient Foundation Update":
- Windows Mandatory File Locking protection with exponential backoff retry
- Pre-execution file lock detection for safe rollbacks
- Cross-language Tree-sitter precision: Go method receivers, TS interfaces, React components
- Transactional file writing (write-temp-then-rename) for race condition prevention
- Threading locks for concurrent JSON state file access
- Enhanced RAG indexing for JS/TS/Go/C++ codebases

V10.32.1 "Visual Identity & Stability Update":
- Overhauled README.md and README_zh.md with modern header/logo
- Fixed version command fallback in unit tests
- Verified 52% coverage gate compliance

V10.32.0 "Dependency Fix Release":
- Added psutil dependency for performance benchmarks
- Fixed ModuleNotFoundError in tests/performance module
- All 1113 unit tests passing

V10.31.1 "The Cognitive Reflex Update (Patch 1)":
- Highlighted Deep Thinking (Reasoning & Critical Thinking) in Vibe Sessions
- Robust NL routing for safety checkpoints and evaluation tools
- Improved keyword parity for traditional Chinese users
- Stabilized CI coverage above 50% gate

V10.31.0 "The Cognitive Reflex Update":
- Agentic Safety Net (Git Checkpoints)
- Active Recall (Brain-driven Error Correction)
- Phase 7-11 Architecture Modernization (Decoupled Tools)

V10.28 "The Diet Update":
- Modular installation extras ([vector], [gui], [mcp])
- Optimized startup < 600ms via lazy loading
- Reorganized codebase into core/services/cli/tools

V10.27 NotebookLM Optimization:

V10.26 Structure Reorganization:
- intelligence/: brain_manager, memory, vector_memory, feedback_learner, auto_learner, pattern_mining
- loop/: shadow_mode, workflow_manager, workflow_evolver, background_agent, transactions
- judge/: rubrics

Backward compatibility is maintained - old import paths still work.
"""

# =============================================================================
# Copyright 2026 Boring206
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

import importlib
from typing import TYPE_CHECKING

__version__ = "11.5.0"

# =============================================================================
# Lazy Loading Configuration
# =============================================================================

# Map exported names to their source modules
_IMPORT_MAP = {
    # Intelligence
    "AutoLearner": "boring.intelligence.auto_learner",
    "ErrorSolutionPair": "boring.intelligence.auto_learner",
    "BrainManager": "boring.intelligence.brain_manager",
    "LearnedPattern": "boring.intelligence.brain_manager",
    "create_brain_manager": "boring.intelligence.brain_manager",
    "FeedbackEntry": "boring.intelligence.feedback_learner",
    "FeedbackLearner": "boring.intelligence.feedback_learner",
    "LoopMemory": "boring.intelligence.memory",
    "MemoryManager": "boring.intelligence.memory",
    "ProjectMemory": "boring.intelligence.memory",
    "Pattern": "boring.intelligence.pattern_mining",
    "PatternMiner": "boring.intelligence.pattern_mining",
    "get_pattern_miner": "boring.intelligence.pattern_mining",
    # Judge
    "CODE_QUALITY_RUBRIC": "boring.judge.rubrics",
    "RUBRIC_REGISTRY": "boring.judge.rubrics",
    "SECURITY_RUBRIC": "boring.judge.rubrics",
    "Criterion": "boring.judge.rubrics",
    "Rubric": "boring.judge.rubrics",
    "get_rubric": "boring.judge.rubrics",
    "list_rubrics": "boring.judge.rubrics",
    # Loop
    "BackgroundTask": "boring.loop.background_agent",
    "BackgroundTaskRunner": "boring.loop.background_agent",
    "OperationSeverity": "boring.loop.shadow_mode",
    "PendingOperation": "boring.loop.shadow_mode",
    "ShadowModeGuard": "boring.loop.shadow_mode",
    "ShadowModeLevel": "boring.loop.shadow_mode",
    "create_shadow_guard": "boring.loop.shadow_mode",
    "TransactionManager": "boring.loop.transactions",
    "TransactionState": "boring.loop.transactions",
    "ProjectContext": "boring.loop.workflow_evolver",
    "ProjectContextDetector": "boring.loop.workflow_evolver",
    "WorkflowEvolver": "boring.loop.workflow_evolver",
    "WorkflowGapAnalyzer": "boring.loop.workflow_evolver",
    "WorkflowManager": "boring.loop.workflow_manager",
    "WorkflowMetadata": "boring.loop.workflow_manager",
    "WorkflowPackage": "boring.loop.workflow_manager",
}

# Backward compatible module aliases
_MODULE_ALIASES = {
    "brain_manager": "boring.intelligence.brain_manager",
    "memory": "boring.intelligence.memory",
    "feedback_learner": "boring.intelligence.feedback_learner",
    "auto_learner": "boring.intelligence.auto_learner",
    "pattern_mining": "boring.intelligence.pattern_mining",
    "shadow_mode": "boring.loop.shadow_mode",
    "workflow_manager": "boring.loop.workflow_manager",
    "workflow_evolver": "boring.loop.workflow_evolver",
    "background_agent": "boring.loop.background_agent",
    "transactions": "boring.loop.transactions",
    "rubrics": "boring.judge.rubrics",
}

# =============================================================================
# Static Type Checking (No Runtime Cost)
# =============================================================================

if TYPE_CHECKING:
    # Intelligence
    # Alias Modules
    # Alias Modules
    from boring.intelligence import (
        auto_learner,
        brain_manager,
        feedback_learner,
        memory,
        pattern_mining,
    )
    from boring.intelligence.auto_learner import AutoLearner, ErrorSolutionPair
    from boring.intelligence.brain_manager import (
        BrainManager,
        LearnedPattern,
        create_brain_manager,
    )
    from boring.intelligence.feedback_learner import FeedbackEntry, FeedbackLearner
    from boring.intelligence.memory import LoopMemory, MemoryManager, ProjectMemory
    from boring.intelligence.pattern_mining import Pattern, PatternMiner, get_pattern_miner
    from boring.judge import rubrics

    # Judge
    from boring.judge.rubrics import (
        CODE_QUALITY_RUBRIC,
        RUBRIC_REGISTRY,
        SECURITY_RUBRIC,
        Criterion,
        Rubric,
        get_rubric,
        list_rubrics,
    )
    from boring.loop import (
        background_agent,
        shadow_mode,
        transactions,
        workflow_evolver,
        workflow_manager,
    )

    # Loop
    from boring.loop.background_agent import BackgroundTask, BackgroundTaskRunner
    from boring.loop.shadow_mode import (
        OperationSeverity,
        PendingOperation,
        ShadowModeGuard,
        ShadowModeLevel,
        create_shadow_guard,
    )
    from boring.loop.transactions import TransactionManager, TransactionState
    from boring.loop.workflow_evolver import (
        ProjectContext,
        ProjectContextDetector,
        WorkflowEvolver,
        WorkflowGapAnalyzer,
    )
    from boring.loop.workflow_manager import (
        WorkflowManager,
        WorkflowMetadata,
        WorkflowPackage,
    )


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Version
    "__version__",
    # Intelligence
    "AutoLearner",
    "ErrorSolutionPair",
    "BrainManager",
    "LearnedPattern",
    "create_brain_manager",
    "FeedbackEntry",
    "FeedbackLearner",
    "LoopMemory",
    "MemoryManager",
    "ProjectMemory",
    "Pattern",
    "PatternMiner",
    "get_pattern_miner",
    # Judge
    "CODE_QUALITY_RUBRIC",
    "RUBRIC_REGISTRY",
    "SECURITY_RUBRIC",
    "Criterion",
    "Rubric",
    "get_rubric",
    "list_rubrics",
    # Loop
    "BackgroundTask",
    "BackgroundTaskRunner",
    "OperationSeverity",
    "PendingOperation",
    "ShadowModeGuard",
    "ShadowModeLevel",
    "create_shadow_guard",
    "TransactionManager",
    "TransactionState",
    "ProjectContext",
    "ProjectContextDetector",
    "WorkflowEvolver",
    "WorkflowGapAnalyzer",
    "WorkflowManager",
    "WorkflowMetadata",
    "WorkflowPackage",
    # Module Aliases
    "brain_manager",
    "memory",
    "shadow_mode",
    "workflow_manager",
    "workflow_evolver",
    "background_agent",
    "transactions",
    "rubrics",
    "feedback_learner",
    "auto_learner",
    "pattern_mining",
]


def __getattr__(name: str):
    """Lazy load modules and classes."""
    # 1. Check Module Aliases
    if name in _MODULE_ALIASES:
        return importlib.import_module(_MODULE_ALIASES[name])

    # 2. Check Class/Function Mappings
    if name in _IMPORT_MAP:
        module_path = _IMPORT_MAP[name]
        module = importlib.import_module(module_path)
        return getattr(module, name)

    raise AttributeError(f"module 'boring' has no attribute '{name}'")


def __dir__():
    """Return all public attributes for autocompletion."""
    return __all__ + list(_MODULE_ALIASES.keys())
