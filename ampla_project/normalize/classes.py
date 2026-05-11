from __future__ import annotations

from lxml.etree import Element

from ..model.item import Item, ItemLink, Property
from .context import NormalizationContext


def normalize_classes(ctx: NormalizationContext) -> dict[str, Item]:
    """
    Normalize all <ClassDefinition[@id]> elements into Item objects.
    Mirrors the XSLT template:
        <xsl:template match="ClassDefinition[@id]">
    """
    classes: dict[str, Item] = {}

    for elem in ctx.root.findall(".//ClassDefinition[@id]"):
        cls = _build_class_item(ctx, elem)
        classes[cls.id] = cls

    return classes


def _build_class_item(ctx: NormalizationContext, elem: Element) -> Item:
    """
    Convert a <ClassDefinition> into a normalized Item.
    Equivalent to the XSLT logic:
        - hash
        - id, name, type
        - fullName (class full name)
        - translation
        - inherited classes
        - inherited property definitions
    """

    class_id = elem.get("id")
    name = elem.get("name")
    type_ = elem.get("type")

    full_name = _compute_class_full_name(elem)
    hash_ = ctx.generate_hash(full_name)
    translation = ctx.get_translation(name)

    item = Item(
        id=class_id,
        name=name,
        type=type_,
        full_name=full_name,
        hash=hash_,
        definition=None,
        translation=translation,
        is_class=True,
    )

    # 1. Inheritance chain
    ancestors = list(elem.iterancestors(tag="ClassDefinition"))
    if len(ancestors) > 1:
        inherits_prop = Property(
            name="(inherits)", value=None, attributes={}, item_links=[]
        )

        # Skip the first ancestor (self)
        for ancestor in ancestors[1:]:
            link = ItemLink(
                target_id=ancestor.get("id"),
                absolute_path=_compute_class_full_name(ancestor),
                property_name="(inherits)",
            )
            inherits_prop.item_links.append(link)

        item.properties["(inherits)"] = inherits_prop

    # 2. Inherited property definitions
    for prop_def in elem.findall(".//PropertyDefinition"):
        prop = Property(
            name=prop_def.get("name"),
            value=(prop_def.text or "").strip(),
            attributes={k: v for k, v in prop_def.attrib.items()},
            item_links=[],
        )
        item.properties[prop.name] = prop

    # 3. Child class definitions (nested classes)
    for child in elem.findall("ClassDefinition"):
        child_item = _build_class_item(ctx, child)
        item.children.append(child_item)

    return item


def _compute_class_full_name(elem: Element) -> str:
    """
    Equivalent to XSLT getClassFullName:
        ancestor-or-self::ClassDefinition[@id]/@name joined with '.'
    """
    names = []
    for ancestor in elem.iterancestors(tag="ClassDefinition"):
        if ancestor.get("id"):
            names.append(ancestor.get("name"))
    names.reverse()
    names.append(elem.get("name"))
    return ".".join(names)


def get_class_full_name_by_id(ctx: NormalizationContext, class_id: str) -> str | None:
    """
    Equivalent to XSLT getClassFullNameById.
    """
    elem = ctx.classes_by_id.get(class_id)
    if elem is None:
        return None
    return _compute_class_full_name(elem)


def resolve_class_association(
    ctx: NormalizationContext, elem: Element, item: Item
) -> None:
    """
    Resolve <Property name="Class"> or <Class> elements on an Item.
    Equivalent to XSLT logic that links Items to ClassDefinitions.
    """

    # 1. Find class reference
    class_prop = elem.find("Property[@name='Class']")
    class_elem = elem.find("Class")

    class_name = None
    if class_prop is not None and class_prop.text:
        class_name = class_prop.text.strip()
    elif class_elem is not None and class_elem.text:
        class_name = class_elem.text.strip()

    if not class_name:
        return

    # 2. Resolve class fullName → class ID
    class_id = None
    for cid, class_def in ctx.classes_by_id.items():
        if class_name == class_def.get(
            "name"
        ) or class_name == _compute_class_full_name(class_def):
            class_id = cid
            break

    # 3. Build ItemLink
    link = ItemLink(
        target_id=class_id,
        absolute_path=class_name,
        property_name="Class",
        broken_target=(class_id is None),
    )

    # 4. Add to item properties
    item.properties["Class"] = Property(
        name="Class", value=class_name, attributes={}, item_links=[link]
    )
