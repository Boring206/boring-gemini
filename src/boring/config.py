from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

# V4.0 Supported Models
SUPPORTED_MODELS = [
    "models/gemini-2.0-flash-exp",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite", 
    "models/gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "deep-research-pro-preview-12-2025",
]


class Settings(BaseSettings):
    """
    Centralized configuration for Boring V4.0.
    Loads from environment variables (BORING_*) or .env file.
    """
    model_config = ConfigDict(
        env_prefix="BORING_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Project Paths
    def _find_project_root() -> Path:
        """Find project root by looking for anchor files.
        
        Search strategy:
        1. First try CWD and its parents (for boring start command)
        2. Then try __file__ location and its parents (for MCP server)
        3. Fall back to CWD if nothing found
        """
        anchor_files = [".git", ".boring_brain", ".agent"]
        
        # Strategy 1: Search from CWD
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            for anchor in anchor_files:
                if (parent / anchor).exists():
                    return parent
        
        # Strategy 2: Search from this file's location (for MCP mode)
        # This file is at src/boring/config.py, so project root is 3 levels up
        file_location = Path(__file__).resolve().parent.parent.parent
        for parent in [file_location] + list(file_location.parents):
            for anchor in anchor_files:
                if (parent / anchor).exists():
                    return parent
        
        # Strategy 3: Fallback to CWD
        return current

    PROJECT_ROOT: Path = Field(default_factory=_find_project_root)
    LOG_DIR: Path = Field(default=Path("logs"))
    BRAIN_DIR: Path = Field(default=Path(".boring_brain"))
    BACKUP_DIR: Path = Field(default=Path(".boring_backups"))
    MEMORY_DIR: Path = Field(default=Path(".boring_memory"))

    # Gemini Settings
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    DEFAULT_MODEL: str = "default"
    TIMEOUT_MINUTES: int = 15
    
    # V4.0 Feature Flags
    USE_FUNCTION_CALLING: bool = True  # Use structured function calls
    USE_VECTOR_MEMORY: bool = False    # Use ChromaDB for semantic memory (requires extra deps)
    USE_INTERACTIONS_API: bool = False # Use new stateful Interactions API (experimental)
    USE_DIFF_PATCHING: bool = True     # Prefer search/replace over full file rewrites
    
    # Loop Settings
    MAX_LOOPS: int = 100
    MAX_HOURLY_CALLS: int = 50
    HISTORY_LIMIT: int = 10  # Number of previous turns to keep in context

    # Special Files
    PROMPT_FILE: str = "PROMPT.md"
    CONTEXT_FILE: str = "GEMINI.md"
    TASK_FILE: str = "@fix_plan.md"
    STATUS_FILE: str = "status.json"

settings = Settings()

# Ensure critical directories exist
def init_directories():
    # Ensure they are Path objects (Pydantic might leave them as strings if loaded from env improperly)
    if isinstance(settings.LOG_DIR, str): settings.LOG_DIR = Path(settings.LOG_DIR)
    if isinstance(settings.BRAIN_DIR, str): settings.BRAIN_DIR = Path(settings.BRAIN_DIR)
    if isinstance(settings.BACKUP_DIR, str): settings.BACKUP_DIR = Path(settings.BACKUP_DIR)
    if isinstance(settings.MEMORY_DIR, str): settings.MEMORY_DIR = Path(settings.MEMORY_DIR)

    # Ensure they are absolute (relative to PROJECT_ROOT if not)
    if not settings.LOG_DIR.is_absolute():
        settings.LOG_DIR = settings.PROJECT_ROOT / settings.LOG_DIR
    if not settings.BRAIN_DIR.is_absolute():
        settings.BRAIN_DIR = settings.PROJECT_ROOT / settings.BRAIN_DIR
    if not settings.BACKUP_DIR.is_absolute():
        settings.BACKUP_DIR = settings.PROJECT_ROOT / settings.BACKUP_DIR
    if not settings.MEMORY_DIR.is_absolute():
        settings.MEMORY_DIR = settings.PROJECT_ROOT / settings.MEMORY_DIR

    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    settings.MEMORY_DIR.mkdir(parents=True, exist_ok=True)

