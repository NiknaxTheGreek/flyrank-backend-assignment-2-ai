# Assignment 2 Requirements Audit

## Scope and contract

| Requirement | Implementation and review evidence |
| --- | --- |
| Preserve Assignment 1 task contract | The API exposes the existing task fields: `id`, `title`, and `done`, through `GET`, `POST`, `PUT`, and `DELETE` task routes. |
| SQLite-backed CRUD | `TaskRepository` performs all task reads and writes with the Python standard-library `sqlite3` module. No in-memory task collection is used. |
| Startup initialization | Application lifespan startup creates the `tasks` table when needed. |
| Starter rows | Startup inserts the three Assignment 1 starter tasks only when the `tasks` table has zero rows. |
| Validation and errors | Request validation returns `400`; missing task IDs return `404`; create returns `201`; successful delete returns `204`. |
| Partial updates | `PUT /tasks/{id}` supports `title`-only, `done`-only, or both fields and retains omitted fields. |
| SQL safety | Task values and IDs are supplied to SQLite as bound `?` parameters. The partial-update statements are fixed, not dynamically assembled from request input. |
| Persistence and safety tests | The test suite includes a two-process Uvicorn restart test with direct SQLite row inspection and injection-looking input. |

## Dependency audit

`pyproject.toml` and `uv.lock` are the dependency source of truth.

| Dependency | Purpose |
| --- | --- |
| `fastapi` | HTTP API and request validation |
| `uvicorn` | ASGI development server and process-level verification |
| `pytest` | Automated test runner |
| `httpx` | FastAPI `TestClient` support |
| Python `sqlite3` | SQLite database access; no external database driver is required |

## Explicitly out of scope

- PostgreSQL
- Docker or Compose files
- Authentication or authorization
- Scraping or AI integrations
- Assignment 3 infrastructure or deployment features