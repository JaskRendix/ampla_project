from __future__ import annotations

from lxml.etree import Element

from ..model.item import ItemLink, Property
from .context import NormalizationContext
from .expressions import normalize_expression_config


def normalize_property(
    ctx: NormalizationContext, item_elem: Element, prop_elem: Element
) -> Property | None:
    """
    Normalize a <Property> element.
    Mirrors dozens of XSLT templates that match specific property names or patterns.
    """

    name = prop_elem.get("name")
    value = (prop_elem.text or "").strip()
    attrs = {k: v for k, v in prop_elem.attrib.items() if k != "name"}

    # 1. SOAP normalization
    if (
        prop_elem.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        is not None
    ):
        return _normalize_soap_property(prop_elem)

    # 2. CSV → ItemLink (EquipmentTypes, ParameterGroups)
    if name in ("EquipmentTypes", "ParameterGroups"):
        return _normalize_csv_property(name, value, attrs)

    # 3. Subscription parsing
    if "Subscription" in name:
        return _normalize_subscription_property(ctx, prop_elem, name, attrs)

    # 4. Favorites (Home, Favorites)
    if name == "Home":
        return _normalize_home_property(prop_elem, name, attrs)

    if name == "Favorites":
        return _normalize_favorites_property(prop_elem, name, attrs)

    # 5. DecisionMatrix special cases
    if (
        name == "Cycles"
        and item_elem.get("type")
        == "Citect.Ampla.General.Server.RecordStates.CycleManager"
    ):
        return _normalize_cycle_manager_property(prop_elem, name, attrs)

    # 6. HistoricalFieldExpression warnings
    if name == "HistoricalFieldExpression":
        return _normalize_historical_expression(item_elem, prop_elem, name, attrs)

    # 7. ExpressionConfig normalization
    if prop_elem.find("HistoricalExpressionConfig/ExpressionConfig") is not None:
        return _normalize_expression_config_property(ctx, prop_elem, name, attrs)

    # 8. Preserve nested XML and extract ordinary property links.
    item_links = _extract_item_links(prop_elem, name)
    if not item_links and name != "DeriveSpecificationFrom":
        item_links = _extract_full_name_link(ctx, name, value)
    extra_xml = _element_to_dict(prop_elem) if len(prop_elem) else None
    return Property(
        name=name,
        value=value,
        attributes=attrs,
        item_links=item_links,
        extra_xml=extra_xml,
    )


def _normalize_soap_property(prop_elem: Element) -> Property:
    return Property(
        name=prop_elem.get("name"),
        value="{SOAP}",
        attributes={"isSoap": "true"},
        item_links=[],
    )


def _normalize_csv_property(name: str, value: str, attrs: dict) -> Property:
    links = [
        ItemLink(target_id=None, absolute_path=part.strip(), property_name=name)
        for part in value.split(",")
        if part.strip()
    ]
    return Property(name=name, value=None, attributes=attrs, item_links=links)


def _normalize_subscription_property(
    ctx: NormalizationContext, prop_elem: Element, name: str, attrs: dict
) -> Property:
    raw = (prop_elem.text or "").strip()
    links = []

    for line in raw.splitlines():
        parts = line.split("|")
        if len(parts) >= 2:
            link = ItemLink(
                target_id=None,
                absolute_path=parts[1],
                property_name=name,
                broken_target=False,
            )
            # Optional fields
            if len(parts) > 2:
                link.event = parts[2]
            if len(parts) > 3:
                link.handler = parts[3]
            if len(parts) > 4:
                link.expression_match = parts[4]
            links.append(link)

    return Property(name=name, value=None, attributes=attrs, item_links=links)


def _normalize_home_property(prop_elem: Element, name: str, attrs: dict) -> Property:
    count = 0
    for descriptor in prop_elem.findall(
        ".//*[@type='Citect.Ampla.General.Common.FavoriteDescriptor,Citect.Ampla.General.Common']"
    ):
        location = descriptor.find("Property[@name='LocationType']")
        if location is not None and (location.text or "") == "Home":
            count += 1

    return Property(
        name=name, value=f"{{{count} Favourite(s)}}", attributes=attrs, item_links=[]
    )


