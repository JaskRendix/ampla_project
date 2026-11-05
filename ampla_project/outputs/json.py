from __future__ import annotations

from typing import Any

from ..model.item import Item, ItemLink, Property
from ..model.project import Project
from ..model.security import (
    SecurityMember,
    SecurityOperation,
    SecurityRole,
    SecurityRoleDefinition,
    SecurityRoleLink,
    SecurityScope,
    SecurityUser,
)


def project_to_json(project: Project) -> dict[str, Any]:
    """
    Convert a fully normalized Project into a JSON‑serializable dict.
    This is the canonical output used for golden‑master tests.
    """

    security = {
        "users": {
            uid: _user_to_dict(user) for uid, user in project.security["users"].items()
        },
        "scopes": {
            sid: _scope_to_dict(scope)
            for sid, scope in project.security["scopes"].items()
        },
    }
    if "authstore_name" in project.security:
        security["authstore_name"] = project.security["authstore_name"]
        security["operations"] = {
            operation_id: _operation_to_dict(operation)
            for operation_id, operation in project.security["operations"].items()
        }
        security["role_definitions"] = {
            role_id: _role_definition_to_dict(role)
            for role_id, role in project.security["role_definitions"].items()
        }

    return {
        "items": {
            item_id: _item_to_dict(item) for item_id, item in project.items.items()
        },
        "classes": {
            cls_id: _item_to_dict(cls) for cls_id, cls in project.classes.items()
        },
        "flow_graph": project.flow_graph,
        "security": security,
        "platform_version": project.platform_version,
        "applications_version": project.applications_version,
        "properties": project.properties,
    }


def _item_to_dict(item: Item) -> dict[str, Any]:
    result = {
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
    if item.decision_matrix_inputs:
        result["decision_matrix_inputs"] = [
            {
                "id": entry.id,
                "name": entry.name,
                "hash": entry.hash,
                "translation": entry.translation,
                "display_order": entry.display_order,
                "item_link": _itemlink_to_dict(entry.item_link),
            }
            for entry in item.decision_matrix_inputs
        ]
    if item.decision_matrix_input_rules:
        result["decision_matrix_input_rules"] = [
            {
                "name": entry.name,
                "display_order": entry.display_order,
                "value": entry.value,
                "item_link": _itemlink_to_dict(entry.item_link),
            }
            for entry in item.decision_matrix_input_rules
        ]
    return result


def _property_to_dict(prop: Property) -> dict[str, Any]:
    return {
        "name": prop.name,
        "value": prop.value,
        "attributes": prop.attributes,
        "item_links": [_itemlink_to_dict(l) for l in prop.item_links],
        "extra_xml": prop.extra_xml,
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
    result: dict[str, Any] = {
        "id": scope.id,
        "name": scope.name,
        "full_name": scope.full_name,
    }
    if scope.valid is not None:
        result["valid"] = scope.valid
    if scope.invalid is not None:
        result["invalid"] = scope.invalid
    if scope.roles is not None:
        result["roles"] = [_role_to_dict(role) for role in scope.roles]
    return result


def _operation_to_dict(operation: SecurityOperation) -> dict[str, Any]:
    return {
        "id": operation.id,
        "name": operation.name,
        "description": operation.description,
        "operation_id": operation.operation_id,
        "role_links": [_role_link_to_dict(link) for link in operation.role_links],
    }


def _role_definition_to_dict(role: SecurityRoleDefinition) -> dict[str, Any]:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "role_links": [_role_link_to_dict(link) for link in role.role_links],
        "operations": role.operations,
    }


def _role_link_to_dict(role_link: SecurityRoleLink) -> dict[str, Any]:
    return {
        "role_id": role_link.role_id,
        "name": role_link.name,
        "role_links": [_role_link_to_dict(link) for link in role_link.role_links],
        "operations": role_link.operations,
    }


def _role_to_dict(role: SecurityRole) -> dict[str, Any]:
    return {
        "role_id": role.role_id,
        "name": role.name,
        "description": role.description,
        "members": [_member_to_dict(member) for member in role.members],
    }


def _member_to_dict(member: SecurityMember) -> dict[str, Any]:
    return {
        "sid": member.sid,
        "type": member.type,
        "user_id": member.user_id,
        "user_name": member.user_name,
        "identity_account": member.identity_account,
        "resolved_by": member.resolved_by,
    }
