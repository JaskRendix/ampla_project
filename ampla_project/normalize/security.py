from __future__ import annotations

from lxml.etree import Element

from ..model.item import Item
from ..model.security import (
    Identity,
    SecurityMember,
    SecurityOperation,
    SecurityRole,
    SecurityRoleDefinition,
    SecurityRoleLink,
    SecurityScope,
    SecurityUser,
)
from .context import NormalizationContext


def normalize_security(
    ctx: NormalizationContext,
    items: dict[str, Item],
    authstore_doc: Element | None = None,
) -> dict[str, object]:
    """
    Build the security model:
    - Users
    - Scopes
    - Identity parsing
    - SecurityID extraction
    - InheritPermissions logic
    Mirrors Project.Security.xslt.
    """
    users = _extract_users(items)
    scopes = _extract_scopes(items)

    security: dict[str, object] = {
        "users": users,
        "scopes": scopes,
    }
    if authstore_doc is not None:
        security.update(_merge_authstore(users, scopes, authstore_doc))
    return security


def _extract_users(items: dict[str, Item]) -> dict[str, SecurityUser]:
    """
    Extract all users:
        Item[@type='Citect.Ampla.StandardItems.User']
    """
    users: dict[str, SecurityUser] = {}

    for item in items.values():
        if item.type != "Citect.Ampla.StandardItems.User":
            continue

        identity_prop = item.properties.get("Identity")
        display_order_prop = item.properties.get("DisplayOrder")
        auth_prop = item.properties.get("Authentication")
        security_id_prop = item.properties.get("SecurityID")

        identity = _parse_identity(identity_prop.value if identity_prop else "")

        users[item.id] = SecurityUser(
            id=item.id,
            name=item.name,
            full_name=item.full_name,
            display_order=int(
                (display_order_prop.value if display_order_prop else 0) or 0
            ),
            authentication=auth_prop.value if auth_prop else None,
            identity=identity,
            security_id=security_id_prop.value if security_id_prop else None,
        )

    return users


def _extract_scopes(items: dict[str, Item]) -> dict[str, SecurityScope]:
    """
    Extract scopes:
    - Global scope
    - Items where InheritPermissions = False
    """
    scopes: dict[str, SecurityScope] = {}

    # Global scope
    scopes["00000000-0000-0000-0000-000000000000"] = SecurityScope(
        id="00000000-0000-0000-0000-000000000000",
        name="{Global}",
        full_name="{Global}",
    )

    # Explicit scopes
    for item in items.values():
        inherit = item.properties.get("InheritPermissions")
        if inherit and inherit.value == "False":
            scopes[item.id] = SecurityScope(
                id=item.id,
                name=item.name,
                full_name=item.full_name,
            )

    return scopes


