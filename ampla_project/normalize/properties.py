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

    if item_elem.get("id") and name in {
        "RunState",
        "DisplayOrderIndex",
        "DisplayOrderGroup",
        "PropertyMaskSets",
        "DataSource",
        "Definition",
    }:
        return None

    # 1. SOAP normalization
    if (
        prop_elem.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        is not None
    ):
        if item_elem.get("type") == (
            "Citect.Ampla.Connectors.OleDbConnector.OleDbAdapter"
        ):
            return _normalize_ole_db_soap_property(prop_elem)
        return _normalize_soap_property(prop_elem)

    # 2. CSV → ItemLink (EquipmentTypes, ParameterGroups)
    if name in ("EquipmentTypes", "ParameterGroups"):
        return _normalize_csv_property(name, value, attrs)

    # 3. Subscription parsing
    if "Subscription" in name:
        return _normalize_subscription_property(prop_elem, name, attrs)

    # 4. Favorites (Home, Favorites)
    if name == "Home":
        return _normalize_home_property(prop_elem, name)

    if name == "Favorites":
        return _normalize_favorites_property(prop_elem, name)

    # 5. DecisionMatrix special cases
    if (
        name == "Cycles"
        and item_elem.get("type")
        == "Citect.Ampla.General.Server.RecordStates.CycleManager"
    ):
        return _normalize_cycle_manager_property(prop_elem, name)

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


def _normalize_ole_db_soap_property(prop_elem: Element) -> Property:
    soap_properties = []
    for descendant in prop_elem.iterdescendants():
        if isinstance(descendant.tag, str) and not descendant.tag.startswith("{"):
            text = "".join(descendant.itertext())
            if text:
                soap_properties.append(
                    {
                        "tag": "soap-property",
                        "attributes": {"name": descendant.tag},
                        "text": text,
                        "tail": None,
                        "children": [],
                    }
                )

    if not soap_properties:
        return Property(
            name=prop_elem.get("name"),
            value="{SOAP}",
            attributes={"isSoap": "true"},
            item_links=[],
        )

    return Property(
        name=prop_elem.get("name"),
        value=None,
        attributes={"isSoap": "true"},
        item_links=[],
        extra_xml={
            "tag": "Property",
            "attributes": {"isSoap": "true"},
            "text": None,
            "tail": None,
            "children": soap_properties,
        },
    )


def _normalize_csv_property(name: str, value: str, attrs: dict) -> Property:
    links = [
        ItemLink(target_id=None, absolute_path=part, property_name=name)
        for part in value.split(",")
    ]
    return Property(name=name, value=None, attributes=attrs, item_links=links)


def _normalize_subscription_property(
    prop_elem: Element, name: str, attrs: dict
) -> Property:
    raw = (prop_elem.text or "").strip()
    links = []

    for line in raw.splitlines():
        parts = line.split("|")
        if len(parts) >= 4:
            link = ItemLink(
                target_id=None,
                absolute_path=parts[1],
                property_name=name,
                broken_target=False,
            )
            link.event = parts[2]
            link.handler = parts[3]
            if len(parts) == 5:
                link.expression_match = parts[4]
            links.append(link)

    return Property(name=name, value=raw, attributes=attrs, item_links=links)


def _normalize_home_property(prop_elem: Element, name: str) -> Property:
    descriptor_type = (
        "Citect.Ampla.General.Common.FavoriteDescriptor," "Citect.Ampla.General.Common"
    )
    count = 0
    for descriptor in prop_elem.findall(f".//*[@type='{descriptor_type}']"):
        location = descriptor.find("Property[@name='LocationType']")
        if location is not None and (location.text or "") == "Home":
            count += 1

    favorites = [
        favorite
        for descriptor in prop_elem.findall(f"Property[@type='{descriptor_type}']")
        if (favorite := _normalize_favorite_descriptor(descriptor)) is not None
    ]
    return Property(
        name=name,
        value=f"{{{count} Favourite(s)}}",
        attributes={},
        item_links=[],
        extra_xml=(
            _favorite_property_xml(name, f"{{{count} Favourite(s)}}", favorites)
            if favorites
            else None
        ),
    )


