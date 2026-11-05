from __future__ import annotations

from fastapi import APIRouter, Query

from ampla_project.outputs.json import project_to_json

from ..deps import load_project

router = APIRouter()


@router.get("/")
def get_security(
    path: str = Query(...),
    authstore_path: str | None = Query(
        None, description="Optional path to the Ampla authorization store XML"
    ),
) -> dict[str, object]:
    project = load_project(path, authstore_path)
    return project_to_json(project)["security"]
