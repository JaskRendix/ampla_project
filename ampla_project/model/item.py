from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ItemLink:
    """
    Represents a reference from one item to another.
    Mirrors the normalized XML <ItemLink>.
    """

    target_id: str | None  # resolved ID (if known)
    absolute_path: str | None  # fullName (if known)
    property_name: str | None = None

    # Broken link flags (equivalent to XSLT broken-* attributes)
    broken_target: bool = False
    broken_absolute: bool = False
    broken_relative: bool = False

    # Optional subscription fields
    event: str | None = None
    handler: str | None = None
    expression_match: str | None = None

    # Optional relative path (before resolution)
    relative_path: str | None = None


@dataclass
class Property:
    """
    Represents a normalized property of an Item.
    Mirrors the normalized XML <Property>.
    """

    name: str
    value: str | None
    attributes: dict[str, str]
    item_links: list[ItemLink] = field(default_factory=list)

    # Optional raw XML for special cases (SOAP, ExpressionConfig, etc.)
    extra_xml: object | None = None


@dataclass
class Item:
    """
    Represents a fully normalized Item.
    Mirrors the normalized XML <Item>.
    """

    id: str
    name: str
    type: str
    full_name: str
    hash: str

    definition: str | None
    translation: str | None

    is_class: bool = False

    properties: dict[str, Property] = field(default_factory=dict)
    children: list["Item"] = field(default_factory=list)

    # Flow + link graph
    link_from: list[ItemLink] = field(default_factory=list)  # forward references
    link_to: list[ItemLink] = field(default_factory=list)  # reverse references

    def get_property(self, name: str) -> Property | None:
        return self.properties.get(name)

    def add_property(self, prop: Property) -> None:
        self.properties[prop.name] = prop

    def add_child(self, child: "Item") -> None:
        self.children.append(child)
