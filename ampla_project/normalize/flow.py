from __future__ import annotations

from ..model.item import Item
from .context import NormalizationContext


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
