#!/usr/bin/env python3
"""
Token Savings Verification Script

Demonstrates how to measure actual token savings from verbosity optimization.
Run this script to see the difference between minimal, standard, and verbose modes.

Usage:
    python scripts/verify_token_savings.py

Requirements:
    pip install tiktoken
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import tiktoken
except ImportError:
    print("❌ tiktoken not installed. Install with: pip install tiktoken")
    sys.exit(1)


def count_tokens(text: str) -> int:
    """Count tokens using OpenAI's tokenizer (close approximation for Gemini)."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def simulate_rag_search_output(verbosity: str, num_results: int = 10) -> str:
    """Simulate boring_rag_search output for different verbosity levels."""

    if verbosity == "minimal":
        # MINIMAL: Only file paths and scores
        lines = [f"🔍 Found {num_results} results for: **authentication**\n"]
        for i in range(num_results):
            lines.append(
                f"{i + 1}. `src/auth/login.py::authenticate_user` (score: 0.{90 - i * 2})\n"
            )
        lines.append("\n💡 Use verbosity='standard' to see code snippets.")
        return "".join(lines)

    elif verbosity == "standard":
        # STANDARD: Paths + truncated code (500 chars)
        lines = [f"🔍 Found {num_results} results for: **authentication**\n"]
        for i in range(num_results):
            lines.append(
                f"### {i + 1}. [VECTOR] `src/auth/login.py` → `authenticate_user` (score: 0.{90 - i * 2})\n"
                f"Lines 45-67 | Type: function\n"
                f"```python\n"
                f"def authenticate_user(username: str, password: str):\n"
                f"    # Verify credentials against database\n"
                f"    user = db.query(User).filter(User.username == username).first()\n"
                f"    if not user or not verify_password(password, user.password_hash):\n"
                f"        raise AuthenticationError('Invalid credentials')\n"
                f"    return generate_token(user)\n"
                f"```\n"
            )
        return "".join(lines)

    else:  # verbose
        # VERBOSE: Full code (no truncation)
        lines = [f"🔍 Found {num_results} results for: **authentication**\n"]
        for i in range(num_results):
            lines.append(
                f"### {i + 1}. [VECTOR] `src/auth/login.py` → `authenticate_user` (score: 0.{90 - i * 2})\n"
                f"Lines 45-67 | Type: function\n"
                f"**Full Code:**\n"
                f"```python\n"
                f"def authenticate_user(username: str, password: str):\n"
                f'    """\n'
                f"    Authenticate a user with username and password.\n"
                f"    \n"
                f"    Args:\n"
                f"        username: User's username\n"
                f"        password: Plain text password\n"
                f"    \n"
                f"    Returns:\n"
                f"        JWT token for authenticated session\n"
                f"    \n"
                f"    Raises:\n"
                f"        AuthenticationError: If credentials are invalid\n"
                f'    """\n'
                f"    # Verify credentials against database\n"
                f"    user = db.query(User).filter(User.username == username).first()\n"
                f"    \n"
                f"    if not user:\n"
                f"        logger.warning(f'Login attempt for non-existent user: {{username}}')\n"
                f"        raise AuthenticationError('Invalid credentials')\n"
                f"    \n"
                f"    if not verify_password(password, user.password_hash):\n"
                f"        logger.warning(f'Invalid password for user: {{username}}')\n"
                f"        user.failed_login_attempts += 1\n"
                f"        db.commit()\n"
                f"        raise AuthenticationError('Invalid credentials')\n"
                f"    \n"
                f"    # Reset failed attempts on successful login\n"
                f"    user.failed_login_attempts = 0\n"
                f"    user.last_login = datetime.now()\n"
                f"    db.commit()\n"
                f"    \n"
                f"    return generate_token(user)\n"
                f"```\n"
            )
        return "".join(lines)


