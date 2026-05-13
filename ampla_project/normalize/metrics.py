from __future__ import annotations

from ..model.item import Item
from ..model.project import ProjectMetrics
from ..model.security import SecurityUser


def calculate_metrics(
    items: dict[str, Item],
    classes: dict[str, Item],
    security: dict[str, SecurityUser],
) -> ProjectMetrics:

    item_counts: dict[str, int] = {}
    total_links: int = 0
    broken_links: int = 0

    # Collect all child IDs to avoid false orphan detection
    child_ids: set[str] = {
        child.id for item in items.values() for child in item.children
    }

    orphans: int = 0

    for item in items.values():

        # 1. Count by item type
        item_counts[item.type] = item_counts.get(item.type, 0) + 1

        # 2. Link health
        for link in item.link_from:
            total_links += 1
            if link.broken_target or link.broken_absolute:
                broken_links += 1

        # 3. Orphan detection
        if (
            not item.children
            and item.id not in child_ids
            and not item.link_to
            and not item.link_from
        ):
            orphans += 1

    # 4. Count classes by type
    class_counts: dict[str, int] = {}
    for cls in classes.values():
        class_counts[cls.type] = class_counts.get(cls.type, 0) + 1

    # 5. Detect unused classes
    used_class_ids: set[str] = {item.type for item in items.values()}
    unused_classes: int = sum(
        1 for cls in classes.values() if cls.name not in used_class_ids
    )

    # 6. Inheritance depth + cycle detection
    def get_parent_class_name(cls: Item) -> str | None:
        prop = cls.properties.get("Parent")
        return prop.value if prop else None

    def inheritance_depth(
        cls_id: str,
        visited: set[str] | None = None,
    ) -> tuple[int, set[str]]:
        if visited is None:
            visited = set()

        if cls_id in visited:
            return -1, visited  # cycle

        visited.add(cls_id)

        cls = classes.get(cls_id)
        if cls is None:
            return 0, visited

        parent_name: str | None = get_parent_class_name(cls)
        if not parent_name:
            return 0, visited

        parent_cls_id: str | None = next(
            (cid for cid, c in classes.items() if c.name == parent_name),
            None,
        )
        if not parent_cls_id:
            return 0, visited

        depth, visited = inheritance_depth(parent_cls_id, visited)
        if depth < 0:
            return -1, visited

        return depth + 1, visited

    max_depth: int = 0
    cycles: int = 0
    cycle_seen: set[str] = set()

    for cls_id in classes:
        if cls_id in cycle_seen:
            continue

        depth, visited = inheritance_depth(cls_id)

        if depth < 0:
            cycles += 1
            cycle_seen.update(visited)
        else:
            max_depth = max(max_depth, depth)

    metrics = ProjectMetrics(
        item_counts=item_counts,
        total_links=total_links,
        broken_links_count=broken_links,
        orphaned_items_count=orphans,
        user_roles_count=len(security.get("users", {})),
    )

    metrics.class_counts = class_counts
    metrics.unused_classes_count = unused_classes
    metrics.class_inheritance_depth_max = max_depth
    metrics.class_inheritance_cycles = cycles

    return metrics
