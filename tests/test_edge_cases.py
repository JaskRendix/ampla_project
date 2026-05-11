import pytest
from lxml.etree import XMLSyntaxError, fromstring

from ampla_project.model.item import Item, ItemLink, Property
from ampla_project.normalize import normalize
from ampla_project.normalize.classes import resolve_class_association
from ampla_project.normalize.context import NormalizationContext
from ampla_project.normalize.expressions import normalize_expression_config
from ampla_project.normalize.flow import build_flow_graph
from ampla_project.normalize.links import build_link_from_to, resolve_item_links
from ampla_project.normalize.security import _parse_identity, normalize_security


def test_malformed_xml_raises_parse_error():
    with pytest.raises(XMLSyntaxError):
        fromstring("<Item id='1'><Property></Item>")


def test_normalization_context_default_display_order_for_version_boundary():
    root = fromstring(
        "<Project><Reference name='Citect.Ampla.StandardItems' version='4.2.0.0'/></Project>"
    )
    ctx = NormalizationContext(root, None)

    assert ctx.default_display_order == 50000

    root = fromstring(
        "<Project><Reference name='Citect.Ampla.StandardItems' version='4.1.9.9'/></Project>"
    )
    ctx = NormalizationContext(root, None)

    assert ctx.default_display_order == 0


def test_normalize_returns_defaults_when_references_are_missing():
    root = fromstring("<Project id='p'><Item id='A' name='A' type='Test'/></Project>")
    project = normalize(root, None)

    assert project.platform_version == "0.0"
    assert project.applications_version == "0.0"
    assert project.properties["id"] == "p"
    assert project.flow_graph == {"A": []}
    assert project.security["users"] == {}
    assert "00000000-0000-0000-0000-000000000000" in project.security["scopes"]


def test_property_without_name_attribute_raises_type_error():
    xml = """
    <Item id='1' name='Test' type='X'>
      <Property>Basic value</Property>
    </Item>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)
    prop = root.find("Property")

    from ampla_project.normalize.properties import normalize_property

    with pytest.raises(TypeError):
        normalize_property(ctx, root, prop)


def test_build_flow_graph_returns_empty_lists_for_no_links(fake_item):
    item_a = fake_item("A")
    item_b = fake_item("B")
    graph = build_flow_graph(None, {"A": item_a, "B": item_b})

    assert graph == {"A": [], "B": []}


def test_build_flow_graph_handles_circular_references(fake_item):
    item_a = fake_item(
        "A",
        properties={
            "Input": Property(
                name="Input",
                value=None,
                attributes={},
                item_links=[ItemLink(target_id="B", absolute_path=None)],
            )
        },
    )
    item_b = fake_item(
        "B",
        properties={
            "Input": Property(
                name="Input",
                value=None,
                attributes={},
                item_links=[ItemLink(target_id="A", absolute_path=None)],
            )
        },
    )
    graph = build_flow_graph(None, {"A": item_a, "B": item_b})

    assert graph == {"A": ["B"], "B": ["A"]}


def test_build_link_from_to_creates_reverse_links_for_cycle():
    item_a = Item(
        id="A",
        name="A",
        type="Test",
        full_name="A",
        hash="h1",
        definition=None,
        translation=None,
        properties={
            "Input": Property(
                name="Input",
                value=None,
                attributes={},
                item_links=[
                    ItemLink(target_id="B", absolute_path="B", property_name="Input")
                ],
            )
        },
    )
    item_b = Item(
        id="B",
        name="B",
        type="Test",
        full_name="B",
        hash="h2",
        definition=None,
        translation=None,
        properties={
            "Input": Property(
                name="Input",
                value=None,
                attributes={},
                item_links=[
                    ItemLink(target_id="A", absolute_path="A", property_name="Input")
                ],
            )
        },
    )

    build_link_from_to(None, {"A": item_a, "B": item_b})

    assert len(item_a.link_from) == 1
    assert item_a.link_from[0].target_id == "B"
    assert len(item_a.link_to) == 1
    assert item_a.link_to[0].target_id == "B"
    assert len(item_b.link_from) == 1
    assert item_b.link_from[0].target_id == "A"
    assert len(item_b.link_to) == 1
    assert item_b.link_to[0].target_id == "A"


def test_resolve_item_links_marks_broken_absolute_and_broken_target():
    root = fromstring("<Project></Project>")
    ctx = NormalizationContext(root, None)
    item_a = Item(
        id="A",
        name="A",
        type="Test",
        full_name="A",
        hash="h1",
        definition=None,
        translation=None,
        properties={
            "BrokenAbsolute": Property(
                name="BrokenAbsolute",
                value=None,
                attributes={},
                item_links=[
                    ItemLink(
                        target_id=None,
                        absolute_path="MissingPath",
                        relative_path="",
                        property_name="BrokenAbsolute",
                    )
                ],
            ),
            "BrokenTarget": Property(
                name="BrokenTarget",
                value=None,
                attributes={},
                item_links=[
                    ItemLink(
                        target_id="MissingId",
                        absolute_path=None,
                        relative_path="",
                        property_name="BrokenTarget",
                    )
                ],
            ),
        },
    )

    resolve_item_links(ctx, {"A": item_a})

    assert item_a.properties["BrokenAbsolute"].item_links[0].broken_absolute is True
    assert item_a.properties["BrokenTarget"].item_links[0].broken_target is True


def test_expression_config_with_missing_targetid_keeps_placeholder(context_factory):
    xml = """
    <Project>
      <Item id='A' name='A' type='Test'>
        <Property name='Check'>
          <HistoricalExpressionConfig>
            <ExpressionConfig format='sum(#ItemReference0#)'>
              <ItemLinkCollection>
                <ItemLink format='val(#ItemReference0#)' />
              </ItemLinkCollection>
            </ExpressionConfig>
          </HistoricalExpressionConfig>
        </Property>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    prop = root.find(".//Property")

    normalize_expression_config(ctx, prop)

    expr = prop.find(".//ExpressionConfig")
    assert expr.get("text") == "sum(#ItemReference0#)"
    link = expr.find(".//ItemLink")
    assert link.get("expressionFormat") == "val(#ItemReference0#)"


