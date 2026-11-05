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


def test_translation_injection_matches_source_and_preserves_fallbacks():
    root = load_xml(Path("tests/data/parity/translations_project.xml"))
    language = load_xml(Path("tests/data/parity/language_fr.html"))

    project = normalize(root, language)

    assert project.items["translated"].translation == "Pompe centrifuge"
    assert project.items["translated"].properties["DisplayName"].value == (
        "Pompe centrifuge"
    )
    assert project.items["preexisting"].translation == "Vanne"
    assert project.items["preexisting"].properties["DisplayName"].value == (
        "Source Display"
    )
    assert project.items["unsupported"].translation == "Dossier"
    assert "DisplayName" not in project.items["unsupported"].properties
    assert project.items["same"].translation is None
    assert project.items["empty"].translation is None
    assert project.items["fallback"].translation is None
    assert project.classes["base"].translation == "Classe de base"
    assert "DisplayName" not in project.classes["base"].properties
    assert project.items["translated"].properties["Input"].value == "Plant.Sensor"


def test_translation_serialization_is_additive_and_language_specific():
    root = load_xml(Path("tests/data/parity/translations_project.xml"))
    french = normalize(root, load_xml(Path("tests/data/parity/language_fr.html")))
    english = normalize(root, load_xml(Path("tests/data/parity/language_en.html")))
    french_data = project_to_json(french)
    english_data = project_to_json(english)

    assert french_data["items"]["translated"]["translation"] == "Pompe centrifuge"
    assert french_data["items"]["translated"]["properties"]["DisplayName"] == {
        "name": "DisplayName",
        "value": "Pompe centrifuge",
        "attributes": {},
        "item_links": [],
        "extra_xml": None,
    }
    assert english_data["items"]["translated"]["translation"] is None
    assert "DisplayName" not in english_data["items"]["translated"]["properties"]
    assert french_data["classes"]["base"]["translation"] == "Classe de base"


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


def test_nested_property_links_match_parity_fixture_and_serialize():
    base = Path("tests/data/parity")
    project = normalize(load_xml(base / "nested_property_links.xml"), None)
    serialized = project_to_json(project)
    expected = json.loads((base / "nested_property_links_expected.json").read_text())

    source = project.items["source"]
    serialized_inputs = serialized["items"]["source"]["properties"]["Inputs"]

    assert [
        link.target_id for link in source.properties["Inputs"].item_links
    ] == expected["link_targets"]
    assert [link.absolute_path for link in source.properties["Inputs"].item_links] == (
        expected["link_paths"]
    )
    assert source.properties["Inputs"].item_links[0].property_name == "Inputs"
    assert source.properties["Inputs"].item_links[0].target_id == "target"
    assert source.properties["Inputs"].item_links[1].target_id == "other"
    assert source.properties["Inputs"].item_links[2].target_id == "area"
    assert source.properties["Inputs"].item_links[3].broken_absolute
    assert source.properties["Inputs"].item_links[4].broken_relative
    assert (
        source.properties["FormulaSource"].item_links[0].target_id
        == expected["formula_source_link"]["target_id"]
    )
    assert source.properties["DeriveSpecificationFrom"].item_links == []

    assert project.items["source"].link_from == (
        source.properties["Inputs"].item_links
        + source.properties["FormulaSource"].item_links
    )
    assert [link.target_id for link in project.items["target"].link_to] == [
        "source",
        "source",
    ]
    assert project.flow_graph == expected["flow_graph"]
    assert project.metrics.total_links == 6
    assert project.metrics.broken_links_count == 2
    assert [
        (
            link["target_id"],
            link["absolute_path"],
            link["property_name"],
        )
        for link in serialized_inputs["item_links"]
    ] == [
        (target_id, path, "Inputs")
        for target_id, path in zip(
            expected["link_targets"], expected["link_paths"], strict=True
        )
    ]
    assert serialized_inputs["extra_xml"] == expected["preserved_inputs_xml"]


