import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

# Base de données en mémoire pour les tests (isolation complète)
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Recrée les tables avant chaque test et les supprime après."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Tests POST /shorten ────────────────────────────────────────────────────────

def test_shorten_url_success():
    response = client.post("/shorten", json={"url": "https://www.example.com/une/url/longue"})
    assert response.status_code == 201
    data = response.json()
    assert "short" in data
    assert "code" in data
    assert len(data["code"]) == 6
    assert data["original"] == "https://www.example.com/une/url/longue"


def test_shorten_same_url_returns_same_code():
    """La même URL longue doit toujours retourner le même code."""
    r1 = client.post("/shorten", json={"url": "https://www.example.com/page"})
    r2 = client.post("/shorten", json={"url": "https://www.example.com/page"})
    assert r1.json()["code"] == r2.json()["code"]


def test_shorten_invalid_url():
    response = client.post("/shorten", json={"url": "pas-une-url"})
    assert response.status_code == 422  # Pydantic validation error


# ── Tests GET /{code} ─────────────────────────────────────────────────────────

def test_redirect_success():
    create = client.post("/shorten", json={"url": "https://www.example.com"})
    code = create.json()["code"]

    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "https://www.example.com"


def test_redirect_unknown_code():
    response = client.get("/xxxxxx", follow_redirects=False)
    assert response.status_code == 404


# ── Tests GET /stats/{code} ───────────────────────────────────────────────────

def test_stats_success():
    create = client.post("/shorten", json={"url": "https://www.example.com/stats-test"})
    code = create.json()["code"]

    # On clique 2 fois
    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)

    stats = client.get(f"/stats/{code}")
    assert stats.status_code == 200
    data = stats.json()
    assert data["clicks"] == 2
    assert data["code"] == code
    assert "created_at" in data


def test_stats_unknown_code():
    response = client.get("/stats/xxxxxx")
    assert response.status_code == 404
