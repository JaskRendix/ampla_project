from __future__ import annotations

from lxml.etree import Element

from ..model.project import Project
from .classes import normalize_classes
from .context import NormalizationContext
from .expression_model import build_expression_model
from .flow import build_flow_graph, build_flow_tree
from .items import normalize_items
from .links import build_link_from_to, resolve_item_links
from .metrics import calculate_metrics
from .security import normalize_security


def normalize(
    root: Element,
    language_doc: Element | None = None,
    authstore_doc: Element | None = None,
) -> Project:
    """
    Top-level normalization entry point.
    This replaces the entire XSLT pipeline with a clean Python pipeline.

    Steps:
      1. Build NormalizationContext (keys, translations, defaults)
      2. Normalize classes
      3. Normalize items and their ExpressionConfig properties
      4. Resolve ItemLinks (absolute, targetID, relative)
      5. Build linkFrom / linkTo
      6. Build Flow graph
      7. Normalize Security
      8. Return Project model
    """

    ctx = NormalizationContext(root=root, language_doc=language_doc)

    classes = normalize_classes(ctx)

    items = normalize_items(ctx)

    resolve_item_links(ctx, items)

    build_link_from_to(ctx, items)

    expression_model = build_expression_model(ctx)

    flow_graph = build_flow_graph(ctx, items)
    flow = build_flow_tree(items)

    security = normalize_security(ctx, items, authstore_doc)

    metrics = calculate_metrics(items, classes, security)

    return Project(
        items=items,
        classes=classes,
        flow_graph=flow_graph,
        security=security,
        metrics=metrics,
        expression_model=expression_model,
        flow=flow,
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
