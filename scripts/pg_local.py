"""Manage a project-owned PostgreSQL cluster under $FINEPRINT_DATA/pgdata (localhost only).

Uses the installed PostgreSQL binaries; never touches any existing server. The
superuser password is generated once into $FINEPRINT_DATA/secrets (outside git).

  python -I scripts/pg_local.py init|start|stop|status
  python -I scripts/pg_local.py createdb fineprint fineprint_test
"""

import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import config  # noqa: E402

CANDIDATE_BINS = [Path(r"C:\Program Files\PostgreSQL\18\bin"), Path("/usr/lib/postgresql/18/bin"),
                  Path("/opt/homebrew/opt/postgresql@18/bin")]


def pg_bin(name):
    found = shutil.which(name)
    if found:
        return found
    for d in CANDIDATE_BINS:
        exe = d / (name + (".exe" if os.name == "nt" else ""))
        if exe.exists():
            return str(exe)
    sys.exit(f"cannot find PostgreSQL binary {name}; add its bin directory to PATH")


def run(*args, **kw):
    print("+", " ".join(str(a) for a in args), file=sys.stderr)
    return subprocess.run([str(a) for a in args], check=True, **kw)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    root = config.data_dir()
    pgdata, sec, logs = root / "pgdata", root / "secrets", root / "runs"
    if cmd == "init":
        if pgdata.exists():
            sys.exit(f"{pgdata} already exists; refusing to re-init")
        sec.mkdir(parents=True, exist_ok=True)
        pw = secrets.token_urlsafe(32)
        pwfile = sec / "pg_superuser_password"
        pwfile.write_text(pw, encoding="utf-8", newline="\n")
        # libpq rejects a CRLF-terminated pgpass line, so force LF on Windows too.
        config.passfile().write_text(f"127.0.0.1:{config.PG_PORT}:*:{config.PG_USER}:{pw}\n", encoding="utf-8",
                                     newline="\n")
        run(pg_bin("initdb"), "-D", pgdata, "-U", config.PG_USER, "--pwfile", pwfile, "-E", "UTF8",
            "--locale=C", "--auth-host=scram-sha-256", "--auth-local=scram-sha-256")
        with open(pgdata / "postgresql.conf", "a", encoding="utf-8") as f:
            f.write(f"\n# fineprint project cluster\nlisten_addresses = '127.0.0.1'\nport = {config.PG_PORT}\n"
                    "shared_buffers = 512MB\nmaintenance_work_mem = 512MB\nmax_wal_size = 4GB\n")
        print("initialized", pgdata)
    elif cmd == "start":
        logs.mkdir(parents=True, exist_ok=True)
        # The postmaster must not inherit our stdio, or callers piping our output never see EOF.
        run(pg_bin("pg_ctl"), "-D", pgdata, "-l", logs / "postgres.log", "-w", "start",
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif cmd == "stop":
        run(pg_bin("pg_ctl"), "-D", pgdata, "-w", "stop", "-m", "fast")
    elif cmd == "status":
        subprocess.run([pg_bin("pg_ctl"), "-D", str(pgdata), "status"])
    elif cmd == "createdb":
        env = dict(os.environ, PGPASSFILE=str(config.passfile()))
        for db in sys.argv[2:]:
            exists = subprocess.run([pg_bin("psql"), "-h", "127.0.0.1", "-p", str(config.PG_PORT), "-U",
                                     config.PG_USER, "-d", "postgres", "-Atc",
                                     f"select 1 from pg_database where datname = '{db}'"],
                                    env=env, capture_output=True, text=True, check=True).stdout.strip()
            if exists:
                print("exists", db)
                continue
            run(pg_bin("createdb"), "-h", "127.0.0.1", "-p", config.PG_PORT, "-U", config.PG_USER, db, env=env)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
