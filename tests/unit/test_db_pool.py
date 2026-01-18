import threading
import time

import pytest

from boring.core.storage.sqlite_store import SQLiteEventStore


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_pool.db"


def test_thread_isolation(db_path):
    store = SQLiteEventStore(db_path)

    conns = {}

    def worker(name):
        # Access internal _get_connection to inspect object
        conns[name] = store._get_connection()

    t1 = threading.Thread(target=worker, args=("t1",))
    t2 = threading.Thread(target=worker, args=("t2",))

    t1.start()
    t1.join()
    t2.start()
    t2.join()

    assert conns["t1"] is not None
    assert conns["t2"] is not None
    assert conns["t1"] != conns["t2"]


def test_connection_reuse(db_path):
    store = SQLiteEventStore(db_path)

    conn1 = store._get_connection()
    conn2 = store._get_connection()

    assert conn1 == conn2


def test_ttl_reconnect(db_path):
    store = SQLiteEventStore(db_path)
    store.MAX_CONNECTION_AGE = 0.1  # 100ms TTL

    conn1 = store._get_connection()

    time.sleep(0.2)

    conn2 = store._get_connection()

    assert conn1 != conn2
    # Ensure old one closed? (Cannot easily check state of closed sqlite obj without using it)


def test_health_check_failure(db_path, monkeypatch):
    """
    Verify that if 'SELECT 1' fails, the pool invalidates the connection.
    We mock the cursor execute to fail.
    """
    store = SQLiteEventStore(db_path)

    # 1. Get initial connection
    conn1 = store._get_connection()
    assert conn1 is not None

    # 2. Mock the 'execute' method on the CLASS of the connection if possible,
    # or better, mock it via monkeypatching cursor/connection in the module BEFORE creation?
    # No, we already have the object.

    # Strategy: Simulating failure by closing it "behind the back"
    # OR using a custom connection factory if sqlite3 allows.

    # Actually, the simplest way is to manually corrupt it or close it,
    # ensuring 'SELECT 1' raises an error.
    conn1.close()
    # Now executing SELECT 1 on closed connection raises ProgrammingError (which is NOT sqlite3.Error in some versions?)
    # or sqlite3.ProgrammingError which inherits from sqlite3.Error.

    # Let's verify what happens when we try to use it via _get_connection
    # _get_connection calls SELECT 1. If it fails, it should create NEW connection.

    # We need to make sure _get_connection SEES the old connection first.
    # It does via thread local.

    conn2 = store._get_connection()

    assert conn2 is not conn1
    assert conn2 is not None
    # conn2 should be fresh and open
    conn2.execute("SELECT 1")


def test_db_health_method(db_path):
    store = SQLiteEventStore(db_path)
    status = store.db_health()
    assert status["status"] == "ok"
