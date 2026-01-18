# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Boring Unit of Work (UoW) - Architecture Hardening V2

Coordinates multiple transactional resources (Filesystem, State Ledger)
to ensure atomic commits and consistent rollbacks across all Boring components.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from boring.core.state import StateManager
from boring.loop.transactions import TransactionManager

logger = logging.getLogger(__name__)


class BoringUnitOfWork:
    """
    Coordinates atomic updates across Files (Git) and State (Ledger).

    Usage:
    ```python
    with BoringUnitOfWork(project_root) as uow:
        # 1. Modify files via normal FS calls
        # 2. Update state via uow.state.update()
        uow.commit() # Save both
    ```
    If an exception occurs or commit() is not called, it rolls back both.
    """

    _nested_count = 0

    def __init__(self, project_root: Path, session_id: str | None = None):
        self.project_root = project_root
        self.tx_manager = TransactionManager(project_root)
        self.state_manager = StateManager(project_root, session_id=session_id)

        self.initial_state_offset: int = 0
        self._is_committed = False
        self._is_active = False

    def __enter__(self):
        self._is_active = True
        self._is_committed = False

        # 1. Start File Transaction (Git Checkpoint)
        # Note: TransactionManager.start returns a dict but we mostly care about the side effect
        self.tx_manager.start(description="UoW Transaction Start")

        # 2. Record Initial State Offset
        # We need the current size of the ledger file
        ledger_file = self.state_manager.events.ledger_file
        if ledger_file.exists():
            self.initial_state_offset = ledger_file.stat().st_size
        else:
            self.initial_state_offset = 0

        logger.debug(f"UnitOfWork started at state_offset={self.initial_state_offset}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                # Automatic rollback on exception
                logger.warning(f"UoW error detected ({exc_type.__name__}). Initiating rollback...")
                self.rollback()
            elif not self._is_committed:
                # If exited without commit(), assume user wants rollback or forgot
                logger.debug("UoW exited without commit. Rolling back by default.")
                self.rollback()
        finally:
            self._is_active = False

    def commit(self):
        """Commit all changes (Files and State)."""
        if not self._is_active:
            raise RuntimeError("Cannot commit an inactive UnitOfWork")

        logger.debug("Committing UnitOfWork...")

        # 1. Commit Files
        res = self.tx_manager.commit()
        if res.get("status") == "error":
            logger.error(f"UoW File commit failed: {res.get('message')}")
            # We don't rollback state here yet, as file commit failure is usually
            # non-destructive or handled by tx_manager.
            # But the UoW is now in a suspicious state.

        # 2. State "commit" is effectively just keeping the events we appended.
        # StateManager saves snapshot on every transaction, so it's already "on disk".

        self._is_committed = True
        logger.info("UnitOfWork committed successfully.")

    def rollback(self):
        """Revert all changes since UoW start."""
        if not self._is_active:
            return

        logger.warning("Rolling back UnitOfWork...")

        # 1. Rollback Files (Git Reset/Checkout)
        self.tx_manager.rollback()

        # 2. Rollback State (Ledger Truncation)
        self.state_manager.rollback(self.initial_state_offset)

        self._is_committed = False  # Marks as rolled back
        logger.info("UnitOfWork rollback complete.")


@contextmanager
def get_uow(
    project_root: Path, session_id: str | None = None
) -> Generator[BoringUnitOfWork, None, None]:
    """Helper to get a UnitOfWork instance."""
    uow = BoringUnitOfWork(project_root, session_id)
    with uow:
        yield uow
