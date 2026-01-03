from typing import Optional
from ..instance import mcp, MCP_AVAILABLE
from ..utils import get_project_root_or_error, configure_runtime_for_project
from ...audit import audited

# ==============================================================================
# KNOWLEDGE TOOLS
# ==============================================================================

@audited
def boring_learn(project_path: Optional[str] = None) -> dict:
    """
    Trigger learning from .boring_memory to .boring_brain.
    
    Extracts successful patterns from loop history and error solutions,
    storing them in learned_patterns/ for future reference.
    
    Args:
        project_path: Optional explicit path to project root
        
    Returns:
        Learning result with patterns extracted
    """
    try:
        from ...brain_manager import BrainManager
        from ...storage import SQLiteStorage
        from ...config import settings
        
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error
        
        configure_runtime_for_project(project_root)
        
        # Initialize storage and brain
        storage = SQLiteStorage(project_root / ".boring_memory", settings.LOG_DIR)
        brain = BrainManager(project_root, settings.LOG_DIR)
        
        # Learn from memory
        return brain.learn_from_memory(storage)
        
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@audited
def boring_create_rubrics(project_path: Optional[str] = None) -> dict:
    """
    Create default evaluation rubrics in .boring_brain/rubrics/.
    
    Creates rubrics for: implementation_plan, task_list, code_quality.
    These are used for LLM-as-Judge evaluation.
    
    Args:
        project_path: Optional explicit path to project root
        
    Returns:
        List of rubrics created
    """
    try:
        from ...brain_manager import BrainManager
        from ...config import settings
        
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error
        
        configure_runtime_for_project(project_root)
        
        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.create_default_rubrics()
        
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@audited
def boring_brain_summary(project_path: Optional[str] = None) -> dict:
    """
    Get summary of .boring_brain knowledge base.
    
    Shows counts of patterns, rubrics, and adaptations.
    
    Args:
        project_path: Optional explicit path to project root
        
    Returns:
        Brain summary
    """
    try:
        from ...brain_manager import BrainManager
        from ...config import settings
        
        project_root, error = get_project_root_or_error(project_path)
        if error:
            return error
        
        configure_runtime_for_project(project_root)
        
        brain = BrainManager(project_root, settings.LOG_DIR)
        return brain.get_brain_summary()
        
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

if MCP_AVAILABLE and mcp is not None:
    mcp.tool()(boring_learn)
    mcp.tool()(boring_create_rubrics)
    mcp.tool()(boring_brain_summary)
