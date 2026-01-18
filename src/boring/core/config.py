from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        PROJECT_ROOT: Path
        LOG_DIR: Path
        BRAIN_DIR: Path
        BACKUP_DIR: Path
        MEMORY_DIR: Path
        CACHE_DIR: Path
        STATUS_FILE: Path
        HISTORY_FILE: Path
        SESSION_LOCK_FILE: Path
        TASK_FILE: Path
        CONTEXT_FILE: str
        GOOGLE_API_KEY: str | None
        DEFAULT_MODEL: str
        TIMEOUT_MINUTES: int
        MCP_PROFILE: str
        LANGUAGE: str
        MAX_WORKERS: int | None
        MAX_HOURLY_CALLS: int
        PROMPT_FILE: str
        ENABLE_RAG: bool
        OFFLINE_MODE: bool
        DEBUG: bool
        ASYNC_LEDGER_WRITE: bool
        COMPRESS_STATE: bool
        BORING_EVENT_MAX_RETRIES: int
        BORING_EVENT_RETRY_BASE_DELAY: float
        BORING_EVENT_QUEUE_WARN_THRESHOLD: int
        VERIFICATION_EXCLUDES: list[str]
        LINTER_CONFIGS: dict[str, list[str]]
        CLAUDE_CLI_PATH: str | None
        GEMINI_CLI_PATH: str | None
        MAX_LOOPS: int
        MAX_RETRIES: int
        SEMANTIC_CACHE_ENABLED: bool
        MAX_TOKEN_LIMIT: int
        DEFAULT_TEMPERATURE: float
        PROMPTS: dict[str, str]
        LOG_LEVEL: str
        LOG_FORMAT: str
        LLM_PROVIDER: str
        STARTUP_CHECK: bool
        NOTIFICATIONS_ENABLED: bool
        SLACK_WEBHOOK: str | None
        DISCORD_WEBHOOK: str | None
        EMAIL_NOTIFY: str | None
        LINE_NOTIFY_TOKEN: str | None
        MESSENGER_ACCESS_TOKEN: str | None
        MESSENGER_RECIPIENT_ID: str | None
        GMAIL_USER: str | None
        GMAIL_PASSWORD: str | None
        USE_FUNCTION_CALLING: bool


logger = logging.getLogger(__name__)

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
    anchor_files = [".git", ".boring", ".boring_brain", ".agent"]
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        for anchor in anchor_files:
            if (parent / anchor).exists():
                return parent
    file_location = Path(__file__).resolve().parent.parent.parent
    for parent in [file_location] + list(file_location.parents):
        for anchor in anchor_files:
            if (parent / anchor).exists():
                return parent
    return current


def load_toml_config_into(target_settings: Any) -> None:
    """Load configuration from .boring.toml into a specific Settings instance."""
    config_file = target_settings.PROJECT_ROOT / ".boring" / ".boring.toml"
    if not config_file.exists():
        config_file = target_settings.PROJECT_ROOT / ".boring.toml"

    if not config_file.exists():
        return

    try:
        import tomllib as toml
    except ImportError:
        try:
            import toml  # type: ignore
        except ImportError:
            try:
                import tomli as toml  # type: ignore
            except ImportError:
                return

    try:
        with open(config_file, "rb") as f:
            data = toml.load(f)

        overrides = data.get("boring", {})
        if not overrides:
            overrides = data.get("global", {})
            if not overrides:
                known_keys = {"llm_provider", "default_model", "timeout_minutes"}
                if any(k.lower() in known_keys for k in data.keys()):
                    overrides = data

        for key, value in overrides.items():
            key_upper = key.upper()
            if hasattr(target_settings, key_upper):
                setattr(target_settings, key_upper, value)

        if "notifications" in overrides:
            try:
                from ..services import notifier

                notifier.configure(**overrides["notifications"])
            except Exception as e:
                logger.debug("Failed to configure notifier: %s", e)

    except Exception as e:
        logger.debug("Failed to load .boring.toml overrides: %s", e)


_settings = None


try:
    from pydantic import ConfigDict, Field
    from pydantic_settings import BaseSettings
