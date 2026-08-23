# Verification Record

This record contains only checks executed during the final Assignment 2 review.

## Executed checks

| Command | Observed result |
| --- | --- |
| `uv run pytest flyrank_assignment_2/tests/test_persistence_security.py -q` | `2 passed` |
| `uv run pytest && uv run python -m compileall -q flyrank_assignment_2` | `13 passed`; Python compilation completed successfully |

The full test run emitted one non-failing FastAPI `TestClient` deprecation
warning concerning its `httpx` usage.

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

## What this record does not claim

- No Docker, PostgreSQL, authentication, or Assignment 3 features were added
  or verified.
- No deployment or checkpoint validation was run.