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
            if link.broken_target or link.broken_absolute or link.broken_relative:
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
    classes_by_full_name = {
        cls.full_name: class_id for class_id, cls in classes.items()
    }
    classes_by_name: dict[str, list[str]] = {}
    for class_id, cls in classes.items():
        classes_by_name.setdefault(cls.name, []).append(class_id)

    def resolve_class_id(reference: str | None) -> str | None:
        if not reference:
            return None
        if reference in classes:
            return reference
        if reference in classes_by_full_name:
            return classes_by_full_name[reference]
        matches = classes_by_name.get(reference, [])
        return matches[0] if len(matches) == 1 else None

    def get_parent_class_id(cls: Item) -> str | None:
        inherits = cls.properties.get("(inherits)")
        if inherits is not None:
            for link in inherits.item_links:
                parent_id = resolve_class_id(link.target_id)
                if parent_id is None:
                    parent_id = resolve_class_id(link.absolute_path)
                if parent_id is not None:
                    return parent_id
            return None

        parent = cls.properties.get("Parent")
        return resolve_class_id(parent.value if parent else None)

    state: dict[str, int] = {}
    depths: dict[str, int | None] = {}
    path: list[str] = []
    cycles_found: set[frozenset[str]] = set()

    def inheritance_depth(class_id: str) -> int | None:
        if state.get(class_id) == 2:
            return depths[class_id]
        if state.get(class_id) == 1:
            cycle_start = path.index(class_id)
            cycles_found.add(frozenset(path[cycle_start:]))
            return None

        state[class_id] = 1
        path.append(class_id)
        parent_id = get_parent_class_id(classes[class_id])
        if parent_id is None:
            depth = 0
        else:
            parent_depth = inheritance_depth(parent_id)
            depth = parent_depth + 1 if parent_depth is not None else None
        path.pop()
        state[class_id] = 2
        depths[class_id] = depth
        return depth

    max_depth = max(
        (
            depth
            for class_id in classes
            if (depth := inheritance_depth(class_id)) is not None
        ),
        default=0,
    )
    cycles = len(cycles_found)

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
