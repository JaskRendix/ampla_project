from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ampla_project.outputs.json import project_to_json

from ..deps import load_project

router = APIRouter()


@router.get("/")
def get_project(
    path: str = Query(..., description="Path to Ampla project XML")
) -> dict[str, Any]:
    project = load_project(path)
    return project_to_json(project)
