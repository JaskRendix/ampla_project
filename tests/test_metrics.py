from ampla_project.model.item import Item, ItemLink, Property
from ampla_project.model.security import Identity, SecurityUser
from ampla_project.normalize.metrics import calculate_metrics


def make_item(
    item_id,
    type_="TypeA",
    full_name=None,
    children=None,
    link_from=None,
    link_to=None,
    properties=None,
):
    return Item(
        id=item_id,
        name=item_id,
        type=type_,
        full_name=full_name or item_id,
        hash=f"h:{item_id}",
        definition=None,
        translation=None,
        properties=properties or {},
        children=children or [],
        link_from=link_from or [],
        link_to=link_to or [],
    )


def make_class(class_id, name, parent=None):
    props = {}
    if parent:
        props["Parent"] = Property(name="Parent", value=parent, attributes={})
    return Item(
        id=class_id,
        name=name,
        type="Class",
        full_name=name,
        hash=f"h:{name}",
        definition=None,
        translation=None,
        properties=props,
        is_class=True,
    )


def make_user(user_id):
    return SecurityUser(
        id=user_id,
        name=user_id,
        full_name=user_id,
        display_order=0,
        authentication=None,
        identity=Identity(account=None, sid=None, raw=""),
        security_id=None,
    )


def test_item_counts():
    items = {
        "A": make_item("A", type_="T1"),
        "B": make_item("B", type_="T1"),
        "C": make_item("C", type_="T2"),
    }
    classes = {}
    security = {"users": {}}

    m = calculate_metrics(items, classes, security)

    assert m.item_counts == {"T1": 2, "T2": 1}


def test_total_links_and_broken_links():
    link1 = ItemLink(target_id="B", absolute_path="B")
    link2 = ItemLink(target_id=None, absolute_path=None, broken_target=True)

    items = {
        "A": make_item("A", link_from=[link1, link2]),
        "B": make_item("B"),
    }
    classes = {}
    security = {"users": {}}

    m = calculate_metrics(items, classes, security)

    assert m.total_links == 2
    assert m.broken_links_count == 1


def test_orphan_detection():
    # A → B, C is orphan
    link = ItemLink(target_id="B", absolute_path="B")
    items = {
        "A": make_item("A", link_from=[link]),
        "B": make_item("B", link_to=[link]),
        "C": make_item("C"),  # orphan
    }
    classes = {}
    security = {"users": {}}

    m = calculate_metrics(items, classes, security)

    assert m.orphaned_items_count == 1


def test_class_counts():
    classes = {
        "C1": make_class("C1", "ClassA"),
        "C2": make_class("C2", "ClassB"),
        "C3": make_class("C3", "ClassB"),
    }
    items = {}
    security = {"users": {}}

    m = calculate_metrics(items, classes, security)

    assert m.class_counts == {"Class": 3}


def test_unused_classes():
    classes = {
        "C1": make_class("C1", "ClassA"),
        "C2": make_class("C2", "ClassB"),
    }
    items = {
        "I1": make_item("I1", type_="ClassA"),
    }
    security = {"users": {}}

    m = calculate_metrics(items, classes, security)

    assert m.unused_classes_count == 1  # ClassB unused


def test_inheritance_depth():
    # ClassA → ClassB → ClassC
    classes = {
        "A": make_class("A", "ClassA", parent="ClassB"),
        "B": make_class("B", "ClassB", parent="ClassC"),
        "C": make_class("C", "ClassC"),
    }
    items = {}
    security = {"users": {}}

    m = calculate_metrics(items, classes, security)

    assert m.class_inheritance_depth_max == 2  # A → B → C


def test_inheritance_cycle_detection():
    # A → B → A (cycle)
    classes = {
        "A": make_class("A", "ClassA", parent="ClassB"),
        "B": make_class("B", "ClassB", parent="ClassA"),
    }
    items = {}
    security = {"users": {}}

    m = calculate_metrics(items, classes, security)

    assert m.class_inheritance_cycles == 1
    assert m.class_inheritance_depth_max == 0  # no valid depth


def test_user_roles_count():
    users = {
        "u1": make_user("u1"),
        "u2": make_user("u2"),
    }
    items = {}
    classes = {}

    m = calculate_metrics(items, classes, {"users": users})

    assert m.user_roles_count == 2


def test_empty_inputs():
    m = calculate_metrics({}, {}, {"users": {}})

    assert m.item_counts == {}
    assert m.total_links == 0
    assert m.broken_links_count == 0
    assert m.orphaned_items_count == 0
    assert m.class_counts == {}
    assert m.unused_classes_count == 0
    assert m.class_inheritance_depth_max == 0
    assert m.class_inheritance_cycles == 0
    assert m.user_roles_count == 0


def test_item_with_children_not_orphan():
    child = make_item("Child")
    parent = make_item("Parent", children=[child])

    m = calculate_metrics({"P": parent, "C": child}, {}, {"users": {}})

    assert m.orphaned_items_count == 0
