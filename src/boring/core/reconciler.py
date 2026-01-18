import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from boring.core.events import EventStore
from boring.core.state import ProjectState, StateManager

logger = logging.getLogger(__name__)


@dataclass
class IntegrityReport:
    """Report of system integrity check."""

    timestamp: str
    ledger_status: str  # OK, CORRUPT, MISSING
    ledger_issues: list[str]
    state_status: str  # OK, STALE, CORRUPT
    state_issues: list[str]
    brain_status: str  # OK, WARNING
    brain_issues: list[str]
    meta: dict


@dataclass
class FixReport:
    """Report of applied fixes."""

    timestamp: str
    fixes_applied: list[str]
    remaining_issues: list[str]


class SystemReconciler:
    """
    Self-Healing Doctor for the Boring System.

    Responsibilities:
    1. Verify Event Ledger Integrity (Sequence, JSON format).
    2. Verify State Consistency (Replay vs Snapshot).
    3. Verify Brain Integrity (SQLite vs Vector).
    4. Auto-Fix detected issues.
    """

    def __init__(self, project_root: Path):
        self.root = project_root
        self.state_manager = StateManager(project_root)
        self.event_store = EventStore(project_root)
        self._brain = None
        self._checkpoint_file = self.root / ".boring" / "reconcile.json"

    @property
    def brain(self):
        """Lazy load BrainManager to avoid heavy startup cost."""
        if self._brain is None:
            from boring.intelligence.brain_manager import BrainManager

            self._brain = BrainManager(self.root)
        return self._brain

    def _load_checkpoint(self) -> dict:
        """Load the last successful verification checkpoint."""
        if self._checkpoint_file.exists():
            try:
                return json.loads(self._checkpoint_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"offset": 0, "last_seq": -1, "last_checksum": None}

    def _save_checkpoint(self, offset: int, last_seq: int, last_checksum: str | None):
        """Save a new verification checkpoint."""
        data = {
            "offset": offset,
            "last_seq": last_seq,
            "last_checksum": last_checksum,
            "verified_at": datetime.now().isoformat(),
        }
        self._checkpoint_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def check_integrity(self, deep_scan: bool = True) -> IntegrityReport:
        """
        Comprehensive system integrity check.
        V14.7: Now includes Operational Health from Supervisor.
        """
        timestamp = datetime.now().isoformat()
        ledger_status = "OK"
        ledger_issues = []
        state_status = "OK"
        state_issues = []
        brain_status = "OK"
        brain_issues = []

        # 0. Check Operational Health (V14.7)
        try:
            from boring.core.supervisor import get_supervisor

            get_supervisor(self.root).check_health()
        except Exception as e:
            logger.debug(f"Supervisor health check skipped: {e}")

        # 1. Check Ledger (Incremental Optimization V14.6)
        try:
            checkpoint = self._load_checkpoint()  # Ensure checkpoint is loaded
            # [V14.7] SQLite Migration: Use Sequence ID instead of Bytes
            start_seq = checkpoint["last_seq"] + 1
            if start_seq < 0:
                start_seq = 0

            latest_seq = self.event_store.latest_seq

            # Fast Path: Only skip if the latest sequence matches exactly what we've already verified.
            should_scan = True
            if not deep_scan:
                if latest_seq == checkpoint["last_seq"]:
                    should_scan = False
                    logger.debug(
                        "Reconciler: Fast path - Ledger matches checkpoint, skipping scan."
                    )
                else:
                    logger.debug(
                        f"Reconciler: Scan required. Ledger seq {latest_seq} != Checkpoint seq {checkpoint['last_seq']}"
                    )

            if should_scan:
                # Load expected values from checkpoint for scan
                expected_prev = checkpoint["last_checksum"]
                expected_seq = checkpoint["last_seq"]

                valid_events, corruption_found, deep_issues, final_info = self._scan_ledger(
                    start_offset=start_seq,
                    expected_prev_hash=expected_prev,
                    expected_seq=expected_seq,
                )

                if corruption_found:
                    ledger_status = "CORRUPT"
                    ledger_issues.extend(deep_issues)
                else:
                    # Update checkpoint on success
                    # Offset is deprecated/unused for SQLite, we use 0 or last_seq
                    self._save_checkpoint(0, final_info["last_seq"], final_info["last_checksum"])

                    if not valid_events and start_seq == 0 and latest_seq > -1:
                        # Only warn if DB has events but we found none?
                        # latest_seq > -1 means DB has events. valid_events=0 means all failed?
                        pass
            else:
                # Fast path pass
                ledger_status = "OK"

        except Exception as e:
            ledger_status = "CORRUPT"
            ledger_issues.append(f"Ledger scan failed: {e}")

        # 2. Check State Consistency (Optimized)
        # Only run deep state replay if deep_scan is True or if we suspect issues
        if deep_scan:
            try:
                # Replay from scratch to ensure Truth
                replayed_state = self._replay_all_events()
                snapshot_state = self.state_manager._load_snapshot()

                if not snapshot_state:
                    if replayed_state.version:
                        state_status = "MISSING"
                        state_issues.append("State snapshot missing")
                else:
                    if not self._states_match(replayed_state, snapshot_state):
                        state_status = "STALE"
                        state_issues.append("Snapshot does not match replayed ledger state")

            except Exception as e:
                state_status = "ERROR"
                state_issues.append(f"State verification failed: {e}")
        else:
            # Lightweight state check
            if not self.state_manager.snapshot_file.exists():
                state_status = "MISSING"
                state_issues.append("State snapshot missing")

        # 3. Check Brain
        try:
            health = self.brain.get_health_report()
            if isinstance(health, dict):
                if health.get("health_status") != "OK":
                    brain_status = "WARNING"
                    brain_issues.extend(health.get("issues", []))

            if self.brain.vector_store:
                db_count = self.brain.get_pattern_stats()["total"]
                vec_count = self.brain.vector_store.count()
                if db_count != vec_count:
                    brain_status = "WARNING"
                    brain_issues.append(f"Vector Index Mismatch (DB={db_count}, Vec={vec_count})")

        except Exception as e:
            brain_status = "ERROR"
            brain_issues.append(f"Brain check failed: {e}")

        return IntegrityReport(
            timestamp=timestamp,
            ledger_status=ledger_status,
            ledger_issues=ledger_issues,
            state_status=state_status,
            state_issues=state_issues,
            brain_status=brain_status,
            brain_issues=brain_issues,
            meta={"root": str(self.root)},
        )

    def fix_issues(self, report: IntegrityReport) -> FixReport:
        """Attempt to fix issues identified in the report."""
        fixes = []
        remaining = []

        if report.state_status in ["STALE", "MISSING", "CORRUPT"]:
            try:
                logger.info("Auto-fixing State: Rebuilding from Ledger...")
                replayed_state = self._replay_all_events()
                with self.state_manager.state_lock:
                    self.state_manager._state = replayed_state
                    if self.event_store.ledger_file.exists():
                        replayed_state.ledger_offset = self.event_store.ledger_file.stat().st_size
                    self.state_manager._save_snapshot()
                    fixes.append("Rebuilt state.json from event ledger")
            except Exception as e:
                remaining.append(f"Failed to fix state: {e}")

        if report.brain_status == "WARNING":
            try:
                logger.info("Auto-fixing Brain: Syncing and Rebuilding Index...")
                with self.brain.brain_transaction():
                    if any("Vector Index Mismatch" in issue for issue in report.brain_issues):
                        self.brain._rebuild_index()
                        fixes.append("Rebuilt Brain Vector Index")
                    else:
                        self.brain.sync()
            except Exception as e:
                remaining.append(f"Failed to fix brain: {e}")

        return FixReport(
            timestamp=datetime.now().isoformat(),
            fixes_applied=fixes,
            remaining_issues=remaining + report.ledger_issues,
        )

    def _replay_all_events(self) -> ProjectState:
        """Replay history from ZERO to calc Truth."""
        state = ProjectState()
        if self.event_store.ledger_file.exists():
            for event in self.event_store.stream(start_offset=0):
                self.state_manager._apply_event(state, event)
        return state

    def _scan_ledger(
        self, start_offset: int = 0, expected_prev_hash: str = None, expected_seq: int = -1
    ) -> tuple[int, bool, list[str], dict]:
        """Deep scan ledger with support for incremental verification."""
        valid_count = 0
        issues = []
        last_checksum = expected_prev_hash
        last_seq = expected_seq

        if not self.event_store.ledger_file.exists():
            return 0, False, [], {"last_seq": -1, "last_checksum": None}

        try:
            import hashlib

            for event in self.event_store.stream(start_offset=start_offset):
                # 1. Sequence check
                if event.seq != last_seq + 1:
                    issues.append(
                        f"Sequence gap: Event {event.id} has seq {event.seq}, expected {last_seq + 1}"
                    )

                # 2. Hash chain check
                if event.prev_hash != last_checksum:
                    issues.append(f"Hash chain break: Event {event.id} prev_hash mismatch")

                # 3. Checksum check (Deep verification)
                content_str = f"{event.type}{json.dumps(event.payload, sort_keys=True)}{event.session_id}{event.seq}{event.prev_hash}"
                recalc = hashlib.sha256(content_str.encode()).hexdigest()
                if recalc != event.checksum:
                    issues.append(f"Checksum mismatch: Event {event.id} is altered")

                last_checksum = event.checksum
                last_seq = event.seq
                valid_count += 1

        except Exception as e:
            issues.append(f"Scan interrupted at offset {start_offset}: {str(e)}")

        return (
            valid_count,
            len(issues) > 0,
            issues,
            {"last_seq": last_seq, "last_checksum": last_checksum},
        )

    def _states_match(self, state_a: ProjectState, state_b: ProjectState) -> bool:
        """Deep compare two states."""
        dump_a = state_a.model_dump(exclude={"ledger_offset", "last_updated"})
        dump_b = state_b.model_dump(exclude={"ledger_offset", "last_updated"})
        return dump_a == dump_b
