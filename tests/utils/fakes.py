from __future__ import annotations


class FakeItemLink:
    """
    Minimal stand‑in for ItemLink.
    Only the fields needed by flow, link resolution, or property tests.
    """

    def __init__(
        self,
        target_id=None,
        absolute_path=None,
        property_name=None,
        broken_target=False,
        broken_absolute=False,
        broken_relative=False,
        relative_path=None,
    ):
        self.target_id = target_id
        self.absolute_path = absolute_path
        self.property_name = property_name
        self.broken_target = broken_target
        self.broken_absolute = broken_absolute
        self.broken_relative = broken_relative
        self.relative_path = relative_path


class FakeProperty:
    """
    Minimal stand‑in for Property.
    """

    def __init__(self, name, value=None, item_links=None, attributes=None):
        self.name = name
        self.value = value
        self.item_links = item_links or []
        self.attributes = attributes or {}
        self.extra_xml = None


class FakeItem:
    """
    Minimal stand‑in for Item.
    Used for flow tests, link tests, and isolated property tests.
    """

    def __init__(
        self,
        item_id: str,
        name: str | None = None,
        type_: str = "Test",
        links_from=None,
        properties=None,
    ):
        self.id = item_id
        self.name = name or item_id
        self.type = type_
        self.full_name = self.name

        # Flow graph uses link_from
        self.link_from = []
        if links_from:
            for target in links_from:
                self.link_from.append(FakeItemLink(target_id=target))

        # Reverse links (not needed in most tests)
        self.link_to = []

        # Properties
        self.properties = properties or {}

        # Children (not needed in most tests)
        self.children = []


class FakeContext:
    """
    Minimal stand‑in for NormalizationContext.
    Only includes fields used by tests.
    """

    def __init__(self, items_by_id=None, classes_by_id=None):
        self.items_by_id = items_by_id or {}
        self.classes_by_id = classes_by_id or {}

    # Used by class tests
    def generate_hash(self, value: str) -> str:
        return f"hash:{value}"

    # Used by item/class tests
    def get_translation(self, name: str) -> str | None:
        return None
