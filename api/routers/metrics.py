from __future__ import annotations

from fastapi import APIRouter, Query

from ampla_project.model.project import ProjectMetrics

from ..deps import load_project

router = APIRouter()


@router.get("/")
def get_metrics(path: str = Query(...)) -> ProjectMetrics:
    project = load_project(path)
    return project.metrics
