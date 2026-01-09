"""
Boring for Gemini - AI Coding Assistant

V10.26 Structure Reorganization:
- intelligence/: brain_manager, memory, vector_memory, feedback_learner, auto_learner, pattern_mining
- loop/: shadow_mode, workflow_manager, workflow_evolver, background_agent, transactions
- judge/: rubrics

Backward compatibility is maintained - old import paths still work.
"""

__version__ = "10.26.0"

# =============================================================================
# Backward Compatibility Layer (V10.26)
# These re-exports maintain compatibility with old import paths.
# New code should use the new paths (e.g., from boring.intelligence import MemoryManager)
# =============================================================================

# From intelligence/ (moved from root)
from boring.intelligence.auto_learner import (
    AutoLearner as AutoLearner,
)
from boring.intelligence.auto_learner import (
    ErrorSolutionPair as ErrorSolutionPair,
)
from boring.intelligence.brain_manager import (
    BrainManager as BrainManager,
)
from boring.intelligence.brain_manager import (
    LearnedPattern as LearnedPattern,
)
from boring.intelligence.brain_manager import (
    create_brain_manager as create_brain_manager,
)
from boring.intelligence.feedback_learner import (
    FeedbackEntry as FeedbackEntry,
)
from boring.intelligence.feedback_learner import (
    FeedbackLearner as FeedbackLearner,
)
from boring.intelligence.memory import (
    LoopMemory as LoopMemory,
)
from boring.intelligence.memory import (
    MemoryManager as MemoryManager,
)
from boring.intelligence.memory import (
    ProjectMemory as ProjectMemory,
)
from boring.intelligence.pattern_mining import (
    Pattern as Pattern,
)
from boring.intelligence.pattern_mining import (
    PatternMiner as PatternMiner,
)
from boring.intelligence.pattern_mining import (
    get_pattern_miner as get_pattern_miner,
)
from boring.intelligence.vector_memory import (
    CHROMADB_AVAILABLE as CHROMADB_AVAILABLE,
)
from boring.intelligence.vector_memory import (
    Experience as Experience,
)
from boring.intelligence.vector_memory import (
    VectorMemory as VectorMemory,
)
from boring.intelligence.vector_memory import (
    create_vector_memory as create_vector_memory,
)

# From judge/ (moved from root)
from boring.judge.rubrics import (
    CODE_QUALITY_RUBRIC as CODE_QUALITY_RUBRIC,
)
from boring.judge.rubrics import (
    RUBRIC_REGISTRY as RUBRIC_REGISTRY,
)
from boring.judge.rubrics import (
    SECURITY_RUBRIC as SECURITY_RUBRIC,
)
from boring.judge.rubrics import (
    Criterion as Criterion,
)
from boring.judge.rubrics import (
    Rubric as Rubric,
)
from boring.judge.rubrics import (
    get_rubric as get_rubric,
)
from boring.judge.rubrics import (
    list_rubrics as list_rubrics,
)

# From loop/ (moved from root)
from boring.loop.background_agent import (
    BackgroundTask as BackgroundTask,
)
from boring.loop.background_agent import (
    BackgroundTaskRunner as BackgroundTaskRunner,
)
from boring.loop.shadow_mode import (
    OperationSeverity as OperationSeverity,
)
from boring.loop.shadow_mode import (
    PendingOperation as PendingOperation,
)
from boring.loop.shadow_mode import (
    ShadowModeGuard as ShadowModeGuard,
)
from boring.loop.shadow_mode import (
    ShadowModeLevel as ShadowModeLevel,
)
from boring.loop.shadow_mode import (
    create_shadow_guard as create_shadow_guard,
)
from boring.loop.transactions import (
    TransactionManager as TransactionManager,
)
from boring.loop.transactions import (
    TransactionState as TransactionState,
)
from boring.loop.workflow_evolver import (
    ProjectContext as ProjectContext,
)
from boring.loop.workflow_evolver import (
    ProjectContextDetector as ProjectContextDetector,
)
from boring.loop.workflow_evolver import (
    WorkflowEvolver as WorkflowEvolver,
)
from boring.loop.workflow_evolver import (
    WorkflowGapAnalyzer as WorkflowGapAnalyzer,
)
from boring.loop.workflow_manager import (
    WorkflowManager as WorkflowManager,
)
from boring.loop.workflow_manager import (
    WorkflowMetadata as WorkflowMetadata,
)
from boring.loop.workflow_manager import (
    WorkflowPackage as WorkflowPackage,
)

# Public API
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
    "CHROMADB_AVAILABLE",
    "Experience",
    "VectorMemory",
    "create_vector_memory",
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
]

# Backward compatible module aliases
# These allow `from boring import memory` to work
brain_manager = None  # Lazy load
memory = None
vector_memory = None
shadow_mode = None
workflow_manager = None
workflow_evolver = None
background_agent = None
transactions = None
rubrics = None
feedback_learner = None
auto_learner = None
pattern_mining = None


def __getattr__(name: str):
    """Lazy module loading for backward compatibility."""
    import importlib

    module_map = {
        "brain_manager": "boring.intelligence.brain_manager",
        "memory": "boring.intelligence.memory",
        "vector_memory": "boring.intelligence.vector_memory",
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

    if name in module_map:
        # Note: Add deprecation warning when desired
        # import warnings
        # warnings.warn(
        #     f"Importing '{name}' from boring is deprecated. "
        #     f"Use '{module_map[name]}' instead.",
        #     DeprecationWarning,
        #     stacklevel=2,
        # )
        return importlib.import_module(module_map[name])

    raise AttributeError(f"module 'boring' has no attribute '{name}'")
