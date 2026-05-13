from __future__ import annotations

from fastapi import APIRouter, Query

from ampla_project.model.item import Item

from ..deps import load_project

router = APIRouter()


@router.get("/")
def list_items(path: str = Query(...)) -> dict[str, Item]:
    project = load_project(path)
    return project.items


@router.get("/{item_id}")
def get_item(item_id: str, path: str = Query(...)) -> Item | None:
    project = load_project(path)
    return project.items.get(item_id)
