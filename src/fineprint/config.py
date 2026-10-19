"""Local paths and database connection settings (no secrets live in the repo).

FINEPRINT_DATA  root for raw downloads, the project PostgreSQL cluster, secrets, run logs
                (default: ~/fineprint-data, deliberately outside any synced/OneDrive folder)
FINEPRINT_DSN   libpq conninfo; overrides the project cluster entirely if set
"""

from __future__ import annotations

import os
from pathlib import Path

PG_PORT = 55432
PG_USER = "fineprint"
DEFAULT_DB = "fineprint"


def data_dir() -> Path:
    return Path(os.environ.get("FINEPRINT_DATA", Path.home() / "fineprint-data")).resolve()


def passfile() -> Path:
    return data_dir() / "secrets" / "pgpass.conf"


def dsn(dbname: str = DEFAULT_DB) -> str:
    override = os.environ.get("FINEPRINT_DSN")
    if override:
        return override
    return (f"host=127.0.0.1 port={PG_PORT} user={PG_USER} dbname={dbname} "
            f"passfile='{passfile().as_posix()}' application_name=fineprint")
