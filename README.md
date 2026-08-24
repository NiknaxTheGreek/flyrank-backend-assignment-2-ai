# FlyRank Backend Assignment 2 — Connect CRUD to Database

This repository is the AI-generated Assignment 2 implementation. It keeps the Assignment 1 task API contract unchanged while replacing in-memory storage with SQLite persistence.

## Run from a clean clone

Requires Python 3.13+.

```bash
python -m venv .venv
python -m pip install .
python -m uvicorn app.main:app --app-dir flyrank_assignment_2 --host 127.0.0.1 --port 8000
```

Swagger UI: `http://localhost:8000/docs`

By default the database file is `flyrank_assignment_2/data/tasks.sqlite3`. Override it with `TASK_DATABASE_PATH=/path/to/tasks.sqlite3`.

## Assignment contract

The external API remains the same as Assignment 1:

| Method | Route | Success | Failure |
|---|---|---:|---|
| GET | `/` | 200 | — |
| GET | `/health` | 200 | — |
| GET | `/tasks` | 200 | — |
| GET | `/tasks/{id}` | 200 | 404 |
| POST | `/tasks` | 201 | 400 |
| PUT | `/tasks/{id}` | 200 | 400 / 404 |
| DELETE | `/tasks/{id}` | 204 | 404 |

The storage implementation is SQLite. The `tasks` table is created automatically. Exactly three starter tasks are inserted only when the table is empty. All dynamic SQL values are parameterized.

## Persistence and database evidence

The final acceptance workflow verifies the following against a fresh SQLite file:

1. startup creates the table and exactly three starter rows;
2. an API-created task is updated;
3. the server is stopped and restarted against the same database file;
4. the updated row still exists after restart;
5. startup does not duplicate the three starter rows;
6. a direct SQLite query reads the same persisted data;
7. DB Browser for SQLite is opened against the verification database and a screenshot is captured as evidence.

Executed evidence is stored under `docs/` after the evidence workflow completes:

- `docs/sql-query.txt` — actual SQL query and returned rows;
- `docs/db-browser.png` — DB Browser for SQLite screenshot;
- `docs/persistence-check.txt` — restart/persistence checkpoint.

The detailed implementation notes and earlier verification record remain in [`flyrank_assignment_2/README.md`](flyrank_assignment_2/README.md) and [`flyrank_assignment_2/VERIFICATION.md`](flyrank_assignment_2/VERIFICATION.md).

## Tests

```bash
python -m pytest -q
```

The suite covers CRUD compatibility, validation, seed-on-empty behavior, parameterized-query safety, persistence across separate Uvicorn processes, deletion persistence, and non-duplicate seeding.

## Scope

This assignment deliberately uses SQLite. Docker/PostgreSQL containerization belongs to Assignment 3 and is not claimed here.
