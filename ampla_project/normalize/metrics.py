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
    total_links = 0
    broken_links = 0
    orphans = 0

    for item in items.values():

        # 1. Count by item type
        item_counts[item.type] = item_counts.get(item.type, 0) + 1

        # 2. Link health
        for link in item.link_from:
            total_links += 1
            if link.broken_target or link.broken_absolute:
                broken_links += 1

        # 3. Orphan detection
        if not item.link_to and not item.children:
            orphans += 1

    # 4. Count classes by type
    class_counts: dict[str, int] = {}
    for cls in classes.values():
        class_counts[cls.type] = class_counts.get(cls.type, 0) + 1

    # 5. Detect unused classes (classes with no instances)
    used_class_ids = {item.type for item in items.values()}
    unused_classes = [
        cls_id for cls_id in classes if classes[cls_id].name not in used_class_ids
    ]

    # 6. Inheritance depth + cycle detection
    def get_parent_class_name(cls: Item) -> str | None:
        prop = cls.properties.get("Parent")
        return prop.value if prop else None

    def inheritance_depth(cls_id: str, visited=None) -> int:
        if visited is None:
            visited = set()

        if cls_id in visited:
            return -1  # cycle

        visited.add(cls_id)

        cls = classes.get(cls_id)
        if cls is None:
            return 0

        parent_name = get_parent_class_name(cls)
        if not parent_name:
            return 0

        # find parent class by name
        parent_cls = next(
            (cid for cid, c in classes.items() if c.name == parent_name), None
        )
        if not parent_cls:
            return 0

        depth = inheritance_depth(parent_cls, visited)
        if depth < 0:
            return -1

        return depth + 1

    max_depth = 0
    cycles = 0

    for cls_id in classes:
        depth = inheritance_depth(cls_id)
        if depth < 0:
            cycles += 1
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
    metrics.unused_classes_count = len(unused_classes)
    metrics.class_inheritance_depth_max = max_depth
    metrics.class_inheritance_cycles = cycles

    return metrics
