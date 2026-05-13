from __future__ import annotations

from fastapi import APIRouter, Query

from ampla_project.model.item import Item

from ..deps import load_project

router = APIRouter()


@router.get("/")
def list_classes(path: str = Query(...)) -> dict[str, Item]:
    project = load_project(path)
    return project.classes


@router.get("/{class_id}")
def get_class(class_id: str, path: str = Query(...)) -> Item | None:
    project = load_project(path)
    return project.classes.get(class_id)