def test_source_specific_item_transforms_match_parity_fixture():
    project = normalize(load_xml(Path("tests/data/parity/source_specific_items.xml")))

    matrix = project.items["matrix"]
    assert "RunState" not in matrix.properties
    assert [entry.name for entry in matrix.decision_matrix_inputs] == [
        "InputA",
        "InputB",
    ]
    assert [
        (
            entry.item_link.target_id,
            entry.item_link.absolute_path,
            entry.display_order,
        )
        for entry in matrix.decision_matrix_inputs
    ] == [
        ("input-a", "Matrix.InputA", "7"),
        ("input-b", "Matrix.InputB", "50000"),
    ]

    rule = project.items["rule"]
    assert "DisplayOrderIndex" not in rule.properties
    assert [
        (
            entry.name,
            entry.value,
            entry.display_order,
            entry.item_link.target_id,
        )
        for entry in rule.decision_matrix_input_rules
    ] == [
        ("InputA", "True", "7", "input-a"),
        ("InputB", "Ignore", "50000", "input-b"),
    ]
    assert rule.properties["DisplayOrder"].value == "50000"

    assert project.items["resolver"].properties["Action"].value == "Module"
    assert project.items["resolver"].properties["ResolverOperation"].value == "Sum"
    assert project.items["user"].properties["Authentication"].value == (
        "WindowsIntegrated"
    )
    assert project.security["users"]["user"].authentication == "WindowsIntegrated"
    assert (
        project.items["oledb-variable"].properties["SampleTypeCode"].value == "Double"
    )
    assert project.items["oledb-default"].properties["SampleTypeCode"].value == "Single"
    assert "DataSource" not in project.items["oledb-variable"].properties
    assert "DataSource" not in project.items["ordinary"].properties
    assert "RunState" not in project.items["ordinary"].properties
    assert "Definition" not in project.items["defined-item"].properties
    assert project.items["defined-item"].definition == "DefinitionTarget"

    adapter_property = project.items["adapter"].properties["ConnectionString"]
    assert adapter_property.value is None
    assert adapter_property.attributes == {"isSoap": "true"}
    assert adapter_property.extra_xml["children"] == [
        {
            "tag": "soap-property",
            "attributes": {"name": "Server"},
            "text": "db.example",
            "tail": None,
            "children": [],
        },
        {
            "tag": "soap-property",
            "attributes": {"name": "Database"},
            "text": "plant",
            "tail": None,
            "children": [],
        },
    ]

    empty_soap = project.items["empty-adapter"].properties["ConnectionString"]
    assert empty_soap.value == "{SOAP}"


def test_source_specific_items_serialize_without_changing_existing_fields():
    project = normalize(load_xml(Path("tests/data/parity/source_specific_items.xml")))
    data = project_to_json(project)
    matrix = data["items"]["matrix"]

    assert matrix["decision_matrix_inputs"] == [
        {
            "id": "input-a",
            "name": "InputA",
            "hash": project.items["input-a"].hash,
            "translation": None,
            "display_order": "7",
            "item_link": {
                "target_id": "input-a",
                "absolute_path": "Matrix.InputA",
                "property_name": None,
                "broken_target": False,
                "broken_absolute": False,
                "broken_relative": False,
                "event": None,
                "handler": None,
                "expression_match": None,
                "relative_path": None,
            },
        },
        {
            "id": "input-b",
            "name": "InputB",
            "hash": project.items["input-b"].hash,
            "translation": None,
            "display_order": "50000",
            "item_link": {
                "target_id": "input-b",
                "absolute_path": "Matrix.InputB",
                "property_name": None,
                "broken_target": False,
                "broken_absolute": False,
                "broken_relative": False,
                "event": None,
                "handler": None,
                "expression_match": None,
                "relative_path": None,
            },
        },
    ]
    assert data["items"]["rule"]["decision_matrix_input_rules"][0] == {
        "name": "InputA",
        "display_order": "7",
        "value": "True",
        "item_link": {
            "target_id": "input-a",
            "absolute_path": "Matrix.InputA",
            "property_name": None,
            "broken_target": False,
            "broken_absolute": False,
            "broken_relative": False,
            "event": None,
            "handler": None,
            "expression_match": None,
            "relative_path": None,
        },
    }
    assert (
        data["items"]["adapter"]["properties"]["ConnectionString"]["extra_xml"][
            "children"
        ][0]["tag"]
        == "soap-property"
    )


def test_favorite_and_subscription_property_transforms_match_source_shape():
    project = normalize(
        load_xml(Path("tests/data/parity/source_specific_properties.xml"))
    )
    properties = project.items["favorites"].properties

    assert properties["Home"].value == "{1 Favourite(s)}"
    assert properties["Home"].attributes == {}
    assert properties["Home"].extra_xml["children"][1] == {
        "tag": "Favorite",
        "attributes": {
            "name": "Home view",
            "module": "Production",
            "location": "Plant.Area",
            "view": "Overview",
        },
        "text": None,
        "tail": None,
        "children": [],
    }

    favorites = properties["Favorites"]
    assert favorites.value == "{1 Favourite(s)}"
    assert favorites.attributes == {}
    assert favorites.extra_xml["children"][1] == {
        "tag": "Favorites",
        "attributes": {"name": "My Favorites"},
        "text": None,
        "tail": None,
        "children": [
            {
                "tag": "Favorite",
                "attributes": {
                    "name": "Pump downtime",
                    "module": "Downtime",
                    "filter": "Status=Down",
                    "location": "Plant.Area.Pump",
                },
                "text": None,
                "tail": None,
                "children": [],
            }
        ],
    }
    assert project.items["empty-favorites"].properties["Favorites"].value == (
        "{0 Favorite(s)}"
    )
    assert properties["MySubscription"].value == "unfinished|/Plant/Area"
    assert properties["MySubscription"].item_links == []
    serialized = project_to_json(project)
    assert (
        serialized["items"]["favorites"]["properties"]["Favorites"]["extra_xml"]
        == favorites.extra_xml
    )
