from pathlib import Path

from lxml.etree import fromstring

from ampla_project.model.item import Item
from ampla_project.normalize import normalize
from ampla_project.normalize.classes import (
    get_class_full_name_by_id,
    normalize_classes,
    resolve_class_association,
)
from ampla_project.normalize.context import NormalizationContext
from ampla_project.outputs.json import project_to_json

PARITY_DATA = Path("tests/data/parity")


def load_parity_fixture(name):
    return fromstring((PARITY_DATA / name).read_bytes())


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


def test_multilevel_class_inheritance_preserves_nearest_and_all_ancestors():
    project = normalize(load_parity_fixture("class_inheritance.xml"))

    assert project.classes["base"].full_name == "Base"
    assert project.classes["derived"].full_name == "Base.Derived"
    assert project.classes["leaf"].full_name == "Base.Derived.Leaf"

    assert "(inherits)" not in project.classes["base"].properties
    assert [
        (link.target_id, link.absolute_path)
        for link in project.classes["derived"].properties["(inherits)"].item_links
    ] == [("base", "Base")]
    assert [
        (link.target_id, link.absolute_path)
        for link in project.classes["leaf"].properties["(inherits)"].item_links
    ] == [("derived", "Base.Derived"), ("base", "Base")]

    assert set(project.classes["base"].properties) == {"BaseOnly"}
    assert set(project.classes["derived"].properties) == {
        "BaseOnly",
        "DerivedOnly",
        "(inherits)",
    }
    assert set(project.classes["leaf"].properties) == {
        "BaseOnly",
        "DerivedOnly",
        "LeafOnly",
        "(inherits)",
    }
    assert set(project.classes["sibling"].properties) == {
        "BaseOnly",
        "DerivedOnly",
        "SiblingOnly",
        "(inherits)",
    }
    assert project.classes["derived"].properties["BaseOnly"].value == "base value"
    assert project.classes["leaf"].properties["DerivedOnly"].value == "2"
    assert "LeafOnly" not in project.classes["derived"].properties
    assert "SiblingOnly" not in project.classes["leaf"].properties


def test_class_inheritance_serialization_preserves_chain_and_property_ownership():
    project = normalize(load_parity_fixture("class_inheritance.xml"))
    data = project_to_json(project)

    assert data["classes"]["leaf"]["properties"]["(inherits)"]["item_links"] == [
        {
            "target_id": "derived",
            "absolute_path": "Base.Derived",
            "property_name": "(inherits)",
            "broken_target": False,
            "broken_absolute": False,
            "broken_relative": False,
            "event": None,
            "handler": None,
            "expression_match": None,
            "relative_path": None,
        },
        {
            "target_id": "base",
            "absolute_path": "Base",
            "property_name": "(inherits)",
            "broken_target": False,
            "broken_absolute": False,
            "broken_relative": False,
            "event": None,
            "handler": None,
            "expression_match": None,
            "relative_path": None,
        },
    ]
    assert "LeafOnly" not in data["classes"]["derived"]["properties"]
    assert data["classes"]["leaf"]["properties"]["BaseOnly"]["value"] == "base value"


def test_source_class_association_forms_resolve_to_class_links():
    project = normalize(load_parity_fixture("class_associations.xml"))

    direct = project.items["associated"].properties["ClassAssociation"]
    assert direct.attributes == {"class": "true"}
    assert [(link.target_id, link.absolute_path) for link in direct.item_links] == [
        ("derived", "Base.Derived")
    ]

    equipment = project.items["equipment"].properties["TargetEquipmentClass"]
    assert equipment.attributes["class"] == "true"
    assert [(link.target_id, link.absolute_path) for link in equipment.item_links] == [
        ("derived", "Base.Derived")
    ]

    named = project.items["named-class"].properties["Class"]
    assert [(link.target_id, link.absolute_path) for link in named.item_links] == [
        ("derived", "Base.Derived")
    ]

    element = project.items["element-class"].properties["Class"]
    assert [(link.target_id, link.absolute_path) for link in element.item_links] == [
        ("derived", "Base.Derived")
    ]

    ambiguous = project.items["ambiguous-class"].properties["Class"].item_links[0]
    assert ambiguous.target_id is None
    assert ambiguous.broken_target

    qualified = project.items["qualified-class"].properties["Class"].item_links[0]
    assert (qualified.target_id, qualified.absolute_path) == (
        "drive-b",
        "PlantB.Drive",
    )


def test_class_associations_serialize_through_project_model():
    project = normalize(load_parity_fixture("class_associations.xml"))
    data = project_to_json(project)

    direct = data["items"]["associated"]["properties"]["ClassAssociation"]
    assert direct["attributes"] == {"class": "true"}
    assert direct["item_links"][0]["target_id"] == "derived"
    assert direct["item_links"][0]["absolute_path"] == "Base.Derived"

    equipment = data["items"]["equipment"]["properties"]["TargetEquipmentClass"]
    assert equipment["attributes"]["class"] == "true"
    assert equipment["item_links"][0]["target_id"] == "derived"