def simulate_code_review_output(verbosity: str, num_issues: int = 12) -> str:
    """Simulate boring_code_review output for different verbosity levels."""

    if verbosity == "minimal":
        return (
            f"🔍 auth.py: {num_issues} 問題\n"
            f"🔴 High: 3 | 🟡 Medium: 5 | 🟢 Low: 4\n"
            f"🧠 2 patterns\n"
            f"💡 Use verbosity='standard' for details"
        )

    elif verbosity == "standard":
        lines = [
            "🔍 Code Review: `auth.py`\n\n",
            "1. 🔴 **Security**: Missing authentication on admin endpoint\n",
            "   💡 建議: Add @require_auth decorator\n",
            "2. 🟡 **Error Handling**: Bare except clause at line 45\n",
            "   💡 建議: Catch specific exceptions\n",
            "3. 🟢 **Naming**: Variable name 'x' is not descriptive\n",
            "   💡 建議: Rename to 'user_count'\n",
            "\n🧠 **專案 Pattern 建議**:\n",
            "   - Use @audit decorator: For security-sensitive operations\n",
            "\n🔗 ✅ Brain Pattern 整合",
        ]
        return "".join(lines)

    else:  # verbose
        lines = [
            "🔍 Code Review: `auth.py`\n\n",
        ]
        for i in range(num_issues):
            severity = "🔴" if i < 3 else "🟡" if i < 8 else "🟢"
            lines.append(
                f"{i + 1}. {severity} **Issue {i + 1}** (Line {45 + i * 5}): Detailed description of the issue\n"
                f"   💡 建議: Specific suggestion for fixing this issue\n"
            )
        lines.append(
            "\n🧠 **專案 Pattern 建議** (5 patterns):\n"
            "   - [code_style] Use @audit decorator\n"
            "     → For security-sensitive operations\n"
            "   - [error_solution] Handle specific exceptions\n"
            "     → Avoid bare except clauses\n"
        )
        return "".join(lines)


def simulate_vibe_check_output(verbosity: str, score: int = 73) -> str:
    """Simulate boring_vibe_check output for different verbosity levels."""

    if verbosity == "minimal":
        return f"📊 Vibe Score: {score}/100 | C-Tier 🥉\n💡 Use verbosity='standard' for details"

    elif verbosity == "standard":
        return (
            f"📊 Vibe Score: {score}/100 | C-Tier 🥉\n\n"
            f"🔍 Top Issues (5/12):\n"
            f"  - [auth.py:45] Missing error handling\n"
            f"  - [utils.py:23] Inefficient loop\n"
            f"  - [api.py:12] Missing docstring\n"
            f"  - [db.py:89] SQL injection risk\n"
            f"  - [main.py:5] Unused import\n"
            f"  ... and 7 more\n\n"
            f"🔒 Critical Security (2):\n"
            f"  - 🔒 [CRITICAL] Exposed API key in config.py:15\n"
            f"  - 🔒 [HIGH] Hardcoded password in auth.py:45\n\n"
            f"📝 5 missing docstrings\n\n"
            f"🔗 ✅ 分數已記錄\n"
            f"\n💡 Use verbosity='verbose' for full report"
        )

    else:  # verbose
        return (
            f"📊 Vibe Check: `.`\n"
            f"Score: {score}/100 | C-Tier 🥉\n\n"
            f"🔍 Code Quality Issues (12):\n"
            f"  - [auth.py:45] Missing error handling\n"
            f"  - [utils.py:23] Inefficient loop  \n"
            f"  - [api.py:12] Missing docstring\n"
            f"  - [db.py:89] SQL injection risk\n"
            f"  - [main.py:5] Unused import\n"
            f"  - [models.py:34] Circular import\n"
            f"  - [views.py:78] Long method (>50 lines)\n"
            f"  - [services.py:12] Missing type hints\n"
            f"  - [tests.py:45] Flaky test\n"
            f"  - [config.py:23] Magic number\n"
            f"  - [helpers.py:67] Complex conditional\n"
            f"  - [validators.py:89] Duplicate code\n\n"
            f"🔒 Security Issues (3):\n"
            f"  - 🔒 [CRITICAL] Exposed API key (config.py:15)\n"
            f"  - 🔒 [HIGH] Hardcoded password (auth.py:45)\n"
            f"  - 🔒 [MEDIUM] Weak cryptography (utils.py:123)\n\n"
            f"📝 Documentation: 5 missing docstrings\n\n"
            f"🔗 ✅ 分數已記錄"
        )


