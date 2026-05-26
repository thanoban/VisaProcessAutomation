import os
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).resolve().parent / "test_visaflow.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.database.base import Base
from backend.database.session import engine, init_db
from backend.main import create_app


def _remove_test_db_with_retry() -> None:
    for _ in range(10):
        if not TEST_DB.exists():
            return
        try:
            TEST_DB.unlink()
            return
        except PermissionError:
            time.sleep(0.1)
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture(autouse=True)
def reset_db():
    engine.dispose()
    _remove_test_db_with_retry()
    init_db()
    yield
    engine.dispose()


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
