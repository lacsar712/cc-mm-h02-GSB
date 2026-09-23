import os
import pathlib
import tempfile

import pytest
from fastapi.testclient import TestClient

_DB_PATH = pathlib.Path(tempfile.gettempdir()) / "methane_test.db"
if _DB_PATH.exists():
    _DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ.setdefault("JWT_SECRET", "test-secret")

from app.main import Reading, SessionLocal, app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client: TestClient, username: str, password: str) -> dict:
    res = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture(scope="module")
def viewer_headers(client):
    return login(client, "viewer", "view123456")


@pytest.fixture(scope="module")
def writer_headers(client):
    return login(client, "gasman", "gas123456")


def row_count() -> int:
    db = SessionLocal()
    try:
        return db.query(Reading).count()
    finally:
        db.close()


@pytest.fixture
def count_snapshot():
    return row_count()
