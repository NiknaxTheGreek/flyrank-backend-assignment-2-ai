# Verification Record

This record contains only checks executed after the Assignment 1 contract
compatibility update.

## Executed checks

| Command | Observed result |
| --- | --- |
| `uv run pytest flyrank_assignment_2/tests/test_tasks.py -q` | `9 passed` |
| `uv run pytest flyrank_assignment_2/tests/test_persistence_security.py -q` | `2 passed` |
| `uv run pytest -q` | `11 passed` |
| `git diff --check` | Passed with no output |

The task-route and full-suite commands each emitted one non-failing FastAPI
`TestClient` deprecation warning concerning their `httpx` usage.

The task-route checkpoint includes an executed `GET /docs` assertion with a
`200` response.

## Process-level persistence/security verification

The dedicated persistence/security module launched one Uvicorn process, made
API requests, stopped it, and launched a second Uvicorn process using the same
temporary SQLite file. Its passing assertions verified:

- The starter rows appeared on a new database.
- A task created and updated in the first process remained available after the
  second process started.
- A deleted starter task remained absent after restart and returned `404`.
- The restart did not add another set of starter rows.
- A title containing `Robert'); DROP TABLE tasks; --` was stored as literal
  data.
- Direct parameterized SQLite queries confirmed the `tasks` table existed, the
  expected row count and rows were present, the updated task held the literal
  title, and the deleted row was absent.
- An existing non-empty relational `tasks` table was not reseeded.
- Assignment 1 compatibility tests confirmed the missing-task and
  invalid-request JSON error shapes, title-only POST behavior, nullable and
  coercible PUT fields, and zero/negative numeric ID handling.

## What this record does not claim

- No Docker, PostgreSQL, authentication, or Assignment 3 features were added
  or verified.
- No deployment or production checkpoint validation was run or claimed.