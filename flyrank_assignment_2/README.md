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
| `GET` | `/` | `200` |
| `GET` | `/health` | `200` |
| `GET` | `/tasks` | `200` |
| `GET` | `/tasks/{id}` | `200`, `404` |
| `POST` | `/tasks` | `201`, `400` |
| `PUT` | `/tasks/{id}` | `200`, `400`, `404` |
| `DELETE` | `/tasks/{id}` | `204`, `404` |

`POST /tasks` requires a non-blank `title`, rejects extra fields, and always
creates the task with `done: false`. `PUT /tasks/{id}` accepts either or both
Assignment 1 task fields and retains omitted fields. Invalid request bodies
return `{"error": "Invalid request body"}` with `400`; unknown numeric task IDs
return the Assignment 1 `404` error shape.

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

## Assumptions and limitations

- Persistence is a local SQLite file (`flyrank_assignment_2/data/tasks.sqlite3`
  by default). It is suitable for this standalone assignment and remains
  available when the same file is reused after a process restart.
- SQLite is not a substitute for a managed, shared production database. This
  implementation is not designed for multi-region deployment, horizontal
  scaling, or sustained high-concurrency writes across multiple application
  processes.
- Authentication, authorization, backups, and deployment infrastructure are
  intentionally outside this assignment's scope.