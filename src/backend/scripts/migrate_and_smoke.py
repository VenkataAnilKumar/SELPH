"""Run backend migration + smoke tests in one command.

Usage:
  python scripts/migrate_and_smoke.py
  python scripts/migrate_and_smoke.py --skip-migrate
  python scripts/migrate_and_smoke.py --skip-tests
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse


def _backend_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _check_db_reachable(database_url: str, timeout_seconds: int = 3) -> tuple[bool, str]:
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    if not host:
        return False, "DATABASE_URL missing host"

    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, "ok"
    except OSError as exc:
        return False, f"cannot reach database at {host}:{port} ({exc})"


def _with_host(database_url: str, host: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.hostname:
        return database_url

    userinfo = ""
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += f":{parsed.password}"
        userinfo += "@"

    port = parsed.port or 5432
    netloc = f"{userinfo}{host}:{port}"
    return parsed._replace(netloc=netloc).geturl()


def _candidate_db_urls(database_url: str) -> list[str]:
    parsed = urlparse(database_url)
    host = parsed.hostname
    if not host:
        return [database_url]

    candidates = [database_url]
    for fallback in ("127.0.0.1", "localhost", "postgres"):
        if fallback != host:
            candidates.append(_with_host(database_url, fallback))
    return candidates


def _wait_for_db(database_url: str, max_wait_seconds: int, attempt_timeout_seconds: int = 3) -> tuple[bool, str, str]:
    deadline = time.monotonic() + max_wait_seconds
    last_detail = "database not reachable"
    candidates = _candidate_db_urls(database_url)

    while time.monotonic() < deadline:
        for candidate in candidates:
            ok, detail = _check_db_reachable(candidate, timeout_seconds=attempt_timeout_seconds)
            if ok:
                return True, "ok", candidate
            last_detail = detail
        time.sleep(1)

    return False, last_detail, database_url


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd), check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Alembic migration and backend smoke tests")
    parser.add_argument("--skip-migrate", action="store_true", help="Skip alembic upgrade step")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest smoke step")
    parser.add_argument(
        "--test-path",
        default="tests/test_phase10_end_to_end.py",
        help="Smoke test path to run (default: tests/test_phase10_end_to_end.py)",
    )
    parser.add_argument(
        "--alembic-config",
        default="alembic.ini",
        help="Alembic config path relative to backend root",
    )
    parser.add_argument(
        "--db-wait-seconds",
        type=int,
        default=45,
        help="Maximum seconds to wait for database socket readiness before migration",
    )
    args = parser.parse_args()

    root = _backend_root()
    database_url = os.environ.get("DATABASE_URL", "postgresql://localhost/selph")

    if not args.skip_migrate:
        ok, detail, resolved_database_url = _wait_for_db(database_url, max_wait_seconds=args.db_wait_seconds)
        if not ok:
            print(f"Migration precheck failed: {detail}")
            print("Hint: start PostgreSQL and ensure DATABASE_URL points to a reachable instance.")
            return 2

        if resolved_database_url != database_url:
            print(f"Database reachable via fallback host; using {resolved_database_url}")
            os.environ["DATABASE_URL"] = resolved_database_url

        code = _run([sys.executable, "-m", "alembic", "-c", args.alembic_config, "upgrade", "head"], cwd=root)
        if code != 0:
            return code

    if not args.skip_tests:
        code = _run([sys.executable, "-m", "pytest", args.test_path, "-q"], cwd=root)
        if code != 0:
            return code

    print("Migration + smoke completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
