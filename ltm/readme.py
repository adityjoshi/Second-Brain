import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

Q3_DIR = Path(__file__).resolve().parents[1] / "q3"
for mod in ("database", "models", "schemas", "main"):
    sys.modules.pop(mod, None)
sys.path.insert(0, str(Q3_DIR))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


NOTEBOOK = {"title": "Morning Pages", "author": "Riya Kapoor"}
ENTRY = {"heading": "First Light", "mood": "calm", "word_count": 180}


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded(client):
    notebook = client.post("/notebooks", json=NOTEBOOK).json()
    entry = client.post(
        f"/notebooks/{notebook['id']}/entries", json=ENTRY
    ).json()
    return notebook, entry


def test_create_notebook(client):
    response = client.post("/notebooks", json=NOTEBOOK)
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "Morning Pages",
        "author": "Riya Kapoor",
    }
    assert "entries" not in response.json()


def test_add_entry(client):
    notebook_id = client.post("/notebooks", json=NOTEBOOK).json()["id"]
    response = client.post(f"/notebooks/{notebook_id}/entries", json=ENTRY)
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "heading": "First Light",
        "mood": "calm",
        "word_count": 180,
    }


def test_get_notebook_nests_entries(seeded, client):
    notebook, _ = seeded
    response = client.get(f"/notebooks/{notebook['id']}")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "title": "Morning Pages",
        "author": "Riya Kapoor",
        "entries": [
            {
                "id": 1,
                "heading": "First Light",
                "mood": "calm",
                "word_count": 180,
            }
        ],
    }


def test_get_notebook_filter_and_sort(seeded, client):
    notebook, _ = seeded
    client.post(
        f"/notebooks/{notebook['id']}/entries",
        json={"heading": "Busy Day", "mood": "stressed", "word_count": 90},
    )
    client.post(
        f"/notebooks/{notebook['id']}/entries",
        json={"heading": "Quiet Note", "mood": "calm", "word_count": 40},
    )

    response = client.get(
        f"/notebooks/{notebook['id']}",
        params={"mood": "calm", "sort": "word_count"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Morning Pages"
    assert body["author"] == "Riya Kapoor"
    assert [e["mood"] for e in body["entries"]] == ["calm", "calm"]
    assert [e["word_count"] for e in body["entries"]] == [40, 180]


def test_get_notebook_sort_by_heading(seeded, client):
    notebook, _ = seeded
    client.post(
        f"/notebooks/{notebook['id']}/entries",
        json={"heading": "Alpha", "mood": "calm", "word_count": 10},
    )
    response = client.get(
        f"/notebooks/{notebook['id']}",
        params={"sort": "heading"},
    )
    assert response.status_code == 200
    headings = [e["heading"] for e in response.json()["entries"]]
    assert headings == sorted(headings)


def test_clear_entries(seeded, client):
    notebook, _ = seeded
    other = client.post(
        "/notebooks",
        json={"title": "Night Log", "author": "Asha"},
    ).json()
    client.post(
        f"/notebooks/{other['id']}/entries",
        json={"heading": "Keep Me", "mood": "happy", "word_count": 50},
    )

    response = client.delete(f"/notebooks/{notebook['id']}/entries")
    assert response.status_code == 204
    assert response.content == b""

    cleared = client.get(f"/notebooks/{notebook['id']}").json()
    assert cleared["title"] == "Morning Pages"
    assert cleared["entries"] == []

    other_body = client.get(f"/notebooks/{other['id']}").json()
    assert len(other_body["entries"]) == 1


def test_get_missing_notebook_returns_404(client):
    assert client.get("/notebooks/999").status_code == 404


def test_add_entry_missing_notebook_returns_404(client):
    response = client.post("/notebooks/999/entries", json=ENTRY)
    assert response.status_code == 404


def test_clear_entries_missing_notebook_returns_404(client):
    assert client.delete("/notebooks/999/entries").status_code == 404


def test_create_notebook_empty_title_returns_422(client):
    response = client.post(
        "/notebooks", json={"title": "", "author": "Riya Kapoor"}
    )
    assert response.status_code == 422


def test_create_notebook_empty_author_returns_422(client):
    response = client.post(
        "/notebooks", json={"title": "Morning Pages", "author": ""}
    )
    assert response.status_code == 422


def test_add_entry_empty_heading_returns_422(seeded, client):
    notebook, _ = seeded
    response = client.post(
        f"/notebooks/{notebook['id']}/entries",
        json={"heading": "", "mood": "calm", "word_count": 10},
    )
    assert response.status_code == 422


def test_add_entry_empty_mood_returns_422(seeded, client):
    notebook, _ = seeded
    response = client.post(
        f"/notebooks/{notebook['id']}/entries",
        json={"heading": "Note", "mood": "", "word_count": 10},
    )
    assert response.status_code == 422


def test_add_entry_word_count_zero_returns_422(seeded, client):
    notebook, _ = seeded
    response = client.post(
        f"/notebooks/{notebook['id']}/entries",
        json={"heading": "Note", "mood": "calm", "word_count": 0},
    )
    assert response.status_code == 422


def test_add_entry_word_count_one_accepted(seeded, client):
    notebook, _ = seeded
    response = client.post(
        f"/notebooks/{notebook['id']}/entries",
        json={"heading": "Tiny", "mood": "calm", "word_count": 1},
    )
    assert response.status_code == 201
    assert response.json()["word_count"] == 1


def test_invalid_sort_author_returns_422(seeded, client):
    notebook, _ = seeded
    response = client.get(
        f"/notebooks/{notebook['id']}", params={"sort": "author"}
    )
    assert response.status_code == 422


def test_empty_sort_returns_422(seeded, client):
    notebook, _ = seeded
    response = client.get(f"/notebooks/{notebook['id']}?sort=")
    assert response.status_code == 422
