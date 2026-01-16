"""
Internationalization (i18n) Utility.
Handles loading of locale files and text translation.
Default Language: Traditional Chinese (zh).
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Import lazily to avoid heavy deps at module import time.
try:
    from rich.console import Console
except Exception:  # pragma: no cover - fallback if rich isn't available
    Console = None


def _load_pyproject_language(project_root: Path | None = None) -> str | None:
    root = project_root or Path.cwd()
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    try:
        try:
            import tomllib as toml
        except ImportError:
            import tomli as toml
        data = toml.loads(pyproject_path.read_text(encoding="utf-8"))
        tool_cfg = data.get("tool", {}).get("boring", {})
        if isinstance(tool_cfg, dict):
            lang = tool_cfg.get("language") or tool_cfg.get("lang")
            if isinstance(lang, str) and lang.strip():
                return lang.strip()
            i18n_cfg = tool_cfg.get("i18n", {})
            if isinstance(i18n_cfg, dict):
                lang = i18n_cfg.get("language") or i18n_cfg.get("lang")
                if isinstance(lang, str) and lang.strip():
                    return lang.strip()
    except Exception:
        return None
    return None


def _resolve_language(lang: str | None = None) -> str:
    if lang:
        return lang
    env_lang = os.environ.get("BORING_LANG") or os.environ.get("BORING_LANGUAGE")
    if env_lang:
        return env_lang
    try:
        from boring.core.config import settings

        if getattr(settings, "LANGUAGE", None):
            return settings.LANGUAGE
    except Exception as e:
        logger.debug("Failed to load language from settings: %s", e)
    pyproject_lang = _load_pyproject_language()
    if pyproject_lang:
        return pyproject_lang
    return "zh"


class Translator:
    def __init__(self, lang: str | None = None):
        # Default to Traditional Chinese per User Rules
        self.lang = _resolve_language(lang)
        self.translations: dict[str, str] = {}
        self._load_translations()

    def _load_translations(self):
        """Load JSON locale file."""
        try:
            # Locate 'locales' dir relative to this file
            base_dir = Path(__file__).parent.parent / "locales"
            locale_file = base_dir / f"{self.lang}.json"

            if locale_file.exists():
                content = locale_file.read_text(encoding="utf-8")
                self.translations = json.loads(content)
            else:
                # Fallback to EN if specific lang missing? Or just empty?
                # Try 'en' as fallback
                fallback = base_dir / "en.json"
                if fallback.exists() and self.lang != "en":
                    self.translations = json.loads(fallback.read_text(encoding="utf-8"))
        except Exception as e:
            logger.debug("Failed to load translations: %s", e)

    def get(self, key: str, **kwargs) -> str:
        """
        Get translated string.
        Supports format arguments: T.get("hello", name="World") -> "Hello World"
        """
        text = self.translations.get(key, key)  # Return key if missing
        try:
            if kwargs:
                return TranslatedString(text.format(**kwargs))
        except Exception as e:
            logger.debug("Failed to format translation key '%s': %s", key, e)
        return TranslatedString(text)

    def __call__(self, key: str, **kwargs) -> str:
        """Shortcut for get."""
        return self.get(key, **kwargs)

    def set_language(self, lang: str):
        """Switch language in-place."""
        self.lang = lang
        self._load_translations()


# Global Instance
T = Translator()


def set_language(lang: str):
    """Switch language at runtime."""
    T.set_language(lang)


class LocalizedConsole(Console):  # type: ignore[misc]
    """Console wrapper that auto-translates plain string output."""

    def print(self, *objects, **kwargs):  # type: ignore[override]
        if objects and isinstance(objects[0], str) and not isinstance(objects[0], TranslatedString):
            objects = (T(objects[0]),) + objects[1:]
        return super().print(*objects, **kwargs)


class TranslatedString(str):
    """Marker type to avoid double-translation in LocalizedConsole."""
