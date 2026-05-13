from __future__ import annotations

from fastapi import APIRouter, Query

from ..deps import load_project

router = APIRouter()


@router.get("/")
def get_security(path: str = Query(...)) -> dict[str, object]:
    project = load_project(path)
    return project.security
