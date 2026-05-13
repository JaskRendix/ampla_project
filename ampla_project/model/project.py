from __future__ import annotations

from dataclasses import dataclass, field

from .item import Item


@dataclass
class ProjectMetrics:
    """Calculated statistics for the project."""

    item_counts: dict[str, int] = field(default_factory=dict)
    total_links: int = 0
    broken_links_count: int = 0
    orphaned_items_count: int = 0
    user_roles_count: int = 0
    class_counts: dict[str, int] = field(default_factory=dict)
    unused_classes_count: int = 0
    class_inheritance_depth_max: int = 0
    class_inheritance_cycles: int = 0


@dataclass
class ProjectProperty:
    """
    Represents a top-level project property.
    Mirrors <ProjectProperty name="...">value</ProjectProperty>
    """

    name: str
    value: str


@dataclass
class Project:
    """
    Represents the fully normalized project.
    This is the final output of normalize().
    """

    # Core normalized content
    items: dict[str, Item]  # All normalized items
    classes: dict[str, Item]  # Normalized class definitions

    # Graphs
    flow_graph: dict[str, list[str]]  # producer_id → [consumer_ids]
    security: dict[str, object]  # users + scopes

    # Metadata
    platform_version: str
    applications_version: str
    properties: dict[str, str]  # raw project-level attributes

    metrics: ProjectMetrics = field(default_factory=ProjectMetrics)

    def get_item(self, item_id: str) -> Item | None:
        return self.items.get(item_id)

    def get_class(self, class_id: str) -> Item | None:
        return self.classes.get(class_id)

    def all_items(self) -> list[Item]:
        return list(self.items.values())

    def all_classes(self) -> list[Item]:
        return list(self.classes.values())

    def find_by_full_name(self, full_name: str) -> Item | None:
        for item in self.items.values():
            if item.full_name == full_name:
                return item
        return None
