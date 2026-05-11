from __future__ import annotations

from ..model.item import Item, ItemLink
from .context import NormalizationContext


def resolve_item_links(ctx: NormalizationContext, items: dict[str, Item]) -> None:
    """
    Resolve all ItemLink objects:
    - absolutePath → target_id
    - targetID → absolutePath
    - relativePath → resolved ID
    - mark broken links
    """
    for item in items.values():
        for prop in item.properties.values():
            for link in prop.item_links:
                _resolve_single_link(ctx, items, item, link)


def build_link_from_to(ctx: NormalizationContext, items: dict[str, Item]) -> None:
    """
    Build reverse links (linkTo) based on linkFrom.
    Equivalent to Project.LinkTo.xslt.
    """
    # Initialize containers
    for item in items.values():
        item.link_from = []  # forward references
        item.link_to = []  # reverse references

    # Build forward references
    for item in items.values():
        for prop in item.properties.values():
            for link in prop.item_links:
                if link.target_id:
                    item.link_from.append(link)

    # Build reverse references
    for item in items.values():
        for link in item.link_from:
            target = items.get(link.target_id)
            if target:
                target.link_to.append(
                    ItemLink(
                        target_id=item.id,
                        absolute_path=item.full_name,
                        property_name=link.property_name,
                    )
                )


def _resolve_single_link(
    ctx: NormalizationContext, items: dict[str, Item], item: Item, link: ItemLink
) -> None:
    """
    Resolve a single ItemLink:
    - If absolutePath is present → resolve to ID
    - If targetID is present → resolve to absolutePath
    - If relativePath is present → resolve via ancestor chain
    """

    # 1. Resolve absolutePath → target_id
    if link.absolute_path and not link.target_id:
        target = _find_item_by_fullname(items, link.absolute_path)
        if target:
            link.target_id = target.id
        else:
            link.broken_absolute = True

    # 2. Resolve targetID → absolutePath
    if link.target_id and not link.absolute_path:
        target = items.get(link.target_id)
        if target:
            link.absolute_path = target.full_name
        else:
            link.broken_target = True

    # 3. Relative path resolution (Parent.Parent.this)
    if getattr(link, "relative_path", None):
        resolved = _resolve_relative_path(ctx, items, item, link.relative_path)
        if resolved:
            link.target_id = resolved.id
            link.absolute_path = resolved.full_name
        else:
            link.broken_relative = True


def _find_item_by_fullname(items: dict[str, Item], full_name: str) -> Item | None:
    """
    Equivalent to key('items-by-fullName').
    """
    for item in items.values():
        if item.full_name == full_name:
            return item
    return None


def _resolve_relative_path(
    ctx: NormalizationContext, items: dict[str, Item], item: Item, path: str
) -> Item | None:
    """
    Implements the XSLT logic from findRelativeId:
    - Parent.Parent.this
    - Parent
    - this
    - absolute fullName
    - child paths
    """

    parts = path.split(".")
    ancestors = _get_ancestor_chain(ctx, item)

    index = len(ancestors) - 1  # start at current item

    for part in parts:
        if part == "Parent":
            index -= 1
            if index < 0:
                return None
        elif part == "this":
            continue
        else:
            # treat as absolute fullName
            return _find_item_by_fullname(items, path)

    if 0 <= index < len(ancestors):
        return ancestors[index]

    return None


def _get_ancestor_chain(ctx: NormalizationContext, item: Item) -> list[Item]:
    """
    Build ancestor chain from root → item.
    """
    chain = []
    current = item
    while current:
        chain.append(current)
        parent = _find_parent(ctx, current)
        current = parent
    return chain


def _find_parent(ctx: NormalizationContext, item: Item) -> Item | None:
    """
    Find parent Item by checking fullName prefix.
    """
    parts = item.full_name.split(".")
    if len(parts) <= 1:
        return None

    parent_full = ".".join(parts[:-1])
    return _find_item_by_fullname(ctx.items_by_id, parent_full)