def simulate_security_scan_output(verbosity: str, num_issues: int = 15) -> str:
    """Simulate boring_security_scan output."""

    if verbosity == "minimal":
        return {
            "status": "failed",
            "summary": f"🛡️ Scan completed. Found {num_issues} issues. (Secrets: 3, SAST: 12, Deps: 0)",
            "hint": "💡 Use `verbosity='standard'` to see critical issues.",
        }

    elif verbosity == "standard":
        return {
            "status": "failed",
            "total_issues": num_issues,
            "breakdown": {"secrets": 3, "sast": 12, "dependencies": 0},
            "top_issues": [
                {
                    "severity": "CRITICAL" if i < 2 else "HIGH",
                    "category": "Secrets Detection" if i < 3 else "SAST",
                    "file": f"src/config.py:{10 + i}",
                    "description": "Hardcoded AWS Key" if i < 3 else "SQL Injection risk",
                }
                for i in range(5)
            ],
            "message": f"Found {num_issues} issues. Showing top 5.",
            "hint": "💡 Use `verbosity='verbose'` for full report and recommendations.",
        }

    else:  # verbose
        return {
            "passed": False,
            "checked_categories": ["Secrets", "SAST", "Deps"],
            "total_issues": num_issues,
            "secrets_found": 3,
            "vulnerabilities_found": 12,
            "dependency_issues": 0,
            "issues": [
                {
                    "severity": "CRITICAL" if i < 2 else "HIGH" if i < 5 else "MEDIUM",
                    "category": "Secrets Detection" if i < 3 else "SAST",
                    "file": f"src/config.py:{10 + i}",
                    "line": 10 + i,
                    "description": "Hardcoded AWS Key" if i < 3 else "SQL Injection risk",
                    "recommendation": "Use env vars" if i < 3 else "Use parameterized queries",
                }
                for i in range(num_issues)
            ],
            "message": f"Scan failed. Found {num_issues} issues.",
        }


def simulate_perf_tips_output(verbosity: str, num_tips: int = 8) -> str:
    """Simulate boring_perf_tips output."""

    if verbosity == "minimal":
        return {
            "status": "SUCCESS",
            "vibe_summary": (
                f"⚡ api.py: {num_tips} 效能問題\n"
                f"🐌 High: 2 | 🐢 Medium/Low: {num_tips - 2}\n"
                f"💡 Use verbosity='standard' for tips"
            ),
            "file": "api.py",
            "tips_count": num_tips,
        }

    elif verbosity == "standard":
        summary_lines = ["⚡ Performance Tips: `api.py`", ""]
        for i in range(5):
            icon = "🐌" if i < 2 else "🐢"
            summary_lines.append(f"{i + 1}. {icon} **N+1 Query detected** (Line {10 + i * 5})")
            summary_lines.append("   🚀 優化: Use select_related()")

        summary_lines.append(f"\n... and {num_tips - 5} more issues.")
        summary_lines.append("💡 Use verbosity='verbose' for full list.")

        return {
            "status": "SUCCESS",
            "file": "api.py",
            "tips_count": num_tips,
            "vibe_summary": "\n".join(summary_lines),
            "suggested_fix_prompt": "Please fix N+1 queries...",
        }

    else:  # verbose
        summary_lines = ["⚡ Performance Tips: `api.py`", ""]
        for i in range(num_tips):
            icon = "🐌" if i < 2 else "🐢"
            summary_lines.append(f"{i + 1}. {icon} **N+1 Query detected** (Line {10 + i * 5})")
            summary_lines.append("   🚀 優化: Use select_related()")

        return {
            "status": "SUCCESS",
            "file": "api.py",
            "tips_count": num_tips,
            "tips": [{"msg": "..."} for _ in range(num_tips)],
            "vibe_summary": "\n".join(summary_lines),
            "suggested_fix_prompt": "Please fix N+1 queries...",
        }


