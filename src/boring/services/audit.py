"""
Audit Logging Service for Boring V14.0

Provides immutable-audit-log-style tracking for sensitive operations using SQLite.
Integrates with Vibe features (Error Translation, Tutorial Hooks).
"""

import inspect
import json
import logging
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Represents a security-relevant event."""

    event_type: str
    resource: str
    action: str
    actor: str
    details: dict
    timestamp: str = ""


class AuditLogger:
    """
    Manages secure audit logs using SQLite.
    Singleton pattern for global access.
    """

    _instance: Optional["AuditLogger"] = None

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            # Default to global storage for Enterprise Compliance
            boring_home = Path.home() / ".boring"
            boring_home.mkdir(parents=True, exist_ok=True)
            self.db_path = boring_home / "audit.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.enabled = True
        self._conn = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create cached connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self._conn

    @classmethod
    def get_instance(cls) -> "AuditLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_db(self):
        """Initialize audit database schema."""
        try:
            conn = self._get_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details TEXT,
                    duration_ms INTEGER,
                    hash TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_logs(event_type)")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize audit DB: {e}")

    def log(
        self,
        event_type: str,
        resource: str,
        action: str,
        details: dict | None = None,
        actor: str = "agent",
        duration_ms: int = 0,
    ):
        """Log an event to the audit trail."""
        if not self.enabled:
            return

        try:
            timestamp = datetime.now().isoformat()
            # Sanitize details
            sanitized_details = self._sanitize_args(details or {})
            details_json = json.dumps(sanitized_details)

            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO audit_logs (timestamp, event_type, resource, action, actor, details, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (timestamp, event_type, resource, action, actor, details_json, duration_ms),
            )
            conn.commit()
        except Exception as e:
            # Silent fail to avoid breaking operations
            logger.warning(f"Failed to write audit log: {e}")

    def _sanitize_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive data using Vault service."""
        try:
            from .vault import Vault

            # Vault returns a sanitized copy
            return Vault.get_instance().sanitize(args)
        except ImportError:
            # Fallback if Vault not found
            return getattr(self, "_fallback_sanitize", lambda x: x)(args)

    def get_logs(self, limit: int = 100, event_type: str | None = None) -> list[dict]:
        """Retrieve recent audit logs."""
        try:
            query = "SELECT * FROM audit_logs"
            params = []

            if event_type:
                query += " WHERE event_type = ?"
                params.append(event_type)

            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []


def audited(func: Callable) -> Callable:
    """
    Decorator to automatically log tool invocations.
    Integrates with ErrorTranslator and TutorialManager.
    """
    sig = inspect.signature(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        # RBAC Check (V14 Enterprise)
        try:
            from .rbac import RoleManager

            if not RoleManager.get_instance().check_access(func.__name__):
                error_msg = f"Access Denied: Role '{RoleManager.get_instance().current_role}' cannot execute '{func.__name__}'"
                # Log Denial
                AuditLogger.get_instance().log(
                    event_type="ACCESS_DENIED",
                    resource=func.__name__,
                    action="EXECUTE",
                    actor="agent",
                    details={"error": error_msg},
                )
                raise PermissionError(error_msg)
        except ImportError:
            pass

        start_time = time.time()

        # Lazy imports to avoid circular dependencies
        try:
            from ..error_translator import ErrorTranslator

            translator = ErrorTranslator()
            translator_available = True
        except ImportError:
            translator_available = False

        try:
            from ..tutorial import TutorialManager

            tutorial_manager = TutorialManager()
        except ImportError:
            tutorial_manager = None

        # Capture arguments
        try:
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            all_args = dict(bound_args.arguments)
            if "self" in all_args:
                all_args.pop("self")
            if "cls" in all_args:
                all_args.pop("cls")
        except Exception:
            all_args = kwargs

        try:
            result = func(*args, **kwargs)

            # Vibe/Error Translation for dict results
            if (
                isinstance(result, dict)
                and result.get("status") == "ERROR"
                and "message" in result
                and translator_available
            ):
                explanation = translator.translate(result["message"])
                result["vibe_explanation"] = explanation.friendly_message
                if explanation.fix_command:
                    result["vibe_fix"] = explanation.fix_command

                if tutorial_manager:
                    try:
                        tutorial_manager.show_tutorial("first_error")
                    except Exception:
                        pass

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            vibe_msg = error_msg
            if translator_available:
                vibe_msg = translator.translate(error_msg).friendly_message

            if tutorial_manager:
                try:
                    tutorial_manager.show_tutorial("first_error")
                except Exception:
                    pass

            # Log Exception
            AuditLogger.get_instance().log(
                event_type="TOOL_EXCEPTION",
                resource=func.__name__,
                action="EXECUTE",
                actor="agent",
                details={"error": error_msg, "vibe_explanation": vibe_msg, "args": all_args},
                duration_ms=duration_ms,
            )
            raise e

        # Log Success
        duration_ms = int((time.time() - start_time) * 1000)

        result_summary = result
        if isinstance(result, dict):
            result_summary = result.copy()  # Shallow copy for logging
        else:
            result_summary = {"value": str(result)[:200]}

        AuditLogger.get_instance().log(
            event_type="TOOL_EXECUTION",
            resource=func.__name__,
            action="EXECUTE",
            actor="agent",
            details={"args": all_args, "result": result_summary},
            duration_ms=duration_ms,
        )

        return result

    return wrapper
