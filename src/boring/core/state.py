from __future__ import annotations

import contextlib
import json
import logging
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from boring.core.config import settings
from boring.flow.states import FlowStage

if TYPE_CHECKING:
    from pydantic import BaseModel

    class ProjectState(BaseModel):
        version: str
        stage: FlowStage
        user_goal: str
        has_constitution: bool
        has_plan: bool
        has_tasks: bool
        total_tasks: int
        completed_tasks: int
        session_id: str
        last_updated: datetime
        ledger_offset: int
else:
    # Lazy Proxy for Pydantic Model
    _ProjectState_Class = None

    def _get_project_state_class():
        global _ProjectState_Class
        if _ProjectState_Class is None:
            from pydantic import BaseModel, Field

            class ProjectState(BaseModel):
                """
                The Source of Truth for the Boring Project.
                Persisted to .boring/state.json
                """

                version: str = "1.0"
                stage: FlowStage = FlowStage.SETUP
                user_goal: str = ""

                # Checkpoints (Gates)
                has_constitution: bool = False
                has_plan: bool = False
                has_tasks: bool = False

                # Progress
                total_tasks: int = 0
                completed_tasks: int = 0

                # Context
                session_id: str = ""
                last_updated: datetime = Field(default_factory=datetime.now)
                # V14.5: Ledger Optimization
                # For SQLite: This tracks LAST APPLIED SEQUENCE ID.
                # Default -1 means "No events applied".
                ledger_offset: int = -1

            _ProjectState_Class = ProjectState
        return _ProjectState_Class

    class ProjectState:
        """Proxy that defers pydantic.BaseModel inheritance until used."""

        def __new__(cls, *args, **kwargs):
            return _get_project_state_class()(*args, **kwargs)


logger = logging.getLogger(__name__)

# Events store is now also lazy protected in its own module
from boring.core.events import EventStore, LedgerCorruptionError
from boring.utils.lock import RobustLock


