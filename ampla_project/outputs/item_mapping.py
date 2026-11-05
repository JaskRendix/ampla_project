from __future__ import annotations

from ..model.item import Item
from ..model.project import Project


def item_id_fullname_type_rows(project: Project) -> list[dict[str, str]]:
    """Return the source helper's rows in normalized project-tree order."""
    rows = []
    for roots in (project.classes, project.items):
        nested_ids = {child.id for item in roots.values() for child in item.children}
        for item in roots.values():
            if item.id not in nested_ids:
                _append_item_rows(item, rows)
    return rows


def item_id_fullname_type_to_text(project: Project) -> str:
    """Format the mapping as the pipe-delimited text emitted by the source XSLT."""
    rows = item_id_fullname_type_rows(project)
    lines = ["ItemId|Fullname|Type"]
    lines.extend(f"{row['item_id']}|{row['full_name']}|{row['type']}" for row in rows)
    return "\r\n".join(lines)


def _append_item_rows(item: Item, rows: list[dict[str, str]]) -> None:
    rows.append(
        {
            "item_id": item.id,
            "full_name": item.full_name,
            "type": item.type or "",
        }
    )
    for child in item.children:
        _append_item_rows(child, rows)
