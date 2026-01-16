"""
Compliance Service.
Checks project files for license headers and policy violations.
"""

from pathlib import Path

HEADER_KEYWORDS = [
    "Copyright",
    "Boring206",
    "Licensed under the Apache License",
    "SPDX-License-Identifier: Apache-2.0",
]


class ComplianceManager:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

    def scan_headers(self) -> list[str]:
        """Scan python files for license headers."""
        violations = []
        for path in self.project_root.rglob("*.py"):
            if "venv" in path.parts or ".boring" in path.parts:
                continue

            try:
                content = path.read_text(encoding="utf-8")
                # Check for at least one keyword
                if not any(k in content for k in HEADER_KEYWORDS):
                    violations.append(str(path.relative_to(self.project_root)))
            except Exception:
                pass  # Skip binary or unreadable

        return violations

    def generate_report(self) -> dict:
        """Generate full compliance report."""
        headers = self.scan_headers()
        score = 100 - (len(headers) * 5)  # Arbitrary scoring
        score = max(0, score)

        return {
            "score": score,
            "header_violations": headers,
            "status": "PASS" if score > 80 else "FAIL",
        }