def main():
    """Run token savings verification."""

    print("=" * 70)
    print("🎯 Token Savings Verification - Boring MCP V10.28 (Phase 2)")
    print("=" * 70)
    print()

    # ... existing tests ...

    # Test boring_rag_search
    print("📊 Test 1: boring_rag_search (10 results)\n")
    print("-" * 70)

    rag_minimal = simulate_rag_search_output("minimal")
    rag_standard = simulate_rag_search_output("standard")
    rag_verbose = simulate_rag_search_output("verbose")

    rag_minimal_tokens = count_tokens(rag_minimal)
    rag_standard_tokens = count_tokens(rag_standard)
    rag_verbose_tokens = count_tokens(rag_verbose)

    print(f"{'Mode':<12} {'Tokens':>8} {'vs Standard':>12} {'vs Verbose':>12}")
    print("-" * 70)
    print(
        f"{'minimal':<12} {rag_minimal_tokens:>8} {'-' + str(int((1 - rag_minimal_tokens / rag_standard_tokens) * 100)) + '%':>12} {'-' + str(int((1 - rag_minimal_tokens / rag_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'standard':<12} {rag_standard_tokens:>8} {'baseline':>12} {'-' + str(int((1 - rag_standard_tokens / rag_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'verbose':<12} {rag_verbose_tokens:>8} {'+' + str(int((rag_verbose_tokens / rag_standard_tokens - 1) * 100)) + '%':>12} {'baseline':>12}"
    )
    print()

    # Test boring_code_review
    print("📊 Test 2: boring_code_review (12 issues)\n")
    print("-" * 70)

    review_minimal = simulate_code_review_output("minimal")
    review_standard = simulate_code_review_output("standard")
    review_verbose = simulate_code_review_output("verbose")

    review_minimal_tokens = count_tokens(review_minimal)
    review_standard_tokens = count_tokens(review_standard)
    review_verbose_tokens = count_tokens(review_verbose)

    print(f"{'Mode':<12} {'Tokens':>8} {'vs Standard':>12} {'vs Verbose':>12}")
    print("-" * 70)
    print(
        f"{'minimal':<12} {review_minimal_tokens:>8} {'-' + str(int((1 - review_minimal_tokens / review_standard_tokens) * 100)) + '%':>12} {'-' + str(int((1 - review_minimal_tokens / review_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'standard':<12} {review_standard_tokens:>8} {'baseline':>12} {'-' + str(int((1 - review_standard_tokens / review_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'verbose':<12} {review_verbose_tokens:>8} {'+' + str(int((review_verbose_tokens / review_standard_tokens - 1) * 100)) + '%':>12} {'baseline':>12}"
    )
    print()

    # Test boring_vibe_check
    print("📊 Test 3: boring_vibe_check\n")
    print("-" * 70)

    vibe_minimal = simulate_vibe_check_output("minimal")
    vibe_standard = simulate_vibe_check_output("standard")
    vibe_verbose = simulate_vibe_check_output("verbose")

    vibe_minimal_tokens = count_tokens(vibe_minimal)
    vibe_standard_tokens = count_tokens(vibe_standard)
    vibe_verbose_tokens = count_tokens(vibe_verbose)

    print(f"{'Mode':<12} {'Tokens':>8} {'vs Standard':>12} {'vs Verbose':>12}")
    print("-" * 70)
    print(
        f"{'minimal':<12} {vibe_minimal_tokens:>8} {'-' + str(int((1 - vibe_minimal_tokens / vibe_standard_tokens) * 100)) + '%':>12} {'-' + str(int((1 - vibe_minimal_tokens / vibe_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'standard':<12} {vibe_standard_tokens:>8} {'baseline':>12} {'-' + str(int((1 - vibe_standard_tokens / vibe_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'verbose':<12} {vibe_verbose_tokens:>8} {'+' + str(int((vibe_verbose_tokens / vibe_standard_tokens - 1) * 100)) + '%':>12} {'baseline':>12}"
    )
    print()

    # Test boring_security_scan (Phase 2)
    print("📊 Test 4: boring_security_scan (15 issues)\n")
    print("-" * 70)

    sec_minimal = str(simulate_security_scan_output("minimal", 15))
    sec_standard = str(simulate_security_scan_output("standard", 15))
    sec_verbose = str(simulate_security_scan_output("verbose", 15))

    sec_minimal_tokens = count_tokens(sec_minimal)
    sec_standard_tokens = count_tokens(sec_standard)
    sec_verbose_tokens = count_tokens(sec_verbose)

    print(f"{'Mode':<12} {'Tokens':>8} {'vs Standard':>12} {'vs Verbose':>12}")
    print("-" * 70)
    print(
        f"{'minimal':<12} {sec_minimal_tokens:>8} {'-' + str(int((1 - sec_minimal_tokens / sec_standard_tokens) * 100)) + '%':>12} {'-' + str(int((1 - sec_minimal_tokens / sec_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'standard':<12} {sec_standard_tokens:>8} {'baseline':>12} {'-' + str(int((1 - sec_standard_tokens / sec_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'verbose':<12} {sec_verbose_tokens:>8} {'+' + str(int((sec_verbose_tokens / sec_standard_tokens - 1) * 100)) + '%':>12} {'baseline':>12}"
    )
    print()

    # Test boring_perf_tips (Phase 2)
    print("📊 Test 5: boring_perf_tips (8 tips)\n")
    print("-" * 70)

    perf_minimal = str(simulate_perf_tips_output("minimal", 8))
    perf_standard = str(simulate_perf_tips_output("standard", 8))
    perf_verbose = str(simulate_perf_tips_output("verbose", 8))

    perf_minimal_tokens = count_tokens(perf_minimal)
    perf_standard_tokens = count_tokens(perf_standard)
    perf_verbose_tokens = count_tokens(perf_verbose)

    print(f"{'Mode':<12} {'Tokens':>8} {'vs Standard':>12} {'vs Verbose':>12}")
    print("-" * 70)
    print(
        f"{'minimal':<12} {perf_minimal_tokens:>8} {'-' + str(int((1 - perf_minimal_tokens / perf_standard_tokens) * 100)) + '%':>12} {'-' + str(int((1 - perf_minimal_tokens / perf_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'standard':<12} {perf_standard_tokens:>8} {'baseline':>12} {'-' + str(int((1 - perf_standard_tokens / perf_verbose_tokens) * 100)) + '%':>12}"
    )
    print(
        f"{'verbose':<12} {perf_verbose_tokens:>8} {'+' + str(int((perf_verbose_tokens / perf_standard_tokens - 1) * 100)) + '%':>12} {'baseline':>12}"
    )
    print()

    # Overall summary
    print("=" * 70)
    print("📈 Overall Token Savings Summary (Phase 1 + 2)")
    print("=" * 70)
    print()

    total_minimal = (
        rag_minimal_tokens
        + review_minimal_tokens
        + vibe_minimal_tokens
        + sec_minimal_tokens
        + perf_minimal_tokens
    )
    total_standard = (
        rag_standard_tokens
        + review_standard_tokens
        + vibe_standard_tokens
        + sec_standard_tokens
        + perf_standard_tokens
    )
    total_verbose = (
        rag_verbose_tokens
        + review_verbose_tokens
        + vibe_verbose_tokens
        + sec_verbose_tokens
        + perf_verbose_tokens
    )

    minimal_vs_standard = int((1 - total_minimal / total_standard) * 100)
    minimal_vs_verbose = int((1 - total_minimal / total_verbose) * 100)

    print("Total Tokens (all 5 tools):")
    print(
        f"  minimal:  {total_minimal:>6} tokens ({minimal_vs_standard}% vs standard, {minimal_vs_verbose}% vs verbose)"
    )
    print(f"  standard: {total_standard:>6} tokens (baseline)")
    print(f"  verbose:  {total_verbose:>6} tokens")
    print()
    print(f"✅ Using MINIMAL verbosity saves {minimal_vs_standard}-{minimal_vs_verbose}% tokens!")
    print()
    print("💡 Tip: Set BORING_MCP_VERBOSITY=minimal for maximum token savings")
    print("=" * 70)


if __name__ == "__main__":
    main()
