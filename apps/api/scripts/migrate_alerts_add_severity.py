r"""Manually add the `severity` column to the SQLite `alerts` table.

Run this from `apps/api`:

    .\venv\Scripts\python.exe scripts\migrate_alerts_add_severity.py

This script is intentionally manual. The app does not auto-migrate existing
SQLite tables.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings


def _sqlite_path_from_url(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise RuntimeError(
            "This helper only supports sqlite:/// URLs. "
            f"Current DATABASE_URL: {database_url}"
        )

    raw_path = database_url[len(prefix) :]
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def main() -> None:
    db_path = _sqlite_path_from_url(settings.database_url)
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found at {db_path}. Start the backend once first."
        )

    conn = sqlite3.connect(db_path)
    try:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(alerts)").fetchall()
        }
        if not columns:
            raise RuntimeError(
                "The `alerts` table does not exist yet. Start the backend once first."
            )

        if "severity" in columns:
            print("No migration needed: `alerts.severity` already exists.")
            return

        conn.execute(
            "ALTER TABLE alerts "
            "ADD COLUMN severity VARCHAR(8) NOT NULL DEFAULT 'warning'"
        )
        conn.commit()
        print(f"Migration complete: added `severity` to `alerts` in {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
