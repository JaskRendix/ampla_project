from ampla_project.normalize.flow import build_flow_graph
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
