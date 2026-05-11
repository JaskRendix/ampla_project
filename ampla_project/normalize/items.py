from __future__ import annotations

from lxml.etree import Element

from ..model.item import Item, Property
from .classes import resolve_class_association
from .context import NormalizationContext
from .properties import normalize_property


def normalize_items(ctx: NormalizationContext) -> dict[str, Item]:
    """
    Entry point: normalize all <Item[@id]> elements into Item objects.
    Mirrors the XSLT template: <xsl:template match="Item[@id]">.
    """
    items: dict[str, Item] = {}

    for elem in ctx.root.findall(".//Item[@id]"):
        item = build_item(ctx, elem)
        items[item.id] = item

    return items


def build_item(ctx: NormalizationContext, elem: Element) -> Item:
    """
    Build a normalized Item object from a raw XML <Item>.
    Equivalent to:
        <xsl:template match="Item[@id]">
            <Item>
                <addItemAttributes/>
                <apply Property/>
                <addPropertyDisplayOrder/>
                <apply Item/>
            </Item>
        </xsl:template>
    """

    item_id = elem.get("id")
    name = elem.get("name")
    type_ = elem.get("type")

    full_name = compute_full_name(elem)
    hash_ = ctx.generate_hash(full_name)

    definition = extract_definition(elem)
    translation = ctx.get_translation(name)

    item = Item(
        id=item_id,
        name=name,
        type=type_,
        full_name=full_name,
        hash=hash_,
        definition=definition,
        translation=translation,
        is_class=False,
    )

    # Normalize all <Property> children
    for prop_elem in elem.findall("Property"):
        prop = normalize_property(ctx, elem, prop_elem)
        if prop:
            item.properties[prop.name] = prop

    # Add default DisplayOrder if missing
    if "DisplayOrder" not in item.properties:
        item.properties["DisplayOrder"] = Property(
            name="DisplayOrder",
            value=str(ctx.default_display_order),
            attributes={},
            item_links=[],
        )

    # Normalize class associations
    resolve_class_association(ctx, elem, item)

    # Normalize child items recursively
    for child_elem in elem.findall("Item"):
        child = build_item(ctx, child_elem)
        item.children.append(child)

    return item


def compute_full_name(elem: Element) -> str:
    """
    Equivalent to XSLT getItemFullName:
        ancestor-or-self::Item[@id]/@name joined with '.'
    """
    names = []
    for ancestor in elem.iterancestors(tag="Item"):
        if ancestor.get("id"):
            names.append(ancestor.get("name"))
    names.reverse()
    names.append(elem.get("name"))
    return ".".join(names)


def extract_definition(elem: Element) -> str | None:
    """
    Equivalent to:
        <xsl:variable name="definition" select="Property[@name='Definition']/ItemLink/@absolutePath"/>
    """
    prop = elem.find("Property[@name='Definition']/ItemLink")
    if prop is not None:
        return prop.get("absolutePath")
    return None