def _normalize_favorites_property(prop_elem: Element, name: str) -> Property:
    descriptor_type = (
        "Citect.Ampla.General.Common.FavoriteDescriptor," "Citect.Ampla.General.Common"
    )
    collection_type = (
        "Citect.Ampla.General.Common.FavoriteDescriptorCollection,"
        "Citect.Ampla.General.Common"
    )
    favs = prop_elem.findall(f".//*[@type='{descriptor_type}']")
    corrupt = []
    for f in favs:
        location = f.find("Property[@name='LocationType']")
        if location is not None and (location.text or "") != "Favorite":
            corrupt.append(f)

    text = f"{{{len(favs)} Favourite(s)}}" if favs else "{0 Favorite(s)}"
    if not favs:
        return Property(name=name, value=text, attributes={}, item_links=[])

    text_attributes = {"isCorrupt": "true"} if corrupt else {}
    children: list[dict[str, object]] = [
        {
            "tag": "text",
            "attributes": text_attributes,
            "text": text,
            "tail": None,
            "children": [],
        }
    ]
    children.extend(
        _normalize_favorite_collection(collection)
        for collection in prop_elem.findall(f"Property[@type='{collection_type}']")
    )
    return Property(
        name=name,
        value=text,
        attributes={},
        item_links=[],
        extra_xml={
            "tag": "Property",
            "attributes": {"name": name},
            "text": None,
            "tail": None,
            "children": children,
        },
    )


def _favorite_property_xml(
    name: str, text: str, favorites: list[dict[str, object]]
) -> dict[str, object]:
    return {
        "tag": "Property",
        "attributes": {"name": name},
        "text": None,
        "tail": None,
        "children": [
            {
                "tag": "text",
                "attributes": {},
                "text": text,
                "tail": None,
                "children": [],
            },
            *favorites,
        ],
    }


def _normalize_favorite_descriptor(elem: Element) -> dict[str, object] | None:
    if elem.find("Property[@name='Location']") is None:
        return None

    attributes = {
        "name": _favorite_value(elem, "Name") or "",
        "module": _favorite_value(elem, "Module") or "",
    }
    for xml_name, property_name in (
        ("filter", "Filter"),
        ("location", "Location"),
        ("recurse", "Recurse"),
        ("view", "ViewName"),
    ):
        value = _favorite_value(elem, property_name)
        if value is not None:
            attributes[xml_name] = value
    return {
        "tag": "Favorite",
        "attributes": attributes,
        "text": None,
        "tail": None,
        "children": [],
    }


def _normalize_favorite_collection(elem: Element) -> dict[str, object]:
    collection_type = (
        "Citect.Ampla.General.Common.FavoriteDescriptorCollection,"
        "Citect.Ampla.General.Common"
    )
    descriptor_type = (
        "Citect.Ampla.General.Common.FavoriteDescriptor," "Citect.Ampla.General.Common"
    )
    children: list[dict[str, object]] = []
    for item in elem.findall(f"Item[@type='{collection_type}']"):
        children.append(_normalize_favorite_collection(item))
    for item in elem.findall(f"Item[@type='{descriptor_type}']"):
        favorite = _normalize_favorite_descriptor(item)
        if favorite is not None:
            children.append(favorite)
    return {
        "tag": "Favorites",
        "attributes": {"name": _favorite_value(elem, "Name") or ""},
        "text": None,
        "tail": None,
        "children": children,
    }


def _favorite_value(elem: Element, name: str) -> str | None:
    prop = elem.find(f"Property[@name='{name}']")
    return (prop.text or "") if prop is not None else None


def _normalize_cycle_manager_property(prop_elem: Element, name: str) -> Property:
    links = [
        ItemLink(target_id=None, absolute_path=child.text.strip(), property_name=name)
        for child in prop_elem.findall("Property/Item")
        if child.text and child.text.strip()
    ]
    return Property(name=name, value=None, attributes={}, item_links=links)


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
