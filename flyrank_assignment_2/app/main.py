"""FastAPI entry point for the SQLite-backed Task API."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, field_validator

from .database import TaskRepository


DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "tasks.sqlite3"
)


class Task(BaseModel):
    id: int
    title: str | None
    done: bool | None


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str

    @field_validator("title")
    @classmethod
    def title_cannot_be_blank(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title must not be blank")
        return title


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    done: bool | None = None

    @field_validator("title")
    @classmethod
    def title_cannot_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        if not title:
            raise ValueError("title must not be blank")
        return title

def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Create an independently configurable application instance."""
    repository = TaskRepository(
        database_path
        or os.environ.get("TASK_DATABASE_PATH")
        or DEFAULT_DATABASE_PATH
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        repository.initialize()
        yield

    app = FastAPI(
        title="FlyRank Backend Assignment 2",
        version="1.0.0",
        description="SQLite-backed persistence for the Assignment 1 task CRUD API.",
        lifespan=lifespan,
    )
    app.state.repository = repository

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Keep Assignment 1's client-facing validation response unchanged.
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({"error": "Invalid request body"}),
        )

    def get_repository(request: Request) -> TaskRepository:
        return request.app.state.repository

    @app.get("/", status_code=status.HTTP_200_OK)
    def api_information() -> dict[str, str]:
        return {
            "message": "FlyRank Task API is running.",
            "tasks": "/tasks",
            "docs": "/docs",
        }

    @app.get("/tasks", response_model=list[Task], status_code=status.HTTP_200_OK)
    def list_tasks(request: Request) -> list[dict[str, object]]:
        return get_repository(request).list_tasks()

    @app.get("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
    def get_task(
        request: Request,
        task_id: int,
    ) -> dict[str, object]:
        task = get_repository(request).get_task(task_id)
        if task is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )
        return task

    @app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
    def create_task(payload: TaskCreate, request: Request) -> dict[str, object]:
        return get_repository(request).create_task(payload.title, False)

    @app.put("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
    def update_task(
        payload: TaskUpdate,
        request: Request,
        task_id: int,
    ) -> dict[str, object]:
        repository = get_repository(request)
        if repository.get_task(task_id) is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )

        supplied = payload.model_fields_set
        if not supplied or supplied.isdisjoint({"title", "done"}):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Request body must include title and/or done"},
            )

        task = repository.update_task(
            task_id,
            title=payload.title,
            done=payload.done,
            fields=supplied,
        )
        if task is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )
        return task

    @app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(
        request: Request,
        task_id: int,
    ) -> Response:
        deleted = get_repository(request).delete_task(task_id)
        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Task {task_id} not found"},
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()