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
    ancestors = [
        ancestor
        for ancestor in elem.iterancestors(tag="ClassDefinition")
        if ancestor.get("id")
    ]
    if ancestors:
        inherits_prop = Property(
            name="(inherits)", value=None, attributes={}, item_links=[]
        )

        for ancestor in ancestors:
            link = ItemLink(
                target_id=ancestor.get("id"),
                absolute_path=_compute_class_full_name(ancestor),
                property_name="(inherits)",
            )
            inherits_prop.item_links.append(link)

        item.properties["(inherits)"] = inherits_prop

    # Apply inherited definitions from oldest ancestor to this class.
    for definition_owner in [*reversed(ancestors), elem]:
        for prop_def in definition_owner.findall("PropertyDefinition"):
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

    # 1. Resolve the legacy Class property/element reference.
    class_prop = elem.find("Property[@name='Class']")
    class_elem = elem.find("Class")

    class_name = None
    if class_prop is not None and class_prop.text:
        class_name = class_prop.text.strip()
    elif class_elem is not None and class_elem.text:
        class_name = class_elem.text.strip()

    if class_name:
        class_id, full_name = _resolve_class_reference(ctx, class_name)
        item.properties["Class"] = Property(
            name="Class",
            value=class_name,
            attributes={},
            item_links=[
                ItemLink(
                    target_id=class_id,
                    absolute_path=full_name or class_name,
                    property_name="Class",
                    broken_target=class_id is None,
                )
            ],
        )

    # Project.Normalize.xslt emits ItemClassAssociation as a class property.
    associations = elem.findall("ItemClassAssociation[@classDefinitionId]")
    if associations:
        links = []
        for association in associations:
            class_id = association.get("classDefinitionId")
            links.append(
                ItemLink(
                    target_id=class_id,
                    absolute_path=(
                        get_class_full_name_by_id(ctx, class_id) if class_id else None
                    ),
                    property_name="ClassAssociation",
                    broken_target=class_id not in ctx.classes_by_id,
                )
            )
        item.properties["ClassAssociation"] = Property(
            name="ClassAssociation",
            value=None,
            attributes={"class": "true"},
            item_links=links,
        )

    # EquipmentTemplate targets are class references, not ordinary item links.
    if item.type == "Citect.Ampla.General.Server.Templating.EquipmentTemplate":
        target_elem = elem.find("Property[@name='TargetEquipmentClass']")
        if target_elem is not None:
            class_ref = target_elem.get("classDefinitionId") or (
                target_elem.text.strip() if target_elem.text else ""
            )
            class_id, full_name = _resolve_class_reference(ctx, class_ref)
            property_ = item.properties.get("TargetEquipmentClass")
            if property_ is not None:
                property_.attributes["class"] = "true"
                property_.item_links.append(
                    ItemLink(
                        target_id=class_id,
                        absolute_path=full_name or (class_ref or None),
                        property_name="TargetEquipmentClass",
                        broken_target=class_id is None,
                    )
                )


def _resolve_class_reference(
    ctx: NormalizationContext, class_ref: str
) -> tuple[str | None, str | None]:
    if not class_ref:
        return None, None

    class_elem = ctx.classes_by_id.get(class_ref)
    if class_elem is not None:
        return class_ref, _compute_class_full_name(class_elem)

    exact_matches = [
        (class_id, elem)
        for class_id, elem in ctx.classes_by_id.items()
        if class_ref == _compute_class_full_name(elem)
    ]
    if len(exact_matches) == 1:
        class_id, elem = exact_matches[0]
        return class_id, _compute_class_full_name(elem)

    name_matches = [
        (class_id, elem)
        for class_id, elem in ctx.classes_by_id.items()
        if class_ref == elem.get("name")
    ]
    if len(name_matches) == 1:
        class_id, elem = name_matches[0]
        return class_id, _compute_class_full_name(elem)
    return None, None