def test_expression_config_with_missing_item_target_inserts_missing_marker(
    context_factory,
):
    xml = """
    <Project>
      <Item id='A' name='A' type='Test'>
        <Property name='Check'>
          <HistoricalExpressionConfig>
            <ExpressionConfig format='sum(#ItemReference0#)'>
              <ItemLinkCollection>
                <ItemLink targetID='MissingItem' format='val(#ItemReference0#)' />
              </ItemLinkCollection>
            </ExpressionConfig>
          </HistoricalExpressionConfig>
        </Property>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    prop = root.find(".//Property")

    normalize_expression_config(ctx, prop)

    expr = prop.find(".//ExpressionConfig")
    assert expr.get("text") == "sum(Project.[Missing:MissingItem])"
    link = expr.find(".//ItemLink")
    assert link.get("expressionFormat") == "val(Project.[Missing:MissingItem])"


def test_resolve_class_association_marks_unknown_class_as_broken_target(
    context_factory,
):
    xml = """
    <Project>
      <Item id='1' name='Item1' type='Test'>
        <Property name='Class'>NonexistentClass</Property>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    item_elem = root.find("Item")
    item = Item(
        id="1",
        name="Item1",
        type="Test",
        full_name="Item1",
        hash=ctx.generate_hash("Item1"),
        definition=None,
        translation=None,
    )

    resolve_class_association(ctx, item_elem, item)

    class_prop = item.properties["Class"]
    assert class_prop.value == "NonexistentClass"
    assert class_prop.item_links[0].broken_target is True


def test_normalize_security_handles_no_users_and_returns_global_scope(context_factory):
    xml = """
    <Project>
      <Item id='A' name='A' type='Test' />
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    security = normalize_security(ctx, {})

    assert security["users"] == {}
    assert list(security["scopes"]) == ["00000000-0000-0000-0000-000000000000"]


def test_normalize_security_user_with_missing_identity_and_securityid(context_factory):
    xml = """
    <Project>
      <Item id='User1' name='User1' type='Citect.Ampla.StandardItems.User'>
        <Property name='DisplayOrder'>1</Property>
        <Property name='Authentication'>Local</Property>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    user_item = Item(
        id="User1",
        name="User1",
        type="Citect.Ampla.StandardItems.User",
        full_name="User1",
        hash=ctx.generate_hash("User1"),
        definition=None,
        translation=None,
        properties={
            "DisplayOrder": Property(
                name="DisplayOrder", value="1", attributes={}, item_links=[]
            ),
            "Authentication": Property(
                name="Authentication", value="Local", attributes={}, item_links=[]
            ),
            "SecurityID": Property(
                name="SecurityID", value="", attributes={}, item_links=[]
            ),
        },
    )

    security = normalize_security(ctx, {"User1": user_item})

    assert "User1" in security["users"]
    user = security["users"]["User1"]
    assert user.identity.account is None
    assert user.identity.sid is None
    assert user.security_id == ""


