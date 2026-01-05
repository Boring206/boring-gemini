"""
Security Module for Boring V4.0

Provides security utilities including:
- File path validation with whitelist
- Path traversal prevention
- Sensitive data masking
- Input sanitization
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .logger import log_status

# =============================================================================
# FILE PATH SECURITY
# =============================================================================

# Allowed file extensions for AI-generated content
ALLOWED_EXTENSIONS: set[str] = {
    # Code
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt", ".scala",
    # Config
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env.example",
    # Documentation
    ".md", ".txt", ".rst", ".adoc",
    # Web
    ".html", ".css", ".scss", ".less",
    # Data
    ".csv", ".xml",
    # Shell
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
}

# Directories that should never be written to
BLOCKED_DIRECTORIES: set[str] = {
    ".git",
    ".github/workflows",  # Prevent CI tampering
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".env",  # Don't allow overwriting .env
}

# Filenames that should never be modified
BLOCKED_FILENAMES: set[str] = {
    ".env",
    ".gitignore",  # Only block in certain contexts
    "secrets.json",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
}


@dataclass
class PathValidationResult:
    """Result of path validation."""
    is_valid: bool
    reason: Optional[str] = None
    normalized_path: Optional[str] = None


def validate_file_path(
    path: str,
    project_root: Path,
    allowed_extensions: set[str] = None,
    log_dir: Path = Path("logs")
) -> PathValidationResult:
    """
    Validate a file path for security concerns.

    Checks:
    1. No path traversal (../)
    2. Path is within project root
    3. Extension is in whitelist
    4. Not in blocked directories
    5. Not a blocked filename

    Args:
        path: Relative path to validate
        project_root: Project root directory
        allowed_extensions: Custom allowed extensions (defaults to ALLOWED_EXTENSIONS)
        log_dir: Directory for logging

    Returns:
        PathValidationResult with validation status and details
    """
    if not path or not path.strip():
        return PathValidationResult(False, "Empty path")

    # Normalize path
    path = path.strip().strip('"').strip("'")

    # Check for obvious path traversal
    if ".." in path:
        log_status(log_dir, "WARN", f"Path traversal attempt blocked: {path}")
        return PathValidationResult(False, "Path traversal not allowed")

    # Check for absolute paths
    if path.startswith("/") or path.startswith("\\") or (len(path) > 1 and path[1] == ":"):
        log_status(log_dir, "WARN", f"Absolute path blocked: {path}")
        return PathValidationResult(False, "Absolute paths not allowed")

    # Resolve to absolute and check containment
    try:
        full_path = (project_root / path).resolve()
        project_root_resolved = project_root.resolve()

        # Ensure path is within project root (case-insensitive on Windows)
        import os
        if os.name == 'nt':  # Windows
            # Use case-insensitive string comparison
            full_str = str(full_path).lower()
            root_str = str(project_root_resolved).lower()
            if not full_str.startswith(root_str):
                log_status(log_dir, "WARN", f"Path outside project root: {path}")
                return PathValidationResult(False, "Path must be within project root")
        else:
            if not full_path.is_relative_to(project_root_resolved):
                log_status(log_dir, "WARN", f"Path outside project root: {path}")
                return PathValidationResult(False, "Path must be within project root")
    except Exception as e:
        return PathValidationResult(False, f"Invalid path: {e}")

    # Check extension
    extensions = allowed_extensions or ALLOWED_EXTENSIONS
    if full_path.suffix.lower() not in extensions:
        return PathValidationResult(
            False,
            f"Extension '{full_path.suffix}' not allowed. Allowed: {', '.join(sorted(extensions)[:10])}..."
        )

    # Check blocked directories
    path_parts = Path(path).parts
    for blocked in BLOCKED_DIRECTORIES:
        if blocked in path_parts:
            log_status(log_dir, "WARN", f"Blocked directory access: {path}")
            return PathValidationResult(False, f"Cannot write to {blocked}/")

    # Check blocked filenames
    if full_path.name in BLOCKED_FILENAMES:
        log_status(log_dir, "WARN", f"Blocked filename: {path}")
        return PathValidationResult(False, f"Cannot modify {full_path.name}")

    # Get normalized relative path (Windows-compatible)
    try:
        if os.name == 'nt':  # Windows
            # Manual relative path calculation for case differences
            full_str = str(full_path)
            root_str = str(project_root_resolved)
            if full_str.lower().startswith(root_str.lower()):
                # Strip root and any leading separator
                normalized = full_str[len(root_str):].lstrip('\\').lstrip('/')
            else:
                normalized = path
        else:
            normalized = str(full_path.relative_to(project_root_resolved))
    except ValueError:
        normalized = path

    return PathValidationResult(True, None, normalized)


def is_safe_path(path: str, project_root: Path) -> bool:
    """Quick check if a path is safe to write to."""
    result = validate_file_path(path, project_root)
    return result.is_valid


# =============================================================================
# SENSITIVE DATA MASKING
# =============================================================================

# Patterns for sensitive data
SENSITIVE_PATTERNS = [
    # Google API keys
    (r'AIza[A-Za-z0-9_-]{35}', '[GOOGLE_API_KEY]'),
    # Generic API keys
    (r'(?i)(api[_-]?key|apikey|secret[_-]?key)\s*[=:]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', r'\1=[REDACTED]'),
    # Bearer tokens
    (r'(?i)bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', 'Bearer [JWT_TOKEN]'),
    # AWS keys
    (r'AKIA[A-Z0-9]{16}', '[AWS_ACCESS_KEY]'),
    # Generic secrets
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']+["\']?', r'\1=[REDACTED]'),
]


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data in text before logging.

    Args:
        text: Text that may contain sensitive data

    Returns:
        Text with sensitive data masked
    """
    if not text:
        return text

    masked = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = re.sub(pattern, replacement, masked)

    return masked


def safe_log(log_dir: Path, level: str, message: str):
    """Log message with sensitive data masked."""
    from .logger import log_status
    masked_message = mask_sensitive_data(message)
    log_status(log_dir, level, masked_message)


# =============================================================================
# INPUT SANITIZATION
# =============================================================================

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing potentially dangerous characters.

    Args:
        filename: Raw filename

    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove null bytes and other control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    return filename or "unnamed"


def sanitize_content(content: str, max_length: int = 1_000_000) -> str:
    """
    Sanitize content before writing to files.

    Args:
        content: Raw content
        max_length: Maximum allowed length

    Returns:
        Sanitized content
    """
    if not content:
        return ""

    # Truncate if too long
    if len(content) > max_length:
        content = content[:max_length] + "\n# ... content truncated ...\n"

    return content
