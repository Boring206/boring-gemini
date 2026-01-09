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

from boring.core.logger import log_status

# =============================================================================
# FILE PATH SECURITY
# =============================================================================

# Allowed file extensions for AI-generated content
ALLOWED_EXTENSIONS: set[str] = {
    # Code
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".swift",
    ".kt",
    ".scala",
    # Config
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env.example",
    # Documentation
    ".md",
    ".txt",
    ".rst",
    ".adoc",
    # Web
    ".html",
    ".css",
    ".scss",
    ".less",
    # Data
    ".csv",
    ".xml",
    # Shell
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".bat",
    ".cmd",
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
    path: str, project_root: Path, allowed_extensions: set[str] = None, log_dir: Path = Path("logs")
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

        if os.name == "nt":  # Windows
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

    # Check extension
    extensions = allowed_extensions or ALLOWED_EXTENSIONS
    if full_path.suffix.lower() not in extensions:
        return PathValidationResult(
            False,
            f"Extension '{full_path.suffix}' not allowed. Allowed: {', '.join(sorted(extensions)[:10])}...",
        )

    # Get normalized relative path (Windows-compatible)
    try:
        if os.name == "nt":  # Windows
            # Manual relative path calculation for case differences
            full_str = str(full_path)
            root_str = str(project_root_resolved)
            if full_str.lower().startswith(root_str.lower()):
                # Strip root and any leading separator
                normalized = full_str[len(root_str) :].lstrip("\\").lstrip("/")
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
    (r"AIza[A-Za-z0-9_-]{35}", "[GOOGLE_API_KEY]"),
    # Generic API keys
    (
        r'(?i)(api[_-]?key|apikey|secret[_-]?key)\s*[=:]\s*["\']?([A-Za-z0-9_-]{20,})["\']?',
        r"\1=[REDACTED]",
    ),
    # Bearer tokens
    (r"(?i)bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "Bearer [JWT_TOKEN]"),
    # AWS keys
    (r"AKIA[A-Z0-9]{16}", "[AWS_ACCESS_KEY]"),
    # Generic secrets
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']+["\']?', r"\1=[REDACTED]"),
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
    from boring.core.logger import log_status

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
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

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


# =============================================================================
# SECURITY SCANNER (SAST + Secret Detection + Dependency Scan)
# =============================================================================

# Extended secret patterns for comprehensive detection
SECRET_SCAN_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"(?i)aws(.{0,20})?['\"][0-9a-zA-Z/+]{40}['\"]",
    "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
    "GitHub OAuth": r"gho_[a-zA-Z0-9]{36}",
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Slack Token": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}",
    "Private Key": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    "Generic Secret": r"(?i)(password|secret|api_key|apikey|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
    "JWT Token": r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
    "Database URL": r"(?i)(mysql|postgres|mongodb|redis):\/\/[^:]+:[^@]+@",
    "OpenAI Key": r"sk-[a-zA-Z0-9]{48}",
    "Stripe Key": r"sk_live_[a-zA-Z0-9]{24}",
    "Anthropic Key": r"sk-ant-[a-zA-Z0-9]{32}",
    # JS/TS Ecosystem Tokens (Phase 13 Enhancement)
    "NPM Token": r"npm_[a-zA-Z0-9]{36}",
    "Vercel Token": r"vercel_[a-zA-Z0-9]{24}",
    "Yarn Token": r"yarn_[a-zA-Z0-9]{40}",
    "Supabase Key": r"sbp_[a-zA-Z0-9]{40}",
    "Firebase Key": r"AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}",
    "Netlify Token": r"nft_[a-zA-Z0-9]{40}",
}


@dataclass
class SecurityIssue:
    """Represents a security issue found during scanning."""

    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # secret, vulnerability, dependency
    file_path: str
    line_number: int
    description: str
    recommendation: str


@dataclass
class SecurityReport:
    """Security scan report."""

    issues: list = None
    scanned_files: int = 0
    secrets_found: int = 0
    vulnerabilities_found: int = 0
    dependency_issues: int = 0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []

    @property
    def total_issues(self) -> int:
        return len(self.issues)

    @property
    def passed(self) -> bool:
        return not any(i.severity in ("CRITICAL", "HIGH") for i in self.issues)


