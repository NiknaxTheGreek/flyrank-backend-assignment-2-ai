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
    assert client.get(f"/tasks/{task_id}").json() == {
        "error": f"Task {task_id} not found"
    }
    assert client.put("/tasks/9999", json={"done": True}).json() == {
        "error": "Task 9999 not found"
    }
    assert client.delete("/tasks/9999").json() == {
        "error": "Task 9999 not found"
    }


def test_assignment_1_root_compatibility(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_assignment_1_health_compatibility(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("method", "url", "payload"),
    [
        ("post", "/tasks", {}),
        ("post", "/tasks", {"title": "   "}),
        ("post", "/tasks", {"title": "Wrong type", "done": "true"}),
        ("get", "/tasks/not-an-id", None),
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
    assert response.json() == {"error": "Invalid request body"}


def test_assignment_1_post_update_and_path_compatibility(client: TestClient) -> None:
    rejected_post = client.post("/tasks", json={"title": "Do not accept done", "done": True})
    assert rejected_post.status_code == 400
    assert rejected_post.json() == {"error": "Invalid request body"}

    empty_update = client.put("/tasks/1", json={})
    assert empty_update.status_code == 400
    assert empty_update.json() == {
        "error": "Request body must include title and/or done"
    }

    nullable_title = client.put("/tasks/1", json={"title": None})
    assert nullable_title.status_code == 200
    assert nullable_title.json() == {"id": 1, "title": None, "done": False}

    nullable_done = client.put("/tasks/1", json={"done": None})
    assert nullable_done.status_code == 200
    assert nullable_done.json() == {"id": 1, "title": None, "done": None}

    coercible_done = client.put("/tasks/2", json={"done": "true"})
    assert coercible_done.status_code == 200
    assert coercible_done.json() == {
        "id": 2,
        "title": "Build a CRUD API",
        "done": True,
    }

    for task_id in (0, -1):
        missing = client.get(f"/tasks/{task_id}")
        assert missing.status_code == 404
        assert missing.json() == {"error": f"Task {task_id} not found"}


def test_docs_are_available(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200


def test_data_persists_across_application_restarts(database_path: Path) -> None:
    with TestClient(create_app(database_path)) as first_client:
        created = first_client.post(
            "/tasks",
            json={"title": "Survive a restart"},
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