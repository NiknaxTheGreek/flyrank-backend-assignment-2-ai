from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_server(database_path: Path, port: int) -> subprocess.Popen[str]:
    environment = os.environ.copy()
    environment["TASK_DATABASE_PATH"] = str(database_path)
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(PROJECT_ROOT), environment.get("PYTHONPATH", "")])
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "flyrank_assignment_2.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"FastAPI process exited during startup:\n{output}")
        try:
            status_code, _ = _request(port, "GET", "/")
            if status_code == 200:
                return process
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)

    process.terminate()
    output, _ = process.communicate(timeout=5)
    raise RuntimeError(f"FastAPI process did not start:\n{output}")


def _stop_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stdout:
        process.stdout.read()


@contextmanager
def _running_server(database_path: Path, port: int) -> Iterator[None]:
    process = _start_server(database_path, port)
    try:
        yield
    finally:
        _stop_server(process)


def _request(
    port: int,
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> tuple[int, object | None]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=body,
        headers={"Content-Type": "application/json"} if body else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            raw_body = response.read()
            return response.status, json.loads(raw_body) if raw_body else None
    except urllib.error.HTTPError as error:
        raw_body = error.read()
        return error.code, json.loads(raw_body) if raw_body else None


def _database_rows(database_path: Path) -> list[tuple[int, str, int]]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id ASC"
        ).fetchall()
    return [(int(task_id), str(title), int(done)) for task_id, title, done in rows]


def test_real_restart_persistence_and_sql_injection_safety(tmp_path: Path) -> None:
    database_path = tmp_path / "restart-verification.sqlite3"
    first_port = _free_port()
    second_port = _free_port()
    injection_looking_title = "Robert'); DROP TABLE tasks; --"

    with _running_server(database_path, first_port):
        status_code, starter_tasks = _request(first_port, "GET", "/tasks")
        assert status_code == 200
        assert starter_tasks == [
            {"id": 1, "title": "Learn FastAPI", "done": False},
            {"id": 2, "title": "Build a CRUD API", "done": False},
            {"id": 3, "title": "Read the assignment", "done": True},
        ]

        status_code, created_task = _request(
            first_port,
            "POST",
            "/tasks",
            {"title": "Created before restart"},
        )
        assert status_code == 201
        assert isinstance(created_task, dict)
        created_id = int(created_task["id"])

        status_code, updated_task = _request(
            first_port,
            "PUT",
            f"/tasks/{created_id}",
            {"title": injection_looking_title, "done": True},
        )
        assert status_code == 200
        assert updated_task == {
            "id": created_id,
            "title": injection_looking_title,
            "done": True,
        }

        status_code, _ = _request(first_port, "DELETE", "/tasks/1")
        assert status_code == 204

        with sqlite3.connect(database_path) as connection:
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ? AND name = ?",
                ("table", "tasks"),
            ).fetchone()
            count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            stored_task = connection.execute(
                "SELECT id, title, done FROM tasks WHERE id = ?",
                (created_id,),
            ).fetchone()
            deleted_task = connection.execute(
                "SELECT id FROM tasks WHERE id = ?",
                (1,),
            ).fetchone()

        assert table == ("tasks",)
        assert count == 3
        assert stored_task == (created_id, injection_looking_title, 1)
        assert deleted_task is None

    with _running_server(database_path, second_port):
        status_code, tasks_after_restart = _request(second_port, "GET", "/tasks")
        assert status_code == 200
        assert tasks_after_restart == [
            {"id": 2, "title": "Build a CRUD API", "done": False},
            {"id": 3, "title": "Read the assignment", "done": True},
            {
                "id": created_id,
                "title": injection_looking_title,
                "done": True,
            },
        ]
        assert _request(second_port, "GET", "/tasks/1")[0] == 404

        with sqlite3.connect(database_path) as connection:
            count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            rows = _database_rows(database_path)
            stored_task = connection.execute(
                "SELECT title, done FROM tasks WHERE id = ?",
                (created_id,),
            ).fetchone()

        assert count == 3
        assert rows == [
            (2, "Build a CRUD API", 0),
            (3, "Read the assignment", 1),
            (created_id, injection_looking_title, 1),
        ]
        assert stored_task == (injection_looking_title, 1)


def test_existing_relational_task_rows_are_not_reseeded(tmp_path: Path) -> None:
    database_path = tmp_path / "existing.sqlite3"
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
            (1, "Existing row", 0),
        )

    # The application must not seed over an existing relational row.
    with _running_server(database_path, _free_port()):
        rows = _database_rows(database_path)
        assert rows == [(1, "Existing row", 0)]