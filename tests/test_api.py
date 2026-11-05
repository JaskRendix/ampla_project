from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

SAMPLE = str(Path("tests/data/sample1/input.xml"))


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_project():
    r = client.get("/project", params={"path": SAMPLE})
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, dict)

    assert "items" in data
    assert isinstance(data["items"], dict)

    assert "classes" in data
    assert isinstance(data["classes"], dict)

    assert "flow_graph" in data
    assert isinstance(data["flow_graph"], dict)

    assert "security" in data
    assert isinstance(data["security"], dict)
    assert "users" in data["security"]
    assert "scopes" in data["security"]

    assert "platform_version" in data
    assert isinstance(data["platform_version"], str)

    assert "applications_version" in data
    assert isinstance(data["applications_version"], str)

    assert "properties" in data
    assert isinstance(data["properties"], dict)


def test_project_api_exposes_source_compatible_flow_tree():
    path = str(Path("tests/data/parity/flow_cycle.xml").resolve())
    response = client.get("/project", params={"path": path})

    assert response.status_code == 200
    data = response.json()
    assert data["flow"][0]["item_id"] == "root"
    assert data["flow"][0]["links"][0]["property_name"] == "RootInput"
    assert data["flow_graph"] == {
        "root": ["cycle-a"],
        "cycle-a": ["cycle-b"],
        "cycle-b": ["cycle-a"],
    }
    flow_response = client.get("/flow", params={"path": path})
    assert flow_response.status_code == 200
    assert flow_response.json() == data["flow_graph"]


def test_project_api_serializes_item_id_fullname_type_mapping():
    path = str(Path("tests/data/parity/item_mapping.xml").resolve())
    response = client.get("/project", params={"path": path})

    assert response.status_code == 200
    rows = response.json()["item_id_fullname_type"]
    assert rows[0] == {
        "item_id": "class-base",
        "full_name": "BaseClass",
        "type": "Example.Base",
    }
    assert rows[-1] == {
        "item_id": "standalone",
        "full_name": "Standalone",
        "type": "Example.Standalone",
    }


def test_items():
    r = client.get("/items", params={"path": SAMPLE})
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, dict)
    if items:
        any_id = next(iter(items))
        r2 = client.get(f"/items/{any_id}", params={"path": SAMPLE})
        assert r2.status_code == 200
        assert r2.json()["id"] == any_id


def test_classes():
    r = client.get("/classes", params={"path": SAMPLE})
    assert r.status_code == 200
    classes = r.json()
    assert isinstance(classes, dict)
    # sample1 has no classes, so no iteration


def test_flow():
    r = client.get("/flow", params={"path": SAMPLE})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_links():
    r = client.get("/links", params={"path": SAMPLE})
    assert r.status_code == 200
    links = r.json()
    assert isinstance(links, dict)
    for v in links.values():
        assert "link_from" in v
        assert "link_to" in v


def test_security():
    r = client.get("/security", params={"path": SAMPLE})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_security_api_preserves_source_user_and_scope_ordering():
    path = str(Path("tests/data/parity/security_ordering.xml").resolve())
    expected_user_ids = [
        "user-first",
        "user-second",
        "user-zed",
        "user-alpha",
        "user-zulu",
        "user-ten",
    ]
    expected_scope_ids = [
        "00000000-0000-0000-0000-000000000000",
        "scope-first",
        "scope-second",
        "scope-zed",
        "scope-alpha",
        "scope-zulu",
        "scope-ten",
    ]

    project_response = client.get("/project", params={"path": path})
    security_response = client.get("/security", params={"path": path})

    assert project_response.status_code == 200
    assert security_response.status_code == 200
    project_security = project_response.json()["security"]
    security = security_response.json()
    assert security == project_security
    assert list(security["users"]) == expected_user_ids
    assert list(security["scopes"]) == expected_scope_ids


