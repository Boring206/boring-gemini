from pathlib import Path

from ..config import settings


def load_custom_rules(project_root: Path) -> dict:
    """
    Load custom verification rules from .boring.toml.

    Supports:
    - [boring.verification.custom_rules]: List of custom shell commands
    - [boring.verification.excludes]: Additional exclude patterns
    - [boring.linter_configs]: Override linter arguments
    """
    rules = {
        "custom_commands": [],
        "excludes": list(settings.VERIFICATION_EXCLUDES),
        "linter_configs": dict(settings.LINTER_CONFIGS),
    }

    config_file = project_root / ".boring.toml"
    if not config_file.exists():
        return rules

    try:
        try:
            import tomllib as toml
        except ImportError:
            try:
                import tomli as toml
            except ImportError:
                return rules

        with open(config_file, "rb") as f:
            data = toml.load(f)

        # Load [boring.verification] section
        verification = data.get("boring", {}).get("verification", {})

        # Custom commands
        if "custom_rules" in verification:
            rules["custom_commands"] = verification["custom_rules"]

        # Additional excludes
        if "excludes" in verification:
            rules["excludes"].extend(verification["excludes"])

        # Linter config overrides
        linter_cfg = data.get("boring", {}).get("linter_configs", {})
        rules["linter_configs"].update(linter_cfg)

    except Exception:
        pass

    return rules
