"""
Backward compatibility stub for boring.transactions

This module has been moved to boring.loop.transactions
This stub file ensures existing imports continue to work.

Migration: Change `from boring.transactions import X` to `from boring.loop.transactions import X`
"""

from boring.loop.transactions import *  # noqa: F401, F403
from boring.loop.transactions import (
    TransactionManager,
    TransactionState,
)

__all__ = ["TransactionManager", "TransactionState"]
