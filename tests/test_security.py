from pathlib import Path

from lxml.etree import parse

from ampla_project.model.item import Item, Property
from ampla_project.normalize import normalize
from ampla_project.normalize.security import (
    _extract_scopes,
    _extract_users,
    _parse_identity,
    normalize_security,
)
from ampla_project.outputs.json import project_to_json


def _load_fixture(name: str):
    return parse(Path("tests/data/parity") / name).getroot()


def test_identity_parsing():
    idn = _parse_identity("APAC\\user|S-1-5-21-123|<NULL>")
    assert idn.account == "APAC\\user"
    assert idn.sid == "S-1-5-21-123"


def test_identity_parsing_handles_null_account_and_sid():
    idn = _parse_identity("<NULL>|<NULL>")

    assert idn.account is None
    assert idn.sid is None
    assert idn.raw == "<NULL>|<NULL>"


def test_identity_parsing_handles_missing_fields():
    idn = _parse_identity("OnlyAccount")

    assert idn.account == "OnlyAccount"
    assert idn.sid is None


def test_extract_users_skips_non_user_item_types():
    items = {
        "A": Item(
            id="A",
            name="A",
            type="Test",
            full_name="A",
            hash="h1",
            definition=None,
            translation=None,
            properties={
                "DisplayOrder": Property(
                    name="DisplayOrder", value="1", attributes={}, item_links=[]
                ),
                "Authentication": Property(
                    name="Authentication", value="Local", attributes={}, item_links=[]
                ),
            },
        )
    }

    users = _extract_users(items)
    assert users == {}


def test_extract_users_builds_security_user_for_user_item():
    items = {
        "User1": Item(
            id="User1",
            name="User1",
            type="Citect.Ampla.StandardItems.User",
            full_name="User1",
            hash="h1",
            definition=None,
            translation=None,
            properties={
                "DisplayOrder": Property(
                    name="DisplayOrder", value="5", attributes={}, item_links=[]
                ),
                "Authentication": Property(
                    name="Authentication", value="Local", attributes={}, item_links=[]
                ),
                "Identity": Property(
                    name="Identity",
                    value="APAC\\user|S-1-5-21-123|<NULL>",
                    attributes={},
                    item_links=[],
                ),
                "SecurityID": Property(
                    name="SecurityID", value="SEC123", attributes={}, item_links=[]
                ),
            },
        )
    }

    users = _extract_users(items)
    assert "User1" in users
    user = users["User1"]
    assert user.display_order == 5
    assert user.authentication == "Local"
    assert user.identity.account == "APAC\\user"
    assert user.security_id == "SEC123"


def test_extract_scopes_includes_explicit_inherit_permissions_false():
    items = {
        "A": Item(
            id="A",
            name="A",
            type="Test",
            full_name="A",
            hash="h1",
            definition=None,
            translation=None,
            properties={
                "InheritPermissions": Property(
                    name="InheritPermissions",
                    value="False",
                    attributes={},
                    item_links=[],
                ),
            },
        )
    }

    scopes = _extract_scopes(items)

    assert "00000000-0000-0000-0000-000000000000" in scopes
    assert "A" in scopes
    assert scopes["A"].full_name == "A"


def test_normalize_security_includes_global_scope_and_user_entries():
    items = {
        "User1": Item(
            id="User1",
            name="User1",
            type="Citect.Ampla.StandardItems.User",
            full_name="User1",
            hash="h1",
            definition=None,
            translation=None,
            properties={
                "DisplayOrder": Property(
                    name="DisplayOrder", value="2", attributes={}, item_links=[]
                ),
                "Authentication": Property(
                    name="Authentication", value="Local", attributes={}, item_links=[]
                ),
                "Identity": Property(
                    name="Identity",
                    value="APAC\\user|S-1-5-21-123|<NULL>",
                    attributes={},
                    item_links=[],
                ),
            },
        )
    }

    security = normalize_security(None, items)
    assert "User1" in security["users"]
    assert "00000000-0000-0000-0000-000000000000" in security["scopes"]


def test_authstore_merges_roles_operations_scope_assignments_and_members():
    project = normalize(
        _load_fixture("authstore_project.xml"),
        authstore_doc=_load_fixture("authstore.xml"),
    )
    security = project.security

    assert security["authstore_name"] == "Ampla Security"
    assert list(security["operations"]) == ["op-read", "op-write"]
    assert [operation.name for operation in security["operations"].values()] == [
        "Read",
        "Write",
    ]
    assert security["role_definitions"]["role-editor"].role_links[0].role_id == (
        "role-base"
    )
    assert security["role_definitions"]["role-editor"].operations == ["Write"]
    assert security["operations"]["op-read"].role_links[0].role_id == "role-base"
    assert (
        security["operations"]["op-read"].role_links[0].role_links[0].role_id
        == "role-editor"
    )

    global_scope = security["scopes"]["00000000-0000-0000-0000-000000000000"]
    assert global_scope.valid == "Default scope"
    members = global_scope.roles[0].members
    assert [member.sid for member in members] == [
        "S-1-5-21-111-222-333-1001",
        "S-1-5-32-544",
        "S-1-5-99-unknown",
        "S-1-9-2002",
    ]
    assert members[0].user_id == "alice"
    assert members[0].resolved_by == "identity"
    assert members[1].identity_account == r".\Administrators"
    assert members[1].resolved_by == "well_known_sid"
    assert members[2].user_name == "S-1-5-99-unknown"
    assert members[2].resolved_by is None
    assert members[3].user_id == "bob"
    assert members[3].resolved_by == "security_id"

    assert security["scopes"]["scope-one"].valid == "Scope is Valid"
    assert security["scopes"]["scope-one"].roles[0].role_id == "role-base"
    assert security["scopes"]["scope-extra"].invalid == (
        "Warning: Scope does not exist in Ampla Project."
    )
    assert security["scopes"]["scope-missing"].invalid == (
        "Warning: Scope does not exist in Authorization Store (AuthStore.xml)"
    )


def test_authstore_json_serialization_is_additive_and_complete():
    project = normalize(
        _load_fixture("authstore_project.xml"),
        authstore_doc=_load_fixture("authstore.xml"),
    )
    security = project_to_json(project)["security"]

    assert set(security) == {
        "authstore_name",
        "operations",
        "role_definitions",
        "scopes",
        "users",
    }
    assert security["operations"]["op-write"]["operation_id"] == 2
    assert security["role_definitions"]["role-editor"]["role_links"][0] == {
        "role_id": "role-base",
        "name": "Base",
        "role_links": [],
        "operations": ["Read"],
    }
    assert security["scopes"]["scope-one"]["roles"][0]["members"][0] == {
        "sid": "S-1-5-21-111-222-333-1001",
        "type": "windows",
        "user_id": "alice",
        "user_name": "Alice",
        "identity_account": r"DOMAIN\alice",
        "resolved_by": "identity",
    }


def test_normalization_without_authstore_keeps_security_json_shape():
    project = normalize(_load_fixture("authstore_project.xml"))
    security = project_to_json(project)["security"]

    assert set(security) == {"scopes", "users"}
    assert set(security["scopes"]["scope-one"]) == {"id", "name", "full_name"}
