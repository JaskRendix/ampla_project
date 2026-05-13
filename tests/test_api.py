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


def test_metrics():
    r = client.get("/metrics", params={"path": SAMPLE})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