class SecurityScanner:
    """
    Comprehensive security scanner for code and dependencies.

    Features:
    - Secret detection (API keys, tokens, passwords)
    - SAST via bandit (if installed)
    - Dependency vulnerability scanning via pip-audit
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.report = SecurityReport()

    def scan_secrets(self, extensions: list = None) -> list:
        """Scan files for hardcoded secrets and credentials."""
        if extensions is None:
            # Comprehensive list covering all common text file types
            extensions = [
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",  # Code
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
                ".conf",  # Config
                ".env",
                ".env.example",
                ".env.local",  # Environment files
                ".txt",
                ".md",
                ".rst",  # Documentation & Text
                ".sh",
                ".bash",
                ".zsh",
                ".ps1",
                ".bat",
                ".cmd",  # Shell scripts
                ".xml",
                ".html",
                ".properties",  # Other configs
                ".sql",  # Database files
            ]

        issues = []
        files_scanned = 0

        for ext in extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if any(
                    part in file_path.parts
                    for part in [
                        ".git",
                        "node_modules",
                        "__pycache__",
                        ".venv",
                        "venv",
                        ".boring_cache",
                    ]
                ):
                    continue

                files_scanned += 1
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.split("\n")

                    for pattern_name, pattern in SECRET_SCAN_PATTERNS.items():
                        for line_num, line in enumerate(lines, 1):
                            if re.search(pattern, line):
                                issue = SecurityIssue(
                                    severity="HIGH",
                                    category="secret",
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    line_number=line_num,
                                    description=f"Potential {pattern_name} detected",
                                    recommendation="Move to environment variable or secrets manager",
                                )
                                issues.append(issue)
                except Exception:
                    pass

        self.report.scanned_files = files_scanned
        self.report.secrets_found = len(issues)
        self.report.issues.extend(issues)
        return issues

    def scan_vulnerabilities(self, target: str = "src/") -> list:
        """Run bandit SAST scanner on Python code."""
        import subprocess

        issues = []
        target_path = self.project_root / target

        if not target_path.exists():
            return issues

        try:
            result = subprocess.run(
                ["bandit", "-r", str(target_path), "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=30,  # Reduced from 120 to prevent long hangs
            )

            if result.stdout:
                import json

                try:
                    data = json.loads(result.stdout)
                    for vuln in data.get("results", []):
                        issue = SecurityIssue(
                            severity=vuln.get("issue_severity", "LOW"),
                            category="vulnerability",
                            file_path=vuln.get("filename", "unknown"),
                            line_number=vuln.get("line_number", 0),
                            description=vuln.get("issue_text", "Unknown vulnerability"),
                            recommendation=f"CWE: {vuln.get('issue_cwe', {}).get('id', 'N/A')}",
                        )
                        issues.append(issue)
                except Exception:
                    pass

        except FileNotFoundError:
            pass  # bandit not installed
        except Exception:
            pass

        self.report.vulnerabilities_found = len(issues)
        self.report.issues.extend(issues)
        return issues

    def scan_dependencies(self) -> list:
        """Check dependencies for known vulnerabilities."""
        import subprocess

        issues = []

        # Run pip-audit for Python
        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json", "--progress-spinner", "off"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )
            if result.stdout:
                import json

                try:
                    data = json.loads(result.stdout)
                    for vuln in data:
                        issue = SecurityIssue(
                            severity="HIGH" if vuln.get("fix_versions") else "MEDIUM",
                            category="dependency",
                            file_path="pyproject.toml/requirements.txt",
                            line_number=0,
                            description=f"{vuln.get('name')}: {vuln.get('vulns', [{}])[0].get('id', 'Unknown')}",
                            recommendation=f"Upgrade to {vuln['fix_versions'][0]}"
                            if vuln.get("fix_versions")
                            else "Update dependency",
                        )
                        issues.append(issue)
                except Exception:
                    pass
        except (FileNotFoundError, Exception):
            pass

        # Run npm audit for JS/TS if package.json exists
        if (self.project_root / "package.json").exists():
            try:
                # Check if npm is available first
                import shutil

                if shutil.which("npm"):
                    result = subprocess.run(
                        ["npm", "audit", "--json"],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root,
                        timeout=30,
                    )
                    if result.stdout:
                        import json

                        try:
                            # npm audit exits with 1 if vulns found, but still prints JSON
                            data = json.loads(result.stdout)
                            if "advisories" in data:  # npm 6
                                vulns = data["advisories"].values()
                            elif "vulnerabilities" in data:  # npm 7+
                                vulns = data["vulnerabilities"].values()
                            else:
                                vulns = []

                            for vuln in vulns:
                                # Normalize npm 7 structure if nested
                                if isinstance(vuln, dict):
                                    severity = vuln.get("severity", "low").upper()
                                    pkg_name = (
                                        vuln.get("name") or vuln.get("module_name") or "unknown"
                                    )
                                    # Map npm severity
                                    if severity in ["CRITICAL", "HIGH"]:
                                        sec_severity = severity
                                    else:
                                        sec_severity = "MEDIUM" if severity == "MODERATE" else "LOW"

                                    issue = SecurityIssue(
                                        severity=sec_severity,
                                        category="dependency",
                                        file_path="package.json",
                                        line_number=0,
                                        description=f"npm: {pkg_name} ({vuln.get('title', 'Vulnerability')})",
                                        recommendation="Run 'npm audit fix'",
                                    )
                                    issues.append(issue)
                        except Exception:
                            pass
            except Exception:
                pass

        self.report.dependency_issues = len(issues)
        self.report.issues.extend(issues)
        return issues

    def full_scan(self) -> SecurityReport:
        """
        Run all security scans in parallel for better performance.

        V10.22: Uses ThreadPoolExecutor for parallel scanning.
        """
        import concurrent.futures

        # Run all scans in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.scan_secrets): "secrets",
                executor.submit(self.scan_vulnerabilities): "vulnerabilities",
                executor.submit(self.scan_dependencies): "dependencies",
            }

            # Wait for all to complete (results are stored in self.report)
            for future in concurrent.futures.as_completed(futures):
                futures[future]
                try:
                    future.result()  # Raises exception if scan failed
                except Exception:
                    pass  # Individual scan failures are handled internally

        return self.report


def run_security_scan(project_path: str = None) -> dict:
    """
    Run security scan on a project.

    Returns:
        Security scan results as dict
    """
    from boring.core.config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    scanner = SecurityScanner(path)
    report = scanner.full_scan()

    return {
        "passed": report.passed,
        "total_issues": report.total_issues,
        "secrets_found": report.secrets_found,
        "vulnerabilities_found": report.vulnerabilities_found,
        "dependency_issues": report.dependency_issues,
        "issues": [
            {
                "severity": i.severity,
                "category": i.category,
                "file": i.file_path,
                "line": i.line_number,
                "description": i.description,
                "recommendation": i.recommendation,
            }
            for i in report.issues
        ],
    }
