from __future__ import annotations

from dataclasses import dataclass, field

from .item import Item


@dataclass
class ExpressionDependency:
    expression_item_id: str
    expression_property_name: str
    target_item_id: str | None
    target_full_name: str | None
    property_name: str | None
    dependency_type: str | None
    resolved: bool


@dataclass
class ExpressionReference:
    expression_item_id: str
    property_name: str
    target_item_id: str | None
    absolute_path: str | None
    format: str | None
    expression_format: str | None
    resolved: bool


@dataclass
class ExpressionPropertyLink:
    expression_item_id: str
    property_name: str
    expression_type: str
    expression_full_name: str
    dependency_type: str | None


@dataclass
class ExpressionStream:
    item_id: str
    name: str
    data_type: str | None
    property_links: list[ExpressionPropertyLink] = field(default_factory=list)


@dataclass
class ExpressionModel:
    expression_item_ids: list[str] = field(default_factory=list)
    source_item_ids: list[str] = field(default_factory=list)
    dependencies: list[ExpressionDependency] = field(default_factory=list)
    references: list[ExpressionReference] = field(default_factory=list)
    streams: list[ExpressionStream] = field(default_factory=list)


@dataclass
class FlowNode:
    item_id: str
    name: str | None
    type: str | None
    full_name: str
    hash: str
    definition: str | None
    translation: str | None
    links: list["FlowLink"] = field(default_factory=list)


@dataclass
class FlowLink:
    property_name: str | None
    item: FlowNode


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
    expression_model: ExpressionModel | None = None
    flow: list[FlowNode] = field(default_factory=list)

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
