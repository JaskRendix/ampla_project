from lxml.etree import fromstring

from ampla_project.model.item import Item
from ampla_project.normalize.classes import (
    get_class_full_name_by_id,
    normalize_classes,
    resolve_class_association,
)
from ampla_project.normalize.context import NormalizationContext


def test_class_association_resolves():
    xml = """
    <Root>
      <ClassDefinition id="C1" name="Base" />
      <Item id="I1" name="X">
        <Property name="Class">Base</Property>
      </Item>
    </Root>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    item_elem = root.find("Item")
    item = Item(
        id="I1",
        name="X",
        type="T",
        full_name="X",
        hash="h",
        definition=None,
        translation=None,
    )

    resolve_class_association(ctx, item_elem, item)

    assert "Class" in item.properties
    assert item.properties["Class"].item_links[0].target_id == "C1"


def test_normalize_classes_builds_nested_classes_and_property_definitions():
    xml = """
    <Project>
      <ClassDefinition id="C1" name="Base" type="TypeA">
        <PropertyDefinition name="BaseProp">Value</PropertyDefinition>
        <ClassDefinition id="C2" name="Derived" type="TypeB">
          <PropertyDefinition name="DerivedProp">DerivedValue</PropertyDefinition>
        </ClassDefinition>
      </ClassDefinition>
    </Project>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    classes = normalize_classes(ctx)

    assert classes["C1"].full_name == "Base"
    assert classes["C1"].properties["BaseProp"].value == "Value"
    assert classes["C1"].children[0].id == "C2"
    assert classes["C1"].children[0].full_name == "Base.Derived"
    assert classes["C2"].properties["DerivedProp"].value == "DerivedValue"


def test_get_class_full_name_by_id_returns_none_for_missing_class():
    xml = "<Project></Project>"
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    assert get_class_full_name_by_id(ctx, "Missing") is None


def test_resolve_class_association_resolves_nested_class_full_name():
    xml = """
    <Project>
      <ClassDefinition id="C1" name="Base">
        <ClassDefinition id="C2" name="Derived" />
      </ClassDefinition>
      <Item id="I1" name="X">
        <Class>Base.Derived</Class>
      </Item>
    </Project>
    """
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)

    item_elem = root.find("Item")
    item = Item(
        id="I1",
        name="X",
        type="T",
        full_name="X",
        hash="h",
        definition=None,
        translation=None,
    )

    resolve_class_association(ctx, item_elem, item)

    assert item.properties["Class"].item_links[0].target_id == "C2"
    assert item.properties["Class"].value == "Base.Derived"


def test_resolve_class_association_skips_when_no_class_reference():
    xml = "<Project><Item id='I1' name='X'/></Project>"
    root = fromstring(xml)
    ctx = NormalizationContext(root, None)
    item_elem = root.find("Item")
    item = Item(
        id="I1",
        name="X",
        type="T",
        full_name="X",
        hash="h",
        definition=None,
        translation=None,
    )

    resolve_class_association(ctx, item_elem, item)

    assert "Class" not in item.properties
