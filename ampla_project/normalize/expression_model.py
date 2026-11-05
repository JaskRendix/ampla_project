from __future__ import annotations

from lxml.etree import Element

from ..model.project import (
    ExpressionDependency,
    ExpressionModel,
    ExpressionPropertyLink,
    ExpressionReference,
    ExpressionStream,
)
from .context import NormalizationContext


def build_expression_model(ctx: NormalizationContext) -> ExpressionModel | None:
    """Extract dependency and stream relationships represented by the source XSLTs."""
    model = ExpressionModel()
    item_elements = ctx.root.findall(".//Item[@id]")
    item_elements_by_id = {
        elem.get("id"): elem for elem in item_elements if elem.get("id")
    }
    source_ids: set[str] = set()
    expression_ids: set[str] = set()
    dependency_targets_by_property: dict[
        tuple[str, str], list[ExpressionDependency]
    ] = {}

    for item_elem in item_elements:
        item_id = item_elem.get("id")
        if not item_id:
            continue
        for property_elem in item_elem.findall("Property"):
            property_name = property_elem.get("name") or ""
            dependencies = property_elem.findall(".//Dependency")
            if not dependencies:
                continue
            expression_ids.add(item_id)
            for dependency_elem in dependencies:
                dependency_type = dependency_elem.get("dependencyType")
                for item_property_link in _children(
                    dependency_elem, "ItemPropertyLink"
                ):
                    linked_property_name = item_property_link.get("propertyName")
                    for link_elem in _children(item_property_link, "ItemLink"):
                        target_id = link_elem.get("targetID") or link_elem.get(
                            "targetId"
                        )
                        target_elem = item_elements_by_id.get(target_id or "")
                        resolved = target_elem is not None
                        if target_id and resolved:
                            source_ids.add(target_id)
                        target_full_name = (
                            _item_full_name(target_elem)
                            if target_elem is not None
                            else link_elem.get("absolutePath")
                        )
                        dependency = ExpressionDependency(
                            expression_item_id=item_id,
                            expression_property_name=property_name,
                            target_item_id=target_id,
                            target_full_name=target_full_name,
                            property_name=linked_property_name,
                            dependency_type=dependency_type,
                            resolved=resolved,
                        )
                        model.dependencies.append(dependency)
                        if target_id and linked_property_name:
                            dependency_targets_by_property.setdefault(
                                (target_id, linked_property_name), []
                            ).append(dependency)

            for expression_config in property_elem.findall(".//ExpressionConfig"):
                for link_elem in expression_config.findall(
                    "ItemLinkCollection/ItemLink"
                ):
                    target_id = link_elem.get("targetID") or link_elem.get("targetId")
                    target_elem = item_elements_by_id.get(target_id or "")
                    model.references.append(
                        ExpressionReference(
                            expression_item_id=item_id,
                            property_name=property_name,
                            target_item_id=target_id,
                            absolute_path=(
                                _item_full_name(target_elem)
                                if target_elem is not None
                                else link_elem.get("absolutePath")
                            ),
                            format=link_elem.get("format"),
                            expression_format=link_elem.get("expressionFormat"),
                            resolved=target_elem is not None,
                        )
                    )

    model.expression_item_ids = [
        elem.get("id") for elem in item_elements if elem.get("id") in expression_ids
    ]
    model.source_item_ids = [
        elem.get("id") for elem in item_elements if elem.get("id") in source_ids
    ]

    for source_id in model.source_item_ids:
        source_elem = item_elements_by_id[source_id]
        for stream_elem in _type_streams(ctx, source_elem.get("type")):
            stream_name = stream_elem.get("name")
            if not stream_name:
                continue
            refs = dependency_targets_by_property.get((source_id, stream_name), [])
            if not refs:
                continue
            property_links: list[ExpressionPropertyLink] = []
            seen_properties: set[tuple[str, str]] = set()
            for dependency in refs:
                identity = (
                    dependency.expression_item_id,
                    dependency.expression_property_name,
                )
                if identity in seen_properties:
                    continue
                seen_properties.add(identity)
                expression_elem = item_elements_by_id[dependency.expression_item_id]
                property_links.append(
                    ExpressionPropertyLink(
                        expression_item_id=dependency.expression_item_id,
                        property_name=dependency.expression_property_name,
                        expression_type=expression_elem.get("type") or "",
                        expression_full_name=_item_full_name(expression_elem),
                        dependency_type=dependency.dependency_type,
                    )
                )
            model.streams.append(
                ExpressionStream(
                    item_id=source_id,
                    name=stream_name,
                    data_type=stream_elem.get("dataType"),
                    property_links=property_links,
                )
            )

    if not model.dependencies and not model.references:
        return None
    return model


def _type_streams(ctx: NormalizationContext, item_type: str | None) -> list[Element]:
    if not item_type:
        return []
    streams = []
    for type_elem in ctx.root.findall(".//Reference/Type"):
        if item_type not in (type_elem.get("fullName"), type_elem.get("name")):
            continue
        streams.extend(_children(type_elem, "Stream"))
    return streams


def _item_full_name(item_elem: Element) -> str:
    names = [
        ancestor.get("name")
        for ancestor in reversed(list(item_elem.iterancestors(tag="Item")))
        if ancestor.get("id")
    ]
    names.append(item_elem.get("name"))
    return ".".join(name or "" for name in names)


def _children(elem: Element, name: str) -> list[Element]:
    return [child for child in elem if _local_name(child) == name]


def _local_name(elem: Element) -> str:
    return elem.tag.rsplit("}", 1)[-1] if isinstance(elem.tag, str) else ""
