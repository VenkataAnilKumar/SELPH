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
    args = parser.parse_args()

    root = _backend_root()
    database_url = os.environ.get("DATABASE_URL", "postgresql://localhost/selph")

    if not args.skip_migrate:
        ok, detail = _check_db_reachable(database_url)
        if not ok:
            print(f"Migration precheck failed: {detail}")
            print("Hint: start PostgreSQL and ensure DATABASE_URL points to a reachable instance.")
            return 2

        code = _run(["alembic", "-c", args.alembic_config, "upgrade", "head"], cwd=root)
        if code != 0:
            return code

    if not args.skip_tests:
        code = _run(["pytest", args.test_path, "-q"], cwd=root)
        if code != 0:
            return code

    print("Migration + smoke completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
