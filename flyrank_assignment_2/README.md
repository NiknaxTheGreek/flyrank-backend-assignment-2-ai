# FlyRank Backend Assignment 2

An independent FastAPI implementation of the Assignment 1 task CRUD API. The
public task contract stays small and unchanged; the persistence layer is now a
SQLite database instead of an in-memory collection.

## Task shape

```json
{
  "id": 1,
  "title": "Learn FastAPI",
  "done": false
}
```

## Routes

| Method | Route | Success |
| --- | --- | --- |
| `GET` | `/tasks` | `200` |
| `GET` | `/tasks/{id}` | `200`, `404` |
| `POST` | `/tasks` | `201`, `400` |
| `PUT` | `/tasks/{id}` | `200`, `400`, `404` |
| `DELETE` | `/tasks/{id}` | `204`, `404` |

`POST /tasks` requires a non-blank `title` and accepts an optional boolean
`done` (default `false`). `PUT /tasks/{id}` accepts either or both fields.
Malformed IDs and invalid request bodies return `400`; unknown task IDs return
`404`.

## SQLite initialization and seeding

At application startup, the service creates the `tasks` table if it does not
exist. If the table contains no tasks, it receives these three starter tasks:

1. Learn FastAPI
2. Build a CRUD API
3. Read the assignment

When tasks already exist, startup leaves them unchanged, so normal restarts
never create duplicates. All SQL values are sent as SQLite parameters rather
than interpolated into SQL strings.

## Run

From the project root:

```bash
uv run uvicorn app.main:app --app-dir flyrank_assignment_2 --reload
```

The interactive API documentation is available at `/docs`.

By default, data is saved to `flyrank_assignment_2/data/tasks.sqlite3`. To use
another SQLite file, set `TASK_DATABASE_PATH` before starting the app.

## Test

```bash
uv run pytest
```

The suite covers CRUD happy paths, validation and `404` behavior, title-only
and done-only updates, startup seed behavior, deletion persistence, and restart
survival. The persistence/security stage starts two separate Uvicorn processes
with the same SQLite file and verifies rows directly through SQLite queries.

For the review checklist and dependency scope, see
[REQUIREMENTS_AUDIT.md](REQUIREMENTS_AUDIT.md). The latest executed verification
record is kept in [VERIFICATION.md](VERIFICATION.md).