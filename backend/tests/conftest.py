import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def client_env(monkeypatch):
    """内存 SQLite 替换 Postgres，TestClient 进入时会跑真实 startup（含种子数据）。"""
    from app import main

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session_local = sessionmaker(bind=test_engine)
    monkeypatch.setattr(main, "engine", test_engine)
    monkeypatch.setattr(main, "SessionLocal", test_session_local)

    with TestClient(main.app) as client:
        yield client, test_session_local, main.Reading


def login(client, username, password):
    res = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def row_count(session_local, reading_model):
    db = session_local()
    try:
        return db.query(reading_model).count()
    finally:
        db.close()
