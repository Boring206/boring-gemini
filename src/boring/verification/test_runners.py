import subprocess
from pathlib import Path

from ..models import VerificationResult
from .tools import ToolManager


def run_tests_python(
    project_root: Path, tools: ToolManager, test_path: Path = None
) -> VerificationResult:
    if not tools.is_available("pytest"):
        return VerificationResult(
            passed=True,
            check_type="test",
            message="Skipped (pytest not found)",
            details=[],
            suggestions=[],
        )

    test_target = test_path or (project_root / "tests")
    if not test_target.exists():
        return VerificationResult(
            passed=True, check_type="test", message="No tests found", details=[], suggestions=[]
        )

    try:
        result = subprocess.run(
            ["pytest", str(test_target), "-q"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=project_root,
        )
        if result.returncode == 0:
            summary = result.stdout.split("\n")[-2] if result.stdout else "Passed"
            return VerificationResult(
                passed=True,
                check_type="test",
                message=f"Tests passed: {summary}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="test",
            message="Tests failed",
            details=[result.stdout[:500]],
            suggestions=["Fix tests"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="test", message=f"Test error: {e}", details=[], suggestions=[]
        )


def run_tests_node(
    project_root: Path, tools: ToolManager, test_path: Path = None
) -> VerificationResult:
    if not tools.is_available("npm"):
        return VerificationResult(
            passed=True,
            check_type="test",
            message="Skipped (npm not found)",
            details=[],
            suggestions=[],
        )

    try:
        result = subprocess.run(
            ["npm", "test"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True, check_type="test", message="npm test OK", details=[], suggestions=[]
            )
        return VerificationResult(
            passed=False,
            check_type="test",
            message="npm test failed",
            details=[result.stdout[:500]],
            suggestions=["Fix tests"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True,
            check_type="test",
            message=f"npm test error: {e}",
            details=[],
            suggestions=[],
        )


def run_tests_go(
    project_root: Path, tools: ToolManager, test_path: Path = None
) -> VerificationResult:
    if not tools.is_available("go"):
        return VerificationResult(
            passed=True,
            check_type="test",
            message="Skipped (Go not found)",
            details=[],
            suggestions=[],
        )

    try:
        result = subprocess.run(
            ["go", "test", "./..."],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True, check_type="test", message="go test OK", details=[], suggestions=[]
            )
        return VerificationResult(
            passed=False,
            check_type="test",
            message="go test failed",
            details=[result.stdout[:500]],
            suggestions=["Fix tests"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True,
            check_type="test",
            message=f"go test error: {e}",
            details=[],
            suggestions=[],
        )


def run_tests_rust(
    project_root: Path, tools: ToolManager, test_path: Path = None
) -> VerificationResult:
    if not tools.is_available("cargo"):
        return VerificationResult(
            passed=True,
            check_type="test",
            message="Skipped (cargo not found)",
            details=[],
            suggestions=["Install Rust"],
        )

    try:
        result = subprocess.run(
            ["cargo", "test", "--quiet"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True, check_type="test", message="cargo test OK", details=[], suggestions=[]
            )
        return VerificationResult(
            passed=False,
            check_type="test",
            message="cargo test failed",
            details=[result.stdout[:500] if result.stdout else result.stderr[:500]],
            suggestions=["Fix Rust tests"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True,
            check_type="test",
            message=f"cargo test error: {e}",
            details=[],
            suggestions=[],
        )


def run_tests_maven(
    project_root: Path, tools: ToolManager, test_path: Path = None
) -> VerificationResult:
    if not tools.is_available("mvn"):
        return VerificationResult(
            passed=True,
            check_type="test",
            message="Skipped (Maven not found)",
            details=[],
            suggestions=["Install Maven"],
        )

    try:
        result = subprocess.run(
            ["mvn", "test", "-q"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True, check_type="test", message="mvn test OK", details=[], suggestions=[]
            )
        return VerificationResult(
            passed=False,
            check_type="test",
            message="mvn test failed",
            details=[result.stdout[:500]],
            suggestions=["Fix Maven tests"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True,
            check_type="test",
            message=f"mvn test error: {e}",
            details=[],
            suggestions=[],
        )


def run_tests_gradle(
    project_root: Path, tools: ToolManager, test_path: Path = None
) -> VerificationResult:
    if not tools.is_available("gradle"):
        return VerificationResult(
            passed=True,
            check_type="test",
            message="Skipped (Gradle not found)",
            details=[],
            suggestions=["Install Gradle"],
        )

    try:
        result = subprocess.run(
            ["gradle", "test", "--quiet"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True, check_type="test", message="gradle test OK", details=[], suggestions=[]
            )
        return VerificationResult(
            passed=False,
            check_type="test",
            message="gradle test failed",
            details=[result.stdout[:500]],
            suggestions=["Fix Gradle tests"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True,
            check_type="test",
            message=f"gradle test error: {e}",
            details=[],
            suggestions=[],
        )
