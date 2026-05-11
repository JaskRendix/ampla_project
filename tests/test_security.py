from ampla_project.model.item import Item, Property
from ampla_project.normalize.security import (
    _extract_scopes,
    _extract_users,
    _parse_identity,
    normalize_security,
)


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

    users = _extract_users(None, items)
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

    users = _extract_users(None, items)
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

    scopes = _extract_scopes(None, items)

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
