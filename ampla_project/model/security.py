from __future__ import annotations

from dataclasses import dataclass


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
