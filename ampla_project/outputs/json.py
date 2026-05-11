from __future__ import annotations

from typing import Any

from ..model.item import Item, ItemLink, Property
from ..model.project import Project
from ..model.security import SecurityScope, SecurityUser


def project_to_json(project: Project) -> dict[str, Any]:
    """
    Convert a fully normalized Project into a JSON‑serializable dict.
    This is the canonical output used for golden‑master tests.
    """

    return {
        "items": {
            item_id: _item_to_dict(item) for item_id, item in project.items.items()
        },
        "classes": {
            cls_id: _item_to_dict(cls) for cls_id, cls in project.classes.items()
        },
        "flow_graph": project.flow_graph,
        "security": {
            "users": {
                uid: _user_to_dict(u) for uid, u in project.security["users"].items()
            },
            "scopes": {
                sid: _scope_to_dict(s) for sid, s in project.security["scopes"].items()
            },
        },
        "platform_version": project.platform_version,
        "applications_version": project.applications_version,
        "properties": project.properties,
    }


def _item_to_dict(item: Item) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "type": item.type,
        "full_name": item.full_name,
        "hash": item.hash,
        "definition": item.definition,
        "translation": item.translation,
        "is_class": item.is_class,
        "properties": {
            name: _property_to_dict(p) for name, p in item.properties.items()
        },
        "children": [child.id for child in item.children],
        "link_from": [_itemlink_to_dict(l) for l in item.link_from],
        "link_to": [_itemlink_to_dict(l) for l in item.link_to],
    }


def _property_to_dict(prop: Property) -> dict[str, Any]:
    return {
        "name": prop.name,
        "value": prop.value,
        "attributes": prop.attributes,
        "item_links": [_itemlink_to_dict(l) for l in prop.item_links],
        "extra_xml": None,  # not serialized (non‑deterministic)
    }


def _itemlink_to_dict(link: ItemLink) -> dict[str, Any]:
    return {
        "target_id": link.target_id,
        "absolute_path": link.absolute_path,
        "property_name": link.property_name,
        "broken_target": link.broken_target,
        "broken_absolute": link.broken_absolute,
        "broken_relative": link.broken_relative,
        "event": link.event,
        "handler": link.handler,
        "expression_match": link.expression_match,
        "relative_path": link.relative_path,
    }


def _user_to_dict(user: SecurityUser) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "full_name": user.full_name,
        "display_order": user.display_order,
        "authentication": user.authentication,
        "identity": {
            "account": user.identity.account,
            "sid": user.identity.sid,
            "raw": user.identity.raw,
        },
        "security_id": user.security_id,
    }


def _scope_to_dict(scope: SecurityScope) -> dict[str, Any]:
    return {
        "id": scope.id,
        "name": scope.name,
        "full_name": scope.full_name,
    }
