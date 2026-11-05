from __future__ import annotations

from lxml.etree import Element

from .context import NormalizationContext


def normalize_expression_config(ctx: NormalizationContext, prop_elem: Element) -> None:
    """
    Normalize <ExpressionConfig> blocks inside HistoricalExpressionConfig.
    Mirrors XSLT templates:
        - match="ExpressionConfig"
        - match="ExpressionConfig/ItemLinkCollection/ItemLink"
        - formatExpression
        - findReplace
        - getProjectFullName
    """

    for expr in prop_elem.findall(".//ExpressionConfig"):
        _normalize_single_expression_config(ctx, expr)


def _normalize_single_expression_config(
    ctx: NormalizationContext, expr_elem: Element
) -> None:
    """
    Add 'text' attribute with formatted expression.
    """
    format_str = expr_elem.get("format", "")
    item_links = expr_elem.findall("ItemLinkCollection/ItemLink")

    formatted = _format_expression(ctx, format_str, item_links)
    expr_elem.set("text", formatted)

    for link in item_links:
        _normalize_item_link(ctx, link, item_links)


def _normalize_item_link(
    ctx: NormalizationContext,
    link_elem: Element,
    fallback_links: list[Element] | None = None,
) -> None:
    nested_links = link_elem.findall("ItemLinkCollection/ItemLink")
    link_format = link_elem.get("format", "")
    format_links = nested_links or fallback_links or []
    link_elem.set(
        "expressionFormat",
        _format_expression(ctx, link_format, format_links),
    )
    for nested_link in nested_links:
        _normalize_item_link(ctx, nested_link)


def _format_expression(
    ctx: NormalizationContext,
    format_str: str,
    item_links: list[Element],
) -> str:
    """
    Equivalent to XSLT formatExpression:
        - Replace #ItemReferenceN# with project fullName
        - Uses recursive findReplace logic
    """

    result = format_str

    for index, link in enumerate(item_links):
        placeholder = f"#ItemReference{index}#"
        target_id = link.get("targetID") or link.get("targetId") or ""
        full = _get_project_full_name(ctx, target_id)
        result = result.replace(placeholder, full)

    return result


def _get_project_full_name(ctx: NormalizationContext, item_id: str) -> str:
    """
    Equivalent to XSLT getProjectFullName:
        Project.[Area].[Equipment].[Variable]
    Brackets names containing characters outside ASCII letters.
    """

    elem = ctx.items_by_id.get(item_id)
    if elem is None:
        return ""

    names = []
    for ancestor in elem.iterancestors(tag="Item"):
        if ancestor.get("id"):
            names.append(_bracket_if_non_ascii(ancestor.get("name")))

    names.reverse()
    names.append(_bracket_if_non_ascii(elem.get("name")))

    return "Project." + ".".join(names)


def _bracket_if_non_ascii(name: str | None) -> str:
    if not name:
        return ""
    if any(
        not ("A" <= character <= "Z" or "a" <= character <= "z") for character in name
    ):
        return f"[{name}]"
    return name