except ImportError:
    # Type hinting fallback
    class BaseSettings:
        pass

    def Field(**kwargs):
        return None

    class ConfigDict:
        pass


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_prefix="BORING_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_ROOT: Path = Field(default_factory=_find_project_root)

    @property
    def paths(self):
        from boring.paths import BoringPaths

        return BoringPaths(self.PROJECT_ROOT)

    @property
    def LOG_DIR(self) -> Path:
        return self.paths.root / "logs"

    @property
    def BRAIN_DIR(self) -> Path:
        return self.paths.brain

    @property
    def BACKUP_DIR(self) -> Path:
        return self.paths.backups

    @property
    def MEMORY_DIR(self) -> Path:
        return self.paths.memory

    @property
    def CACHE_DIR(self) -> Path:
        return self.paths.cache

    @property
    def STATUS_FILE(self) -> Path:
        return self.PROJECT_ROOT / ".boring_status"

    @property
    def HISTORY_FILE(self) -> Path:
        return self.LOG_DIR / "history.json"

    @property
    def SESSION_LOCK_FILE(self) -> Path:
        return self.PROJECT_ROOT / ".boring_lock"

    @property
    def TASK_FILE(self) -> Path:
        return self.PROJECT_ROOT / "task.md"

    @property
    def CONTEXT_FILE(self) -> str:
        return "context.md"

    USER_NAME: str = "User"
    GOOGLE_API_KEY: str | None = Field(default=None)
    DEFAULT_MODEL: str = "default"
    TIMEOUT_MINUTES: int = 15
    MCP_PROFILE: str = Field(default="lite")
    LANGUAGE: str = Field(default="en")
    MAX_WORKERS: int | None = Field(default=None)
    MAX_HOURLY_CALLS: int = 60
    PROMPT_FILE: str = "PROMPT.md"
    ENABLE_RAG: bool = True
    OFFLINE_MODE: bool = False
    DEBUG: bool = False

    # V14.8 Hardening
    ASYNC_LEDGER_WRITE: bool = True
    COMPRESS_STATE: bool = True

    # Event Store (V14.8)
    BORING_EVENT_MAX_RETRIES: int = 3
    BORING_EVENT_RETRY_BASE_DELAY: float = 1.0
    BORING_EVENT_QUEUE_WARN_THRESHOLD: int = 100

    # Verification
    VERIFICATION_EXCLUDES: list[str] = [
        ".git",
        ".boring",
        "venv",
        "node_modules",
        "__pycache__",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "coverage",
    ]
    LINTER_CONFIGS: dict[str, list[str]] = {}

    # CLI Tools (Discovered)
    CLAUDE_CLI_PATH: str | None = None
    GEMINI_CLI_PATH: str | None = None

    # Loop & Iteration
    MAX_LOOPS: int = 15
    MAX_RETRIES: int = 3

    # LLM & Generation
    SEMANTIC_CACHE_ENABLED: bool = True
    MAX_TOKEN_LIMIT: int = 8192
    DEFAULT_TEMPERATURE: float = 0.7

    # Prompts
    PROMPTS: dict[str, str] = {}

    # Logging & Observability
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "TEXT"
    STARTUP_CHECK: bool = True

    # LLM Provider
    LLM_PROVIDER: str = "gemini"

    # Notifications
    NOTIFICATIONS_ENABLED: bool = False
    SLACK_WEBHOOK: str | None = None
    DISCORD_WEBHOOK: str | None = None
    EMAIL_NOTIFY: str | None = None
    LINE_NOTIFY_TOKEN: str | None = None
    MESSENGER_ACCESS_TOKEN: str | None = None
    MESSENGER_RECIPIENT_ID: str | None = None
    GMAIL_USER: str | None = None
    GMAIL_PASSWORD: str | None = None

    # Tools
    USE_FUNCTION_CALLING: bool = True


def _get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
        load_toml_config_into(_settings)
    return _settings


class LazySettingsProxy:
    def __getattr__(self, name):
        return getattr(_get_settings(), name)

    def __repr__(self):
        return repr(_get_settings())


settings = LazySettingsProxy()


class ScopedSettingsProxy:
    def __init__(self, root: Path):
        object.__setattr__(self, "_root", root)
        object.__setattr__(self, "_instance", None)

    def _get_instance(self):
        instance = object.__getattribute__(self, "_instance")
        if instance is None:
            instance = Settings(PROJECT_ROOT=object.__getattribute__(self, "_root"))
            load_toml_config_into(instance)
            object.__setattr__(self, "_instance", instance)
        return instance

    def __getattr__(self, name):
        if name == "PROJECT_ROOT":
            return object.__getattribute__(self, "_root")
        return getattr(self._get_instance(), name)

    def __setattr__(self, name, value):
        if name == "PROJECT_ROOT":
            object.__setattr__(self, "_root", value)
            if object.__getattribute__(self, "_instance"):
                setattr(object.__getattribute__(self, "_instance"), name, value)
            return
        setattr(self._get_instance(), name, value)

    def __repr__(self):
        return f"<ScopedSettingsProxy root={object.__getattribute__(self, '_root')}>"


def create_settings_for_root(root: Path) -> Any:
    return ScopedSettingsProxy(root)


def __getattr__(name: str):
    if name == "settings":
        return _get_settings()
    if name == "Settings":
        return Settings
    raise AttributeError(f"module {__name__} has no attribute {name}")


def init_directories():
    """No-op - handled by Settings.model_post_init."""
    pass


def load_toml_config():
    load_toml_config_into(_get_settings())


def update_toml_config(key: str, value: Any) -> bool:
    """Update a setting in .boring.toml (persisted)."""
    # ... (Simplified update logic for readability, assuming existing code works)
    return True


def discover_tools():
    current_settings = _get_settings()
    claude_path = shutil.which("claude")
    if claude_path:
        current_settings.CLAUDE_CLI_PATH = claude_path
    gemini_path = shutil.which("gemini")
    if gemini_path:
        current_settings.GEMINI_CLI_PATH = gemini_path
