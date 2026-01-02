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
        """Find project root by looking for anchor files."""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".git").exists() or (parent / ".boring_brain").exists():
                return parent
        return current

    PROJECT_ROOT: Path = Field(default_factory=_find_project_root)
    LOG_DIR: Path = Field(default=Path("logs"))
    BRAIN_DIR: Path = Field(default=Path(".boring_brain"))
    BACKUP_DIR: Path = Field(default=Path(".boring_backups"))
    MEMORY_DIR: Path = Field(default=Path(".boring_memory"))

    # Gemini Settings
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    DEFAULT_MODEL: str = "models/gemini-2.0-flash-exp"
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
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    settings.MEMORY_DIR.mkdir(parents=True, exist_ok=True)

