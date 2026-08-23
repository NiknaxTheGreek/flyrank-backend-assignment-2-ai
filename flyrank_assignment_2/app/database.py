"""SQLite persistence for the task API."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any


STARTER_TASKS: tuple[tuple[str, int], ...] = (
    ("Learn FastAPI", 0),
    ("Build a CRUD API", 0),
    ("Read the assignment", 1),
)


class TaskRepository:
    """Small, parameterized repository that owns all task database access."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create the schema and seed an empty tasks table."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
                )
                """
            )

            task_count = connection.execute(
                "SELECT COUNT(*) FROM tasks"
            ).fetchone()[0]
            if task_count == 0:
                connection.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, ?)",
                    STARTER_TASKS,
                )

    @staticmethod
    def _serialize(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, done FROM tasks ORDER BY id ASC"
            ).fetchall()
        return [self._serialize(row) for row in rows if row is not None]

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, done FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._serialize(row)

    def create_task(self, title: str, done: bool) -> dict[str, Any]:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                (title, int(done)),
            )
            row = connection.execute(
                "SELECT id, title, done FROM tasks WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        task = self._serialize(row)
        if task is None:  # Defensive guard; INSERT must return a row above.
            raise RuntimeError("Created task could not be retrieved.")
        return task

    def update_task(
        self,
        task_id: int,
        *,
        title: str | None = None,
        done: bool | None = None,
        fields: Iterable[str],
    ) -> dict[str, Any] | None:
        requested_fields = set(fields)
        if requested_fields == {"title"}:
            query = "UPDATE tasks SET title = ? WHERE id = ?"
            values: tuple[Any, ...] = (title, task_id)
        elif requested_fields == {"done"}:
            query = "UPDATE tasks SET done = ? WHERE id = ?"
            values = (int(bool(done)), task_id)
        elif requested_fields == {"title", "done"}:
            query = "UPDATE tasks SET title = ?, done = ? WHERE id = ?"
            values = (title, int(bool(done)), task_id)
        else:
            return self.get_task(task_id)

        with self._connect() as connection:
            cursor = connection.execute(query, values)
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT id, title, done FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._serialize(row)

    def delete_task(self, task_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM tasks WHERE id = ?",
                (task_id,),
            )
        return cursor.rowcount > 0