import os
import tempfile
import pytest
from sqlalchemy import create_engine, text, inspect
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole
from app.models.policy import Policy, PolicyStatus
from app.models.scheme import Scheme, SchemeStatus
from app.db.database import get_db, Base
import importlib.util


def test_migration_0010_upgrade_and_citizen_dashboard():
    """
    Simulate pre-0010 production state (where saved_policies only has policy_id),
    populate existing saved_policies records (policy-only),
    run migration 0010_saved_policies_scheme_id upgrade(),
    and verify that schema is upgraded and citizen dashboard returns HTTP 200.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    sqlite_url = f"sqlite:///{db_path}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

    try:
        # Create all tables from Base metadata except saved_policies
        other_tables = [table for name, table in Base.metadata.tables.items() if name != "saved_policies"]
        Base.metadata.create_all(engine, tables=other_tables)

        # Create pre-0010 saved_policies table (missing scheme_id, policy_id is NOT NULL)
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE saved_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    policy_id INTEGER NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(policy_id) REFERENCES policies(id) ON DELETE CASCADE
                );
            """))

            # Populate pre-existing records (representing production data)
            conn.execute(text(
                "INSERT INTO users (id, name, email, password_hash, role, is_active, is_verified) "
                "VALUES (1, 'Prod Citizen', 'prod_citizen@example.com', 'hashed_pw', 'CITIZEN', 1, 1)"
            ))
            conn.execute(text(
                "INSERT INTO policies (id, title, category, status, is_active) "
                "VALUES (10, 'National Health Policy', 'Health', 'PUBLISHED', 1)"
            ))
            conn.execute(text(
                "INSERT INTO schemes (id, name, category, status, is_active) "
                "VALUES (20, 'Ayushman Bharat Scheme', 'Health', 'ACTIVE', 1)"
            ))
            conn.execute(text(
                "INSERT INTO saved_policies (id, user_id, policy_id, notes) "
                "VALUES (100, 1, 10, 'Pre-existing production policy bookmark')"
            ))

        # Verify scheme_id does NOT exist yet in saved_policies
        inspector_before = inspect(engine)
        cols_before = [col["name"] for col in inspector_before.get_columns("saved_policies")]
        assert "scheme_id" not in cols_before
        assert "policy_id" in cols_before

        # Execute migration 0010 upgrade()
        migration_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic", "versions", "0010_saved_policies_scheme_id.py"))
        spec = importlib.util.spec_from_file_location("migration_0010", migration_path)
        migration_0010 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_0010)

        with engine.begin() as conn:
            ctx = MigrationContext.configure(conn, opts={"as_sql": False})
            op = Operations(ctx)
            migration_0010.op = op
            migration_0010.upgrade()

        # Verify scheme_id column NOW exists
        inspector_after = inspect(engine)
        cols_after = [col["name"] for col in inspector_after.get_columns("saved_policies")]
        assert "scheme_id" in cols_after
        assert "policy_id" in cols_after

        # Verify existing data was preserved intact
        with engine.begin() as conn:
            result = conn.execute(text("SELECT id, user_id, policy_id, scheme_id, notes FROM saved_policies WHERE id = 100")).fetchone()
            assert result is not None
            assert result[0] == 100
            assert result[1] == 1
            assert result[2] == 10
            assert result[3] is None
            assert result[4] == "Pre-existing production policy bookmark"

            # Insert a new saved scheme record (scheme_id=20, policy_id=NULL)
            conn.execute(text(
                "INSERT INTO saved_policies (id, user_id, policy_id, scheme_id, notes, created_at) "
                "VALUES (101, 1, NULL, 20, 'New scheme bookmark', CURRENT_TIMESTAMP)"
            ))

        # Test FastAPI dashboard endpoint with this upgraded database
        from sqlalchemy.orm import sessionmaker
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        token = create_access_token(subject=1, role="CITIZEN")
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/dashboard/citizen", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert "saved_policies" in data
        saved = data["saved_policies"]
        assert len(saved) == 2

        # Check policy item
        policy_item = next(item for item in saved if item["item_type"] == "policy")
        assert policy_item["id"] == 100
        assert policy_item["policy_id"] == 10
        assert policy_item["scheme_id"] is None
        assert policy_item["title"] == "National Health Policy"

        # Check scheme item
        scheme_item = next(item for item in saved if item["item_type"] == "scheme")
        assert scheme_item["id"] == 101
        assert scheme_item["policy_id"] is None
        assert scheme_item["scheme_id"] == 20
        assert scheme_item["title"] == "Ayushman Bharat Scheme"

        app.dependency_overrides.clear()

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)
