# Assignment 2 Requirements Audit

## Scope and contract

| Requirement | Implementation and review evidence |
| --- | --- |
| Preserve Assignment 1 task contract | The API retains the Assignment 1 CRUD routes, task keys, status codes, request handling, and JSON error bodies. `POST` accepts only `title` and creates `done: false`; `PUT` retains Assignment 1's accepted field semantics. |
| SQLite-backed CRUD | `TaskRepository` performs all task reads and writes with the Python standard-library `sqlite3` module. No in-memory task collection is used. |
| Startup initialization | Application lifespan startup creates the `tasks` table when needed and migrates the earlier non-null SQLite columns without discarding existing rows, so Assignment 1-compatible nullable update values persist. |
| Starter rows | Startup inserts the three Assignment 1 starter tasks only when the `tasks` table has zero rows. |
| Validation and errors | Invalid requests return Assignment 1's `{"error": "Invalid request body"}` with `400`; empty updates return Assignment 1's specific `400` body; missing numeric IDs return Assignment 1's ID-specific `404` body. Create returns `201`; successful delete returns `204`. |
| Partial updates | `PUT /tasks/{id}` supports `title`-only, `done`-only, or both fields and retains omitted fields. |
| SQL safety | Task values and IDs are supplied to SQLite as bound `?` parameters. The partial-update statements are fixed, not dynamically assembled from request input. |
| Persistence and safety tests | The suite includes Assignment 1 compatibility checks, a `/docs` assertion, and a two-process Uvicorn restart test with direct SQLite row inspection and injection-looking input. |

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

## Assumptions and limitations

- Data is persisted in one local SQLite file and survives restarts that reuse
  that file.
- The service targets assignment-scale usage, not a distributed or
  high-concurrency production deployment.
- No managed database, backup policy, authentication layer, or deployment
  validation is included.