def _merge_authstore(
    users: dict[str, SecurityUser],
    project_scopes: dict[str, SecurityScope],
    authstore_doc: Element,
) -> dict[str, object]:
    application = _first(authstore_doc, "AzApplication")
    if application is None:
        raise ValueError("AuthStore document is missing AzApplication")

    operations: dict[str, SecurityOperation] = {}
    operation_elements = sorted(
        _children(application, "AzOperation"),
        key=lambda operation: _operation_sort_key(
            _first_text(operation, "OperationID")
        ),
    )
    for operation in operation_elements:
        operation_id = operation.get("Guid")
        if not operation_id:
            continue
        order_text = _first_text(operation, "OperationID")
        try:
            numeric_order = int(order_text) if order_text else None
        except ValueError:
            numeric_order = None
        operations[operation_id] = SecurityOperation(
            id=operation_id,
            name=operation.get("Name") or "",
            description=operation.get("Description") or "",
            operation_id=numeric_order,
            role_links=[],
        )

    task_elements = _descendants(application, "AzTask")
    tasks_by_id = {task.get("Guid"): task for task in task_elements if task.get("Guid")}
    role_definition_elements = [
        task for task in task_elements if task.get("RoleDefinition") == "True"
    ]
    role_definitions: dict[str, SecurityRoleDefinition] = {}
    for task in role_definition_elements:
        role_id = task.get("Guid")
        if not role_id:
            continue
        role_links = [
            _direct_role_link(tasks_by_id.get(link.text or ""), operations)
            for link in _children(task, "TaskLink")
        ]
        role_links = [link for link in role_links if link is not None]
        role_definitions[role_id] = SecurityRoleDefinition(
            id=role_id,
            name=task.get("Name") or "",
            description=task.get("Description") or "",
            role_links=role_links,
            operations=_operation_names(task, operations),
        )

    for operation_id, operation in operations.items():
        role_ids = {
            task.get("Guid")
            for task in role_definition_elements
            if any(
                (link.text or "") == operation_id
                for link in _children(task, "OperationLink")
            )
        }
        operation.role_links = [
            link
            for role_id in sorted(role_ids)
            if (
                link := _operation_role_link(
                    tasks_by_id.get(role_id), role_definition_elements, frozenset()
                )
            )
            is not None
        ]

    authstore_scopes: dict[str, SecurityScope] = {}
    global_scope = SecurityScope(
        id="00000000-0000-0000-0000-000000000000",
        name="{Global}",
        full_name="{Global}",
        valid="Default scope",
        roles=_scope_roles(_children(application, "AzRole"), tasks_by_id, users),
    )
    authstore_scopes[global_scope.id] = global_scope

    for scope_elem in _children(application, "AzScope"):
        scope_id = scope_elem.get("Name")
        if not scope_id:
            continue
        description = scope_elem.get("Description") or ""
        prefix = "Security scope for "
        name = description.split(prefix, 1)[1] if prefix in description else description
        matching_project_scope = project_scopes.get(scope_id)
        authstore_scopes[scope_id] = SecurityScope(
            id=scope_id,
            name=name,
            full_name=(
                matching_project_scope.full_name if matching_project_scope else name
            ),
            valid="Scope is Valid" if matching_project_scope else None,
            invalid=(
                None
                if matching_project_scope
                else "Warning: Scope does not exist in Ampla Project."
            ),
            roles=_scope_roles(_children(scope_elem, "AzRole"), tasks_by_id, users),
        )

    for project_scope_id, project_scope in project_scopes.items():
        if project_scope_id not in authstore_scopes:
            authstore_scopes[project_scope_id] = SecurityScope(
                id=project_scope.id,
                name=project_scope.name,
                full_name=project_scope.full_name,
                invalid=(
                    "Warning: Scope does not exist in Authorization Store "
                    "(AuthStore.xml)"
                ),
                roles=[],
            )

    return {
        "authstore_name": application.get("Name") or "",
        "operations": operations,
        "role_definitions": role_definitions,
        "scopes": authstore_scopes,
    }


def _scope_roles(
    role_elements: list[Element],
    tasks_by_id: dict[str, Element],
    users: dict[str, SecurityUser],
) -> list[SecurityRole]:
    roles: list[SecurityRole] = []
    for role_elem in role_elements:
        task_links = _children(role_elem, "TaskLink")
        role_task = tasks_by_id.get(task_links[0].text or "") if task_links else None
        if role_task is None:
            continue
        role_id = role_task.get("Guid") or ""
        roles.append(
            SecurityRole(
                role_id=role_id,
                name=role_task.get("Name") or "",
                description=role_elem.get("Description") or "",
                members=sorted(
                    (
                        _resolve_member(member.text or "", users)
                        for member in _children(role_elem, "Member")
                    ),
                    key=lambda member: member.sid,
                ),
            )
        )
    return roles


def _resolve_member(sid: str, users: dict[str, SecurityUser]) -> SecurityMember:
    for user in users.values():
        if user.identity.sid == sid:
            return SecurityMember(
                sid=sid,
                type=_member_type(sid),
                user_id=user.id,
                user_name=user.name,
                identity_account=user.identity.account,
                resolved_by="identity",
            )

    for user in users.values():
        if user.security_id == sid:
            return SecurityMember(
                sid=sid,
                type=_member_type(sid),
                user_id=user.id,
                user_name=user.name,
                identity_account=None,
                resolved_by="security_id",
            )

    account = _well_known_account(sid)
    return SecurityMember(
        sid=sid,
        type=_member_type(sid),
        user_id=None,
        user_name=sid,
        identity_account=account,
        resolved_by="well_known_sid" if account else None,
    )


