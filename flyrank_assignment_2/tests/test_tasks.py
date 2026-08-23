from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flyrank_assignment_2.app.main import create_app


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "tasks.sqlite3"


@pytest.fixture
def client(database_path: Path):
    with TestClient(create_app(database_path)) as test_client:
        yield test_client


def test_crud_lifecycle_and_status_codes(client: TestClient) -> None:
    information = client.get("/")
    assert information.status_code == 200
    assert information.json()["tasks"] == "/tasks"

    initial_tasks = client.get("/tasks")
    assert initial_tasks.status_code == 200
    assert initial_tasks.json() == [
        {"id": 1, "title": "Learn FastAPI", "done": False},
        {"id": 2, "title": "Build a CRUD API", "done": False},
        {"id": 3, "title": "Read the assignment", "done": True},
    ]

    created = client.post("/tasks", json={"title": "Write persistence tests"})
    assert created.status_code == 201
    assert created.json() == {
        "id": 4,
        "title": "Write persistence tests",
        "done": False,
    }

    task_id = created.json()["id"]
    fetched = client.get(f"/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json() == created.json()

    updated = client.put(
        f"/tasks/{task_id}",
        json={"title": "Ship persistence tests", "done": True},
    )
    assert updated.status_code == 200
    assert updated.json() == {
        "id": task_id,
        "title": "Ship persistence tests",
        "done": True,
    }

    title_only = client.put(f"/tasks/{task_id}", json={"title": "Title only"})
    assert title_only.status_code == 200
    assert title_only.json() == {
        "id": task_id,
        "title": "Title only",
        "done": True,
    }

    done_only = client.put(f"/tasks/{task_id}", json={"done": False})
    assert done_only.status_code == 200
    assert done_only.json() == {
        "id": task_id,
        "title": "Title only",
        "done": False,
    }

    deleted = client.delete(f"/tasks/{task_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/tasks/{task_id}").status_code == 404
    assert client.put("/tasks/9999", json={"done": True}).status_code == 404
    assert client.delete("/tasks/9999").status_code == 404


@pytest.mark.parametrize(
    ("method", "url", "payload"),
    [
        ("post", "/tasks", {}),
        ("post", "/tasks", {"title": "   "}),
        ("post", "/tasks", {"title": "Wrong type", "done": "true"}),
        ("put", "/tasks/1", {}),
        ("put", "/tasks/1", {"title": None}),
        ("put", "/tasks/1", {"done": None}),
        ("get", "/tasks/not-an-id", None),
        ("get", "/tasks/0", None),
    ],
)
def test_invalid_requests_return_400(
    client: TestClient,
    method: str,
    url: str,
    payload: dict[str, object] | None,
) -> None:
    response = getattr(client, method)(url, json=payload) if payload is not None else getattr(client, method)(url)
    assert response.status_code == 400


def test_data_persists_across_application_restarts(database_path: Path) -> None:
    with TestClient(create_app(database_path)) as first_client:
        created = first_client.post(
            "/tasks",
            json={"title": "Survive a restart", "done": True},
        )
        assert created.status_code == 201
        created_task = created.json()

    with TestClient(create_app(database_path)) as restarted_client:
        response = restarted_client.get(f"/tasks/{created_task['id']}")
        assert response.status_code == 200
        assert response.json() == created_task
        assert len(restarted_client.get("/tasks").json()) == 4


def test_empty_database_is_reseeded_without_duplicates(database_path: Path) -> None:
    with TestClient(create_app(database_path)) as first_client:
        for task in first_client.get("/tasks").json():
            assert first_client.delete(f"/tasks/{task['id']}").status_code == 204

    with TestClient(create_app(database_path)) as restarted_client:
        assert restarted_client.get("/tasks").json() == [
            {"id": 4, "title": "Learn FastAPI", "done": False},
            {"id": 5, "title": "Build a CRUD API", "done": False},
            {"id": 6, "title": "Read the assignment", "done": True},
        ]

    with TestClient(create_app(database_path)) as third_client:
        assert len(third_client.get("/tasks").json()) == 3