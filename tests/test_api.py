import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server"))

from app import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app("sqlite:///:memory:")
    return app.test_client()


@pytest.fixture
def auth(client):
    r = client.post("/api/register", json={"username": "wara", "password": "secret123"})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def test_register_login(client):
    assert client.post("/api/register", json={"username": "ab", "password": "x"}).status_code == 400
    client.post("/api/register", json={"username": "wara", "password": "secret123"})
    assert client.post("/api/register", json={"username": "wara", "password": "secret123"}).status_code == 409
    assert client.post("/api/login", json={"username": "wara", "password": "salah"}).status_code == 401
    assert client.post("/api/login", json={"username": "wara", "password": "secret123"}).status_code == 200


def test_requires_auth(client):
    assert client.get("/api/tasks").status_code == 401
    assert client.get("/api/stats", headers={"Authorization": "Bearer palsu"}).status_code == 401


def test_sessions_and_stats(client, auth):
    sid = client.post("/api/subjects", json={"name": "Jaringan"}, headers=auth).get_json()["id"]
    assert client.post("/api/sessions", json={"subject_id": sid, "minutes": 25}, headers=auth).status_code == 201
    client.post("/api/sessions", json={"subject_id": sid, "minutes": 50}, headers=auth)
    assert client.post("/api/sessions", json={"subject_id": sid, "minutes": 0}, headers=auth).status_code == 400
    assert client.post("/api/sessions", json={"subject_id": 999, "minutes": 5}, headers=auth).status_code == 404

    s = client.get("/api/stats?days=7", headers=auth).get_json()
    assert s["total_minutes"] == 75
    assert s["by_subject"] == {"Jaringan": 75}
    assert s["streak"] == 1
    assert len(s["daily"]) == 7


def test_tasks_crud(client, auth):
    t = client.post("/api/tasks", json={"title": "Laporan", "deadline": "2026-12-01T10:00:00"}, headers=auth).get_json()
    assert t["done"] is False
    r = client.patch(f"/api/tasks/{t['id']}", json={"done": True}, headers=auth)
    assert r.get_json()["done"] is True
    assert client.delete(f"/api/tasks/{t['id']}", headers=auth).status_code == 204
    assert client.get("/api/tasks", headers=auth).get_json() == []


def test_isolation_between_users(client, auth):
    client.post("/api/tasks", json={"title": "Rahasia"}, headers=auth)
    other = client.post("/api/register", json={"username": "orang2", "password": "secret123"}).get_json()
    h2 = {"Authorization": f"Bearer {other['token']}"}
    assert client.get("/api/tasks", headers=h2).get_json() == []
    assert client.patch("/api/tasks/1", json={"done": True}, headers=h2).status_code == 404


def test_concept_map(client, auth):
    m = client.post("/api/maps", json={"title": "Hukum Ohm"}, headers=auth).get_json()
    data = {
        "nodes": [
            {"id": 1, "text": "V = I·R", "kind": "rumus", "x": 0, "y": 0},
            {"id": 2, "text": "Rangkaian LED", "kind": "penerapan", "x": 200, "y": 100},
        ],
        "edges": [{"from": 1, "to": 2, "label": "dipakai di"}],
    }
    assert client.put(f"/api/maps/{m['id']}", json={"data": data}, headers=auth).status_code == 200
    got = client.get(f"/api/maps/{m['id']}", headers=auth).get_json()
    assert json.loads(got["data"]) == data
    assert client.put(f"/api/maps/{m['id']}", json={"data": {"x": 1}}, headers=auth).status_code == 400
