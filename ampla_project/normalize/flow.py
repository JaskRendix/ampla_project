from __future__ import annotations

from ..model.item import Item
from ..model.project import FlowLink, FlowNode
from .context import NormalizationContext


def build_flow_tree(items: dict[str, Item]) -> list[FlowNode]:
    """Build the root and immediate-link structure produced by Project.Flow.xslt."""
    roots = sorted(
        (item for item in items.values() if item.link_to and not item.link_from),
        key=lambda item: (item.type or "", item.full_name or ""),
    )
    flow: list[FlowNode] = []

    for item in roots:
        node = _flow_node(item)
        node.links = [
            FlowLink(
                property_name=link.property_name,
                item=_flow_node(target),
            )
            for link in item.link_to
            if (target := items.get(link.target_id or "")) is not None
        ]
        flow.append(node)

    return flow


def build_flow_graph(
    ctx: NormalizationContext, items: dict[str, Item]
) -> dict[str, list[str]]:
    """
    Build a directed flow graph:
        producer_id → [consumer_id, ...]
    Equivalent to Project.Flow.xslt.
    """

    graph: dict[str, list[str]] = {}

    for item in items.values():
        graph[item.id] = []

    for item in items.values():
        for prop in item.properties.values():
            for link in prop.item_links:
                if not link.target_id:
                    continue

                # Flow direction: target → item
                producer = link.target_id
                consumer = item.id

                if producer in graph:
                    graph[producer].append(consumer)

    return graph


def _flow_node(item: Item) -> FlowNode:
    return FlowNode(
        item_id=item.id,
        name=item.name,
        type=item.type,
        full_name=item.full_name,
        hash=item.hash,
        definition=item.definition,
        translation=item.translation,
    )