class StateManager:
    """
    Manages ProjectState using Event Sourcing with Snapshot Optimization.
    The State is a projection of the Event Ledger, cached in state.json.

    Architecture Hardening V2: Atomic Transactions & Robust Sync
    """

    def __init__(self, project_root: Path, session_id: str = None):
        self.root = project_root
        from boring.core.config import settings

        self.events = EventStore(project_root, async_mode=settings.ASYNC_LEDGER_WRITE)
        self.session_id = session_id
        self.snapshot_file = self.root / ".boring" / "state.json"
        self.lock_file = self.root / ".boring" / "state_lock"

        # Robust Global Lock for State Transactions
        self.state_lock = RobustLock(self.lock_file)

        # Defer hydration until .current is accessed
        self._state = None

        # Track last sync to detect disk changes
        self._last_snapshot_mtime = 0.0

    @property
    def current(self) -> Any:
        """
        Get current state.
        Note: This performs a READ check. For strict consistency during updates,
        use `state_transaction()` context manager.
        """
        if self._state is None:
            self._state = self._hydrate()
        else:
            # Lightweight consistency check: has snapshot changed on disk?
            # If so, we might be looking at stale data compared to another process.
            # We do NOT auto-sync here aggressively to avoid read-locks,
            # but we respect _last_snapshot_mtime.
            try:
                if self.snapshot_file.exists():
                    mtime = self.snapshot_file.stat().st_mtime
                    if mtime > self._last_snapshot_mtime:
                        logger.debug("State snapshot changed on disk, reloading...")
                        self._state = self._hydrate()
            except OSError:
                pass

        return self._state

    def _hydrate(self) -> Any:
        """Replay history to build the current state (Optimized)."""
        # 1. Try Load Snapshot
        state = self._load_snapshot()
        if not state:
            state = ProjectState()

        # 2. Replay Delta (Events after snapshot offset)
        # ledger_offset is now Last Applied Seq.
        last_applied = getattr(state, "ledger_offset", -1)
        start_seq = last_applied + 1

        # Optimization: Only stream if we are behind
        latest = self.events.latest_seq
        if latest >= start_seq:
            try:
                for event in self.events.stream(start_offset=start_seq):
                    self._apply_event(state, event)
                    # Update local tracker of last applied
                    state.ledger_offset = event.seq

            except LedgerCorruptionError:
                logger.critical("FATAL: Ledger corruption detected. System integrity compromised.")
                raise

        # In-memory session tracking
        if self.session_id:
            state.session_id = self.session_id

        return state

    def _load_snapshot(self) -> Any | None:
        """Load state from JSON snapshot. Supports Gzip (V14.1)."""
        snapshot_gz = self.snapshot_file.with_suffix(".json.gz")

        target_file = None
        if snapshot_gz.exists():
            target_file = snapshot_gz
        elif self.snapshot_file.exists():
            target_file = self.snapshot_file

        if not target_file:
            return None

        try:
            if target_file.suffix == ".gz":
                import gzip

                with gzip.open(target_file, "rt", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = target_file.read_text(encoding="utf-8")

            if not content.strip():
                return None

            data = json.loads(content)

            # Update mtime tracker
            self._last_snapshot_mtime = target_file.stat().st_mtime

            return ProjectState(**data)

        except json.JSONDecodeError as e:
            # CORRUPTION DETECTED
            logger.error(f"CRITICAL: State snapshot corrupted: {e}. Moving to .corrupted")
            try:
                corrupted_path = target_file.with_suffix(
                    f".corrupted.{int(datetime.now().timestamp())}"
                )
                target_file.rename(corrupted_path)
            except OSError:
                pass
            return None  # Fallback to full rebuild from Ledger

        except Exception as e:
            # IO/Permission Error - Do NOT swallow. Failure to read state is fatal.
            logger.critical(f"FATAL: Could not read state snapshot {target_file.name}: {e}")
            raise

    def _save_snapshot(self):
        """Persist current state to JSON atomically. Supports Gzip (V14.1)."""
        try:
            from boring.core.utils import TransactionalFileWriter

            # model_dump_json is available on the proxied instance
            data = self._state.model_dump_json(indent=2)

            if settings.COMPRESS_STATE:
                target = self.snapshot_file.with_suffix(".json.gz")
                if TransactionalFileWriter.write_gzip(target, data):
                    # Remove uncompressed if exists for consistency
                    if self.snapshot_file.exists():
                        with contextlib.suppress(OSError):
                            self.snapshot_file.unlink()
                    self._last_snapshot_mtime = target.stat().st_mtime
            else:
                if TransactionalFileWriter.write_text(self.snapshot_file, data):
                    # Remove compressed if exists for consistency
                    gz = self.snapshot_file.with_suffix(".json.gz")
                    if gz.exists():
                        with contextlib.suppress(OSError):
                            gz.unlink()
                    self._last_snapshot_mtime = self.snapshot_file.stat().st_mtime

        except Exception as e:
            logger.warning(f"Failed to save state snapshot: {e}")
            # If we fail to save snapshot, it's bad but not fatal to memory state.
            # Next hydrate will just have to replay more events.

    def _apply_event(self, state: Any, event: Any):
        """Reducer: Apply a single event to the state."""
        payload = event.payload

        if event.type == "UserGoalUpdated":
            state.user_goal = payload.get("goal", "")
            state.has_plan = False
            state.has_tasks = False
            if state.stage in [FlowStage.BUILD, FlowStage.POLISH]:
                state.stage = FlowStage.DESIGN

        elif event.type == "StageChanged":
            new_stage = payload.get("stage")
            if isinstance(new_stage, str):
                try:
                    state.stage = FlowStage(new_stage)
                except ValueError:
                    pass
            else:
                state.stage = new_stage

        elif event.type == "StateUpdated":
            for k, v in payload.items():
                if k == "stage" and isinstance(v, str):
                    try:
                        v = FlowStage(v)
                    except ValueError:
                        pass

                if hasattr(state, k):
                    setattr(state, k, v)

        elif event.type == "ArtifactCreated":
            artifact_type = payload.get("type")
            if artifact_type == "constitution":
                state.has_constitution = True
            elif artifact_type == "plan":
                state.has_plan = True
            elif artifact_type == "tasks":
                state.has_tasks = True

        state.last_updated = event.timestamp

    def sync(self):
        """
        Forces the state to match disk (snapshot + ledger).
        MUST be called inside a lock to ensure we don't drift immediately.
        """
        # Always re-hydrate inside a transaction to ensure we are based on strict latest
        self._state = self._hydrate()

    @contextlib.contextmanager
    def state_transaction(self) -> Generator[Any, None, None]:
        """
        Context manager for Atomic State Updates.
        1. Acquires Global State Lock.
        2. Syncs state from disk (Catch up).
        3. Yields State for modification.
        4. Saves Snapshot.
        5. Releases Lock.
        """
        # 1. Acquire Lock
        with self.state_lock:
            # 2. Sync (Catch up)
            self.sync()

            # 3. Yield for mutation
            yield self._state

            # 4. Save Snapshot (Atomic Commit of the view)
            # Note: actual Events were appended during the mutation (update/set_goal calls)
            # We just need to save the projection.
            self._save_snapshot()

    def update(self, **kwargs):
        """Record a generic state update event."""
        serializable_kwargs = {}
        for k, v in kwargs.items():
            if hasattr(v, "value"):
                serializable_kwargs[k] = v.value
            else:
                serializable_kwargs[k] = v

        with self.state_transaction() as state:
            event, offset = self.events.append(
                "StateUpdated", serializable_kwargs, session_id=self.session_id, wait=True
            )
            self._apply_event(state, event)
            state.ledger_offset = offset

    def transition_to(self, new_stage: FlowStage):
        """Explicitly transition to a new stage."""
        with self.state_transaction() as state:
            event, offset = self.events.append(
                "StageChanged", {"stage": new_stage.value}, session_id=self.session_id, wait=True
            )
            self._apply_event(state, event)
            state.ledger_offset = offset

    def set_goal(self, goal: str):
        """Set user goal and invalidates stale plans."""
        with self.state_transaction() as state:
            event, offset = self.events.append(
                "UserGoalUpdated", {"goal": goal}, session_id=self.session_id, wait=True
            )
            self._apply_event(state, event)
            state.ledger_offset = offset

    def rollback(self, target_offset: int):
        """
        Forceful rollback of the state ledger and re-hydration.
        """
        with self.state_lock:
            # 1. Truncate Ledger to target_offset (The Fix for Risk-008)
            self.events.truncate(target_offset)

            # 2. Reset in-memory state and cache
            self._state = None
            if self.snapshot_file.exists():
                try:
                    self.snapshot_file.unlink()
                    logger.info("Rollback: Deleted state snapshot.")
                except OSError as e:
                    logger.error(f"Rollback: Failed to delete snapshot: {e}")

            # [V14.8 Fix] Also delete compressed snapshot if exists
            snapshot_gz = self.snapshot_file.with_suffix(".json.gz")
            if snapshot_gz.exists():
                try:
                    snapshot_gz.unlink()
                    logger.info("Rollback: Deleted compressed state snapshot.")
                except OSError as e:
                    logger.error(f"Rollback: Failed to delete compressed snapshot: {e}")

            # 3. Reload from fresh ledger
            self.sync()
            logger.info("State rolled back (truncated).")
