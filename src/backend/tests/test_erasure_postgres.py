"""Erasure against real Postgres, where foreign keys are enforced (SQLite does not).

Runs in the CI migration-smoke job (DATABASE_URL = migrated Postgres); skipped otherwise.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _migrated_postgres() -> bool:
    if not DATABASE_URL.startswith("postgresql"):
        return False
    try:
        return "alembic_version" in inspect(create_engine(DATABASE_URL)).get_table_names()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _migrated_postgres(), reason="requires a migrated Postgres DATABASE_URL")


@pytest.fixture
def real_database():
    """Other suites leave a SQLite get_db override on the app; this test must hit Postgres."""
    from app.database import get_db
    from app.main import app

    saved = app.dependency_overrides.pop(get_db, None)
    yield
    if saved is not None:
        app.dependency_overrides[get_db] = saved


def test_erasure_respects_foreign_keys_and_leaves_other_users_alone(real_database):
    from app.main import app
    from app.models import Base, DeletionCertificate, User
    from app.services import erasure
    from tests.test_erasure import CONFIRM, PASSWORD, _populate, _signup, _user_scoped_counts

    client = TestClient(app)
    Session = sessionmaker(bind=create_engine(DATABASE_URL))
    tag = uuid.uuid4().hex[:8]
    a_id, a_headers = _signup(client, f"erase-a-{tag}@example.com")
    b_id, b_headers = _signup(client, f"erase-b-{tag}@example.com")

    with Session() as db:
        _populate(client, db, a_id, a_headers, f"A{tag}")
        _populate(client, db, b_id, b_headers, f"B{tag}")
        b_before = _user_scoped_counts(db, b_id)
        assert len(_user_scoped_counts(db, a_id)) >= 12  # the awkward tables are really populated

    r = client.request("DELETE", "/v1/privacy/account", headers=a_headers, json={"password": PASSWORD, "confirm": CONFIRM})
    assert r.status_code == 200, r.text
    cert_id = r.json()["certificate_id"]

    with Session() as db:
        assert _user_scoped_counts(db, a_id) == {}
        assert db.get(User, a_id) is None
        assert _user_scoped_counts(db, b_id) == b_before
        cert = db.get(DeletionCertificate, cert_id)
        assert erasure.verify_certificate(cert)
        audit = Base.metadata.tables["audit_logs"]
        assert db.execute(select(func.count()).select_from(audit).where(audit.c.user_id == a_id)).scalar() == 0