def test_metrics():
    r = client.get("/metrics", params={"path": SAMPLE})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_api_preserves_nested_property_links():
    path = str(Path("tests/data/parity/nested_property_links.xml").resolve())

    project_response = client.get("/project", params={"path": path})
    assert project_response.status_code == 200
    project_data = project_response.json()
    inputs = project_data["items"]["source"]["properties"]["Inputs"]
    assert [link["target_id"] for link in inputs["item_links"]] == [
        "target",
        "other",
        "area",
        None,
        None,
    ]
    assert inputs["extra_xml"]["children"][0]["tag"] == "ItemLinkCollection"
    assert project_data["flow_graph"]["target"] == ["source", "source"]

    items_response = client.get("/items/source", params={"path": path})
    assert items_response.status_code == 200
    assert items_response.json()["properties"]["Inputs"]["item_links"] == (
        inputs["item_links"]
    )

    links_response = client.get("/links", params={"path": path})
    assert links_response.status_code == 200
    assert links_response.json()["source"]["link_from"] == [
        "target",
        "other",
        "area",
        None,
        None,
        "target",
    ]


def test_classes_api_preserves_inheritance_and_associations():
    path = str(Path("tests/data/parity/class_inheritance.xml").resolve())
    response = client.get("/classes", params={"path": path})

    assert response.status_code == 200
    classes = response.json()
    assert [
        link["target_id"]
        for link in classes["leaf"]["properties"]["(inherits)"]["item_links"]
    ] == ["derived", "base"]
    assert "LeafOnly" not in classes["derived"]["properties"]

    association_path = str(Path("tests/data/parity/class_associations.xml").resolve())
    item_response = client.get("/items/associated", params={"path": association_path})
    assert item_response.status_code == 200
    assert (
        item_response.json()["properties"]["ClassAssociation"]["item_links"][0][
            "absolute_path"
        ]
        == "Base.Derived"
    )
    equipment_response = client.get(
        "/items/equipment", params={"path": association_path}
    )
    assert equipment_response.status_code == 200
    assert (
        equipment_response.json()["properties"]["TargetEquipmentClass"]["item_links"][
            0
        ]["target_id"]
        == "derived"
    )


def test_api_exposes_source_specific_item_normalization():
    path = str(Path("tests/data/parity/source_specific_items.xml").resolve())
    response = client.get("/project", params={"path": path})

    assert response.status_code == 200
    data = response.json()
    assert [
        entry["name"] for entry in data["items"]["matrix"]["decision_matrix_inputs"]
    ] == [
        "InputA",
        "InputB",
    ]
    assert data["items"]["resolver"]["properties"]["Action"]["value"] == "Module"
    assert (
        data["items"]["adapter"]["properties"]["ConnectionString"]["extra_xml"][
            "children"
        ][0]["tag"]
        == "soap-property"
    )
    item_response = client.get("/items/matrix", params={"path": path})
    assert item_response.status_code == 200
    assert [
        entry["name"] for entry in item_response.json()["decision_matrix_inputs"]
    ] == [
        "InputA",
        "InputB",
    ]


def test_project_and_security_api_merge_authstore_data():
    project_path = str(Path("tests/data/parity/authstore_project.xml").resolve())
    authstore_path = str(Path("tests/data/parity/authstore.xml").resolve())
    params = {"path": project_path, "authstore_path": authstore_path}

    project_response = client.get("/project", params=params)
    assert project_response.status_code == 200
    project_security = project_response.json()["security"]
    assert project_security["role_definitions"]["role-editor"]["operations"] == [
        "Write"
    ]
    assert project_security["scopes"]["scope-one"]["roles"][0]["role_id"] == "role-base"

    security_response = client.get("/security", params=params)
    assert security_response.status_code == 200
    assert security_response.json() == project_security


def test_project_api_accepts_optional_translation_language():
    project_path = str(Path("tests/data/parity/translations_project.xml").resolve())
    language_path = str(Path("tests/data/parity/language_fr.html").resolve())

    response = client.get(
        "/project", params={"path": project_path, "language_path": language_path}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"]["translated"]["translation"] == "Pompe centrifuge"
    assert data["items"]["translated"]["properties"]["DisplayName"]["value"] == (
        "Pompe centrifuge"
    )
    assert data["classes"]["base"]["translation"] == "Classe de base"


def test_project_api_exposes_expression_dependency_model():
    path = str(Path("tests/data/parity/expression_dependencies.xml").resolve())
    response = client.get("/project", params={"path": path})

    assert response.status_code == 200
    expression_model = response.json()["expression_model"]
    assert expression_model["expression_item_ids"] == ["source-a", "calculated"]
    assert expression_model["source_item_ids"] == ["source-a", "source-b"]
    assert expression_model["dependencies"][3]["resolved"] is False
    assert expression_model["streams"][0]["item_id"] == "source-a"
