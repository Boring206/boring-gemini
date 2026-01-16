from difflib import get_close_matches


def suggest_correction(typo: str, choices: list[str], cutoff: float = 0.6) -> str | None:
    """
    Find the closest match for a typo from a list of choices.

    Args:
        typo: The mistyped string.
        choices: List of valid strings.
        cutoff: Similarity threshold (0.0 to 1.0).

    Returns:
        The best match or None.
    """
    matches = get_close_matches(typo, choices, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def get_boring_commands() -> list[str]:
    """Return a list of common boring commands."""
    return [
        "start",
        "stop",
        "flow",
        "fix",
        "check",
        "save",
        "watch",
        "evolve",
        "guide",
        "status",
        "clean",
        "doctor",
        "setup-extensions",
        "mcp-register",
        "health",
        "version",
        "wizard",
        "model",
        "offline",
    ]
