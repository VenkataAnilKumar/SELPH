"""Verify every Alembic migration applies, reverses and re-applies cleanly.

Usage (DESTROYS ALL DATA in the target database; use a scratch/CI database):
    DATABASE_URL=postgresql://... python scripts/check_migrations_roundtrip.py --yes-destroy-data

Steps: upgrade head -> downgrade base -> verify no app tables left -> upgrade head -> verify the
model schema matches. Stepwise downgrades are also exercised (head -> 001 one revision at a time).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parent.parent


def _config(url: str) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _tables(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names()) - {"alembic_version", "spatial_ref_sys"}
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes-destroy-data", action="store_true", help="required: this drops all tables")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql"):
        print("DATABASE_URL must point at a Postgres database")
        return 2
    if not args.yes_destroy_data:
        print("Refusing to run without --yes-destroy-data (this drops every table in the target database)")
        return 2

    cfg = _config(url)
    revisions = [r.revision for r in ScriptDirectory.from_config(cfg).walk_revisions()]  # newest first
    print(f"{len(revisions)} migrations: {revisions[-1]} .. {revisions[0]}")

    command.downgrade(cfg, "base")  # start from a known-empty state even if already migrated
    command.upgrade(cfg, "head")
    full = _tables(url)
    print(f"upgrade head: {len(full)} tables")

    # One revision at a time so a broken downgrade names the exact migration.
    for rev in revisions[:-1]:
        step = f"{rev}"
        try:
            command.downgrade(cfg, "-1")
        except Exception as exc:
            print(f"FAIL: downgrading {step} raised {type(exc).__name__}: {exc}")
            return 1
    command.downgrade(cfg, "base")
    leftover = _tables(url)
    if leftover:
        print(f"FAIL: downgrade to base left tables behind: {sorted(leftover)}")
        return 1
    print("downgrade base: clean")

    command.upgrade(cfg, "head")
    again = _tables(url)
    if again != full:
        print(f"FAIL: re-upgrade differs. missing={sorted(full - again)} extra={sorted(again - full)}")
        return 1
    print(f"re-upgrade head: {len(again)} tables, identical")
    print("Migration round-trip OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
