"""
Vault Service (Secrets Management & Sanitization).
Detects and redacts sensitive information from logs and outputs.
"""

import re
from typing import Any


class Vault:
    # Common Secret Patterns
    PATTERNS = [
        # Generic API Keys (sk-, gh-, etc)
        r"(sk-[a-zA-Z0-9]{32,})",  # OpenAI
        r"(ghp_[a-zA-Z0-9]{36})",  # GitHub Personal Access Token
        r"(gho_[a-zA-Z0-9]{36})",  # GitHub OAuth
        r"(xox[baprs]-[a-zA-Z0-9-]{10,48})",  # Slack
        r"(ey[a-zA-Z0-9]{20,}\.[a-zA-Z0-9]{20,}\.[a-zA-Z0-9]{20,})",  # JWT (rough)
        r"([a-f0-9]{32,})",  # Generic Hex Tokens (32+ chars)
        r"(AIza[0-9A-Za-z-_]{35})",  # Google Cloud API Key
    ]

    # Sensitive Keys (Case Insensitive)
    SENSITIVE_KEYS: set[str] = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "client_secret",
        "token",
        "api_key",
        "access_token",
        "refresh_token",
        "auth",
        "authorization",
        "credential",
        "credentials",
        "private_key",
        "ssh_key",
    }

    _instance = None

    @classmethod
    def get_instance(cls) -> "Vault":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.compiled_patterns = [re.compile(p) for p in self.PATTERNS]

    def sanitize(self, data: Any) -> Any:
        """
        Recursively sanitize data structure.
        Returns a COPY with secrets redacted.
        """
        if isinstance(data, dict):
            return {k: self._sanitize_value(k, v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize(item) for item in data]
        elif isinstance(data, str):
            return self._redact_string(data)
        else:
            return data

    def _sanitize_value(self, key: str, value: Any) -> Any:
        """Sanitize a specific key-value pair."""
        # Check Key Name (Heuristic)
        if str(key).lower() in self.SENSITIVE_KEYS:
            return "[REDACTED_KEY]"

        # Check Value Content
        return self.sanitize(value)

    def _redact_string(self, text: str) -> str:
        """Apply regex redaction to string."""
        if not text:
            return text

        # Optimization: Don't regex very short strings
        if len(text) < 10:
            return text

        redacted = text
        for pattern in self.compiled_patterns:
            redacted = pattern.sub("[REDACTED_PATTERN]", redacted)

        # Length Truncation (Audit Log Requirement)
        if len(redacted) > 1000:
            redacted = redacted[:500] + f"... [truncated {len(redacted)} chars]"

        return redacted
