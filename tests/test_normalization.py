import json
from pathlib import Path

from lxml.etree import fromstring, parse

from ampla_project.normalize import normalize
from ampla_project.outputs.json import project_to_json


def load_xml(path):
    return parse(path).getroot()


def test_normalization_sample1():
    base = Path("tests/data/sample1")

    root = load_xml(base / "input.xml")
    lang = load_xml(base / "language.xml") if (base / "language.xml").exists() else None

    project = normalize(root, lang)
    result = project_to_json(project)

    expected = json.loads((base / "expected.json").read_text())

    assert result == expected


def test_normalize_resolves_class_associations_and_links():
    xml = """
    <Project>
      <ClassDefinition id="C1" name="Base" />
      <Item id="I1" name="Item1" type="X">
        <Property name="Class">Base</Property>
        <Property name="EquipmentTypes">Item2</Property>
      </Item>
      <Item id="I2" name="Item2" type="X" />
    </Project>
    """
    project = normalize(fromstring(xml), None)

    assert project.classes["C1"].name == "Base"
    assert project.items["I1"].properties["Class"].item_links[0].target_id == "C1"
    assert (
        project.items["I1"].properties["EquipmentTypes"].item_links[0].target_id == "I2"
    )
    assert project.flow_graph == {"I1": [], "I2": ["I1"]}


def test_normalize_loads_translations_from_language_document():
    xml = """
    <Project>
      <Item id="I1" name="Hello" type="X" />
    </Project>
    """
    lang = """
    <html>
      <body>
        <div id="Hello">Bonjour</div>
      </body>
    </html>
    """

    project = normalize(fromstring(xml), fromstring(lang))

    assert project.items["I1"].translation == "Bonjour"


def test_normalize_extracts_project_attributes_and_versions():
    xml = """
    <Project id="p" name="Project">
      <Reference name="Citect.Ampla.StandardItems" version="5.0.0.0" />
      <Reference name="Citect.Ampla.General.Server" version="6.1.0.0" />
    </Project>
    """
    project = normalize(fromstring(xml), None)

    assert project.platform_version == "5.0.0.0"
    assert project.applications_version == "6.1.0.0"
    assert project.properties["id"] == "p"
    assert project.properties["name"] == "Project"


def test_normalize_builds_nested_item_full_names_and_default_display_order():
    xml = """
    <Project>
      <Reference name="Citect.Ampla.StandardItems" version="4.2.0.0" />
      <Item id="A" name="Area" type="X">
        <Item id="B" name="Equipment" type="X" />
      </Item>
    </Project>
    """
    project = normalize(fromstring(xml), None)

    assert project.items["A"].full_name == "Area"
    assert project.items["B"].full_name == "Area.Equipment"
    assert project.items["A"].properties["DisplayOrder"].value == "50000"
    assert project.items["B"].properties["DisplayOrder"].value == "50000"
