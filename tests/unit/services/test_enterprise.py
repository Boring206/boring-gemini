"""
Unit tests for Enterprise Features (Audit, RBAC, Vault, Compliance).
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from boring.services.audit import AuditLogger
from boring.services.compliance import ComplianceManager
from boring.services.rbac import RoleManager
from boring.services.vault import Vault


def test_audit_logging(tmp_path):
    """Test AuditLogger initialization and logging."""
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(db_path=db_path)

    logger.log(
        event_type="TEST_EVENT",
        resource="test_tool",
        action="EXECUTE",
        actor="pytest",
        details={"arg": "value"},
    )

    logs = logger.get_logs(limit=10)
    assert len(logs) == 1
    assert logs[0]["event_type"] == "TEST_EVENT"


def test_rbac_logic():
    """Test Role-Based Access Control."""
    rbac = RoleManager.get_instance()
    # Mock admin role
    rbac.current_role = "admin"
    assert rbac.check_access("any_tool")

    # Mock viewer role
    rbac.current_role = "viewer"
    assert rbac.check_access("read_file")
    assert not rbac.check_access("boring_fix")  # Denied


def test_vault_redaction():
    """Test secret redaction."""
    vault = Vault.get_instance()

    data = {
        "password": "secret_password",
        "api_key": "sk-12345678901234567890123456789012",  # Mock simplistic signature?
        "safe": "hello",
    }

    sanitized = vault.sanitize(data)
    assert sanitized["password"] == "[REDACTED_KEY]"
    assert sanitized["safe"] == "hello"


def test_compliance_scan(tmp_path):
    """Test compliance header check."""
    # Create valid file
    valid = tmp_path / "valid.py"
    valid.write_text("# Copyright Boring206\nprint('ok')", encoding="utf-8")

    # Create invalid file
    invalid = tmp_path / "invalid.py"
    invalid.write_text("print('bad')", encoding="utf-8")

    manager = ComplianceManager(project_root=tmp_path)
    violations = manager.scan_headers()

    assert "invalid.py" in str(violations[0])
    assert len(violations) == 1
