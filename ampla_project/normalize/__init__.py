from __future__ import annotations

from lxml.etree import Element

from ..model.project import Project
from .classes import normalize_classes
from .context import NormalizationContext
from .expressions import normalize_expression_config
from .flow import build_flow_graph
from .items import normalize_items
from .links import build_link_from_to, resolve_item_links
from .metrics import calculate_metrics
from .security import normalize_security


def normalize(root: Element, language_doc: Element | None = None) -> Project:
    """
    Top-level normalization entry point.
    This replaces the entire XSLT pipeline with a clean Python pipeline.

    Steps:
      1. Build NormalizationContext (keys, translations, defaults)
      2. Normalize classes
      3. Normalize items
      4. Resolve ItemLinks (absolute, targetID, relative)
      5. Build linkFrom / linkTo
      6. Normalize ExpressionConfig
      7. Build Flow graph
      8. Normalize Security
      9. Return Project model
    """

    ctx = NormalizationContext(root=root, language_doc=language_doc)

    classes = normalize_classes(ctx)

    items = normalize_items(ctx)

    resolve_item_links(ctx, items)

    build_link_from_to(ctx, items)

    for item in items.values():
        for prop in item.properties.values():
            if prop.extra_xml is not None:
                normalize_expression_config(ctx, prop.extra_xml)

    flow_graph = build_flow_graph(ctx, items)

    security = normalize_security(ctx, items)

    metrics = calculate_metrics(items, classes, security)

    return Project(
        items=items,
        classes=classes,
        flow_graph=flow_graph,
        security=security,
        metrics=metrics,
        platform_version=_get_platform_version(root),
        applications_version=_get_applications_version(root),
        properties=_extract_project_properties(root),
    )


def _get_platform_version(root: Element) -> str:
    ref = root.find("Reference[@name='Citect.Ampla.StandardItems']")
    return ref.get("version") if ref is not None else "0.0"


def _get_applications_version(root: Element) -> str:
    ref = root.find("Reference[@name='Citect.Ampla.General.Server']")
    return ref.get("version") if ref is not None else "0.0"


def _extract_project_properties(root: Element) -> dict[str, str]:
    props = {}
    for attr in root.attrib:
        props[attr] = root.get(attr)
    return props
