from __future__ import annotations

from lxml.etree import Element

from ..model.item import (
    DecisionMatrixInput,
    DecisionMatrixInputRule,
    Item,
    ItemLink,
    Property,
)
from .classes import resolve_class_association
from .context import NormalizationContext
from .properties import normalize_property


def normalize_items(ctx: NormalizationContext) -> dict[str, Item]:
    """
    Entry point: normalize all <Item[@id]> elements into Item objects.
    Mirrors the XSLT template: <xsl:template match="Item[@id]">.
    """
    items: dict[str, Item] = {}

    for elem in ctx.root.findall(".//Item[@id]"):
        item = build_item(ctx, elem)
        items[item.id] = item

    return items


def build_item(ctx: NormalizationContext, elem: Element) -> Item:
    """
    Build a normalized Item object from a raw XML <Item>.
    Equivalent to:
        <xsl:template match="Item[@id]">
            <Item>
                <addItemAttributes/>
                <apply Property/>
                <addPropertyDisplayOrder/>
                <apply Item/>
            </Item>
        </xsl:template>
    """

    item_id = elem.get("id")
    name = elem.get("name")
    type_ = elem.get("type")

    full_name = compute_full_name(elem)
    hash_ = ctx.generate_hash(full_name)

    definition = extract_definition(elem)
    translation = ctx.get_translation(name)

    item = Item(
        id=item_id,
        name=name,
        type=type_,
        full_name=full_name,
        hash=hash_,
        definition=definition,
        translation=translation,
        is_class=False,
    )

    # Normalize all <Property> children
    for prop_elem in elem.findall("Property"):
        prop = normalize_property(ctx, elem, prop_elem)
        if prop:
            item.properties[prop.name] = prop

    if (
        item.translation
        and item.type in ctx.types_with_display_name
        and "DisplayName" not in item.properties
    ):
        item.properties["DisplayName"] = Property(
            name="DisplayName",
            value=item.translation,
            attributes={},
            item_links=[],
        )

    _add_source_defaults(item)
    _add_decision_matrix_data(ctx, elem, item)

    # Add default DisplayOrder if missing
    if "DisplayOrder" not in item.properties:
        item.properties["DisplayOrder"] = Property(
            name="DisplayOrder",
            value=str(ctx.default_display_order),
            attributes={},
            item_links=[],
        )

    # Normalize class associations
    resolve_class_association(ctx, elem, item)

    # Normalize child items recursively
    for child_elem in elem.findall("Item"):
        child = build_item(ctx, child_elem)
        item.children.append(child)

    return item


def _add_source_defaults(item: Item) -> None:
    defaults = {
        "Citect.Ampla.Metrics.Server.Resolvers.Resolver": {
            "Action": "Module",
            "ResolverOperation": "Sum",
        },
        "Citect.Ampla.StandardItems.User": {"Authentication": "WindowsIntegrated"},
        "Citect.Ampla.Connectors.OleDbConnector.OleDbVariable": {
            "SampleTypeCode": "Single"
        },
    }
    for name, value in defaults.get(item.type, {}).items():
        if name not in item.properties:
            item.properties[name] = Property(
                name=name, value=value, attributes={}, item_links=[]
            )


def _add_decision_matrix_data(
    ctx: NormalizationContext, elem: Element, item: Item
) -> None:
    matrix_type = "Citect.Ampla.General.Server.DecisionMatrix"
    rule_type = "Citect.Ampla.General.Server.DecisionMatrixRule"
    variable_type = "Citect.Ampla.StandardItems.CalculatedVariable"

    def display_order(variable: Element) -> str:
        order = variable.find("Property[@name='DisplayOrder']")
        return (
            (order.text or "").strip()
            if order is not None
            else str(ctx.default_display_order)
        )

    if item.type == matrix_type:
        for variable in elem.findall(f"Item[@type='{variable_type}']"):
            variable_id = variable.get("id")
            variable_name = variable.get("name")
            if not variable_id or not variable_name:
                continue
            full_name = ".".join((item.full_name, variable_name))
            item.decision_matrix_inputs.append(
                DecisionMatrixInput(
                    id=variable_id,
                    name=variable_name,
                    hash=ctx.generate_hash(full_name),
                    translation=ctx.get_translation(variable_name),
                    display_order=display_order(variable),
                    item_link=ItemLink(
                        target_id=variable_id,
                        absolute_path=full_name,
                    ),
                )
            )
    elif item.type == rule_type:
        parent = elem.getparent()
        if parent is None:
            return
        for variable in parent.findall(f"Item[@type='{variable_type}']"):
            variable_name = variable.get("name")
            variable_id = variable.get("id")
            if not variable_name or not variable_id:
                continue
            rule_value = elem.find(f"Property[@name='{variable_name}']")
            item.decision_matrix_input_rules.append(
                DecisionMatrixInputRule(
                    name=variable_name,
                    display_order=display_order(variable),
                    value=(
                        (rule_value.text or "").strip()
                        if rule_value is not None
                        else "Ignore"
                    ),
                    item_link=ItemLink(
                        target_id=variable_id,
                        absolute_path=compute_full_name(variable),
                    ),
                )
            )


def compute_full_name(elem: Element) -> str:
    """
    Equivalent to XSLT getItemFullName:
        ancestor-or-self::Item[@id]/@name joined with '.'
    """
    names = []
    for ancestor in elem.iterancestors(tag="Item"):
        if ancestor.get("id"):
            names.append(ancestor.get("name"))
    names.reverse()
    names.append(elem.get("name"))
    return ".".join(names)


def extract_definition(elem: Element) -> str | None:
    """
    Equivalent to:
        <xsl:variable name="definition" select="Property[@name='Definition']/ItemLink/@absolutePath"/>
    """
    prop = elem.find("Property[@name='Definition']/ItemLink")
    if prop is not None:
        return prop.get("absolutePath")
    return None