def _normalize_favorites_property(
    prop_elem: Element, name: str, attrs: dict
) -> Property:
    favs = prop_elem.findall(
        ".//*[@type='Citect.Ampla.General.Common.FavoriteDescriptor,Citect.Ampla.General.Common']"
    )
    corrupt = []
    for f in favs:
        location = f.find("Property[@name='LocationType']")
        if location is not None and (location.text or "") != "Favorite":
            corrupt.append(f)

    text = f"{{{len(favs)} Favourite(s)}}"
    if corrupt:
        attrs = dict(attrs)
        attrs["isCorrupt"] = "true"

    return Property(name=name, value=text, attributes=attrs, item_links=[])


def _normalize_cycle_manager_property(
    prop_elem: Element, name: str, attrs: dict
) -> Property:
    links = [
        ItemLink(target_id=None, absolute_path=child.text.strip(), property_name=name)
        for child in prop_elem.findall("Property/Item")
        if child.text and child.text.strip()
    ]
    return Property(name=name, value=None, attributes=attrs, item_links=links)


def _normalize_historical_expression(
    item_elem: Element, prop_elem: Element, name: str, attrs: dict
) -> Property:
    capture = item_elem.find("Property[@name='CaptureValueForManualRecords']")
    refresh = item_elem.find("Property[@name='RefreshOnManualEntry']")
    expr = prop_elem.find("HistoricalExpressionConfig/ExpressionConfig")

    if (
        capture is not None
        and capture.text == "True"
        and refresh is not None
        and refresh.text == "True"
        and expr is not None
        and (expr.get("format") == "" or expr.get("format") is None)
    ):
        attrs = dict(attrs)
        attrs["message"] = "No expression specified for Manual records."

    return Property(
        name=name,
        value=None,
        attributes=attrs,
        item_links=_extract_item_links(prop_elem, name),
        extra_xml=_element_to_dict(prop_elem) if len(prop_elem) else None,
    )


def _normalize_expression_config_property(
    ctx: NormalizationContext, prop_elem: Element, name: str, attrs: dict
) -> Property:
    """
    Normalize ExpressionConfig blocks:
    - formatExpression
    - findReplace
    - getProjectFullName
    """
    normalize_expression_config(ctx, prop_elem)
    return Property(
        name=name,
        value=None,
        attributes=attrs,
        item_links=_extract_item_links(prop_elem, name),
        extra_xml=_element_to_dict(prop_elem),
    )


def _extract_item_links(prop_elem: Element, property_name: str) -> list[ItemLink]:
    links: list[ItemLink] = []
    for link_elem in prop_elem.findall(".//ItemLink"):
        links.append(
            ItemLink(
                target_id=link_elem.get("targetID") or link_elem.get("targetId"),
                absolute_path=link_elem.get("absolutePath"),
                property_name=property_name,
                relative_path=link_elem.get("relativePath"),
                broken_target=link_elem.get("broken-targetID") == "true",
                broken_absolute=link_elem.get("broken-absolutePath") == "true",
                broken_relative=link_elem.get("broken-relativePath") == "true",
            )
        )
    return links


def _extract_full_name_link(
    ctx: NormalizationContext, property_name: str, value: str
) -> list[ItemLink]:
    return [
        ItemLink(
            target_id=target.get("id"),
            absolute_path=value,
            property_name=property_name,
        )
        for target in ctx.items_by_full_name.get(value, [])
    ]


def _element_to_dict(elem: Element) -> dict[str, object]:
    return {
        "tag": elem.tag,
        "attributes": dict(elem.attrib),
        "text": elem.text,
        "tail": elem.tail,
        "children": [_element_to_dict(child) for child in elem],
    }
