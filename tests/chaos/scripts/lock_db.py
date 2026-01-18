import os
import sqlite3
import sys
import time


def lock_database(db_path, duration):
    try:
        # Use full path
        db_path = os.path.abspath(db_path)

        # Connect
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()

        # Lock exclusively
        cursor.execute("BEGIN EXCLUSIVE TRANSACTION")

        # Signal to parent process that lock is acquired
        print("LOCKED", flush=True)

        # Hold lock
        time.sleep(duration)

        # Release (though close will do it)
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: lock_db.py <db_path> <duration_seconds>")
        sys.exit(1)

    db_path = sys.argv[1]
    duration = float(sys.argv[2])

    lock_database(db_path, duration)
