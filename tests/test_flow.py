from pathlib import Path

from ampla_project.normalize import normalize
from ampla_project.normalize.flow import build_flow_graph
from ampla_project.outputs.json import project_to_json
from tests.utils.fakes import FakeItem, FakeItemLink, FakeProperty


def test_flow_direction():
    # B → A
    A = FakeItem(
        "A",
        properties={
            "Input": FakeProperty("Input", item_links=[FakeItemLink(target_id="B")])
        },
    )
    B = FakeItem("B")

    items = {"A": A, "B": B}
    graph = build_flow_graph(None, items)

    assert graph["B"] == ["A"]


def test_build_flow_graph_returns_empty_dictionary_for_no_items():
    graph = build_flow_graph(None, {})

    assert graph == {}


def test_build_flow_graph_ignores_links_with_no_target():
    item_a = FakeItem(
        "A",
        properties={
            "Input": FakeProperty("Input", item_links=[FakeItemLink(target_id=None)])
        },
    )
    item_b = FakeItem("B")

    graph = build_flow_graph(None, {"A": item_a, "B": item_b})

    assert graph == {"A": [], "B": []}


def test_build_flow_graph_handles_multiple_consumers():
    item_a = FakeItem(
        "A",
        properties={
            "Input1": FakeProperty("Input1", item_links=[FakeItemLink(target_id="B")]),
            "Input2": FakeProperty("Input2", item_links=[FakeItemLink(target_id="C")]),
        },
    )
    item_b = FakeItem("B")
    item_c = FakeItem("C")

    graph = build_flow_graph(None, {"A": item_a, "B": item_b, "C": item_c})

    assert graph["B"] == ["A"]
    assert graph["C"] == ["A"]


def test_build_flow_graph_preserves_duplicate_links():
    item_a = FakeItem(
        "A",
        properties={
            "Input": FakeProperty(
                "Input",
                item_links=[FakeItemLink(target_id="B"), FakeItemLink(target_id="B")],
            )
        },
    )
    item_b = FakeItem("B")

    graph = build_flow_graph(None, {"A": item_a, "B": item_b})

    assert graph["B"] == ["A", "A"]


def test_flow_tree_matches_source_root_order_branching_and_link_metadata():
    root = load_flow_fixture("flow_branching.xml")
    project = normalize(root)
    flow = project_to_json(project)["flow"]

    assert flow == [
        {
            "item_id": "root-a",
            "name": "Zeta",
            "type": "Source.A",
            "full_name": "Zeta",
            "hash": project.items["root-a"].hash,
            "definition": None,
            "translation": None,
            "links": [
                {
                    "property_name": "RootInput",
                    "item": {
                        "item_id": "child-a",
                        "name": "ChildA",
                        "type": "Consumer",
                        "full_name": "ChildA",
                        "hash": project.items["child-a"].hash,
                        "definition": None,
                        "translation": None,
                        "links": [],
                    },
                }
            ],
        },
        {
            "item_id": "root-z",
            "name": "Alpha",
            "type": "Source.Z",
            "full_name": "Alpha",
            "hash": project.items["root-z"].hash,
            "definition": None,
            "translation": None,
            "links": [
                {
                    "property_name": "SecondInput",
                    "item": {
                        "item_id": "child-b",
                        "name": "ChildB",
                        "type": "Consumer",
                        "full_name": "ChildB",
                        "hash": project.items["child-b"].hash,
                        "definition": None,
                        "translation": None,
                        "links": [],
                    },
                },
                {
                    "property_name": "FirstInput",
                    "item": {
                        "item_id": "child-b",
                        "name": "ChildB",
                        "type": "Consumer",
                        "full_name": "ChildB",
                        "hash": project.items["child-b"].hash,
                        "definition": None,
                        "translation": None,
                        "links": [],
                    },
                },
            ],
        },
    ]
    assert project.flow_graph["root-z"] == ["child-b", "child-b"]
    assert "grandchild" in project.flow_graph["child-b"]
    assert all(
        link["item"]["item_id"] != "grandchild"
        for root_item in flow
        for link in root_item["links"]
    )
    assert project_to_json(project)["flow"] == flow


def test_flow_tree_uses_source_root_selection_and_terminates_cycles():
    project = normalize(load_flow_fixture("flow_cycle.xml"))
    flow = project_to_json(project)["flow"]

    assert [root["item_id"] for root in flow] == ["root"]
    assert flow[0]["links"] == [
        {
            "property_name": "RootInput",
            "item": {
                "item_id": "cycle-a",
                "name": "CycleA",
                "type": "Node",
                "full_name": "CycleA",
                "hash": project.items["cycle-a"].hash,
                "definition": None,
                "translation": None,
                "links": [],
            },
        }
    ]
    assert project.flow_graph == {
        "root": ["cycle-a"],
        "cycle-a": ["cycle-b"],
        "cycle-b": ["cycle-a"],
    }


def test_flow_roots_are_sorted_by_type_then_full_name():
    project = normalize(load_flow_fixture("flow_root_ordering.xml"))
    flow = project_to_json(project)["flow"]

    assert [root["item_id"] for root in flow] == [
        "root-first",
        "root-a",
        "root-z",
    ]


def load_flow_fixture(name: str):
    from lxml.etree import parse

    return parse(Path("tests/data/parity") / name).getroot()
