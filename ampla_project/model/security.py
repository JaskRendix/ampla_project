from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SecurityOperation:
    id: str
    name: str
    description: str
    operation_id: int | None
    role_links: list["SecurityRoleLink"]


@dataclass
class SecurityRoleLink:
    role_id: str
    name: str
    role_links: list["SecurityRoleLink"]
    operations: list[str]


@dataclass
class SecurityRoleDefinition:
    id: str
    name: str
    description: str
    role_links: list[SecurityRoleLink]
    operations: list[str]


@dataclass
class SecurityMember:
    sid: str
    type: str
    user_id: str | None
    user_name: str
    identity_account: str | None
    resolved_by: str | None


@dataclass
class SecurityRole:
    role_id: str
    name: str
    description: str
    members: list[SecurityMember]


@dataclass
class Identity:
    """
    Represents a parsed identity string:
        account | sid | <NULL>
    Mirrors the XSLT identity parsing logic.
    """

    account: str | None
    sid: str | None
    raw: str


@dataclass
class SecurityUser:
    """
    Represents a normalized security user.
    Mirrors the normalized <User> output of Project.Security.xslt.
    """

    id: str
    name: str
    full_name: str

    display_order: int
    authentication: str | None

    identity: Identity
    security_id: str | None


@dataclass
class SecurityScope:
    """
    Represents a security scope.
    Includes:
      - Global scope
      - Items with InheritPermissions = False
    """

    id: str
    name: str
    full_name: str
    valid: str | None = None
    invalid: str | None = None
    roles: list[SecurityRole] | None = None
