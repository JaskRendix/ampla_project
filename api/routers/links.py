from __future__ import annotations

from fastapi import APIRouter, Query

from ..deps import load_project

router = APIRouter()


@router.get("/")
def get_links(path: str = Query(...)) -> dict[str, dict[str, list[str | None]]]:
    project = load_project(path)
    return {
        item_id: {
            "link_from": [l.target_id for l in item.link_from],
            "link_to": [l.target_id for l in item.link_to],
        }
        for item_id, item in load_project(path).items.items()
    }
