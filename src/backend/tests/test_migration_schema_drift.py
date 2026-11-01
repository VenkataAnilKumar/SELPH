"""Guard: ORM models and migrated Postgres schema must not drift apart.

SQLite-based unit tests build tables from the models, so a column that was never
added by a migration (e.g. users.push_token) only fails in a real deployment.
This runs in the CI migration-smoke job (DATABASE_URL points at a migrated Postgres)
and is skipped otherwise.
"""

import os

import pytest
from sqlalchemy import create_engine, inspect

DATABASE_URL = os.environ.get("DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith("postgresql"),
    reason="requires DATABASE_URL pointing at a migrated Postgres",
)


def test_models_match_migrated_schema():
    from app.models import Base

    inspector = inspect(create_engine(DATABASE_URL))
    db_tables = set(inspector.get_table_names())
    problems = []

    for table in Base.metadata.sorted_tables:
        if table.name not in db_tables:
            problems.append(f"missing table: {table.name}")
            continue
        db_cols = {c["name"]: c for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name not in db_cols:
                problems.append(f"missing column: {table.name}.{col.name}")
            elif db_cols[col.name]["nullable"] != col.nullable:
                problems.append(
                    f"nullability differs: {table.name}.{col.name} "
                    f"(db={db_cols[col.name]['nullable']}, model={col.nullable})"
                )

    assert not problems, "Model/migration drift:\n  " + "\n  ".join(problems)