def _member_type(sid: str) -> str:
    if "S-1-5-" in sid:
        return "windows"
    if "S-1-9-" in sid:
        return "ampla"
    return "unknown"


def _well_known_account(sid: str) -> str | None:
    well_known = {
        "S-1-5-32-544": r".\Administrators",
        "S-1-5-32-545": r".\Users",
        "S-1-5-32-546": r".\Guests",
        "S-1-5-32-547": r".\Power Users",
        "S-1-5-11": "Authenticated Users",
    }
    if sid in well_known:
        return well_known[sid]

    parts = sid.split("-")
    domain_names = {
        "500": "Administrator",
        "512": "Domain Administrators",
        "513": "Domain Users",
    }
    if len(parts) >= 5 and sid.startswith("S-1-5-21-"):
        account_name = domain_names.get(parts[-1])
        if account_name:
            domain = "-".join(parts[:-1])
            return f"({domain})/{account_name}"
    return None


def _direct_role_link(
    task: Element | None, operations: dict[str, SecurityOperation]
) -> SecurityRoleLink | None:
    if task is None:
        return None
    role_id = task.get("Guid")
    if not role_id:
        return None
    return SecurityRoleLink(
        role_id=role_id,
        name=task.get("Name") or "",
        role_links=[],
        operations=_operation_names(task, operations),
    )


def _operation_role_link(
    task: Element | None,
    role_definitions: list[Element],
    visited: frozenset[str],
) -> SecurityRoleLink | None:
    if task is None:
        return None
    role_id = task.get("Guid")
    if not role_id:
        return None
    parents: list[SecurityRoleLink] = []
    if role_id not in visited:
        next_visited = visited | {role_id}
        for parent in role_definitions:
            if any(
                (link.text or "") == role_id for link in _children(parent, "TaskLink")
            ):
                parent_link = _operation_role_link(
                    parent, role_definitions, next_visited
                )
                if parent_link is not None:
                    parents.append(parent_link)
    return SecurityRoleLink(
        role_id=role_id,
        name=task.get("Name") or "",
        role_links=parents,
        operations=[],
    )


def _operation_names(
    task: Element, operations: dict[str, SecurityOperation]
) -> list[str]:
    found = []
    for link in _children(task, "OperationLink"):
        operation = operations.get(link.text or "")
        if operation is not None:
            found.append(operation)
    found.sort(
        key=lambda operation: (
            operation.operation_id is None,
            operation.operation_id if operation.operation_id is not None else 0,
            operation.name,
        )
    )
    return [operation.name for operation in found]


def _children(elem: Element, name: str) -> list[Element]:
    return [child for child in elem if _local_name(child) == name]


def _descendants(elem: Element, name: str) -> list[Element]:
    return [descendant for descendant in elem.iter() if _local_name(descendant) == name]


def _first(elem: Element, name: str) -> Element | None:
    return next(
        (descendant for descendant in elem.iter() if _local_name(descendant) == name),
        None,
    )


def _first_text(elem: Element, name: str) -> str:
    child = next((child for child in elem if _local_name(child) == name), None)
    return (child.text or "").strip() if child is not None else ""


def _operation_sort_key(value: str) -> tuple[bool, int, str]:
    try:
        return False, int(value), ""
    except ValueError:
        return True, 0, value


def _local_name(elem: Element) -> str:
    return elem.tag.rsplit("}", 1)[-1] if isinstance(elem.tag, str) else ""


def _parse_identity(value: str) -> Identity:
    """
    Parse identity strings like:
        APAC\\fisha1|S-1-5-21-1379841381-2888069222-2292527902-168445|<NULL>
    Mirrors XSLT:
        substring-before
        substring-after
    """
    if not value:
        return Identity(account=None, sid=None, raw=value)

    parts = value.split("|")
    account = parts[0] if len(parts) > 0 else None
    sid = parts[1] if len(parts) > 1 else None

    if account == "<NULL>":
        account = None
    if sid == "<NULL>":
        sid = None

    return Identity(account=account, sid=sid, raw=value)
