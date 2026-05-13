from __future__ import annotations

from fastapi import APIRouter, Query

from ..deps import load_project

router = APIRouter()


@router.get("/")
def get_flow_graph(path: str = Query(...)) -> dict[str, list[str]]:
    project = load_project(path)
    return project.flow_graph