def test_normalization_context_loads_translations_and_returns_none_for_same_text():
    xml = """
    <Project>
      <Item id='A' name='Hello'/>
    </Project>
    """
    lang = """
    <html>
      <body>
        <div id='Hello'>Hello</div>
      </body>
    </html>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, fromstring(lang))

    assert ctx.get_translation("Hello") is None


def test_resolve_item_links_relative_path_finds_parent_and_this(context_factory):
    xml = """
    <Project>
      <Item id='Area' name='Area' type='X'>
        <Item id='Equipment' name='Equipment' type='X'>
          <Item id='Variable' name='Variable' type='X'>
            <Property name='Input'>
              <ItemLink relativePath='Parent.this' />
            </Property>
          </Item>
        </Item>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    item = Item(
        id="Variable",
        name="Variable",
        type="X",
        full_name="Area.Equipment.Variable",
        hash=ctx.generate_hash("Area.Equipment.Variable"),
        definition=None,
        translation=None,
        properties={
            "Input": Property(
                name="Input",
                value=None,
                attributes={},
                item_links=[
                    ItemLink(
                        target_id=None, absolute_path=None, relative_path="Parent.this"
                    )
                ],
            )
        },
    )
    ctx.items_by_id = {
        "Area": Item(
            id="Area",
            name="Area",
            type="X",
            full_name="Area",
            hash="h",
            definition=None,
            translation=None,
        ),
        "Area.Equipment": Item(
            id="Equipment",
            name="Equipment",
            type="X",
            full_name="Area.Equipment",
            hash="h",
            definition=None,
            translation=None,
        ),
        "Area.Equipment.Variable": item,
    }

    from ampla_project.normalize.links import _resolve_single_link

    _resolve_single_link(
        ctx, ctx.items_by_id, item, item.properties["Input"].item_links[0]
    )

    assert item.properties["Input"].item_links[0].target_id == "Equipment"
    assert item.properties["Input"].item_links[0].absolute_path == "Area.Equipment"


def test_resolve_item_links_marks_broken_relative_for_invalid_parent_depth(
    context_factory,
):
    xml = """
    <Project>
      <Item id='Root' name='Root' type='X'>
        <Item id='Leaf' name='Leaf' type='X'>
          <Property name='Input'>
            <ItemLink relativePath='Parent.Parent.Parent' />
          </Property>
        </Item>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    item = Item(
        id="Leaf",
        name="Leaf",
        type="X",
        full_name="Root.Leaf",
        hash=ctx.generate_hash("Root.Leaf"),
        definition=None,
        translation=None,
        properties={
            "Input": Property(
                name="Input",
                value=None,
                attributes={},
                item_links=[
                    ItemLink(
                        target_id=None,
                        absolute_path=None,
                        relative_path="Parent.Parent.Parent",
                    )
                ],
            )
        },
    )
    ctx.items_by_id = {
        "Root": Item(
            id="Root",
            name="Root",
            type="X",
            full_name="Root",
            hash="h",
            definition=None,
            translation=None,
        ),
        "Root.Leaf": item,
    }

    from ampla_project.normalize.links import _resolve_single_link

    _resolve_single_link(
        ctx, ctx.items_by_id, item, item.properties["Input"].item_links[0]
    )

    assert item.properties["Input"].item_links[0].broken_relative is True


def test_expression_config_brackets_non_ascii_item_names(context_factory):
    xml = """
    <Project>
      <Item id='A' name='Área' type='X' />
      <Item id='B' name='B' type='X'>
        <Property name='Check'>
          <HistoricalExpressionConfig>
            <ExpressionConfig format='sum(#ItemReference0#)'>
              <ItemLinkCollection>
                <ItemLink targetID='A' format='val(#ItemReference0#)' />
              </ItemLinkCollection>
            </ExpressionConfig>
          </HistoricalExpressionConfig>
        </Property>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = context_factory(root)
    ctx.items_by_id = {"A": root.find("Item[@id='A']"), "B": root.find("Item[@id='B']")}
    prop = root.find(".//Property")

    normalize_expression_config(ctx, prop)

    expr = prop.find(".//ExpressionConfig")
    assert expr.get("text") == "sum(Project.[Área])"
    assert expr.find(".//ItemLink").get("expressionFormat") == "val(Project.[Área])"


def test_build_link_from_to_does_not_build_reverse_link_for_missing_target():
    from ampla_project.normalize.links import build_link_from_to

    item_a = Item(
        id="A",
        name="A",
        type="X",
        full_name="A",
        hash="h1",
        definition=None,
        translation=None,
        properties={
            "Input": Property(
                name="Input",
                value=None,
                attributes={},
                item_links=[
                    ItemLink(
                        target_id="Missing",
                        absolute_path="Missing",
                        property_name="Input",
                    )
                ],
            )
        },
    )
    items = {"A": item_a}

    build_link_from_to(None, items)

    assert item_a.link_from[0].target_id == "Missing"
    assert item_a.link_to == []


def test_parse_identity_handles_empty_and_null_tokens():
    empty_identity = _parse_identity("")
    assert empty_identity.account is None
    assert empty_identity.sid is None
    assert empty_identity.raw == ""

    null_identity = _parse_identity("<NULL>|<NULL>")
    assert null_identity.account is None
    assert null_identity.sid is None
    assert null_identity.raw == "<NULL>|<NULL>"
