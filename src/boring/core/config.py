from pathlib import Path
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

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


class Settings(BaseSettings):
    """
    Centralized configuration for Boring V4.0.
    Loads from environment variables (BORING_*) or .env file.
    """

    model_config = ConfigDict(
        env_prefix="BORING_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_ROOT: Path = Field(default_factory=_find_project_root)
    LOG_DIR: Path = Field(default=Path(".boring/logs"))
    BRAIN_DIR: Path = Field(default=Path(".boring/brain"))
    BACKUP_DIR: Path = Field(default=Path(".boring/backups"))
    MEMORY_DIR: Path = Field(default=Path(".boring/memory"))
    CACHE_DIR: Path = Field(default=Path(".boring/cache"))

    # Gemini Settings
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    DEFAULT_MODEL: str = "models/gemini-2.5-flash"
    TIMEOUT_MINUTES: int = 15
    MCP_PROFILE: str = Field(default="lite", description="Tool profile: ultra_lite, minimal, lite, standard, full")

    # LLM Settings (V10.13 Modular)
    LLM_PROVIDER: str = Field(
        default="gemini-cli", description="gemini-cli, claude-code, mcp-gateway, sdk, ollama"
    )
    LLM_BASE_URL: Optional[str] = Field(default=None)
    LLM_MODEL: Optional[str] = Field(default=None)

    # Tool Discovery
    CLAUDE_CLI_PATH: Optional[str] = None
    GEMINI_CLI_PATH: Optional[str] = None

    # V4.0 Feature Flags
    USE_FUNCTION_CALLING: bool = True  # Use structured function calls

    USE_INTERACTIONS_API: bool = False  # Use new stateful Interactions API (experimental)
    USE_DIFF_PATCHING: bool = True  # Prefer search/replace over full file rewrites

    # Loop Settings
    MAX_LOOPS: int = 100
    MAX_HOURLY_CALLS: int = 50
    HISTORY_LIMIT: int = 10  # Number of previous turns to keep in context

    # Special Files
    PROMPT_FILE: str = "PROMPT.md"
    CONTEXT_FILE: str = "GEMINI.md"
    TASK_FILE: str = "@fix_plan.md"
    STATUS_FILE: str = "status.json"

    # DX Verification Settings (V10.13)
    VERIFICATION_EXCLUDES: list[str] = Field(
        default_factory=lambda: [
            ".git",
            ".github",
            ".vscode",
            ".idea",
            "venv",
            ".venv",
            "node_modules",
            "build",
            "dist",
            "__pycache__",
        ]
    )
    LINTER_CONFIGS: dict = Field(default_factory=dict)  # Map tool name -> list of args
    PROMPTS: dict = Field(default_factory=dict)  # Map prompt name -> template string


settings = Settings()


# Ensure critical directories exist
def init_directories():
    # Ensure they are Path objects (Pydantic might leave them as strings if loaded from env improperly)
    if isinstance(settings.LOG_DIR, str):
        settings.LOG_DIR = Path(settings.LOG_DIR)
    if isinstance(settings.BRAIN_DIR, str):
        settings.BRAIN_DIR = Path(settings.BRAIN_DIR)
    if isinstance(settings.BACKUP_DIR, str):
        settings.BACKUP_DIR = Path(settings.BACKUP_DIR)
    if isinstance(settings.MEMORY_DIR, str):
        settings.MEMORY_DIR = Path(settings.MEMORY_DIR)

    # Ensure they are absolute (relative to PROJECT_ROOT if not)
    if not settings.LOG_DIR.is_absolute():
        settings.LOG_DIR = settings.PROJECT_ROOT / settings.LOG_DIR
    if not settings.BRAIN_DIR.is_absolute():
        settings.BRAIN_DIR = settings.PROJECT_ROOT / settings.BRAIN_DIR
    if not settings.BACKUP_DIR.is_absolute():
        settings.BACKUP_DIR = settings.PROJECT_ROOT / settings.BACKUP_DIR
    if not settings.MEMORY_DIR.is_absolute():
        settings.MEMORY_DIR = settings.PROJECT_ROOT / settings.MEMORY_DIR
    if not settings.CACHE_DIR.is_absolute():
        settings.CACHE_DIR = settings.PROJECT_ROOT / settings.CACHE_DIR

    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    settings.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_toml_config():
    """Load configuration from .boring.toml if present."""
    config_file = settings.PROJECT_ROOT / ".boring.toml"
    if not config_file.exists():
        return

    try:
        try:
            import tomllib as toml
        except ImportError:
            try:
                import tomli as toml
            except ImportError:
                # No TOML parser available
                return

        with open(config_file, "rb") as f:
            data = toml.load(f)

        # Support [boring] or top-level keys
        # If [boring] section exists, prioritize it
        overrides = data.get("boring", {})
        if not overrides:
            # Fallback to top-level or [global] if users use that style
            overrides = data.get("global", {})
            if not overrides:
                # Treat whole file as flat config if no sections match
                # Check if known keys exist at top level
                known_keys = {"llm_provider", "default_model", "timeout_minutes"}
                if any(k.lower() in known_keys for k in data.keys()):
                    overrides = data

        for key, value in overrides.items():
            key_upper = key.upper()
            # Security: Only update existing settings
            if hasattr(settings, key_upper):
                setattr(settings, key_upper, value)

    except Exception:
        # Fail silently during config load to avoid breaking startup
        pass


def update_toml_config(key: str, value: any):
    """Update a key in .boring.toml."""
    config_file = settings.PROJECT_ROOT / ".boring.toml"

    # Load existing or create empty
    data = {}
    if config_file.exists():
        try:
            import toml
            with open(config_file) as f:
                data = toml.load(f)
        except Exception:
            pass

    if "boring" not in data:
        data["boring"] = {}

    data["boring"][key.lower()] = value

    try:
        import toml
        with open(config_file, "w") as f:
            toml.dump(data, f)
        # Update current settings object too
        key_upper = key.upper()
        if hasattr(settings, key_upper):
            setattr(settings, key_upper, value)
        return True
    except Exception:
        return False


def discover_tools():
    """Discover available local CLI tools."""
    import shutil

    # Discover Claude Code
    claude_path = shutil.which("claude")
    if claude_path:
        settings.CLAUDE_CLI_PATH = claude_path

    # Discover Gemini CLI
    gemini_path = shutil.which("gemini")
    if gemini_path:
        settings.GEMINI_CLI_PATH = gemini_path


# Auto-load configuration overrides
load_toml_config()
discover_tools()
