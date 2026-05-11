from __future__ import annotations

from ..model.item import Item
from ..model.security import Identity, SecurityScope, SecurityUser
from .context import NormalizationContext


def normalize_security(
    ctx: NormalizationContext, items: dict[str, "Item"]
) -> dict[str, SecurityUser]:
    """
    Build the security model:
    - Users
    - Scopes
    - Identity parsing
    - SecurityID extraction
    - InheritPermissions logic
    Mirrors Project.Security.xslt.
    """
    users = _extract_users(ctx, items)
    scopes = _extract_scopes(ctx, items)

    return {
        "users": users,
        "scopes": scopes,
    }


def _extract_users(
    ctx: NormalizationContext, items: dict[str, "Item"]
) -> dict[str, SecurityUser]:
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


def _extract_scopes(
    ctx: NormalizationContext, items: dict[str, "Item"]
) -> dict[str, SecurityScope]:
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
