import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.database import session as db_session
from backend.main import create_app


@pytest.fixture(autouse=True)
def reset_db(tmp_path):
    test_db = tmp_path / "test_visaflow.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"
    db_session.configure_database(os.environ["DATABASE_URL"])
    db_session.init_db()
    yield
    db_session.engine.dispose()


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
